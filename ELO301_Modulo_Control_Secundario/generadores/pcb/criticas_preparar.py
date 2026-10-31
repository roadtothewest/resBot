"""Prepara el reruteo de los nodos críticos: respalda la placa en C:\\Users\\Public, gira L1 y mueve L2 según
colocacion.py, y borra el cobre libre de SW, BST, OSC_OUT, RF_IN y NetL2_1 más el tramo de V_5V que llegaba al pad
derecho de L1 (con L1 girada ese pad pasa a ser SW)."""
import json, subprocess
from drc_comun import *

print(subprocess.run(['/mnt/sda3/vms/altium/qga.py', r"Copy-Item C:\Users\altium\Documents\Altium\ELO301_G1\ELO301_G1.PcbDoc C:\Users\Public\ELO301_G1_antes_criticas.PcbDoc -Force; (Get-Item C:\Users\Public\ELO301_G1_antes_criticas.PcbDoc).Length"],
                     capture_output=True, text=True).stdout.strip().splitlines()[-1], 'bytes respaldados')
col = json.load(open('/tmp/colocacion.json'))
mover = [p for p in col['placements'] if p['designator'] in ('L1', 'L2')]
print('ubicación:', json.loads(mcp('place_components', {'placements': mover}))['result'])

REDES = ('SW', 'BST', 'OSC_OUT', 'RF_IN', 'NetL2_1')
V5_PISTAS = [(22.81, 16.94, 24.02, 16.94), (24.02, 16.94, 24.02, 18.0), (22.81, 11.81, 22.81, 16.94), (22.45, 11.46, 22.81, 11.81)]
V5_VIA = (22.81, 16.94)
cerca = lambda campo, eje, v: f"(Abs(CoordToMMs(X.{campo} - Board.{eje}Origin) - {v}) < 0.02)"
cond_pistas = ' or '.join('(' + ' and '.join((cerca('x1', 'X', a), cerca('y1', 'Y', b), cerca('x2', 'X', c), cerca('y2', 'Y', d))) + ')'
                          for a, b, c, d in V5_PISTAS)
cond_redes = ' or '.join(f"(nom = '{r}')" for r in REDES)
r = correr(f"""{VARS}{ABRIR}Lista := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eTrackObject, eArcObject, eViaObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject; nt := 0; nv := 0;
while X <> nil do
begin
    if (not X.InComponent) and (not X.InPolygon) and (X.Net <> nil) then
    begin
        nom := X.Net.Name;
        if {cond_redes} then Lista.Add(X)
        else if nom = 'V_5V' then
        begin
            if X.ObjectId = eViaObject then
            begin
                if {cerca('x', 'X', V5_VIA[0])} and {cerca('y', 'Y', V5_VIA[1])} then Lista.Add(X);
            end
            else if X.ObjectId = eTrackObject then
                if {cond_pistas} then Lista.Add(X);
        end;
    end;
    X := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
PCBServer.PreProcess;
try
    for i := 0 to Lista.Count - 1 do
    begin
        X := Lista.Items[i];
        if X.ObjectId = eViaObject then nv := nv + 1 else nt := nt + 1;
        Board.RemovePCBObject(X);
    end;
finally
    PCBServer.PostProcess;
end;
Board.ViewManager_FullUpdate;
{GUARDAR}ResultText := 'borradas ' + IntToStr(nt) + ' pistas y ' + IntToStr(nv) + ' vias';""")
print(r, '| guardado:', hora_pcb())
