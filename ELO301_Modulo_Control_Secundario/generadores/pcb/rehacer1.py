"""Rearma la placa desde el PcbDoc de las 06:42: ubicación final, clases y reglas, plano GND, stackup de 1,6 mm,
pila explícita en pads pasantes y designadores (tamaño y posición fuera de courtyards)."""
import contextlib, io, json, sys
from drc_comun import *
sys.path.insert(0, '/mnt/hdd-viejo-ro/S2-2026/MATERIA/ELO301-Diseno-Equipos-Electronicos/altium/pcb')

# 1) ubicación final
print('ubicación:', json.loads(mcp('place_components', json.load(open('/tmp/colocacion.json'))))['result']['placed_count'])

# 2) clases y reglas
for n, redes in {'Potencia': ['VIN_12V', 'VIN_PROT', 'SW', 'V_5V'], 'Alimentacion': ['V3V3_MCU', 'V3V3_SENS', 'VDDA', 'V5_SENS']}.items():
    mcp('create_net_class', {'class_name': n, 'net_names': redes})
def ancho(mn, pf, mx):
    return ' '.join(f"R.MinWidth[{c}] := MMsToCoord({mn}); R.MaxWidth[{c}] := MMsToCoord({mx}); R.FavoredWidth[{c}] := MMsToCoord({pf});"
                    for c in ('eTopLayer', 'eMidLayer1', 'eBottomLayer'))
nuevas = ''.join(f"""R := PCBServer.PCBRuleFactory(eRule_MaxMinWidth); R.Name := '{n}'; R.Scope1Expression := '{alc}';
{ancho(mn, pf, mx)}
Board.AddPCBObject(R);
""" for n, alc, mn, pf, mx in [('Ancho_Alimentacion', "InNetClass(''Alimentacion'')", 0.25, 0.3, 2.0),
                               ('Ancho_Potencia', "InNetClass(''Potencia'')", 0.3, 0.6, 2.0),
                               ('Ancho_RF', "InNet(''RF_IN'')", 0.35, 0.35, 0.35)])
print(correr(f"""{VARS}    R, CP, CA, SP, GND2, MLS : IDispatch;
{ABRIR}s := '';
It := Board.BoardIterator_Create; It.SetState_FilterAll; It.AddFilter_ObjectSet(MkSet(eClassObject));
X := It.FirstPCBObject;
while X <> nil do
begin
    if X.Name = 'Potencia' then begin X.AddMemberByName('VIN_12V'); X.AddMemberByName('VIN_PROT'); X.AddMemberByName('SW'); X.AddMemberByName('V_5V'); s := s + 'clase Potencia; '; end;
    if X.Name = 'Alimentacion' then begin X.AddMemberByName('V3V3_MCU'); X.AddMemberByName('V3V3_SENS'); X.AddMemberByName('VDDA'); X.AddMemberByName('V5_SENS'); s := s + 'clase Alimentacion; '; end;
    X := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
Lista := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.SetState_FilterAll; It.AddFilter_ObjectSet(MkSet(eRuleObject));
R := It.FirstPCBObject;
while R <> nil do
begin
    try
        if R.Name = 'Clearance' then R.Gap := MMsToCoord(0.15);
        if R.Name = 'Width' then begin {ancho(0.15, 0.2, 2.0)} end;
        if R.Name = 'RoutingVias' then
        begin
            R.MinWidth := MMsToCoord(0.5); R.MaxWidth := MMsToCoord(0.8); R.PreferedWidth := MMsToCoord(0.6);
            R.MinHoleWidth := MMsToCoord(0.25); R.MaxHoleWidth := MMsToCoord(0.4); R.PreferedHoleWidth := MMsToCoord(0.3);
        end;
        if R.Name = 'HoleSize' then begin R.MaxLimit := MMsToCoord(3.5); R.MinLimit := MMsToCoord(0.25); end;
        if R.Name = 'SolderMaskExpansion' then R.Expansion := MMsToCoord(0.05);
        if R.Name = 'SilkToSolderMaskClearance' then R.SetState_SilkToMaskGap(MMsToCoord(0.1));
        if R.Name = 'MinimumSolderMaskSliver' then R.SetState_MinSolderMaskSliver(MMsToCoord(0.07));
        if (Copy(R.Name, 1, 6) = 'Ancho_') or (R.Name = 'Clearance_Poligono') then Lista.Add(R);
    except
        s := s + '[error en ' + R.Name + '] ';
    end;
    R := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
PCBServer.PreProcess;
try
    for i := 0 to Lista.Count - 1 do Board.RemovePCBObject(Lista.Items[i]);
{nuevas}    R := PCBServer.PCBRuleFactory(eRule_Clearance); R.Name := 'Clearance_Poligono'; R.Scope1Expression := 'InPolygon'; R.Scope2Expression := 'All'; R.Gap := MMsToCoord(0.3);
    Board.AddPCBObject(R);
finally
    PCBServer.PostProcess;
end;
It := Board.BoardIterator_Create; It.SetState_FilterAll; It.AddFilter_ObjectSet(MkSet(eRuleObject));
R := It.FirstPCBObject;
while R <> nil do
begin
    if R.RuleKind = eRule_MaxMinWidth then s := s + R.Name + ' p' + IntToStr(R.Priority) + ' ' + FloatToStr(CoordToMMs(R.FavoredWidth[eTopLayer])) + '; ';
    R := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
It := Board.BoardIterator_Create; It.SetState_FilterAll; It.AddFilter_ObjectSet(MkSet(eNetObject));
X := It.FirstPCBObject;
while X <> nil do begin if X.Name = 'GND' then GND := X; X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
Board.LayerStack_V7.LayerObject_V7(eInternalPlane1).NetName := 'GND';
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eSplitPlaneObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
SP := It.FirstPCBObject;
while SP <> nil do
begin
    if SP.Layer = eInternalPlane1 then
    begin
        PCBServer.SendMessageToRobots(SP.I_ObjectAddress, c_Broadcast, PCBM_BeginModify, c_NoEventData);
        SP.Net := GND;
        PCBServer.SendMessageToRobots(SP.I_ObjectAddress, c_Broadcast, PCBM_EndModify, c_NoEventData);
        s := s + '| plano interno: ' + SP.Net.Name + ' ';
    end;
    SP := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
MLS := Board.MasterLayerStack;
PCBServer.PreProcess;
try
    X := MLS.First(eLayerClass_Dielectric);
    while X <> nil do
    begin
        if X.Name = 'Dielectric 1' then begin X.DielectricType := 2; X.DielectricMaterial := 'PP 7628'; X.DielectricConstant := 4.4; X.DielectricHeight := MMsToCoord(0.2104); end;
        if X.Name = 'Dielectric2' then begin X.DielectricType := 1; X.DielectricMaterial := 'FR-4'; X.DielectricConstant := 4.6; X.DielectricHeight := MMsToCoord(1.065); end;
        if X.Name = 'Dielectric3' then begin X.DielectricType := 2; X.DielectricMaterial := 'PP 7628'; X.DielectricConstant := 4.4; X.DielectricHeight := MMsToCoord(0.2104); end;
        X := MLS.Next(eLayerClass_Dielectric, X);
    end;
    X := MLS.First(eLayerClass_Electrical);
    while X <> nil do
    begin
        if (X.Name = 'GND') or (X.Name = 'Senal-Potencia') then X.CopperThickness := MMsToCoord(0.0152) else X.CopperThickness := MMsToCoord(0.035);
        X := MLS.Next(eLayerClass_Electrical, X);
    end;
finally
    PCBServer.PostProcess;
end;
X := MLS.First(eLayerClass_Physical); n := 0;
while X <> nil do begin n := n + Abs(MLS.Get_ZTop(X) - MLS.Get_ZBottom(X)); X := MLS.Next(eLayerClass_Physical, X); end;
s := s + '| espesor ' + FormatFloat('0.000', CoordToMMs(n)) + ' mm ';
{GUARDAR}ResultText := s;"""))
print('guardado:', hora_pcb())

# 5) pila explícita en pads pasantes y 6) designadores de 0,8 mm sin girar, en manual
print(correr(f"""{VARS}    P, It2 : IDispatch;
    BB : TCoordRect;
{ABRIR}n := 0; s := '';
PCBServer.PreProcess;
try
    It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eComponentObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
    C := It.FirstPCBObject;
    while C <> nil do
    begin
        It2 := C.GroupIterator_Create; It2.AddFilter_ObjectSet(MkSet(ePadObject));
        P := It2.FirstPCBObject;
        while P <> nil do
        begin
            if (P.Layer = eMultiLayer) and P.Plated and (P.HoleSize > 0) and (P.Mode = ePadMode_Simple) then
            begin
                P.Mode := ePadMode_LocalStack;
                P.MidXSize := P.TopXSize; P.MidYSize := P.TopYSize; P.MidShape := P.TopShape;
                P.BotXSize := P.TopXSize; P.BotYSize := P.TopYSize; P.BotShape := P.TopShape;
                n := n + 1;
            end;
            P := It2.NextPCBObject;
        end;
        C.GroupIterator_Destroy(It2);
        C.ChangeNameAutoposition(eAutoPos_Manual);
        C.Name.Size := MMsToCoord(0.8); C.Name.Width := MMsToCoord(0.15); C.Name.Rotation := 0;
        C := It.NextPCBObject;
    end;
    Board.BoardIterator_Destroy(It);
finally
    PCBServer.PostProcess;
end;
{GUARDAR}ResultText := 'pads pasantes con pila explicita: ' + IntToStr(n);"""))

with contextlib.redirect_stderr(io.StringIO()):
    import colocacion as col
tam = json.load(open('/tmp/designadores.json'))
cajas = {d: col.caja_colocada(d) for d in col.X}
cara = {d: col.X[d][3] for d in col.X}
tht = {d for d in col.X if col.HUELLA[d] in col.THT}
M_CY, M_TX, BORDE = 0.26, 0.2, 0.4
def choca(b, lado, puestos):
    x0, x1, y0, y1 = b
    if x0 < BORDE or y0 < BORDE or x1 > col.ANCHO - BORDE or y1 > col.ALTO - BORDE:
        return True
    if any((cara[d] == lado or d in tht) and x0 < a1 + M_CY and a0 < x1 + M_CY and y0 < c1 + M_CY and c0 < y1 + M_CY for d, (a0, a1, c0, c1) in cajas.items()):
        return True
    return any(cara[d] == lado and x0 < a1 + M_TX and a0 < x1 + M_TX and y0 < c1 + M_TX and c0 < y1 + M_TX for d, (a0, a1, c0, c1) in puestos.items())
def candidatos(d):
    x0, x1, y0, y1 = cajas[d]; w, h = tam[d]; g = M_CY + 0.01; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for xa in (cx - w / 2, x0, x1 - w):
        yield (xa, xa + w, y1 + g, y1 + g + h); yield (xa, xa + w, y0 - g - h, y0 - g)
    for ya in (cy - h / 2, y1 - h, y0):
        yield (x1 + g, x1 + g + w, ya, ya + h); yield (x0 - g - w, x0 - g, ya, ya + h)
puestos, ocultos = {}, []
for d in sorted(tam, key=lambda d: -(cajas[d][1] - cajas[d][0]) * (cajas[d][3] - cajas[d][2])):
    b = next((b for b in candidatos(d) if not choca(b, cara[d], puestos)), None)
    if b: puestos[d] = b
    else: ocultos.append(d)
mover = ''.join(f"C := Board.GetPcbComponentByRefDes('{d}'); BB := C.Name.BoundingRectangle; C.Name.MoveByXY(Board.XOrigin + MMsToCoord({b[0]:.3f}) - BB.Left, Board.YOrigin + MMsToCoord({b[2]:.3f}) - BB.Bottom);\n" for d, b in puestos.items())
ocultar = ''.join(f"C := Board.GetPcbComponentByRefDes('{d}'); C.NameOn := False;\n" for d in ocultos)
print(correr(f"""{VARS}    BB : TCoordRect;
{ABRIR}PCBServer.PreProcess;
try
{mover}{ocultar}finally
    PCBServer.PostProcess;
end;
Board.ViewManager_FullUpdate;
{GUARDAR}ResultText := 'designadores: {len(puestos)} ubicados, ocultos {' '.join(sorted(ocultos))}';"""))
print('guardado:', hora_pcb())
