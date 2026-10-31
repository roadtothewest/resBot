"""Agrega las vías de costura de /tmp/costura.json (GND, tapadas), vuelve a verter los polígonos y corre el DRC."""
import json
from drc_comun import *

mm = lambda v, eje: f"Board.{eje}Origin + MMsToCoord({v:.4f})"
vias = json.load(open('/tmp/costura.json'))
nuevas = ''.join(f"""X := PCBServer.PCBObjectFactory(eViaObject, eNoDimension, eCreate_Default);
X.x := {mm(x, 'X')}; X.y := {mm(y, 'Y')}; X.Size := MMsToCoord(0.6); X.HoleSize := MMsToCoord(0.3); X.LowLayer := eBottomLayer; X.HighLayer := eTopLayer; X.Net := C;
Board.AddPCBObject(X); PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, X.I_ObjectAddress);
Cache := X.GetState_Cache; Cache.SolderMaskExpansionValid := eCacheManual; X.SetState_Cache := Cache; X.SetState_IsTenting_Top(True); X.SetState_IsTenting_Bottom(True);
""" for x, y in vias)
res = correr(f"""{VARS}{ABRIR}C := nil;
It := Board.BoardIterator_Create; It.SetState_FilterAll; It.AddFilter_ObjectSet(MkSet(eNetObject));
X := It.FirstPCBObject;
while X <> nil do begin if X.Name = 'GND' then C := X; X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
PCBServer.PreProcess;
try
{nuevas}finally
    PCBServer.PostProcess;
end;
s := 'vias de costura: {len(vias)}';
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
