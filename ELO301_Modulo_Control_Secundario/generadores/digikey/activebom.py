"""ActiveBOM (ELO301_G1.BomDoc) con el formato del proyecto del profesor (RS485 Gateway.BomDoc).

Las opciones de vista y de revisión se copian de su archivo (activebom_opciones.txt). Cada línea de la BOM es un
CatalogItem (biblioteca\\símbolo + comentario + descripción, como agrupa Altium) con sus PartChoice tomados de los
parámetros del esquemático: «Supplier 1» (DigiKey, primero) y «Supplier 2» (LCSC). Altium los reconoce como
AUTO_SCHLINKS y, con conexión, completa precio y stock.
Uso (con Altium abierto en la VM): python3 activebom.py  -> escribe ../../altium/ELO301_G1.BomDoc
"""
import collections, datetime, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'pcb'))
from drc_comun import correr, L

SALIDA = os.path.join(AQUI, '..', '..', 'altium', 'ELO301_G1.BomDoc')


def componentes():
    r = correr("""var
    Prj, Fl, C, Pm : IDispatch;
    i, j : Integer;
    s : String;
begin
s := ''; Prj := GetWorkspace.DM_FocusedProject; Prj.DM_Compile; Fl := Prj.DM_DocumentFlattened;
for i := 0 to Fl.DM_ComponentCount - 1 do begin
  C := Fl.DM_Components(i);
  s := s + 'C' + #9 + C.DM_PhysicalDesignator + #9 + C.DM_SourceLibraryName + #9 + C.DM_LibraryReference + #9 + C.DM_Comment + #9 + C.DM_Description + #10;
  for j := 0 to C.DM_ParameterCount - 1 do begin Pm := C.DM_Parameters(j); s := s + 'P' + #9 + C.DM_PhysicalDesignator + #9 + Pm.DM_Name + #9 + Pm.DM_Value + #10; end;
end;
ResultText := s;
end;""", 300)
    comp, par = {}, collections.defaultdict(dict)
    for l in r.splitlines():
        c = l.split('\t')
        if c[0] == 'C': comp[c[1]] = dict(lib=c[2], ref=c[3], com=c[4], desc=c[5])
        elif c[0] == 'P': par[c[1]][c[2]] = c[3] if len(c) > 3 else ''
    return comp, par


def csv(*v):  # como Altium escribe SELECTEDPARAMETERSHASH: comillas si hay espacio, coma o comillas
    return ','.join('"' + x.replace('"', '""') + '"' if any(ch in x for ch in ' ,"') else x for x in v)


def limpio(x):
    return x.replace('|', '/').replace('\n', ' ')


def bomdoc(comp, par):
    grupos = collections.OrderedDict()
    for d in sorted(comp, key=lambda d: (d.rstrip('0123456789'), int(d[len(d.rstrip('0123456789')):] or 0))):
        c = comp[d]
        grupos.setdefault((c['lib'], c['ref'], c['com'], c['desc']), []).append(d)
    ahora = datetime.datetime.now()
    out = [f"|RECORD=BOM|VERSION=6|FILENAME={L}ELO301_G1.$$$|KIND=ALTIUM_DESIGNER_LIVEBOM|DATE={ahora:%d.%m.%Y}|TIME={ahora:%H:%M:%S}|CURRENCY=USD"
           "|PRODUCTIONQUANTITY=1|PERUNITTARGETPRICE=0|PERUNITACTUALPRICE=0"]
    out += open(os.path.join(AQUI, 'activebom_opciones.txt'), encoding='latin-1').read().strip().split('\n')
    sin_digikey = []
    for n, ((lib, ref, com, desc), ds) in enumerate(grupos.items(), 1):
        p = par[ds[0]]
        out.append(f"|RECORD=CatalogItem|ITEMTYPE=Automatic-NonVault|UNIQUEID={lib}\\{ref}|DESIGNITEMID={ref}|ITEMSOURCE={lib}|STATUS=Unknown"
                   f"|DESCRIPTION={limpio(desc)}|USERCOMMENTS={limpio(com)}|NOTE=|LINENUMBER={n}|SELECTEDPARAMETERSHASH={limpio(csv(com, desc))}"
                   f"|COMPONENTPARAMETERS=|CUSTOMPARAMETERS=")
        for k, rango in (('1', 1), ('2', 2)):
            sup, spn = p.get(f'Supplier {k}', ''), p.get(f'Supplier Part Number {k}', '')
            if not sup or not spn: continue
            out.append(f"|RECORD=PartChoice|PARTCHOICETYPE=AUTO_SCHLINKS|SUPPLIERSOURCE=|MANUFACTURER={limpio(p.get('Manufacturer', ''))}"
                       f"|MANUFACTURERALIASES=|MANUFACTURERPARTNO={limpio(p.get('Manufacturer Part Number', ''))}|CIIVAID=|SUPPLIER={sup}|SUPPLIERPARTNO={spn}"
                       f"|PROVIDERNAME=|PROVIDERGUID=|DESCRIPTION={limpio(desc)}|RANK={rango}|AVAILABLEQUANTITY=0|BESTUNITPRICE=0|CURRENCY=USD|ORIGINALCURRENCY=USD"
                       f"|SUPPLIERURL=|PRODUCTPHOTOURL=|MANUFACTURERPACKAGING=|SUPPLIERPACKAGING=|DATASHEETS=|LIFECYCLESTATUSID=|LIFECYCLESTATUS=|LASTUPDATEDAT=0|LASTUPDATED=|PRICECOUNT=0")
        if p.get('Supplier 1') != 'DigiKey': sin_digikey.append(f"{','.join(ds)} ({p.get('Supplier 1') or 'sin proveedor'})")
        out.append("|RECORD=PartChoiceGroups|GROUPBYFIELDCOUNT=0")
    open(SALIDA, 'w', encoding='latin-1', errors='replace', newline='\n').write('\n'.join(out) + '\n')
    return len(grupos), sum(map(len, grupos.values())), sin_digikey


if __name__ == '__main__':
    n, piezas, sin = bomdoc(*componentes())
    print(f'{n} líneas, {piezas} piezas -> {os.path.normpath(SALIDA)}; sin DigiKey como proveedor 1: {sin}')
