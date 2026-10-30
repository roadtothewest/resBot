"""Desrutea la placa (pistas, arcos, vías y polígonos libres) y repone el fanout de GND de /tmp/fanout.json."""
import json, sys
sys.path.insert(0, '/mnt/sda3/vms/altium')
from construir_hoja import mcp, L

def reponer():
    f = json.load(open('/tmp/fanout.json'))
    mm = lambda v, eje: f"Board.{eje}Origin + MMsToCoord({v:.4f})"
    cuerpo = ''.join(f"""V := PCBServer.PCBObjectFactory(eViaObject, eNoDimension, eCreate_Default);
V.x := {mm(vx, 'X')}; V.y := {mm(vy, 'Y')}; V.Size := MMsToCoord(0.6); V.HoleSize := MMsToCoord(0.3); V.LowLayer := eBottomLayer; V.HighLayer := eTopLayer; V.Net := GND;
Board.AddPCBObject(V); PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, V.I_ObjectAddress);
T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
T.x1 := {mm(px, 'X')}; T.y1 := {mm(py, 'Y')}; T.x2 := {mm(vx, 'X')}; T.y2 := {mm(vy, 'Y')}; T.Width := MMsToCoord(0.25); T.Layer := eTopLayer; T.Net := GND;
Board.AddPCBObject(T); PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, T.I_ObjectAddress);
""" for vx, vy, px, py in f['vias'])
    d = json.loads(mcp('run_altium_script', {'script': f"""var
    Board, It, X, GND, V, T : IDispatch;
    Lista : TInterfaceList;
    i : Integer;
Obj1 := Client.OpenDocument('PCB', '{L}ELO301_G1.PcbDoc'); Client.ShowDocument(Obj1);
Board := PCBServer.GetCurrentPCBBoard;
Lista := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(ePolyObject, eTrackObject, eArcObject, eViaObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do
begin
    if X.ObjectId = ePolyObject then Lista.Add(X)
    else if not X.InComponent then
        if (X.ObjectId = eViaObject) or (X.Layer = eTopLayer) or (X.Layer = eMidLayer1) or (X.Layer = eBottomLayer) then Lista.Add(X);
    X := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
It := Board.BoardIterator_Create; It.SetState_FilterAll; It.AddFilter_ObjectSet(MkSet(eNetObject));
X := It.FirstPCBObject;
while X <> nil do begin if X.Name = 'GND' then GND := X; X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
PCBServer.PreProcess;
for i := 0 to Lista.Count - 1 do Board.RemovePCBObject(Lista.Items[i]);
{cuerpo}PCBServer.PostProcess;
Board.ViewManager_FullUpdate;
Obj1.SetModified(True); Obj1.DoFileSave('');
ResultText := 'borrados ' + IntToStr(Lista.Count) + ', fanout GND repuesto: {len(f['vias'])} vias';""", 'timeout_seconds': 300}))
    return d.get('result') or d

if __name__ == '__main__':
    print(reponer())
