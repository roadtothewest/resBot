"""Repone las clases de red que solo existen en la placa (las usan las reglas Ancho_Potencia y Ancho_Alimentacion).
«Update PCB» propone borrarlas («Remove Net Classes»): hay que desmarcar ese grupo, o correr esto después. DRC y guardado."""
from drc_comun import *

CLASES = {'Alimentacion': ['V3V3_MCU', 'V3V3_SENS', 'VDDA', 'V5_SENS'], 'Potencia': ['VIN_12V', 'VIN_PROT', 'SW', 'V_5V']}
nuevas = ''.join(f"""if Pos(';{c};', hay) = 0 then
begin
    NC := PCBServer.PCBClassFactoryByClassMember(eClassMemberKind_Net); NC.SuperClass := False; NC.Name := '{c}';
    Board.AddPCBObject(NC);
""" + ''.join(f"    NC.AddMemberByName('{n}');\n" for n in ns) + f"    s := s + 'repuesta {c}' + #10;\nend;\n" for c, ns in CLASES.items())
r = correr(f"""{VARS}    NC : IDispatch;
    hay : String;
{ABRIR}s := ''; hay := ';';
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eClassObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do begin if X.MemberKind = eClassMemberKind_Net then hay := hay + X.Name + ';'; X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
s := s + 'clases de red antes:' + hay + #10;
PCBServer.PreProcess;
{nuevas}PCBServer.PostProcess;
{RESUMEN}{GUARDAR}ResultText := s;""")
resumen(r, 'placa con las clases de red')
print('\n'.join(l for l in r.split('\n') if l.startswith(('clases', 'repuesta'))), '| PcbDoc guardado', hora_pcb())
