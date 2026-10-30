"""Borra las pistas de GND que no son fanout, agrega las rutas de /tmp/rutas.json (vías tapadas), vuelve a verter
los polígonos y corre el DRC."""
import json
from drc_comun import *

r = json.load(open('/tmp/rutas.json'))
capa = ['eTopLayer', 'eMidLayer1', 'eBottomLayer']
mm = lambda v, eje: f"Board.{eje}Origin + MMsToCoord({v:.4f})"
nuevas = ''.join(f"""T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
T.x1 := {mm(x1, 'X')}; T.y1 := {mm(y1, 'Y')}; T.x2 := {mm(x2, 'X')}; T.y2 := {mm(y2, 'Y')}; T.Width := MMsToCoord({w}); T.Layer := {capa[c]}; T.Net := Redes.Items[Nombres.IndexOf('{red}')];
Board.AddPCBObject(T); PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, T.I_ObjectAddress);
""" for c, x1, y1, x2, y2, w, red in r['pistas']) + ''.join(f"""V := PCBServer.PCBObjectFactory(eViaObject, eNoDimension, eCreate_Default);
V.x := {mm(x, 'X')}; V.y := {mm(y, 'Y')}; V.Size := MMsToCoord(0.6); V.HoleSize := MMsToCoord(0.3); V.LowLayer := eBottomLayer; V.HighLayer := eTopLayer; V.Net := Redes.Items[Nombres.IndexOf('{red}')];
Board.AddPCBObject(V); PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, V.I_ObjectAddress);
Cache := V.GetState_Cache; Cache.SolderMaskExpansionValid := eCacheManual; V.SetState_Cache := Cache; V.SetState_IsTenting_Top(True); V.SetState_IsTenting_Bottom(True);
""" for x, y, red in r['vias'])
res = correr(f"""{VARS}    T, Nombres, Redes : IDispatch;
{ABRIR}Nombres := TStringList.Create; Redes := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.SetState_FilterAll; It.AddFilter_ObjectSet(MkSet(eNetObject));
X := It.FirstPCBObject;
while X <> nil do begin Nombres.Add(X.Name); Redes.Add(X); X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
Lista := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eTrackObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do
begin
    if (not X.InComponent) and (not X.InPolygon) and (X.Net <> nil) then
        if (X.Net.Name = 'GND') and (Abs(CoordToMMs(X.Width) - 0.25) > 0.01) then Lista.Add(X);
    X := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
PCBServer.PreProcess;
try
    for i := 0 to Lista.Count - 1 do Board.RemovePCBObject(Lista.Items[i]);
{nuevas}finally
    PCBServer.PostProcess;
end;
s := 'pistas GND de Situs quitadas: ' + IntToStr(Lista.Count) + ', rutas nuevas: {len(r['pistas'])} pistas y {len(r['vias'])} vias';
Lista := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(ePolyObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do begin Lista.Add(X); X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
for i := 0 to Lista.Count - 1 do
begin
    Poly := Lista.Items[i];
    PCBServer.PreProcess;
    try
        Poly.BeginModify; Poly.SetState_CopperPourInvalid; Poly.Rebuild; Poly.EndModify; Poly.GraphicallyInvalidate;
    finally
        PCBServer.PostProcess;
    end;
end;
Board.ViewManager_FullUpdate;
{GUARDAR}s := s + #10 + 'poligonos revertidos: ' + IntToStr(Lista.Count);
{RESUMEN}ResultText := s;""")
print('\n'.join(l for l in res.split('\n')[:2]))
por = resumen(res, 'DRC')
json.dump(por, open('/tmp/drc.json', 'w'), ensure_ascii=False)
print('guardado:', hora_pcb())
