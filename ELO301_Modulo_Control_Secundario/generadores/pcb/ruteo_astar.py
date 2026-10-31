#!/usr/bin/env python3
"""Ruteo puntual con A* (grilla de 0,05 mm; Top, Senal-Potencia y Bottom; vías pasantes de 0,6/0,3 mm) para las
conexiones que Situs deja sin completar. Lee la geometría volcada de Altium (/tmp/geometria.json: pistas y vías;
/tmp/pads.json: pads) en mm desde el origen de la placa y escribe /tmp/rutas.json con las pistas y vías nuevas.
Uso: ruteo_astar.py  (las conexiones a rutear están en PEDIDOS, abajo; el cobre viejo de esas redes ya debe estar borrado)
ponytail: una conexión a la vez, sin rip-up ni optimización global; si no hay camino lo informa y no escribe nada."""
import heapq
import json
import math
import sys

import numpy as np

PASO, ANCHO, ALTO = 0.05, 70.0, 50.0
NX, NY = int(round(ANCHO / PASO)) + 1, int(round(ALTO / PASO)) + 1
CAPAS = {'Top Layer': 0, 'Mid Layer 1': 1, 'Bottom Layer': 2}
HOLGURA, VIA, HOLGO = 0.15, 0.6, 0.03          # regla de holgura, diámetro de vía, margen por la grilla
BORDE = 0.4
COSTO_VIA, COSTO_GIRO = 20.0, 0.4               # en pasos de grilla (20 = 1 mm)

# (red, pad de origen, pads de destino o None = cualquier otro cobre de la red, ancho de pista, capas permitidas)
TOP = (0,)
PEDIDOS = [('SW', ('U1', '5'), [('C4', '2')], 0.6, TOP),          # nodos críticos: solo en Top, sin vías
           ('SW', ('L1', '1'), None, 0.6, TOP),
           ('BST', ('U1', '6'), [('C4', '1')], 0.2, TOP),
           ('V_5V', ('L1', '2'), None, 0.6, TOP),
           ('OSC_OUT', ('C23', '1'), None, 0.2, TOP),
           ('RF_IN', ('L2', '2'), None, 0.35, TOP),
           ('NetL2_1', ('U6', '14'), [('L2', '1')], 0.2, TOP)]
# tramos fijos que se agregan antes de rutear: (capa, x1, y1, x2, y2, ancho, red) y vías (x, y, red)
MANUALES = {'pistas': [(0, 37.16, 23.75, 37.92, 23.75, 0.2, 'OSC_OUT'),    # U4-6 -> Y1-3 por y = 23,89, entre OSC_IN y NRST:
                       (0, 37.92, 23.75, 38.06, 23.89, 0.2, 'OSC_OUT'),    # la grilla de 0,05 mm no cae en ese pasillo
                       (0, 38.06, 23.89, 39.75, 23.89, 0.2, 'OSC_OUT'),
                       (0, 39.75, 23.89, 39.75, 24.6, 0.2, 'OSC_OUT'),
                       (0, 41.45, 24.6, 42.52, 24.6, 0.25, 'GND'),
                       (0, 61.75, 29.7, 63.53, 29.7, 0.35, 'RF_IN'),        # U6-11 -> J8-1 entrando al centro de ambos pads
                       (0, 63.53, 29.7, 64.83, 31.0, 0.35, 'RF_IN'),
                       (0, 64.83, 31.0, 65.77, 31.0, 0.35, 'RF_IN')],        # vía de Y1-2 a la derecha: libera el paso de OSC_OUT
            'vias': [(42.52, 24.6, 'GND')]}


def ventana(x0, y0, x1, y1):
    i0, i1 = max(int((x0) / PASO), 0), min(int(math.ceil(x1 / PASO)) + 1, NX)
    j0, j1 = max(int((y0) / PASO), 0), min(int(math.ceil(y1 / PASO)) + 1, NY)
    return j0, j1, i0, i1


def malla(j0, j1, i0, i1):
    return np.meshgrid(np.arange(i0, i1) * PASO, np.arange(j0, j1) * PASO)


def marcar_segmento(m, x1, y1, x2, y2, r):
    j0, j1, i0, i1 = ventana(min(x1, x2) - r, min(y1, y2) - r, max(x1, x2) + r, max(y1, y2) + r)
    if j0 >= j1 or i0 >= i1:
        return
    X, Y = malla(j0, j1, i0, i1)
    dx, dy = x2 - x1, y2 - y1
    t = np.clip(((X - x1) * dx + (Y - y1) * dy) / max(dx * dx + dy * dy, 1e-12), 0, 1)
    m[j0:j1, i0:i1] |= np.hypot(X - (x1 + t * dx), Y - (y1 + t * dy)) <= r


def marcar_caja(m, l, b, r_, t, infl):
    j0, j1, i0, i1 = ventana(l - infl, b - infl, r_ + infl, t + infl)
    if j0 >= j1 or i0 >= i1:
        return
    X, Y = malla(j0, j1, i0, i1)
    m[j0:j1, i0:i1] |= np.hypot(np.maximum(np.maximum(l - X, X - r_), 0), np.maximum(np.maximum(b - Y, Y - t), 0)) <= infl


def cobre(geo, pads, quitar):
    """Lista de objetos de cobre (capas, forma, red); `quitar(t)` excluye pistas que se van a borrar."""
    objs = []
    for t in geo['T']:
        if not quitar(t):
            objs.append(([CAPAS[t[0]]], 'seg', (t[1], t[2], t[3], t[4], t[5] / 2), t[6]))
    for v in geo['V']:
        objs.append(([0, 1, 2], 'seg', (v[0], v[1], v[0], v[1], v[2] / 2), v[3]))
    for p in pads:
        capas = [0, 1, 2] if p['capa'] == 'Multi Layer' else [0]
        objs.append((capas, 'caja', tuple(p['caja']), p['net']))
    return objs


def rasterizar(objs, red, infl_pista, infl_via):
    bloq = np.zeros((3, NY, NX), bool)
    bloq_via = np.zeros((NY, NX), bool)
    for capas, forma, g, n in objs:
        if n == red and n:
            continue
        for c in capas:
            if forma == 'seg':
                marcar_segmento(bloq[c], g[0], g[1], g[2], g[3], g[4] + infl_pista)
            else:
                marcar_caja(bloq[c], *g, infl_pista)
        if forma == 'seg':
            marcar_segmento(bloq_via, g[0], g[1], g[2], g[3], g[4] + infl_via)
        else:
            marcar_caja(bloq_via, *g, infl_via)
    k = int(BORDE / PASO)
    for m in (*bloq, bloq_via):
        m[:k, :] = m[-k:, :] = True
        m[:, :k] = m[:, -k:] = True
    return bloq, bloq_via


def celdas(objs_red, capas_ok=(0, 1, 2)):
    """Celdas (capa, j, i) dentro del cobre dado."""
    m = np.zeros((3, NY, NX), bool)
    for capas, forma, g, _ in objs_red:
        for c in capas:
            if c in capas_ok:
                if forma == 'seg':
                    marcar_segmento(m[c], g[0], g[1], g[2], g[3], g[4])
                else:
                    marcar_caja(m[c], *g, 0.0)
    return m


def astar(origen, destino, bloq, bloq_via):
    libre = ~bloq | origen | destino
    ds = np.argwhere(destino)
    puntos = ds[np.linspace(0, len(ds) - 1, min(len(ds), 40)).astype(int)]
    h = lambda c, j, i: float(np.min(np.hypot(puntos[:, 1] - i, puntos[:, 2] - j)))
    abiertos, costo, padre = [], {}, {}
    for c, j, i in np.argwhere(origen):
        s = (int(c), int(j), int(i))
        costo[s] = 0.0
        heapq.heappush(abiertos, (h(*s), 0.0, s))
    pasos = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
    n = 0
    while abiertos and n < 4_000_000:
        _, g, s = heapq.heappop(abiertos)
        if g > costo.get(s, 1e18):
            continue
        n += 1
        c, j, i = s
        if destino[c, j, i]:
            camino = [s]
            while camino[-1] in padre:
                camino.append(padre[camino[-1]])
            return camino[::-1]
        p = padre.get(s)
        dir0 = (j - p[1], i - p[2]) if p and p[0] == c else None
        vecinos = []
        for dj, di, w in pasos:
            jj, ii = j + dj, i + di
            if 0 <= jj < NY and 0 <= ii < NX and libre[c, jj, ii]:
                vecinos.append(((c, jj, ii), w + (COSTO_GIRO if dir0 and dir0 != (dj, di) else 0)))
        if not bloq_via[j, i] or origen[:, j, i].any() or destino[:, j, i].any():
            for cc in range(3):
                if cc != c and libre[cc, j, i]:
                    vecinos.append(((cc, j, i), COSTO_VIA))
        for t, w in vecinos:
            gg = g + w
            if gg < costo.get(t, 1e18):
                costo[t], padre[t] = gg, s
                heapq.heappush(abiertos, (gg + h(*t), gg, t))
    return None


def a_objetos(camino, red, ancho):
    """Camino de celdas -> pistas rectas por capa (tramos colineales unidos) y vías en los cambios de capa."""
    pistas, vias = [], []
    k = 0
    while k < len(camino) - 1:
        c = camino[k][0]
        if camino[k + 1][0] != c:
            vias.append((camino[k][2] * PASO, camino[k][1] * PASO, red))
            k += 1
            continue
        a = k
        d = (camino[k + 1][1] - camino[k][1], camino[k + 1][2] - camino[k][2])
        while k + 1 < len(camino) and camino[k + 1][0] == c and (camino[k + 1][1] - camino[k][1], camino[k + 1][2] - camino[k][2]) == d:
            k += 1
        pistas.append((c, camino[a][2] * PASO, camino[a][1] * PASO, camino[k][2] * PASO, camino[k][1] * PASO, ancho, red))
    return pistas, vias


def quitar_gnd_situs(t):
    """Pistas de GND que no son del fanout (0,25 mm): sobran, cada pad de GND baja al plano por su vía."""
    return t[6] == 'GND' and abs(t[5] - 0.25) > 0.01


def main():
    geo, pads = json.load(open('/tmp/geometria.json')), json.load(open('/tmp/pads.json'))
    todos = cobre(geo, pads, quitar_gnd_situs)
    salida = {'pistas': list(MANUALES['pistas']), 'vias': list(MANUALES['vias']), 'fallas': []}
    todos += [([c], 'seg', (x1, y1, x2, y2, w / 2), r) for c, x1, y1, x2, y2, w, r in MANUALES['pistas']]
    todos += [([0, 1, 2], 'seg', (x, y, x, y, VIA / 2), r) for x, y, r in MANUALES['vias']]
    for red, (des, pin), destinos, ancho, *capas in PEDIDOS:
        capas = capas[0] if capas else (0, 1, 2)
        bloq, bloq_via = rasterizar(todos, red, ancho / 2 + HOLGURA + HOLGO, VIA / 2 + HOLGURA + HOLGO)
        for c in {0, 1, 2} - set(capas):
            bloq[c] = True
        pad0 = next(p for p in pads if p['des'] == des and p['pad'] == pin)
        propios = [o for o in todos if o[3] == red]
        if destinos:
            dest = [o for o in propios if o[1] == 'caja' and any(p['des'] == d and p['pad'] == q and tuple(p['caja']) == o[2]
                                                               for d, q in destinos for p in pads)]
        else:   # ponytail: si la red ya tiene cobre pegado al origen, ese cobre cuenta como destino y no se rutea nada
            dest = [o for o in propios if not (o[1] == 'caja' and o[2] == tuple(pad0['caja']))]
        # dentro del pad solo valen las celdas a holgura de los pads vecinos (una pista ancha no sale rozándolos)
        origen = celdas([(([0, 1, 2] if pad0['capa'] == 'Multi Layer' else [0]), 'caja', tuple(pad0['caja']), red)], capas)
        destino = celdas(dest, capas)
        origen, destino = (m & ~bloq if (m & ~bloq).any() else m for m in (origen, destino))
        camino = astar(origen, destino, bloq, bloq_via)
        if not camino:
            salida['fallas'].append(red)
            continue
        p, v = a_objetos(camino, red, ancho)
        salida['pistas'] += p
        salida['vias'] += v
        todos += [([c], 'seg', (x1, y1, x2, y2, w / 2), r) for c, x1, y1, x2, y2, w, r in p]
        todos += [([0, 1, 2], 'seg', (x, y, x, y, VIA / 2), r) for x, y, r in v]
        print(f'{red}: {len(p)} pistas, {len(v)} vías, largo {sum(math.hypot(x2 - x1, y2 - y1) for _, x1, y1, x2, y2, _, _ in p):.1f} mm',
              file=sys.stderr)
    json.dump(salida, open('/tmp/rutas.json', 'w'))
    if salida['fallas']:
        sys.exit(f"sin camino: {salida['fallas']}")


if __name__ == '__main__':
    main()
