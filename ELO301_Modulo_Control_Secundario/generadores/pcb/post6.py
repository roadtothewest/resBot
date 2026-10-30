"""Tras el ruteo: guarda, quita vías repetidas de igual red y antenas con un extremo realmente libre (sin dejar redes
sin rutear), tapa las vías, quita la serigrafía de L1 junto a sus pads (placa y biblioteca), vierte GND arriba y abajo
y corre el DRC final."""
from drc_comun import *
LIB = L + 'ELO301_G1.PcbLib'

print(correr(f"""{VARS}{ABRIR}{GUARDAR}ResultText := 'ruteo guardado';"""), hora_pcb())

r = correr(f"""{VARS}    SI, T, P1, P2 : IDispatch;
    ex, ey, rr, libres, pasada : Integer;
    conectado : Boolean;
{ABRIR}s := '';
for pasada := 1 to 6 do
begin
    Board.RunBatchDesignRuleCheck('C:\\Users\\Public\\drc_elo301.html', 0, False, False);
    Lista := TInterfaceList.Create;
    It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eViolationObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
    V := It.FirstPCBObject;
    while V <> nil do
    begin
        nom := '';
        try nom := V.Rule.Name; except end;
        if nom = 'NetAntennae' then
        begin
            T := V.Primitive1;
            if (T <> nil) and (T.ObjectId = eTrackObject) and (Lista.IndexOf(T) < 0) then
            begin
                libres := 0;
                for k := 0 to 1 do
                begin
                    if k = 0 then begin ex := T.x1; ey := T.y1; end else begin ex := T.x2; ey := T.y2; end;
                    rr := T.Width div 2;
                    conectado := False;
                    SI := Board.SpatialIterator_Create; SI.AddFilter_ObjectSet(MkSet(eTrackObject, eArcObject, eViaObject, ePadObject)); SI.AddFilter_LayerSet(MkSet(T.Layer, eMultiLayer)); SI.AddFilter_Area(ex - rr, ey - rr, ex + rr, ey + rr);
                    X := SI.FirstPCBObject;
                    while X <> nil do
                    begin
                        if (X.I_ObjectAddress <> T.I_ObjectAddress) and (X.Net <> nil) and (T.Net <> nil) then
                            if X.Net.Name = T.Net.Name then conectado := True;
                        X := SI.NextPCBObject;
                    end;
                    Board.SpatialIterator_Destroy(SI);
                    if not conectado then libres := libres + 1;
                end;
                if libres > 0 then begin Lista.Add(T); s := s + #10 + 'antena fuera: ' + T.Net.Name + ' ' + T.Descriptor; end;
            end;
        end;
        if nom = 'HoleToHoleClearance' then
        begin
            P1 := V.Primitive1; P2 := V.Primitive2;
            if (P1 <> nil) and (P2 <> nil) and (P1.ObjectId = eViaObject) and (P2.ObjectId = eViaObject) and (Lista.IndexOf(P1) < 0) and (Lista.IndexOf(P2) < 0) then
                if P1.Net.Name = P2.Net.Name then begin Lista.Add(P2); s := s + #10 + 'via repetida fuera: ' + P2.Net.Name; end
                else s := s + #10 + 'VIAS DE DISTINTA RED: ' + P1.Net.Name + ' / ' + P2.Net.Name;
        end;
        V := It.NextPCBObject;
    end;
    Board.BoardIterator_Destroy(It);
    if Lista.Count = 0 then Break;
    PCBServer.PreProcess;
    try
        for i := 0 to Lista.Count - 1 do Board.RemovePCBObject(Lista.Items[i]);
    finally
        PCBServer.PostProcess;
    end;
end;
Lista := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eViaObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do begin Lista.Add(X); X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
nv := 0;
PCBServer.PreProcess;
try
    for i := 0 to Lista.Count - 1 do
    begin
        X := Lista.Items[i];
        PCBServer.SendMessageToRobots(X.I_ObjectAddress, c_Broadcast, PCBM_BeginModify, c_NoEventData);
        Cache := X.GetState_Cache;
        Cache.SolderMaskExpansionValid := eCacheManual;
        X.SetState_Cache := Cache;
        X.SetState_IsTenting_Top(True); X.SetState_IsTenting_Bottom(True);
        PCBServer.SendMessageToRobots(X.I_ObjectAddress, c_Broadcast, PCBM_EndModify, c_NoEventData);
        if X.GetState_IsTenting_Top then nv := nv + 1;
    end;
finally
    PCBServer.PostProcess;
end;
s := s + #10 + 'vias tapadas ' + IntToStr(nv) + ' de ' + IntToStr(Lista.Count);
C := Board.GetPcbComponentByRefDes('L1');
Lista := TInterfaceList.Create;
It := C.GroupIterator_Create; It.AddFilter_ObjectSet(MkSet(eTrackObject));
X := It.FirstPCBObject;
while X <> nil do begin if (X.Layer = eTopOverlay) and (X.x1 = X.x2) then Lista.Add(X); X := It.NextPCBObject; end;
C.GroupIterator_Destroy(It);
PCBServer.PreProcess;
try
    for i := 0 to Lista.Count - 1 do try C.RemovePCBObject(Lista.Items[i]); Board.RemovePCBObject(Lista.Items[i]); except s := s + ' (L1 error)'; end;
finally
    PCBServer.PostProcess;
end;
s := s + #10 + 'L1: lineas de serigrafia quitadas ' + IntToStr(Lista.Count);
{GUARDAR}Obj2 := Client.OpenDocument('PCBLIB', '{LIB}');
Lib := PCBServer.GetPCBLibraryByPath('{LIB}');
if Lib = nil then begin Client.ShowDocument(Obj2); Lib := PCBServer.GetCurrentPCBLibrary; end;
FP := Lib.GetComponentByName('SRN4018 - BOURNS');
Lista := TInterfaceList.Create;
It := FP.GroupIterator_Create; It.AddFilter_ObjectSet(MkSet(eTrackObject));
X := It.FirstPCBObject;
while X <> nil do begin if (X.Layer = eTopOverlay) and (X.x1 = X.x2) then Lista.Add(X); X := It.NextPCBObject; end;
FP.GroupIterator_Destroy(It);
PCBServer.PreProcess;
try
    for i := 0 to Lista.Count - 1 do try FP.RemovePCBObject(Lista.Items[i]); except s := s + ' (lib error)'; end;
finally
    PCBServer.PostProcess;
end;
Obj2.SetModified(True); Obj2.DoFileSave('');
s := s + ' | biblioteca: ' + IntToStr(Lista.Count);
Client.ShowDocument(Obj1);
ResultText := s;""")
print(r.strip())
print('guardado:', hora_pcb())

r = correr(f"""{VARS}{ABRIR}It := Board.BoardIterator_Create; It.SetState_FilterAll; It.AddFilter_ObjectSet(MkSet(eNetObject));
X := It.FirstPCBObject;
while X <> nil do begin if X.Name = 'GND' then GND := X; X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
x0 := Board.XOrigin + MMsToCoord(0.3); y0 := Board.YOrigin + MMsToCoord(0.3);
x1 := Board.XOrigin + MMsToCoord(69.7); y1 := Board.YOrigin + MMsToCoord(49.7);
for k := 0 to 1 do
begin
    PCBServer.PreProcess;
    try
        Poly := PCBServer.PCBObjectFactory(ePolyObject, eNoDimension, eCreate_Default);
        if k = 0 then Poly.Layer := eTopLayer else Poly.Layer := eBottomLayer;
        Poly.PolyHatchStyle := ePolySolid;
        Poly.PointCount := 4;
        Seg := TPolySegment;
        Seg.Kind := ePolySegmentLine;
        Seg.vx := x0; Seg.vy := y0; Poly.Segments[0] := Seg;
        Seg.vx := x1; Seg.vy := y0; Poly.Segments[1] := Seg;
        Seg.vx := x1; Seg.vy := y1; Poly.Segments[2] := Seg;
        Seg.vx := x0; Seg.vy := y1; Poly.Segments[3] := Seg;
        Seg.vx := x0; Seg.vy := y0; Poly.Segments[4] := Seg;
        Poly.Net := GND;
        Poly.PourOver := ePolygonPourOver_SameNet;
        Poly.RemoveDead := True;
        if k = 0 then Poly.Name := 'GND_Top' else Poly.Name := 'GND_Bottom';
        Board.AddPCBObject(Poly);
        PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, Poly.I_ObjectAddress);
        Poly.Rebuild;
    finally
        PCBServer.PostProcess;
    end;
end;
Board.ViewManager_FullUpdate;
{GUARDAR}s := '';
{RESUMEN}ResultText := s;""")
por = resumen(r, 'DRC final (con planos GND)')
json.dump(por, open('/tmp/drc.json', 'w'), ensure_ascii=False)
print('guardado:', hora_pcb())
