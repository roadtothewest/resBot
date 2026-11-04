"""Verificación final de la serigrafía contra los mínimos de JLCPCB y las holguras elegidas.
Uso: verificar_seda.py ELO301_G1.PcbDoc designadores_resultado.tsv designadores.tsv"""
import sys, os, math
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import LineString, Point, box
from shapely import affinity
from shapely.ops import unary_union
from altium_leer import leer_pcb, pads_vias, forma_pad
ruta, res_tsv, dims_tsv = sys.argv[1:4]
O = 25.4
comps, redes, pistas, arcos, textos, tab = leer_pcb(ruta); pads, vias = pads_vias(ruta)
cobre = {'top': [], 'bot': []}
for p in pads:
    for l in (['top', 'bot'] if (p['h'] > 0 or p['capa'] == 74) else (['top'] if p['capa'] == 1 else ['bot'])):
        cobre[l].append(forma_pad(p, l))
cu = {l: unary_union(v) for l, v in cobre.items()}
seda = {'top': [], 'bot': []}
for t in pistas:
    if t['capa'] in (33, 34):
        seda['top' if t['capa'] == 33 else 'bot'].append((t, LineString([(t['x1'] - O, t['y1'] - O), (t['x2'] - O, t['y2'] - O)])))
print('Líneas de serigrafía:', sum(len(v) for v in seda.values()), 'anchos', dict(Counter(round(t['w'], 3) for v in seda.values() for t, _ in v)))
for l in ('top', 'bot'):
    d = min(g.distance(cu[l]) - t['w'] / 2 for t, g in seda[l])
    print(f'  {l}: distancia mínima línea-cobre de pad = {d:.3f} mm')
# textos visibles
vis = []
for t in textos:
    if t['capa'] not in (33, 34): continue
    if t['comp'] is not None:
        c = comps[t['comp']]
        if t['des'] and c.get('NAMEON', 'TRUE').upper() != 'TRUE': continue
        if t['coment'] and c.get('COMMENTON', 'FALSE').upper() != 'TRUE': continue
        if not t['des'] and not t['coment']: continue
    vis.append(t)
print('Textos visibles:', len(vis), 'alto/trazo:', dict(Counter((round(t['h'], 3), round(t['trazo'], 3)) for t in vis)))
cajas = {}
for linea in open(res_tsv, encoding='latin-1'):
    f = linea.rstrip('\r\n').split('\t')
    if len(f) >= 6 and f[1] == '1':
        L, B, R, T = (int(v) / 1e4 for v in f[2:6]); cajas[f[0]] = box(L, B, R, T)
for linea in open(dims_tsv, encoding='latin-1'):
    f = linea.rstrip('\r\n').split('\t')
    if f[0] == 'ID':
        L, B, R, T = (int(v) / 1e4 for v in f[4:8]); cajas['ID'] = box(L, B, R, T)
lado = {c.get('SOURCEDESIGNATOR'): ('bot' if c.get('LAYER', '').upper() == 'BOTTOM' else 'top') for c in comps}; lado['ID'] = 'bot'
tornillos = [Point(a['cx'] - O, a['cy'] - O).buffer(a['r'], 32) for a in arcos if a['capa'] == 71 and a['r'] > 3]
placa = box(0, 0, 70, 50)
peor = {'pad': (9, ''), 'seda': (9, ''), 'texto': (9, ''), 'borde': (9, '')}
for d, g in cajas.items():
    l = lado[d]
    peor['pad'] = min(peor['pad'], (g.distance(cu[l]), d))
    peor['seda'] = min(peor['seda'], (min(s.distance(g) - t['w'] / 2 for t, s in seda[l]), d))
    peor['borde'] = min(peor['borde'], (g.exterior.distance(placa.exterior) if placa.contains(g) else -1, d))
    for e, h in cajas.items():
        if e != d and lado[e] == l: peor['texto'] = min(peor['texto'], (g.distance(h), f'{d}/{e}'))
    if any(t.intersects(g) for t in tornillos): print('  TEXTO EN ZONA DE TORNILLO:', d)
print('Designadores visibles (cajas de Altium):', len(cajas) - 1, '+ identificación inferior')
for k, (v, d) in peor.items(): print(f'  mínimo texto-{k}: {v:.3f} mm ({d})')
