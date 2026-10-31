"""Rehace NetL2_1 (U6-14 → L2-1) en Top hasta el centro real del pad, vuelve a verter los polígonos y corre el DRC."""
from drc_comun import *

PISTAS = [(61.75, 33.0, 63.44, 33.0), (63.44, 33.0, 63.83, 33.39)]
mm = lambda v, eje: f"Board.{eje}Origin + MMsToCoord({v:.4f})"
nuevas = ''.join(f"""X := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
X.x1 := {mm(a, 'X')}; X.y1 := {mm(b, 'Y')}; X.x2 := {mm(c, 'X')}; X.y2 := {mm(d, 'Y')}; X.Width := MMsToCoord(0.2); X.Layer := eTopLayer; X.Net := C;
Board.AddPCBObject(X); PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, X.I_ObjectAddress);
""" for a, b, c, d in PISTAS)
res = correr(f"""{VARS}{ABRIR}Lista := TInterfaceList.Create; C := nil;
It := Board.BoardIterator_Create; It.SetState_FilterAll; It.AddFilter_ObjectSet(MkSet(eNetObject));
X := It.FirstPCBObject;
while X <> nil do begin if X.Name = 'NetL2_1' then C := X; X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eTrackObject, eArcObject, eViaObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do
begin
    if (not X.InComponent) and (not X.InPolygon) and (X.Net <> nil) then
        if X.Net.Name = 'NetL2_1' then Lista.Add(X);
    X := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
PCBServer.PreProcess;
try
    for i := 0 to Lista.Count - 1 do Board.RemovePCBObject(Lista.Items[i]);
{nuevas}finally
    PCBServer.PostProcess;
end;
s := 'NetL2_1: quitadas ' + IntToStr(Lista.Count) + ', nuevas {len(PISTAS)}';
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
{GUARDAR}{RESUMEN}ResultText := s;""")
print(res.split('\n')[0])
resumen(res, 'DRC')
print('guardado:', hora_pcb())
