"""Ubica los designadores de 1,2 mm sin choques y escribe designadores_plan.tsv para Altium (DesignadoresUbicar).
Uso: designadores.py placa.PcbDoc designadores.tsv salida.png
Restricciones duras para el rectángulo del texto (el que informa Altium):
- dentro de la placa, a 0,3 mm del borde;
- a 0,21 mm del cobre de los pads de su cara (los THT cuentan en ambas): regla silk-máscara de 0,15 + máscara de 0,05;
- a 0,26 mm de toda línea de serigrafía y de los demás designadores (regla silk-silk de 0,254 mm);
- fuera del cuerpo (Mech 13/14) de toda pieza de su cara, incluida la propia;
- fuera de la zona de tornillo de las M3 (radio 3,45 mm);
- más cerca (0,15 mm o más) de su pieza que de cualquier otra del mismo tipo (mismo prefijo), contando los pads
  pasantes de las piezas de la otra cara, para que no se confunda.
Las perforaciones M3 no llevan designador; los que no caben quedan ocultos.
Las vías tapadas no son obstáculo duro: cada vía bajo el texto suma penalización."""
import math
import os
import sys
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point, box
from shapely import affinity
from shapely.ops import unary_union
from shapely.strtree import STRtree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from altium_leer import leer_pcb, pads_vias, forma_pad

ruta, tsv, png = sys.argv[1:4]
O = 25.4
ANCHO_X, ANCHO_Y = 70.0, 50.0
BORDE, D_PAD, D_SEDA, D_TXT = 0.3, 0.21, 0.26, 0.26
comps, redes, pistas, arcos, textos, tab = leer_pcb(ruta)
pads, vias = pads_vias(ruta)
idx = {c.get('SOURCEDESIGNATOR'): i for i, c in enumerate(comps)}
lado_de = {c.get('SOURCEDESIGNATOR'): ('bot' if c.get('LAYER', 'TOP').upper() == 'BOTTOM' else 'top') for c in comps}




# obstáculos por cara
cobre = {'top': [], 'bot': []}
pads_de = defaultdict(list)
for p in pads:
    lados = ['top', 'bot'] if (p['h'] > 0 or p['capa'] == 74) else (['top'] if p['capa'] == 1 else ['bot'])
    for l in lados:
        g = forma_pad(p, l)
        cobre[l].append(g)
        if l == lado_de.get(p['comp']):
            pads_de[p['comp']].append(g)
seda = {'top': [], 'bot': []}
seda_de = defaultdict(list)
for t in pistas:
    if t['capa'] in (33, 34):
        g = LineString([(t['x1'] - O, t['y1'] - O), (t['x2'] - O, t['y2'] - O)]).buffer(t['w'] / 2, 8)
        seda['top' if t['capa'] == 33 else 'bot'].append(g)
        seda_de[comps[t['comp']].get('SOURCEDESIGNATOR')].append(g)
cuerpo = {'top': [], 'bot': []}
cuerpo_de = {}
for d, i in idx.items():
    ls = [LineString([(t['x1'] - O, t['y1'] - O), (t['x2'] - O, t['y2'] - O)]) for t in pistas if t['comp'] == i and t['capa'] in (69, 70)]
    ls += [Point(a['cx'] - O, a['cy'] - O).buffer(a['r'], 16).exterior for a in arcos if a['comp'] == i and a['capa'] in (69, 70)]
    if ls:
        g = unary_union(ls).envelope if len(ls) > 2 else unary_union(ls).buffer(0.05).envelope
        cuerpo_de[d] = g
        cuerpo[lado_de[d]].append(g)
tornillos = [Point(a['cx'] - O, a['cy'] - O).buffer(a['r'], 32) for a in arcos if a['capa'] == 71 and a['r'] > 3]
via_pts = [Point(v['x'] - O, v['y'] - O).buffer(v['dia'] / 2, 12) for v in vias]
placa = box(BORDE, BORDE, ANCHO_X - BORDE, ANCHO_Y - BORDE)
arbol = {}
for l in ('top', 'bot'):
    arbol[l] = {
        'cobre': (STRtree(cobre[l]), cobre[l], D_PAD),
        'seda': (STRtree(seda[l]), seda[l], D_SEDA),
        'cuerpo': (STRtree(cuerpo[l]), cuerpo[l], 0.0),
    }
arbol_vias = STRtree(via_pts)

# rectángulos de Altium (0,1 µm) -> ancho a lo largo del texto y alto, con rotación 0
dims = {}
for linea in open(tsv, encoding='latin-1'):
    f = linea.rstrip('\r\n').split('\t')
    if len(f) < 8:
        continue
    L, B, R, T = (int(v) / 10000 for v in f[4:8])
    rot = round(float(f[3].replace(',', '.'))) % 180
    w, h = (R - L, T - B) if rot == 0 else (T - B, R - L)
    dims[f[0]] = (w, h, (L, B, R, T))


def libre(g, lado, ignorar=()):
    if not placa.contains(g):
        return False
    for clave, (arb, geoms, dist) in arbol[lado].items():
        for k in arb.query(g.buffer(dist + 1e-3)):
            if geoms[k].distance(g) < dist - 1e-9 or (dist == 0 and geoms[k].intersects(g)):
                return False
    if any(t.intersects(g) for t in tornillos):
        return False
    return True


def candidatos(d):
    w, h, _ = dims[d]
    lado = lado_de[d]
    partes = pads_de[d] + seda_de[d] + ([cuerpo_de[d]] if d in cuerpo_de else [])
    if not partes:
        return []
    K = unary_union(partes).envelope
    kx0, ky0, kx1, ky1 = K.bounds
    cx, cy = (kx0 + kx1) / 2, (ky0 + ky1) / 2
    out = []
    for rot, (tw, th) in ((0, (w, h)), (90, (h, w))):
        for gap in [0.15 + 0.1 * k for k in range(14)]:
            for desl in (0, -0.5, 0.5, -1.0, 1.0, -1.5, 1.5, -2.5, 2.5):
                for lado_k, (px, py) in (('arriba', (cx + desl, ky1 + gap + th / 2)), ('abajo', (cx + desl, ky0 - gap - th / 2)),
                                          ('izq', (kx0 - gap - tw / 2, cy + desl)), ('der', (kx1 + gap + tw / 2, cy + desl))):
                    g = box(px - tw / 2, py - th / 2, px + tw / 2, py + th / 2)
                    costo = math.hypot(px - cx, py - cy) + (0.6 if rot else 0) + 0.15 * abs(desl)
                    out.append((costo, rot, px, py, g))
    out.sort(key=lambda c: c[0])
    return [c for c in out if libre(c[4], lado) and propio(c[4], d)]


def caja_de(d):
    partes = pads_de[d] + seda_de[d] + ([cuerpo_de[d]] if d in cuerpo_de else [])
    return unary_union(partes).envelope if partes else None


CAJAS = {d: caja_de(d) for d in idx}


def prefijo(d):
    return ''.join(ch for ch in d if ch.isalpha())


def cajas_vistas(lado):
    """Lo que se ve de cada pieza desde una cara: su caja si está en esa cara, o sus pads pasantes si está en la otra."""
    out = {}
    for o in idx:
        if lado_de[o] == lado:
            if CAJAS[o] is not None:
                out[o] = CAJAS[o]
        else:
            tht = [forma_pad(p, lado) for p in pads if p['comp'] == o and p['h'] > 0]
            if tht:
                out[o] = unary_union(tht).envelope
    return out


VISTAS = {l: cajas_vistas(l) for l in ('top', 'bot')}


def propio(g, d):
    """El texto debe quedar claramente más cerca de su pieza que de cualquier otra del mismo tipo (mismo prefijo):
    un «J4» junto a una resistencia no se confunde, un «R12» entre dos resistencias sí."""
    yo = g.distance(CAJAS[d])
    return all(g.distance(k) >= yo + 0.15 for o, k in VISTAS[lado_de[d]].items() if o != d and prefijo(o) == prefijo(d))


# las perforaciones M3 no llevan designador
pendientes = [d for d in dims if d != 'ID' and not d.startswith('H')]
cand = {d: candidatos(d) for d in pendientes}
puestos = {}
textos_por_lado = {'top': [], 'bot': []}


def compatible(c, lado):
    g = c[4]
    return all(g.distance(o) >= D_TXT for o in textos_por_lado[lado])


def penal_vias(g):
    return sum(1 for k in arbol_vias.query(g) if via_pts[k].intersects(g))


# los de menos opciones primero; en cada paso se toma el mejor candidato compatible (costo + vías bajo el texto)
restantes = set(pendientes)
while restantes:
    opciones = {d: [c for c in cand[d] if compatible(c, lado_de[d])] for d in restantes}
    d = min(restantes, key=lambda x: (len(opciones[x]) if opciones[x] else 10 ** 6, x))
    restantes.discard(d)
    if not opciones[d]:
        continue
    mejor = min(opciones[d][:400], key=lambda c: c[0] + 1.5 * penal_vias(c[4]))
    puestos[d] = mejor
    textos_por_lado[lado_de[d]].append(mejor[4])

ocultos = sorted(set(dims) - set(puestos) - {'ID'})
print(f'visibles: {len(puestos)} de {len(dims) - 1}; ocultos: {ocultos}')
print('rotados 90°:', sorted(d for d, c in puestos.items() if c[1]))
print('con vías debajo:', {d: penal_vias(c[4]) for d, c in puestos.items() if penal_vias(c[4])})
# identificación de la cara inferior: ¿sigue libre en su lugar?
if 'ID' in dims:
    L, B, R, T = dims['ID'][2]
    g = box(L, B, R, T)
    print('ID en la cara inferior libre:', libre(g, 'bot'), 'y sin choque con designadores:', all(g.distance(o) >= D_TXT for o in textos_por_lado['bot']),
          f'({L:.2f},{B:.2f})-({R:.2f},{T:.2f})')

with open(os.path.join(os.environ['TEMP'], 'altium_simbolos', 'designadores_plan.tsv'), 'w', newline='\r\n') as f:
    for d in sorted(dims):
        if d == 'ID':
            continue
        if d in puestos:
            c = puestos[d]
            f.write(f'{d}\t1\t{c[1]}\t{round(c[2] * 10000)}\t{round(c[3] * 10000)}\n')
        else:
            L, B, R, T = dims[d][2]
            f.write(f'{d}\t0\t0\t{round((L + R) / 2 * 10000)}\t{round((B + T) / 2 * 10000)}\n')

# figura de control
fig, ax = plt.subplots(figsize=(16, 11.5))
for g in cobre['top']:
    ax.fill(*g.exterior.xy, color='#f4c47a', lw=0)
for g in seda['top']:
    ax.fill(*g.exterior.xy, color='k', lw=0)
for g in cuerpo['top']:
    ax.plot(*g.exterior.xy, color='#999999', lw=0.5)
for g in tornillos:
    ax.plot(*g.exterior.xy, color='r', lw=0.5)
for d, c in puestos.items():
    g = c[4]
    ax.fill(*g.exterior.xy, color='#2ca02c' if lado_de[d] == 'top' else '#1f77b4', alpha=0.45, lw=0)
    ax.text(c[2], c[3], d, ha='center', va='center', fontsize=6, rotation=c[1])
ax.set_xlim(0, ANCHO_X); ax.set_ylim(0, ANCHO_Y); ax.set_aspect('equal')
ax.set_title(f'Designadores 1,2 mm: {len(puestos)} visibles (verde cara superior, azul inferior)')
fig.savefig(png, dpi=110, bbox_inches='tight')
