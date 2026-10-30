#!/usr/bin/env python3
"""Fanout de GND hacia el plano interno: una vía de 0,6/0,3 mm junto a cada pad SMD de GND, hacia afuera de su pieza,
con holgura a los pads de otras redes y a las demás vías; los pads sin lugar van con una pista recta al GND con vía más
cercano. Lee los pads volcados de Altium (/tmp/pads.json, mm desde el origen de la placa) y escribe /tmp/fanout.json.
ponytail: búsqueda por candidatos fijos (3 distancias x 8 direcciones); si un pad queda sin vía se informa y se rutea a mano."""
import json
import math
import sys

R, HOLGURA, ENTRE_VIAS, BORDE = 0.3, 0.2, 0.9, 0.8     # mm: radio de la vía, a cobre ajeno, centro a centro, al borde
ANCHO, ALTO = 70.0, 50.0


def dist_caja(x, y, caja):
    l, b, r, t = caja
    return math.hypot(max(l - x, 0, x - r), max(b - y, 0, y - t))


def libre(x, y, pad, pads, vias):
    if not (BORDE <= x <= ANCHO - BORDE and BORDE <= y <= ALTO - BORDE):
        return False
    if any(math.hypot(x - vx, y - vy) < ENTRE_VIAS for vx, vy, *_ in vias):
        return False
    for q in pads:
        d = dist_caja(x, y, q['caja'])
        if q['net'] != 'GND' and d < R + HOLGURA:
            return False
        if q['net'] == 'GND' and d < R + 0.1:                  # sin vía en pad, ni en el propio
            return False
        if q['agujero'] and math.hypot(x - q['centro'][0], y - q['centro'][1]) < q['agujero'] / 2 + 0.15 + 0.3:
            return False
    # la pista pad -> vía (0,25 mm) respeta la holgura de 0,15 mm a pads ajenos
    cx, cy = pad['centro']
    for k in range(21):
        px, py = cx + (x - cx) * k / 20, cy + (y - cy) * k / 20
        if any(q["net"] != "GND" and dist_caja(px, py, q["caja"]) < 0.125 + 0.15 for q in pads):
            return False
    return True


def candidatos(pad):
    l, b, r, t = pad['caja']
    cx, cy = pad['centro']
    ox, oy = cx - pad['comp'][0], cy - pad['comp'][1]
    ejes = [(1 if ox >= 0 else -1, 0), (0, 1 if oy >= 0 else -1)]
    if abs(oy) > abs(ox):
        ejes.reverse()
    ejes += [(-e[0], -e[1]) for e in ejes]                   # hacia afuera primero, después hacia adentro
    for d in (R + 0.15, R + 0.5, R + 0.9):
        for ex, ey in ejes:
            yield (r + d if ex > 0 else l - d if ex < 0 else cx), (t + d if ey > 0 else b - d if ey < 0 else cy)
        for ex, ey in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            yield (r if ex > 0 else l) + ex * d * 0.75, (t if ey > 0 else b) + ey * d * 0.75


def camino_libre(a, b, pads, media=0.125):
    """Pista recta de a a b (0,25 mm) sin pasar a menos de 0,15 mm de pads ajenos."""
    for k in range(41):
        px, py = a[0] + (b[0] - a[0]) * k / 40, a[1] + (b[1] - a[1]) * k / 40
        if any(q['net'] != 'GND' and dist_caja(px, py, q['caja']) < 0.15 + media for q in pads):
            return False
    return True


def fanout(pads):
    """Vías [vx, vy, px, py] y, para los pads sin lugar (VSS del MCU frente a su desacoplo), pistas directas
    [x1, y1, x2, y2] al GND con vía más cercano."""
    vias, sin, pistas = [], [], []
    for pad in (p for p in pads if p['net'] == 'GND' and not p['agujero']):
        v = next(((x, y) for x, y in candidatos(pad) if libre(x, y, pad, pads, vias)), None)
        if v:
            vias.append((round(v[0], 3), round(v[1], 3), *pad['centro']))
        else:
            sin.append(pad)
    destinos = [(v[0], v[1]) for v in vias] + [(v[2], v[3]) for v in vias]
    faltan = []
    for pad in sin:
        a = tuple(pad['centro'])
        b = next((d for d in sorted(destinos, key=lambda d: math.hypot(d[0] - a[0], d[1] - a[1]))
                  if math.hypot(d[0] - a[0], d[1] - a[1]) < 4 and camino_libre(a, d, pads)), None)
        if b:
            pistas.append((*a, *b))
        else:
            faltan.append(f"{pad['des']}-{pad['pad']}")
    return vias, pistas, faltan


if __name__ == '__main__':
    vias, pistas, faltan = fanout(json.load(open('/tmp/pads.json')))
    json.dump({'vias': vias, 'pistas': pistas}, open('/tmp/fanout.json', 'w'))
    print(f'vías: {len(vias)}; pistas directas: {[tuple(round(c, 2) for c in p) for p in pistas]}; sin conexión: {faltan or "ninguno"}', file=sys.stderr)
    # chequeo: ninguna vía a menos de R + HOLGURA de un pad ajeno
    pads = json.load(open('/tmp/pads.json'))
    assert all(dist_caja(x, y, q['caja']) >= R + HOLGURA for x, y, *_ in vias for q in pads if q['net'] != 'GND')
