#!/usr/bin/env python3
"""Revisa la serigrafía en los Gerber contra los mínimos de JLCPCB, sin pasar por Altium.

Uso: python3 revisar_serigrafia.py <zip JLCPCB> <serigrafia_plan.json> [--prueba]

Mide lo que recibe el fabricante: ancho de cada apertura (>= 0,15 mm), separación a las aberturas de máscara y a los agujeros
(>= 0,15 mm; las vías van tapadas y solo se cuentan), distancia al borde, alto de cada texto (>= 1,0 mm), que cada texto no tenga tinta ajena a menos de 0,25 mm y que
tenga una pieza de tinta por letra (si dos letras o un texto y una línea se tocan, las piezas no calzan).
--prueba además rompe la serigrafía a propósito y exige que se detecte.
"""
import json, os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union
from jlcpcb import taladro
from lvs_gerber import capa, piezas

MIN_LINEA, MIN_ALTO, MIN_MASCARA, MIN_SILK, MIN_BORDE, VIA = 0.15, 1.0, 0.149, 0.25, 0.2, 0.5  # 0,149: el Gerber redondea 0,15 a 0,1499


def revisar(a, plan):
    malas = []
    r = min(float(v) for v in re.findall(r'%ADD\d+C,([\d.]+)\*%', a['GKO'])) / 2
    W, H = (v - r for v in capa(a['GKO']).bounds[2:])  # el borde es el eje del trazo del contorno, no su orilla
    hs = taladro(a['TXT'])
    agujeros = unary_union([Point(h[0], h[1]).buffer(h[2] / 2) for h in hs if h[2] > VIA])
    vias = [Point(h[0], h[1]).buffer(h[2] / 2) for h in hs if h[2] <= VIA]  # tapadas con máscara (lo exige lvs_gerber.py): la tinta se imprime encima
    arriba = [dict(t) for t in plan['textos']]
    abajo = [dict(t, caja=(t['x'] - t['w'], t['y'], t['x'], t['y'] + t['h']), rot=0) for t in plan['abajo'] + ([plan['j1']] if 'j1' in plan else [])]
    resumen = {}
    for nombre, cara, m, textos in (('GTO', 'arriba', 'GTS', arriba), ('GBO', 'abajo', 'GBS', abajo)):
        anchos = [float(v) for v in re.findall(r'%ADD\d+C,([\d.]+)\*%', a[nombre])]
        otras = [v for v in re.findall(r'%ADD\d+([A-Z]\w*)', a[nombre]) if v != 'C']
        if otras: malas.append(f'{cara}: aperturas no redondas {otras}')
        if min(anchos) < MIN_LINEA: malas.append(f'{cara}: apertura de {min(anchos)} mm')
        silk = capa(a[nombre])
        d_mascara, d_agujero = silk.distance(capa(a[m])), silk.distance(agujeros)
        if d_mascara < MIN_MASCARA: malas.append(f'{cara}: a {d_mascara:.3f} mm de la máscara')
        if d_agujero < MIN_MASCARA: malas.append(f'{cara}: a {d_agujero:.3f} mm de un agujero')
        x0, y0, x1, y1 = silk.bounds
        d_borde = min(x0, y0, W - x1, H - y1)
        if d_borde < MIN_BORDE: malas.append(f'{cara}: a {d_borde:.3f} mm del borde')
        alto_min = 99
        for t in textos:
            c = box(*t['caja'])
            tinta = silk.intersection(c.buffer(0.03, join_style=2))
            if tinta.is_empty: malas.append(f"{t['t']}: no está en el Gerber"); continue
            b = tinta.bounds
            alto = b[3] - b[1] if t['rot'] == 0 else b[2] - b[0]
            alto_min = min(alto_min, alto)
            if alto < MIN_ALTO: malas.append(f"{t['t']}: alto {alto:.3f} mm")
            n, esperadas = len(piezas(tinta)), len(t['t'].replace(' ', ''))
            if n != esperadas: malas.append(f"{t['t']}: {n} piezas de tinta y {esperadas} letras")
            cerca = silk.intersection(c.buffer(MIN_SILK, join_style=2).difference(c.buffer(0.03, join_style=2)))
            if not cerca.is_empty and cerca.area > 1e-6: malas.append(f"{t['t']}: tinta ajena a menos de {MIN_SILK} mm en {[round(v, 2) for v in cerca.bounds]}")
        resumen[cara] = dict(aperturas=sorted(set(anchos)), mascara=round(d_mascara, 3), agujero=round(d_agujero, 3), sobre_vias=sum(silk.distance(v) == 0 for v in vias), borde=round(d_borde, 3), textos=len(textos), alto_min=round(alto_min, 3))
    return malas, resumen


def prueba(a, plan):
    """Cada daño, aplicado sobre los Gerber reales, tiene que aparecer como falla."""
    t = plan['textos'][0]['caja']; lin = lambda x0, y0, x1, y1: f'D10*X{int(x0 * 1e5)}Y{int(y0 * 1e5)}D02*X{int(x1 * 1e5)}Y{int(y1 * 1e5)}D01*'
    def con(cambio):
        b = dict(a); b['GTO'] = cambio(a['GTO']); return revisar(b, plan)[0]
    agrega = lambda s: (lambda g: g.replace('M02*', s + 'M02*'))
    pad = capa(a['GTS']).representative_point()
    import re
    # línea delgada: la primera apertura redonda que exista pasa a 0,10 mm
    casos = {'línea delgada': lambda g: re.sub(r'(%ADD\d+C,)0\.\d+', r'\g<1>0.10000', g, count=1), 'línea que cruza un texto': agrega(lin(t[0] - .5, (t[1] + t[3]) / 2, t[2] + .5, (t[1] + t[3]) / 2)),
             'línea sobre un pad': agrega(lin(pad.x, pad.y, pad.x + .3, pad.y)), 'línea en el borde': agrega(lin(.05, 25, .05, 26))}
    base = set(revisar(a, plan)[0])  # las fallas que ya hay no cuentan como detección
    for nombre, cambio in casos.items():
        n = len(set(con(cambio)) - base)
        print(f'  prueba «{nombre}»: {n} fallas nuevas' + ('' if n > 0 else ' NO DETECTADA'))
        assert n > 0, nombre


def main(zp, fplan, probar):
    z = zipfile.ZipFile(zp)
    a = {n.rsplit('.', 1)[-1].upper(): z.read(n).decode('latin1') for n in z.namelist()}
    plan = json.load(open(fplan))
    malas, resumen = revisar(a, plan)
    for c, r in resumen.items(): print(c, r)
    for m in malas: print('  FALLA', m)
    if probar: prueba(a, plan)
    print('RESULTADO:', 'OK' if not malas else f'{len(malas)} fallas')
    return 1 if malas else 0


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if x != '--prueba']
    sys.exit(main(*a[:2], '--prueba' in sys.argv))
