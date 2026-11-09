"""Huella en las bibliotecas genéricas CAP, RESISTOR, INDUCTOR y DIODE, que no tenían ninguna.

Sin modelo, al generar salidas Altium advierte «Footprint of component ... cannot be found» por cada una. Las instancias
del esquemático ya traen su huella y no cambian: esto solo completa la biblioteca, como en LED y FERRITE - GENERIC.
INDUCTOR lleva las dos huellas que usa la placa (L1 SRN4018, L2 L0603), para que «Update from Libraries» no le cambie
la suya a ninguna. DIODE - GENERIC no se usa en la placa. Solo toca bibliotecas sin ningún modelo.
Uso (con Altium abierto en la VM): python3 huellas_genericas.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pcb'))
from drc_comun import correr, L

HUELLAS = {'CAP - GENERIC': [('C0603 - MURATA', 'C0603 - MURATA.PcbLib')],
           'RESISTOR - GENERIC': [('R0603 - YAGEO', 'R0603 - YAGEO.PcbLib')],
           'INDUCTOR - GENERIC': [('SRN4018 - BOURNS', 'ELO301_G1.PcbLib'), ('L0603 - GENERIC', 'ELO301_G1.PcbLib')],
           'DIODE - GENERIC': [('SMA - DIODES', 'ELO301_G1.PcbLib')]}

if __name__ == '__main__':
    cod = "var\n    Doc, SL, It, C, Im, PL, Lib : IDispatch;\n    s : String;\n    n : Integer;\nbegin\ns := '';\n"
    for pcblib in sorted({l for v in HUELLAS.values() for _, l in v}):  # primero, que cada huella exista
        cod += f"PL := Client.OpenDocument('PCBLIB', '{L}{pcblib}'); Client.ShowDocument(PL); Lib := PCBServer.GetCurrentPCBLibrary;\n"
        for h in sorted({h for v in HUELLAS.values() for h, l in v if l == pcblib}):
            cod += f"if Lib.GetComponentByName('{h}') = nil then s := s + 'FALTA {h} en {pcblib}; ';\n"
    cod += "if s = '' then begin\n"
    for lib, hs in HUELLAS.items():
        cod += f"""Doc := Client.OpenDocument('SCHLIB', '{L}{lib}.SchLib'); Client.ShowDocument(Doc); SL := SchServer.GetCurrentSchDocument;
It := SL.SchLibIterator_Create; It.AddFilter_ObjectSet(MkSet(eSchComponent)); C := It.FirstSchObject; SL.SchIterator_Destroy(It);
n := 0; It := C.SchIterator_Create; It.AddFilter_ObjectSet(MkSet(eImplementation)); Im := It.FirstSchObject;
while Im <> nil do begin n := n + 1; Im := It.NextSchObject; end;
C.SchIterator_Destroy(It);
if n = 0 then begin
"""
        for i, (h, pcblib) in enumerate(hs):
            cod += (f"  Im := C.AddSchImplementation; Im.ModelName := '{h}'; Im.ModelType := 'PCBLIB'; "
                    f"Im.AddDataFileLink('{h}', '{pcblib}', 'PCBLib'); Im.IsCurrent := {'True' if i == 0 else 'False'};\n")
        cod += f"  Doc.SetModified(True); Doc.DoFileSave(''); s := s + '{lib}: {len(hs)} huella(s); ';\nend else s := s + '{lib}: ya tenía; ';\n"
    print(correr(cod + "end;\nResultText := s;\nend;", 120))
