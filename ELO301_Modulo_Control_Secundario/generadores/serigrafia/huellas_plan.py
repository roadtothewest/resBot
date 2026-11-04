"""Plan de serigrafía para las huellas de las bibliotecas: líneas a 0,18 mm, recortadas a 0,2 mm del cobre de los pads
propios (mismo criterio que en la placa). Lee huellas.tsv (VolcarHuellas) y escribe huellas_plan.tsv para Altium:
biblioteca, índice de huella, capa, extremos originales, número de tramos y tramos (0,1 µm).
Uso: huellas_plan.py ELO301_G1.PcbDoc (de la placa se toma el radio de esquina de los pads redondeados)."""
import os, sys
from collections import Counter
from shapely.geometry import LineString, Point, box
from shapely import affinity
from shapely.ops import unary_union
ANCHO, HOLG, MINIMO = 0.18, 0.2, 0.25
base = os.path.join(os.environ['TEMP'], 'altium_simbolos')
huellas = []          # (lib, idx, nombre, pads, pistas)
idx_por_lib = Counter()
for linea in open(os.path.join(base, 'huellas.tsv'), encoding='latin-1'):
    f = linea.rstrip('\r\n').split('\t')
    if f[0] == 'FP':
        lib = int(f[1]); huellas.append([lib, idx_por_lib[lib], f[2], [], []]); idx_por_lib[lib] += 1
    elif f[0] == 'PAD':
        x, y, xs, ys, forma, rot, h, capa = (int(v) for v in f[1:9])
        huellas[-1][3].append((x / 1e4, y / 1e4, xs / 1e4, ys / 1e4, forma, rot / 1000, h / 1e4, capa))
    elif f[0] == 'TRK':
        capa, x1, y1, x2, y2, w = (int(v) for v in f[1:7])
        huellas[-1][4].append((capa, x1 / 1e4, y1 / 1e4, x2 / 1e4, y2 / 1e4, w / 1e4))
capas = Counter(t[0] for h in huellas for t in h[4])
print('capas de pistas en las huellas:', dict(capas))
SEDA = {33, 34}
# radio de esquina de los pads de rectángulo redondeado: se toma de las instancias en la placa (misma huella y tamaño)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from altium_leer import leer_pcb, pads_vias
_comps = leer_pcb(sys.argv[1])[0]
_pat = {c.get('SOURCEDESIGNATOR'): c.get('PATTERN') for c in _comps}
RADIO = {}
for pp in pads_vias(sys.argv[1])[0]:
    if pp.get('alt') == 9:
        RADIO[(_pat.get(pp['comp']), round(pp['tx'], 3), round(pp['ty'], 3))] = pp['radio']


def forma_pad(p, nombre=''):
    x, y, tx, ty, forma, rot = p[:6]
    r9 = RADIO.get((nombre, round(tx, 3), round(ty, 3)))
    if forma == 9 and r9 is None:
        print('   sin radio para', nombre, tx, ty, '-> rectángulo (conservador)')
    if forma == 9 and r9:
        g = box(-tx / 2 + r9, -ty / 2 + r9, tx / 2 - r9, ty / 2 - r9).buffer(r9, 16)
    elif forma == 1:
        r = min(tx, ty) / 2
        g = box(-tx / 2 + r, -ty / 2 + r, tx / 2 - r, ty / 2 - r).buffer(r, 32) if abs(tx - ty) > 1e-6 else Point(0, 0).buffer(r, 64)
    else:
        g = box(-tx / 2, -ty / 2, tx / 2, ty / 2)
    return affinity.translate(affinity.rotate(g, rot, origin=(0, 0)), x, y)
q = lambda v: str(round(v * 10000))
res = Counter()
with open(os.path.join(base, 'huellas_plan.tsv'), 'w', newline='\r\n') as f:
    for lib, i, nombre, pads, pistas in huellas:
        top = [forma_pad(p, nombre) for p in pads if p[7] in (1, 74) or p[6] > 0]
        zona = unary_union(top).buffer(HOLG + ANCHO / 2, 32) if top else None
        por = Counter()
        for capa, x1, y1, x2, y2, w in pistas:
            if capa not in SEDA: continue
            ln = LineString([(x1, y1), (x2, y2)])
            resto = ln.difference(zona) if zona is not None else ln
            piezas = [g for g in (getattr(resto, 'geoms', None) or [resto]) if not g.is_empty and g.length >= MINIMO]
            estado = 'intacta' if abs(resto.length - ln.length) < 1e-6 else ('eliminada' if not piezas else ('recortada' if len(piezas) == 1 else 'partida'))
            por[estado] += 1; res[estado] += 1
            f.write('\t'.join([str(lib), str(i), str(capa)] + [q(v) for v in (x1, y1, x2, y2)] + [str(len(piezas))] +
                              [q(v) for g in piezas for v in (g.coords[0] + g.coords[-1])]) + '\n')
        print(f'  {nombre:28s} {dict(por)}')
print('total:', dict(res))
