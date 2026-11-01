"""Auditoría 01/11/2026 (placa y esquemático). Placa: antipads del plano GND a 0,3 mm (Power Plane Clearance), comentarios
nuevos de C22/C23/L2 sin mover sus designadores, designador de L2 fuera de la máscara de U6 (ya chocaba), identificación en
la serigrafía inferior, re-vertido de polígonos, DRC y guardado. Esquemático: Y1 de CL 10 pF, C22/C23 de 12 pF y L2 bobinada.
Las salidas se regeneran después con auditoria_salidas.py."""
import subprocess
from drc_comun import *

QGA = '/mnt/sda3/vms/altium/qga.py'
qga = lambda c: subprocess.run([QGA, c], capture_output=True, text=True).stdout.strip()
COMENT = {'C22': '12pF C0G', 'C23': '12pF C0G', 'L2': 'LQW18AN47NJ00D'}
MPN = {'C22': 'GRM1885C1H120JA01D', 'C23': 'GRM1885C1H120JA01D', 'Y1': 'ABM8-25.000MHZ-10-D1G-T', 'L2': 'LQW18AN47NJ00D'}
TEXTO, CAJA = 'ELO301 G1  v1.1  2026-11', (22.0, 8.0, 26.0)   # caja libre en Bottom Overlay: x, y, ancho (mm)
L2_DESIGNADOR = (63.03, 34.1)   # esquina inferior izquierda (mm): sobre L2, fuera de la máscara de U6

print(qga(rf"New-Item -ItemType Directory -Force C:\Users\Public\respaldo_auditoria | Out-Null; Copy-Item {L}*.PcbDoc,{L}*.SchDoc,{L}*.OutJob C:\Users\Public\respaldo_auditoria\ -Force; (Get-ChildItem C:\Users\Public\respaldo_auditoria).Count"), 'archivos respaldados')

# al cambiar el comentario Altium reubica el designador: se guarda su posición y se repone
com = ''.join(f"""    C := Board.GetPcbComponentByRefDes('{d}');
    if C <> nil then
    begin
        x0 := C.Name.XLocation; y0 := C.Name.YLocation;
        C.BeginModify; C.Comment.Text := '{t}'; C.ChangeNameAutoposition(eAutoPos_Manual); C.EndModify;
        C.Name.BeginModify; C.Name.XLocation := x0; C.Name.YLocation := y0; C.Name.EndModify;
    end;
""" for d, t in COMENT.items())
r = correr(f"""{VARS}    T : IDispatch;
    BB : TCoordRect;
{ABRIR}s := '';
Lista := TInterfaceList.Create; T := nil;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eRuleObject, eTextObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do
begin
    if X.ObjectId = eRuleObject then begin if X.RuleKind = eRule_PowerPlaneClearance then Lista.Add(X); end
    else if (X.Layer = eBottomOverlay) and (not X.InComponent) then begin if X.Text = '{TEXTO}' then T := X; end;
    X := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
PCBServer.PreProcess;
try
    for i := 0 to Lista.Count - 1 do
    begin
        X := Lista.items[i]; X.BeginModify; X.Clearance := MMsToCoord(0.3); X.EndModify;
        s := s + 'regla ' + X.Name + ' = 0,3 mm' + #10;
    end;
{com}    C := Board.GetPcbComponentByRefDes('L2'); BB := C.Name.BoundingRectangle;
    C.Name.BeginModify; C.Name.MoveByXY(Board.XOrigin + MMsToCoord({L2_DESIGNADOR[0]}) - BB.Left, Board.YOrigin + MMsToCoord({L2_DESIGNADOR[1]}) - BB.Bottom); C.Name.EndModify;
    if T = nil then
    begin
        T := PCBServer.PCBObjectFactory(eTextObject, eNoDimension, eCreate_Default);
        T.XLocation := Board.XOrigin + MMsToCoord({CAJA[0]}); T.YLocation := Board.YOrigin + MMsToCoord({CAJA[1]});
        T.Layer := eBottomOverlay; T.Text := '{TEXTO}'; T.Size := MMsToCoord(1.0); T.Width := MMsToCoord(0.15); T.MirrorFlag := True;
        Board.AddPCBObject(T); PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, T.I_ObjectAddress);
    end;
    BB := T.BoundingRectangle;
    T.MoveByXY(Board.XOrigin + MMsToCoord({CAJA[0]}) + (MMsToCoord({CAJA[2]}) - (BB.Right - BB.Left)) div 2 - BB.Left, Board.YOrigin + MMsToCoord({CAJA[1]}) - BB.Bottom);
    BB := T.BoundingRectangle;
    s := s + 'texto x=' + FormatFloat('0.00', CoordToMMs(BB.Left - Board.XOrigin)) + '..' + FormatFloat('0.00', CoordToMMs(BB.Right - Board.XOrigin)) + ' y=' + FormatFloat('0.00', CoordToMMs(BB.Bottom - Board.YOrigin)) + '..' + FormatFloat('0.00', CoordToMMs(BB.Top - Board.YOrigin)) + #10;
finally
    PCBServer.PostProcess;
end;
Lista := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(ePolyObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do begin Lista.Add(X); X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
for i := 0 to Lista.Count - 1 do
begin
    Poly := Lista.items[i];
    PCBServer.PreProcess;
    try
        Poly.BeginModify; Poly.SetState_CopperPourInvalid; Poly.Rebuild; Poly.EndModify; Poly.GraphicallyInvalidate;
    finally
        PCBServer.PostProcess;
    end;
end;
{RESUMEN}{GUARDAR}ResultText := s;""")
resumen(r, 'placa tras la auditoría')
print('\n'.join(l for l in r.split('\n') if l.startswith(('regla', 'texto'))), '| PcbDoc guardado', hora_pcb())

casos = ''.join(f"            if d = '{k}' then begin mpn := '{v}';" + (f" X.Comment.Text := '{COMENT[k]}';" if k in COMENT else '') + " end;\n" for k, v in MPN.items())
hojas = ['01_Alimentacion', '02_MCU', '03_Sensores', '04_Conectores']
r = correr("""var
    Doc, It, X, PIt, Par : IDispatch;
    d, mpn, s : String;
    n : Integer;
begin
s := '';
""" + ''.join(f"""Doc := OpenSchDoc('{L}{h}.SchDoc'); n := 0;
It := Doc.SchIterator_Create; It.AddFilter_ObjectSet(MkSet(eSchComponent));
X := It.FirstSchObject;
while X <> nil do
begin
    d := X.Designator.Text; mpn := '';
{casos}    if mpn <> '' then
    begin
        PIt := X.SchIterator_Create; PIt.AddFilter_ObjectSet(MkSet(eParameter));
        Par := PIt.FirstSchObject;
        while Par <> nil do begin if Par.Name = 'Manufacturer Part Number' then Par.Text := mpn; Par := PIt.NextSchObject; end;
        X.SchIterator_Destroy(PIt);
        n := n + 1; s := s + d + ' = ' + X.Comment.Text + ' / ' + mpn + ' ({h})' + #10;
    end;
    X := It.NextSchObject;
end;
Doc.SchIterator_Destroy(It);
if n > 0 then SaveDoc('{L}{h}.SchDoc');
""" for h in hojas) + "ResultText := s;\nend;")
print(r)
