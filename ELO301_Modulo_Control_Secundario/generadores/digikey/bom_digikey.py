"""BOM de fabricación con DigiKey como proveedor principal, leído directamente de los esquemáticos y la placa de Altium.
Agrupa por número de parte, valor y huella. Las perforaciones M3 (H*) no son piezas y quedan fuera.
Columnas: las de DigiKey (fabricante, MPN, código DigiKey) y, para armar en JLCPCB, Comment/Designator/Footprint/LCSC Part #.
Uso: bom_digikey.py <carpeta altium> <archivo .csv de salida>"""
import csv
import os
import re
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'serigrafia'))
from altium_leer import leer_pcb, registros_sch

HOJAS = ('01_Alimentacion', '02_MCU', '03_Sensores', '04_Conectores')
altium, salida = sys.argv[1], sys.argv[2]


def componentes(ruta):
    regs = registros_sch(ruta)
    comps = {i: {'desc': r.get('COMPONENTDESCRIPTION', ''), 'param': {}} for i, r in enumerate(regs) if r.get('RECORD') == '1'}
    for r in regs:
        dueno = int(r.get('OWNERINDEX', -1))
        if dueno in comps:
            if r.get('RECORD') == '34':
                comps[dueno]['des'] = r.get('TEXT', '')
            elif r.get('RECORD') == '41':
                comps[dueno]['param'][r.get('NAME', '')] = r.get('TEXT', '')
    return [c for c in comps.values() if 'des' in c]


def proveedor(p, nombre):
    """Código del proveedor `nombre` en Supplier 1 o Supplier 2."""
    for k in ('1', '2'):
        if p.get(f'Supplier {k}', '').strip().lower() == nombre.lower():
            return p.get(f'Supplier Part Number {k}', '')
    return ''


huella = {c.get('SOURCEDESIGNATOR'): c.get('PATTERN', '') for c in leer_pcb(os.path.join(altium, 'ELO301_G1.PcbDoc'))[0]}
grupos = OrderedDict()
for hoja in HOJAS:
    for c in componentes(os.path.join(altium, hoja + '.SchDoc')):
        d, p = c['des'], c['param']
        if d.startswith('H'):
            continue
        clave = (p.get('Manufacturer Part Number', ''), p.get('Comment', ''), huella.get(d, ''))
        g = grupos.setdefault(clave, {'des': [], 'p': p, 'desc': c['desc'] or p.get('Description', '')})
        g['des'].append(d)


def orden(d):
    m = re.match(r'([A-Z]+)(\d+)', d)
    return (m.group(1), int(m.group(2))) if m else (d, 0)


filas = []
for (mpn, comentario, fp), g in grupos.items():
    p = g['p']
    des = sorted(g['des'], key=orden)
    dk = proveedor(p, 'DigiKey')
    filas.append({
        'Comment': comentario, 'Designator': ','.join(des), 'Footprint': fp, 'Qty': len(des),
        'Description': g['desc'].replace('\xb5', 'u').replace('\xb1', '+/-').replace('\xb0', ' deg'),
        'Manufacturer': p.get('Manufacturer', ''), 'Manufacturer Part Number': mpn,
        'DigiKey Part Number': dk, 'LCSC Part #': proveedor(p, 'LCSC'),
        'Nota': ' / '.join(n for n in ('' if dk else p.get('Nota DigiKey', 'No disponible en DigiKey'), p.get('Nota LCSC', '')) if n),
    })
filas.sort(key=lambda f: orden(f['Designator'].split(',')[0]))
campos = ['Comment', 'Designator', 'Footprint', 'Qty', 'Description', 'Manufacturer', 'Manufacturer Part Number',
          'DigiKey Part Number', 'LCSC Part #', 'Nota']
with open(salida, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=campos)
    w.writeheader()
    w.writerows(filas)
print(f'{len(filas)} líneas, {sum(f["Qty"] for f in filas)} piezas -> {salida}')
for f in filas:
    if not f['DigiKey Part Number'] or not f['LCSC Part #'] or not f['Footprint']:
        print('  falta algo:', f['Designator'], '| MPN', f['Manufacturer Part Number'], '| DigiKey', f['DigiKey Part Number'] or '-',
              '| LCSC', f['LCSC Part #'] or '-', '| huella', f['Footprint'] or '-')
