r"""Plan de serigrafía de la placa: cada línea de Top/Bottom Overlay pasa a ANCHO mm y se recorta lo que quede a menos
de HOLG mm del cobre de un pad de su cara (los THT cuentan en ambas). Los tramos de menos de MINIMO mm se descartan.
Escribe %TEMP%\altium_simbolos\seda_plan.tsv para Placa.pas (SerigrafiaPlaca), en unidades de 0,1 µm.
Uso: seda_plan.py ELO301_G1.PcbDoc [ANCHO=0.18] [HOLG=0.2] [MINIMO=0.25]"""
import os
import sys
from collections import Counter, defaultdict

from shapely.geometry import LineString
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from altium_leer import forma_pad, leer_pcb, pads_vias

ruta = sys.argv[1]
ANCHO, HOLG, MINIMO = (float(v) for v in (sys.argv[2:5] + ['0.18', '0.2', '0.25'][len(sys.argv[2:5]):]))
O = 25.4
comps, redes, pistas, arcos, textos, tab = leer_pcb(ruta)
pads, vias = pads_vias(ruta)
cobre = {'top': [], 'bot': []}
for p in pads:
    if p['h'] > 0 or p['capa'] == 74:
        cobre['top'].append(forma_pad(p, 'top')); cobre['bot'].append(forma_pad(p, 'bot'))
    elif p['capa'] == 1:
        cobre['top'].append(forma_pad(p, 'top'))
    elif p['capa'] == 32:
        cobre['bot'].append(forma_pad(p, 'bot'))
zona = {k: unary_union(v).buffer(HOLG + ANCHO / 2, 32) for k, v in cobre.items()}
res, por = Counter(), defaultdict(Counter)
q = lambda v: str(round(v * 10000))
with open(os.path.join(os.environ['TEMP'], 'altium_simbolos', 'seda_plan.tsv'), 'w', newline='\r\n') as f:
    for t in pistas:
        if t['capa'] not in (33, 34):
            continue
        ln = LineString([(t['x1'] - O, t['y1'] - O), (t['x2'] - O, t['y2'] - O)])
        resto = ln.difference(zona['top' if t['capa'] == 33 else 'bot'])
        piezas = [g for g in (getattr(resto, 'geoms', None) or [resto]) if not g.is_empty and g.length >= MINIMO]
        estado = ('intacto' if abs(resto.length - ln.length) < 1e-3 else
                  'eliminado' if not piezas else 'recortado' if len(piezas) == 1 else 'partido')
        res[estado] += 1
        por[comps[t['comp']].get('PATTERN') if t['comp'] is not None else '(libre)'][estado] += 1
        f.write('\t'.join([str(t['capa'])] + [q(v) for v in ln.coords[0] + ln.coords[-1]] + [str(len(piezas))] +
                          [q(v) for g in piezas for v in g.coords[0] + g.coords[-1]]) + '\n')
print('líneas:', dict(res))
for h, c in sorted(por.items()):
    print(f'  {h:30s} {dict(c)}')
