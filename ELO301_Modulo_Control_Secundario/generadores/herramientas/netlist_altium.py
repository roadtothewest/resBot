"""Netlist aplanada del esquemático compilado en Altium -> JSON {"U4-1": "V3V3_MCU", ...}. Uso: netlist_altium.py salida.json (VM con altium-mcp)."""
import json, sys
sys.path.insert(0, '/mnt/sda3/vms/altium')
from construir_hoja import mcp

S = r"""var
    Prj, Fl, C, P : IDispatch;
    i, j : Integer;
    s : String;
begin
    Prj := GetWorkspace.DM_FocusedProject;
    Prj.DM_Compile;
    Fl := Prj.DM_DocumentFlattened;
    s := '';
    for i := 0 to Fl.DM_ComponentCount - 1 do
    begin
        C := Fl.DM_Components(i);
        for j := 0 to C.DM_PinCount - 1 do
        begin
            P := C.DM_Pins(j);
            s := s + C.DM_PhysicalDesignator + '-' + P.DM_PinNumber + '=' + P.DM_FlattenedNetName + #10;
        end;
    end;
    ResultText := s;
end;
"""
d = json.loads(mcp('run_altium_script', {'script': S, 'timeout_seconds': 120}))
if not d.get('success'): sys.exit(str(d)[:800])
n = dict(sorted(l.strip().split('=', 1) for l in d['result'].split('\n') if '=' in l))
json.dump(n, open(sys.argv[1], 'w'), indent=0, ensure_ascii=False)
print(len(n), 'pines;', len(set(n.values())), 'redes')
