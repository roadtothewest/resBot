"""Funciones comunes: correr scripts, DRC sin diálogo con conexiones pendientes y resumen por regla."""
import collections, json, sys
sys.path.insert(0, '/mnt/sda3/vms/altium')
from construir_hoja import mcp, L

def correr(cuerpo, t=900):
    d = json.loads(mcp('run_altium_script', {'script': cuerpo, 'timeout_seconds': t}))
    if not d.get('success'):
        sys.exit(f"script falló: {d.get('error')} {d.get('altium_message', '')} {d.get('steps', [])[-3:]}")
    return d.get('result', '')

ABRIR = f"Obj1 := Client.OpenDocument('PCB', '{L}ELO301_G1.PcbDoc'); Client.ShowDocument(Obj1);\nBoard := PCBServer.GetCurrentPCBBoard;\n"
RESUMEN = r"""Board.RunBatchDesignRuleCheck('C:\Users\Public\drc_elo301.html', 0, False, False);
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eConnectionObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject; s := s + #10 + 'SIN RUTEAR:';
while X <> nil do
begin
    s := s + ' ' + X.Net.Name + '(' + FormatFloat('0.0', CoordToMMs(X.X1 - Board.XOrigin)) + ',' + FormatFloat('0.0', CoordToMMs(X.Y1 - Board.YOrigin)) + ')-(' + FormatFloat('0.0', CoordToMMs(X.X2 - Board.XOrigin)) + ',' + FormatFloat('0.0', CoordToMMs(X.Y2 - Board.YOrigin)) + ')';
    X := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eViolationObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
V := It.FirstPCBObject; n := 0;
while V <> nil do
begin
    n := n + 1;
    nom := '?';
    try nom := V.Rule.Name; except end;
    if n <= 400 then
    begin
        s := s + #10 + nom + '~' + V.Description;
        try if V.Primitive1 <> nil then s := s + ' | ' + V.Primitive1.Descriptor; except end;
        try if V.Primitive2 <> nil then s := s + ' | ' + V.Primitive2.Descriptor; except end;
    end;
    V := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
s := s + #10 + 'violaciones ' + IntToStr(n);
"""
VARS = """var
    Board, It, X, V, C, GND, Poly, Lib, FP : IDispatch;
    Seg : TPolySegment;
    Cache : TPadCache;
    Lista : TInterfaceList;
    s, nom : String;
    i, k, n, nt, nv, x0, y0, x1, y1 : Integer;
"""

def resumen(r, titulo):
    lineas = r.split('\n')
    print(f'== {titulo}:', [l for l in lineas if l.startswith('violaciones')][0], '|', [l for l in lineas if l.startswith('SIN RUTEAR')][0][:600])
    por = collections.defaultdict(list)
    for l in lineas:
        if '~' in l:
            regla, desc = l.split('~', 1)
            por[regla].append(desc)
    for regla, ds in sorted(por.items(), key=lambda x: -len(x[1])):
        print(f'  {regla}: {len(ds)}')
        for x in ds[:16]:
            print('      ', x[:200])
    return por


# guardado directo del documento abierto (SaveDoc no guardó la placa tras un PreProcess sin PostProcess)
GUARDAR = "Obj1.SetModified(True); Obj1.DoFileSave('');\n"


def hora_pcb():
    import subprocess
    return subprocess.run(['/mnt/sda3/vms/altium/qga.py', r"(Get-Item C:\Users\altium\Documents\Altium\ELO301_G1\ELO301_G1.PcbDoc).LastWriteTime.ToString('HH:mm:ss')"],
                          capture_output=True, text=True).stdout.strip().splitlines()[-1]
