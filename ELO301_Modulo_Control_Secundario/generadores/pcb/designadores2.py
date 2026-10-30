"""Designadores contra la geometría real: fuera de courtyards, a 0,26 mm de toda serigrafía y de otros textos y a
0,17 mm de las aberturas de máscara; se mueven por su punto de ubicación (la caja de Altium queda vieja tras cambiar el
tamaño). Los que no caben se ocultan; tras el DRC se ocultan también los que sigan chocando. Quita además la vía aislada
que quedó junto a U6-8."""
import contextlib, io, json, sys
from drc_comun import *
sys.path.insert(0, '/mnt/hdd-viejo-ro/S2-2026/MATERIA/ELO301-Diseno-Equipos-Electronicos/altium/pcb')
with contextlib.redirect_stderr(io.StringIO()):
    import colocacion as col

geo, pads = json.load(open('/tmp/geometria.json')), json.load(open('/tmp/pads.json'))
cajas = {d: col.caja_colocada(d) for d in col.X}
cara = {d: col.X[d][3] for d in col.X}
tht = {d for d in col.X if col.HUELLA[d] in col.THT}
dist = lambda a, b: ((max(b[0] - a[1], a[0] - b[1], 0)) ** 2 + (max(b[2] - a[3], a[2] - b[3], 0)) ** 2) ** 0.5
solapa = lambda a, b, m: a[0] < b[1] + m and b[0] < a[1] + m and a[2] < b[3] + m and b[2] < a[3] + m
textos = {x[0]: x for x in geo['D']}

def libre(b, d, lado, puestos):
    if b[0] < 0.3 or b[2] < 0.3 or b[1] > 69.7 or b[3] > 49.7:
        return False
    capa = 'Top Overlay' if lado == 'top' else 'Bottom Overlay'
    if any(s[0] == capa and solapa(b, (s[1], s[3], s[2], s[4]), 0.26) for s in geo['S']):
        return False
    if any((p['capa'] == 'Multi Layer' or (p['capa'] == 'Top Layer') == (lado == 'top')) and solapa(b, (p['caja'][0], p['caja'][2], p['caja'][1], p['caja'][3]), 0.17) for p in pads):
        return False
    if any((cara[o] == lado or o in tht) and solapa(b, cajas[o], 0.05) for o in cajas):
        return False
    return not any(cara[o] == lado and solapa(b, q, 0.26) for o, q in puestos.items())

def candidatos(d, w, h):
    x0, x1, y0, y1 = cajas[d]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for g in (0.08, 0.3, 0.6, 1.0):
        for xa in (cx - w / 2, x0, x1 - w):
            yield (xa, xa + w, y1 + g, y1 + g + h)
            yield (xa, xa + w, y0 - g - h, y0 - g)
        for ya in (cy - h / 2, y1 - h, y0):
            yield (x1 + g, x1 + g + w, ya, ya + h)
            yield (x0 - g - w, x0 - g, ya, ya + h)

puestos, ocultos = {}, []
for d in sorted(cajas, key=lambda d: -(cajas[d][1] - cajas[d][0]) * (cajas[d][3] - cajas[d][2])):
    t = textos[d]
    if cara[d] == 'bottom':
        continue                                             # J1: su texto queda en la serigrafía inferior, donde está
    w, h = t[5] - t[3], t[6] - t[4]
    b = next((b for b in candidatos(d, w, h) if libre(b, d, cara[d], puestos)), None)
    if b:
        puestos[d] = b
    else:
        ocultos.append(d)
print(f'ubicados {len(puestos)}, ocultos {len(ocultos)}: {" ".join(sorted(ocultos))}')

mover = ''.join(f"C := Board.GetPcbComponentByRefDes('{d}'); C.NameOn := True; C.Name.MoveToXY(Board.XOrigin + MMsToCoord({b[0] + 0.15:.3f}), Board.YOrigin + MMsToCoord({b[2] + 0.15:.3f}));\n"
                for d, b in puestos.items())
ocultar = ''.join(f"C := Board.GetPcbComponentByRefDes('{d}'); C.NameOn := False;\n" for d in ocultos)
r = correr(f"""{VARS}    T : IDispatch;
    Chocan : TStringList;
{ABRIR}Lista := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eViaObject, eTrackObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do
begin
    if X.ObjectId = eViaObject then
    begin
        if (Abs(CoordToMMs(X.x - Board.XOrigin) - 50.92) < 0.05) and (Abs(CoordToMMs(X.y - Board.YOrigin) - 29.70) < 0.05) then Lista.Add(X);
    end
    else if (not X.InComponent) and (X.Net <> nil) then
        if (X.Net.Name = 'V3V3_SENS') and (Abs(CoordToMMs(X.y1 - Board.YOrigin) - 29.70) < 0.02) and (Abs(CoordToMMs(X.y2 - Board.YOrigin) - 29.70) < 0.02)
           and (Abs(CoordToMMs(X.x1 - Board.XOrigin) - 50.92) < 0.05) then Lista.Add(X);
    X := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
PCBServer.PreProcess;
try
    for i := 0 to Lista.Count - 1 do Board.RemovePCBObject(Lista.Items[i]);
{mover}{ocultar}finally
    PCBServer.PostProcess;
end;
s := 'via y tramo aislados quitados: ' + IntToStr(Lista.Count);
Board.RunBatchDesignRuleCheck('C:\\Users\\Public\\drc_elo301.html', 0, False, False);
Chocan := TStringList.Create;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eViolationObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
V := It.FirstPCBObject;
while V <> nil do
begin
    nom := '';
    try nom := V.Rule.Name; except end;
    if (nom = 'SilkToSilkClearance') or (nom = 'SilkToSolderMaskClearance') then
    begin
        T := V.Primitive1;
        if (T <> nil) and (T.ObjectId = eTextObject) then if T.IsDesignator then if Chocan.IndexOf(T.Text) < 0 then Chocan.Add(T.Text);
        T := V.Primitive2;
        if (T <> nil) and (T.ObjectId = eTextObject) then if T.IsDesignator then if Chocan.IndexOf(T.Text) < 0 then Chocan.Add(T.Text);
    end;
    V := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
PCBServer.PreProcess;
try
    for i := 0 to Chocan.Count - 1 do begin C := Board.GetPcbComponentByRefDes(Chocan[i]); C.NameOn := False; end;
finally
    PCBServer.PostProcess;
end;
s := s + #10 + 'designadores que aun chocaban (ocultos): ' + Chocan.CommaText;
Board.ViewManager_FullUpdate;
{GUARDAR}{RESUMEN}ResultText := s;""")
print('\n'.join(r.split('\n')[:2]))
por = resumen(r, 'DRC final')
json.dump(por, open('/tmp/drc.json', 'w'), ensure_ascii=False)
print('guardado:', hora_pcb())
