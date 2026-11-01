"""Números LCSC en el esquemático (parámetro oculto «LCSC Part #») y C22/C23, J1, J2 con las piezas que JLCPCB puede armar,
leídos del BOM del repo. Después recarga el proyecto (OpenSchDoc edita una copia aparte) para que «Update PCB» vea lo nuevo.
Uso: python3 lcsc_esquematico.py <BOM_ELO301_G1.csv>"""
import csv, sys
from drc_comun import *

NUEVO = {'C22', 'C23', 'J1', 'J2'}   # en estos cambian también fabricante y MPN
tl, tf, tm = [], [], []
for r in csv.DictReader(open(sys.argv[1], newline='')):
    for d in r['Designator'].split(','):
        tl.append(f"{d}={r['LCSC Part #']}")
        if d in NUEVO:
            tf.append(f"{d}={r['Manufacturer']}"); tm.append(f"{d}={r['Manufacturer Part Number']}")
# tablas ';D=valor;' troceadas: DelphiScript no acepta literales de más de 255 caracteres
tabla = lambda v, xs: f"{v} := ';';\n" + ''.join(f"{v} := {v} + '{';'.join(xs[i:i + 8])};';\n" for i in range(0, len(xs), 8))
buscar = lambda v, t: f"    k := Pos(';' + d + '=', {t}); {v} := '';\n    if k > 0 then begin {v} := Copy({t}, k + Length(d) + 2, 60); {v} := Copy({v}, 1, Pos(';', {v}) - 1); end;\n"
hojas = ['01_Alimentacion', '02_MCU', '03_Sensores', '04_Conectores']
r = correr("""var
    Doc, It, X, PIt, Par, P : IDispatch;
    Comps : TInterfaceList;
    TL, TF, TM, d, lcsc, fab, mpn, s : String;
    i, k, n, hay : Integer;
begin
s := '';
""" + tabla('TL', tl) + tabla('TF', tf) + tabla('TM', tm) + ''.join(f"""Doc := OpenSchDoc('{L}{h}.SchDoc'); n := 0;
Comps := TInterfaceList.Create;
It := Doc.SchIterator_Create; It.AddFilter_ObjectSet(MkSet(eSchComponent));
X := It.FirstSchObject;
while X <> nil do begin Comps.Add(X); X := It.NextSchObject; end;
Doc.SchIterator_Destroy(It);
for i := 0 to Comps.Count - 1 do
begin
    X := Comps.items[i]; d := X.Designator.Text;
{buscar('lcsc', 'TL')}{buscar('fab', 'TF')}{buscar('mpn', 'TM')}    if lcsc <> '' then
    begin
        hay := 0;
        PIt := X.SchIterator_Create; PIt.AddFilter_ObjectSet(MkSet(eParameter));
        Par := PIt.FirstSchObject;
        while Par <> nil do
        begin
            if Par.Name = 'LCSC Part #' then begin Par.Text := lcsc; hay := 1; end;
            if (fab <> '') and (Par.Name = 'Manufacturer') then Par.Text := fab;
            if (mpn <> '') and (Par.Name = 'Manufacturer Part Number') then Par.Text := mpn;
            Par := PIt.NextSchObject;
        end;
        X.SchIterator_Destroy(PIt);
        if hay = 0 then
        begin
            P := SchServer.SchObjectFactory(eParameter, eCreate_Default);
            P.Name := 'LCSC Part #'; P.Text := lcsc; P.IsHidden := True;
            P.Location := Point(X.Location.X, X.Location.Y);
            X.AddSchObject(P);
        end;
        n := n + 1;
    end;
end;
if n > 0 then SaveDoc('{L}{h}.SchDoc');
s := s + '{h}: ' + IntToStr(n) + ' componentes' + #10;
""" for h in hojas) + "ResultText := s;\nend;")
print(r)
print(correr(f"""var Obj1 : IDispatch;
begin
GetWorkspace.DM_CloseProject('{L}ELO301_G1.PrjPcb'); GetWorkspace.DM_OpenProject('{L}ELO301_G1.PrjPcb', True);
Obj1 := Client.OpenDocument('SCH', '{L}02_MCU.SchDoc'); Client.ShowDocument(Obj1); ResetParameters; AddStringParameter('Action', 'Document'); RunProcess('Sch:Zoom');
ResultText := 'recargado: ' + GetWorkspace.DM_FocusedProject.DM_ProjectFullPath;
end;"""))
