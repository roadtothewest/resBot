"""Pasa el esquemático plano (etiquetas de red globales) a jerárquico con una hoja superior de módulos.

Se corre UNA vez sobre las hojas planas, con Altium abierto en la VM (altium-mcp), y con el proyecto ya preparado:
00_Modulos.SchDoc (copia de una hoja) agregado al .PrjPcb y AllowPortNetNames=1.
- Hojas hijas: cada etiqueta de red que aparece en más de una hoja pasa a ser un puerto, puesto en el extremo libre del
  cable y apuntando hacia afuera. El extremo lejano del puerto también conecta, así que el ancho se elige para que
  no toque cables ni pines ajenos. Si no hay ancho libre, se acorta el tramo; si tampoco, se deja la etiqueta (solo si
  en esa hoja hay otro puerto con el mismo nombre). Las etiquetas con nombre de alimentación (GND, V3V3_MCU en la 04)
  pasan a ser símbolos de alimentación, que son globales.
- 00_Modulos: un símbolo de hoja por hoja hija, con sus entradas cableadas.
Uso: jerarquia.py aplicar | jerarquia.py revisar <netlist_plana.json>
"""
import collections, json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pcb'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'herramientas'))
from drc_comun import correr, L

HOJAS = ['01_Alimentacion', '02_MCU', '03_Sensores', '04_Conectores']
D = {0: (1, 0), 1: (0, 1), 2: (-1, 0), 3: (0, -1)}
PROY = f'{L}ELO301_G1.PrjPcb'
# dirección real donde un pin de salida empuja la red (el resto bidireccional): salida en 03, entrada en 02
IO = {('03_Sensores', 'GNSS_PPS'): 1, ('03_Sensores', 'UART_GNSS_RX'): 1, ('02_MCU', 'GNSS_PPS'): 2, ('02_MCU', 'UART_GNSS_RX'): 2}
REG = "SL.RegisterSchObjectInContainer({o}); SchServer.RobotManager.SendMessage(SL.I_ObjectAddress, c_BroadCast, SCHM_PrimitiveRegistration, {o}.I_ObjectAddress);\n"
P = lambda x, y: f"Point({x}*10000, {y}*10000)"


def volcar():
    m = lambda e: f"IntToStr(({e}) div 10000)"
    cod = "var\n    Doc, SL, It, X, Pn, PI : IDispatch;\n    s : String;\n    k, i : Integer;\nbegin\ns := '';\n"
    for h in HOJAS:
        cod += f"""Doc := Client.OpenDocument('SCH', '{L}{h}.SchDoc'); Client.ShowDocument(Doc); SL := SchServer.GetCurrentSchDocument;
s := s + '#{h}' + #10;
It := SL.SchIterator_Create; It.AddFilter_ObjectSet(MkSet(eNetLabel, ePowerObject, eWire, eJunction, eSchComponent));
X := It.FirstSchObject;
while X <> nil do begin
  k := X.ObjectId;
  if k = eWire then begin s := s + 'W'; for i := 1 to X.VerticesCount do s := s + '|' + {m('X.Vertex[i].X')} + ',' + {m('X.Vertex[i].Y')}; s := s + #10; end
  else if k = eJunction then s := s + 'J|' + {m('X.Location.X')} + ',' + {m('X.Location.Y')} + #10
  else if k = ePowerObject then s := s + 'P|' + X.Text + '|' + {m('X.Location.X')} + ',' + {m('X.Location.Y')} + #10
  else if k = eNetLabel then s := s + 'L|' + X.Text + '|' + {m('X.Location.X')} + ',' + {m('X.Location.Y')} + #10
  else begin
    PI := X.SchIterator_Create; PI.AddFilter_ObjectSet(MkSet(ePin));
    Pn := PI.FirstSchObject;
    while Pn <> nil do begin
      s := s + 'N|' + {m('Pn.Location.X')} + ',' + {m('Pn.Location.Y')} + '|' + IntToStr(Pn.Orientation) + '|' + {m('Pn.PinLength')} + #10;
      Pn := PI.NextSchObject;
    end;
    X.SchIterator_Destroy(PI);
  end;
  X := It.NextSchObject;
end;
SL.SchIterator_Destroy(It);
"""
    hojas = collections.defaultdict(lambda: collections.defaultdict(list))
    pt = lambda s: tuple(map(int, s.split(',')))
    for l in correr(cod + "ResultText := s;\nend;", 300).splitlines():
        if l.startswith('#'): h = l[1:]; continue
        p = l.split('|')
        if p[0] == 'W': hojas[h]['W'].append([pt(v) for v in p[1:]])
        elif p[0] == 'J': hojas[h]['J'].append(pt(p[1]))
        elif p[0] == 'N':
            (x, y), (dx, dy), n = pt(p[1]), D[int(p[2])], int(p[3])
            hojas[h]['N'] += [(x, y), (x + dx * n, y + dy * n)]  # los dos extremos: sirve sin saber cuál es el eléctrico
        else: hojas[h][p[0]].append((p[1], pt(p[2])))
    return hojas


def sobre(pt, a, b):
    (x, y), (x1, y1), (x2, y2) = pt, a, b
    return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2) and (x2 - x1) * (y - y1) == (y2 - y1) * (x - x1)


def planificar(hojas):
    potencia = {t for g in hojas.values() for t, _ in g['P']}
    donde = collections.defaultdict(set)
    for h, g in hojas.items():
        for t, _ in g['L']: donde[t].add(h)
    cruz = {t for t, hs in donde.items() if len(hs) > 1 and t not in potencia}
    plan = []
    for h, g in hojas.items():
        ocupado = lambda q, w: q in set(g['N']) or any(sobre(q, o[i], o[i + 1]) for o in g['W'] if o is not w for i in range(len(o) - 1))
        for t, loc in g['L']:
            if t not in cruz and t not in potencia: continue
            ws = [w for w in g['W'] if any(sobre(loc, w[i], w[i + 1]) for i in range(len(w) - 1))]
            assert len(ws) == 1, (h, t, loc, ws)
            w = ws[0]; ocup = set(g['N']) | set(g['J']) | {v for o in g['W'] if o is not w for v in o}
            libres = [(e, w[1] if e == w[0] else w[-2]) for e in (w[0], w[-1]) if e not in ocup]
            assert len(libres) == 1, (h, t, loc, w)
            fin, prev = libres[0]
            d = tuple((a - b) and (a - b) // abs(a - b) for a, b in zip(fin, prev))
            p = dict(hoja=h, red=t, label=loc, fin=fin, dir=d, potencia=t in potencia, ancho=0, corto=None)
            if not p['potencia']:
                base = math.ceil((len(t) * 70 + 200) / 100) * 100  # más angosto, Altium lo agranda solo y queda fuera de grilla
                largo = abs(fin[0] - prev[0]) + abs(fin[1] - prev[1])
                # primero recto y sin acortar el tramo; si no, acortándolo; si no, doblando en ángulo recto
                for dd in [d, (d[1], d[0]), (-d[1], -d[0])]:
                    for atras in range(0 if dd == d else 100, largo - 100 + 1, 100):
                        f = (fin[0] - d[0] * atras, fin[1] - d[1] * atras)
                        if not any(ocupado((f[0] + dd[0] * k, f[1] + dd[1] * k), w) for k in range(50, base + 1, 50)):
                            p.update(fin=f, dir=dd, ancho=base, corto=(fin, f) if atras else None)
                            break
                    if p['ancho']: break
            plan.append(p)
    for p in plan:  # sin lugar para el puerto: queda la etiqueta, unida a otro puerto igual de la misma hoja
        if not p['potencia'] and not p['ancho']:
            assert any(q['ancho'] and q['hoja'] == p['hoja'] and q['red'] == p['red'] for q in plan), p
    return plan, sorted(cruz)


def hijas(plan):
    por = collections.defaultdict(list)
    for p in plan:
        if p['potencia'] or p['ancho']: por[p['hoja']].append(p)
    cod = "var\n    Doc, SL, It, X, Q : IDispatch;\n    Lista : TInterfaceList;\n    s : String;\n    i, n : Integer;\nbegin\ns := '';\n"
    for h, ps in por.items():
        cond = ' or '.join(f"((X.Text = '{p['red']}') and (X.Location.X div 10000 = {p['label'][0]}) and (X.Location.Y div 10000 = {p['label'][1]}))" for p in ps)
        cod += f"""Doc := Client.OpenDocument('SCH', '{L}{h}.SchDoc'); Client.ShowDocument(Doc); SL := SchServer.GetCurrentSchDocument;
Lista := TInterfaceList.Create;
It := SL.SchIterator_Create; It.AddFilter_ObjectSet(MkSet(eNetLabel));
X := It.FirstSchObject;
while X <> nil do begin if {cond} then Lista.Add(X); X := It.NextSchObject; end;
SL.SchIterator_Destroy(It);
SchServer.ProcessControl.PreProcess(SL, '');
for i := 0 to Lista.Count - 1 do SL.RemoveSchObject(Lista.Items[i]);
n := 0;
"""
        for p in ps:
            (x, y), (dx, dy) = p['fin'], p['dir']
            if p['corto']:  # acorta el tramo: el extremo libre pasa de corto[0] a corto[1]
                (a, b), (c, e) = p['corto']
                cod += (f"It := SL.SchIterator_Create; It.AddFilter_ObjectSet(MkSet(eWire)); X := It.FirstSchObject;\n"
                        f"while X <> nil do begin for i := 1 to X.VerticesCount do if (X.Vertex[i].X div 10000 = {a}) and (X.Vertex[i].Y div 10000 = {b}) then "
                        f"begin X.SetState_Vertex(i, {P(c, e)}); n := n + 1000; end; X := It.NextSchObject; end;\nSL.SchIterator_Destroy(It);\n")
            if p['potencia']:
                v3 = p['red'] != 'GND'
                cod += (f"Q := SchServer.SchObjectFactory(ePowerObject, eCreate_Default); Q.Location := {P(x, y)}; Q.Text := '{p['red']}'; "
                        f"Q.Style := {2 if v3 else 5}; Q.Orientation := {[k for k, v in D.items() if v == (dx, dy)][0]}; Q.ShowNetName := {v3};\n")
            else:
                w = p['ancho']
                loc, st = {(1, 0): ((x, y), 2), (-1, 0): ((x - w, y), 1), (0, 1): ((x, y), 5), (0, -1): ((x, y - w), 6)}[(dx, dy)]
                cod += (f"Q := SchServer.SchObjectFactory(ePort, eCreate_Default); Q.Location := {P(*loc)}; Q.Name := '{p['red']}'; "
                        f"Q.Width := {w}*10000; Q.Style := {st}; Q.IOType := {IO.get((h, p['red']), 3)}; Q.AutoSize := False;\n")
            cod += REG.format(o='Q') + "n := n + 1;\n"
        cod += f"""SchServer.ProcessControl.PostProcess(SL, '');
Doc.SetModified(True); Doc.DoFileSave('');
s := s + '{h}: etiquetas quitadas ' + IntToStr(Lista.Count) + ', objetos ' + IntToStr(n) + #10;
"""
    return correr(cod + "ResultText := s;\nend;", 600)


def superior(cruz, plan):
    redes = collections.defaultdict(set)
    for p in plan:
        if not p['potencia']: redes[p['hoja']].add(p['red'])
    s03 = [n for n in ['IMU_INT1', 'GNSS_PPS', 'UART_GNSS_TX', 'UART_GNSS_RX', 'SPI_IMU_CS', 'SPI_IMU_SCK', 'SPI_IMU_MISO', 'SPI_IMU_MOSI',
                       'I2C_TOF_SDA', 'I2C_TOF_SCL']]
    s04 = ['SPI_SUP_NSS', 'SPI_SUP_SCK', 'SPI_SUP_MISO', 'SPI_SUP_MOSI', 'SUP_IRQ', 'FOC_CS1', 'FOC_CS2', 'FOC_CS3', 'FOC_CS4',
           'SPI_FOC_SCK', 'SPI_FOC_MISO', 'SPI_FOC_MOSI', 'SWDIO', 'SWCLK', 'NRST', 'UART_DBG_TX', 'UART_DBG_RX']
    assert redes['03_Sensores'] == set(s03) and redes['04_Conectores'] == set(s04 + ['VIN_12V']), redes
    assert redes['02_MCU'] == set(s03 + s04 + ['VIN_SENSE']) and redes['01_Alimentacion'] == {'VIN_12V', 'VIN_SENSE'}, redes
    top = 6900
    bloques = [('PODER', '01_Alimentacion.SchDoc', 900, 1500, top, 1200, [(1, 300, 'VIN_SENSE'), (3, 750, 'VIN_12V')]),
               ('MCU', '02_MCU.SchDoc', 3600, 1500, top, 3900, [(0, 300, 'VIN_SENSE')] + [(1, 300 + 100 * i, n) for i, n in enumerate(s03)]
                + [(1, 2000 + 100 * i, n) for i, n in enumerate(s04)]),
               ('SENSORES', '03_Sensores.SchDoc', 6700, 1500, top, 1500, [(0, 300 + 100 * i, n) for i, n in enumerate(s03)]),
               ('CONECTORES', '04_Conectores.SchDoc', 6700, 1500, top - 1700, 2200,
                [(0, 300 + 100 * i, n) for i, n in enumerate(s04)] + [(3, 750, 'VIN_12V')])]
    cables = [[(2400, 6600), (3600, 6600)], [(1650, 5700), (1650, 2600), (7450, 2600), (7450, 3000)]]
    cables += [[(5100, top - 300 - 100 * i), (6700, top - 300 - 100 * i)] for i in range(len(s03))]
    cables += [[(5100, top - 2000 - 100 * i), (6700, top - 2000 - 100 * i)] for i in range(len(s04))]
    nota = 'CONECTORES: SPI de entrada desde el supervisor (J1), SWD (J1/J2), UART de depuracion (J9) y bus SPI con 4 CS hacia los FOC (J3-J6)'
    cod = f"""var
    Doc, SL, It, X, Sym, E, W : IDispatch;
    Lista : TInterfaceList;
    i : Integer;
    s : String;
begin
Doc := Client.OpenDocument('SCH', '{L}00_Modulos.SchDoc'); Client.ShowDocument(Doc); SL := SchServer.GetCurrentSchDocument;
Lista := TInterfaceList.Create;
It := SL.SchIterator_Create;
It.AddFilter_ObjectSet(MkSet(eSchComponent, eWire, eNetLabel, ePowerObject, eJunction, ePort, eLabel, eNoERC, eBus, eBusEntry, eLine, eRectangle, eNote, eTextFrame, eSheetSymbol, ePolyline, eImage));
X := It.FirstSchObject;
while X <> nil do begin
  if X.ObjectId = eLabel then begin if Pos('Autores', X.Text) = 0 then Lista.Add(X); end else Lista.Add(X);
  X := It.NextSchObject;
end;
SL.SchIterator_Destroy(It);
It := SL.SchIterator_Create; It.AddFilter_ObjectSet(MkSet(eParameter));
X := It.FirstSchObject;
while X <> nil do begin if X.Name = 'Title' then X.Text := 'Modulo de Control Secundario - Diagrama de modulos'; X := It.NextSchObject; end;
SL.SchIterator_Destroy(It);
SchServer.ProcessControl.PreProcess(SL, '');
for i := 0 to Lista.Count - 1 do SL.RemoveSchObject(Lista.Items[i]);
s := 'borrados ' + IntToStr(Lista.Count) + #10;
"""
    for nom, arch, x, w, t, h, ent in bloques:
        cod += (f"Sym := SchServer.SchObjectFactory(eSheetSymbol, eCreate_Default); Sym.Location := {P(x, t)}; Sym.XSize := {w}*10000; Sym.YSize := {h}*10000; "
                f"Sym.SheetName.Text := '{nom}'; Sym.SheetFileName.Text := '{arch}'; Sym.SheetName.Location := {P(x, t + 40)}; "
                f"Sym.SheetFileName.Location := {P(x, t - h - 140)};\n")
        for lado, d, red in ent:
            cod += f"E := SchServer.SchObjectFactory(eSheetEntry, eCreate_Default); E.Side := {lado}; E.DistanceFromTop := {d}*10000; E.Name := '{red}'; E.IOType := {IO.get((arch[:-7], red), 3)}; E.Style := 3; Sym.AddSchObject(E);\n"
        cod += REG.format(o='Sym')
    for c in cables:
        cod += f"W := SchServer.SchObjectFactory(eWire, eCreate_Default); W.Location := {P(*c[0])};"
        for i, v in enumerate(c, 1): cod += f" W.InsertVertex := {i}; W.SetState_Vertex({i}, {P(*v)});"
        cod += "\n" + REG.format(o='W')
    cod += (f"X := SchServer.SchObjectFactory(eLabel, eCreate_Default); X.Location := {P(900, 2300)}; X.Text := '{nota}';\n" + REG.format(o='X') +
            """SchServer.ProcessControl.PostProcess(SL, '');
Doc.SetModified(True); Doc.DoFileSave('');
ResultText := s;
end;""")
    return correr(cod, 600)


def enlazar():
    """La placa sigue enlazada a los Unique ID planos (\\XXXXXXXX). 1) Cada componente del esquemático recupera el ID que
    tiene en la placa (al abrir 00_Modulos, copia de una hoja, Altium renumera los repetidos). 2) La placa pasa a la ruta
    jerárquica (\\SIMBOLO\\XXXXXXXX). Así Update PCB no borra ni vuelve a agregar componentes."""
    from drc_comun import ABRIR
    cod = "var\n    Doc, SL, It, X, Prj, Fl, C, Board, Comp, Obj1 : IDispatch;\n    Lista : TInterfaceList;\n    Viejos, Ids : TStringList;\n    s, u, v : String;\n    i, n, malos : Integer;\nbegin\ns := ''; n := 0; malos := 0;\n"
    cod += f"""{ABRIR}Viejos := TStringList.Create; Lista := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eComponentObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
Comp := It.FirstPCBObject;
while Comp <> nil do begin
  v := Comp.SourceUniqueId; while Pos('\\', v) > 0 do Delete(v, 1, Pos('\\', v));
  Viejos.Add(Comp.Name.Text + '=' + v); Lista.Add(Comp); Comp := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
"""
    for h in HOJAS:
        cod += f"""Doc := Client.OpenDocument('SCH', '{L}{h}.SchDoc'); Client.ShowDocument(Doc); SL := SchServer.GetCurrentSchDocument;
It := SL.SchIterator_Create; It.AddFilter_ObjectSet(MkSet(eSchComponent));
X := It.FirstSchObject; i := 0;
while X <> nil do begin
  v := Viejos.Values[X.Designator.Text];
  if (v <> '') and (X.UniqueId <> v) then begin X.UniqueId := v; i := i + 1; end;
  X := It.NextSchObject;
end;
SL.SchIterator_Destroy(It);
if i > 0 then begin Doc.SetModified(True); Doc.DoFileSave(''); end;
s := s + '{h}: IDs repuestos ' + IntToStr(i) + #10;
"""
    cod += """Prj := GetWorkspace.DM_FocusedProject; Prj.DM_Compile; Fl := Prj.DM_DocumentFlattened;
Ids := TStringList.Create;
for i := 0 to Fl.DM_ComponentCount - 1 do begin C := Fl.DM_Components(i); Ids.Add(C.DM_PhysicalDesignator + '=' + C.DM_UniqueId); end;
PCBServer.PreProcess;
try
for i := 0 to Lista.Count - 1 do begin
  Comp := Lista.Items[i]; u := Ids.Values[Comp.Name.Text]; v := Viejos.Values[Comp.Name.Text];
  if (u = '') or (Copy(u, Length(u) - Length(v) + 1, Length(v)) <> v) then begin malos := malos + 1; s := s + 'NO CALZA ' + Comp.Name.Text + ' ' + v + ' / ' + u + #10; end
  else if Comp.SourceUniqueId <> u then begin Comp.BeginModify; Comp.SourceUniqueId := u; Comp.EndModify; n := n + 1; end;
end;
finally
PCBServer.PostProcess;
end;
s := s + 'esquematico ' + IntToStr(Ids.Count) + ', placa ' + IntToStr(Lista.Count) + ', re-enlazados ' + IntToStr(n) + ', sin calzar ' + IntToStr(malos) + #10;
if (malos = 0) and (Ids.Count = Lista.Count) then begin Obj1.SetModified(True); Obj1.DoFileSave(''); s := s + 'placa guardada'; end;
ResultText := s;
end;"""
    return correr(cod, 600)


def recargar():
    return correr(f"""begin
GetWorkspace.DM_CloseProject('{PROY}'); GetWorkspace.DM_OpenProject('{PROY}', True);
ResultText := GetWorkspace.DM_FocusedProject.DM_ProjectFullPath;
end;""", 300)


if __name__ == '__main__':
    if sys.argv[1] == 'aplicar':
        correr(f"begin GetWorkspace.DM_OpenProject('{PROY}', True); end;", 300)
        plan, cruz = planificar(volcar())
        print(len(cruz), 'redes entre hojas;', sum(1 for p in plan if p['ancho']), 'puertos,', sum(p['potencia'] for p in plan), 'alimentación,',
              'tramos acortados', [(p['hoja'][:2], p['red']) for p in plan if p['corto']],
              'etiquetas que quedan', [(p['hoja'][:2], p['red']) for p in plan if not p['potencia'] and not p['ancho']])
        json.dump(plan, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plan_puertos.json'), 'w'), indent=0)
        print(hijas(plan)); print(superior(cruz, plan))
        for _ in range(2): print(recargar()); print(enlazar())  # la 1.ª repone IDs; la 2.ª, ya recargada, enlaza
    elif sys.argv[1] == 'enlazar':
        for _ in range(2): print(recargar()); print(enlazar())
    elif sys.argv[1] == 'revisar':
        import subprocess
        aqui = os.path.dirname(os.path.abspath(__file__))
        recargar()  # sin recargar, la compilación no ve los cambios hechos por script
        subprocess.run([sys.executable, os.path.join(aqui, '..', 'herramientas', 'netlist_altium.py'), '/tmp/netlist_jer.json'], check=True)
        a, b = json.load(open('/tmp/netlist_jer.json')), json.load(open(sys.argv[2]))
        dif = [(k, b.get(k), a.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
        print('netlist:', 'IDÉNTICA' if not dif else f'{len(dif)} diferencias {dif[:20]}')
        # dos redes distintas con el mismo nombre no se ven en la netlist por nombre: las delata el ERC
        sys.path.insert(0, '/mnt/sda3/vms/altium')
        from construir_hoja import mcp
        erc = json.loads(mcp('get_erc_violations', {}))
        for v in erc['violations']:
            if v['level'] != 'warning': print('ERC', v['level'], v['type'], v['detail'][:150])
        print('ERC:', erc['errors'], 'errores,', erc['warnings'], 'advertencias')
        sys.exit(1 if dif or erc['errors'] or erc['fatal'] else 0)
