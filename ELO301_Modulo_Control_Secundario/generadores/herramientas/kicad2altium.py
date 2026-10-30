#!/usr/bin/env python3
"""Convierte símbolos (.kicad_sym) y huellas (.kicad_mod) de las bibliotecas oficiales de KiCad 10 al formato de
create_symbols_batch / create_footprints_batch de altium-mcp (mils; el origen de un PcbLib está en 50000,50000).
Capas como en las bibliotecas del profesor: F.SilkS -> Top Overlay, F.Fab -> Mech 13, F.CrtYd -> Mech 15.
Uso: kicad2altium.py sym <biblioteca> <símbolo KiCad> <nombre Altium>
     kicad2altium.py fp  <biblioteca.pretty sin extensión> <huella KiCad> <nombre Altium>
     kicad2altium.py test"""
import math
import re
import sys
from pathlib import Path

RAIZ = Path('/mnt/flatpak-sda3/runtime')
KSYM = RAIZ / 'org.kicad.KiCad.Library.Symbols/x86_64/stable/active/files/symbols'
KFP = RAIZ / 'org.kicad.KiCad.Library.Footprints/x86_64/stable/active/files/footprints'
MIL = 1 / 0.0254
ORIGEN = 0   # las huellas que crea create_footprints_batch toman como referencia el 0 absoluto (no el 50000 del PcbLib)
TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')
TIPOS = {'input': 'eElectricInput', 'output': 'eElectricOutput', 'bidirectional': 'eElectricIO',
         'tri_state': 'eElectricHiZ', 'power_in': 'eElectricPower', 'power_out': 'eElectricPower',
         'open_collector': 'eElectricOpenCollector', 'open_emitter': 'eElectricOpenEmitter'}  # resto: pasivo
CAPAS = {'F.SilkS': 'Top Overlay', 'F.Fab': 'Mechanical Layer 13', 'F.CrtYd': 'Mechanical Layer 15'}
FORMAS = {'rect': 2, 'roundrect': 9, 'circle': 1, 'oval': 1}


def parse(texto):
    pila = [[]]
    for t in TOK.findall(texto):
        if t == '(':
            pila.append([])
        elif t == ')':
            x = pila.pop()
            pila[-1].append(x)
        else:
            pila[-1].append(t[1:-1].replace('\\"', '"') if t[0] == '"' else t)
    return pila[0][0]


def hijos(n, clave):
    return [c for c in n[1:] if isinstance(c, list) and c and c[0] == clave]


def hijo(n, clave):
    h = hijos(n, clave)
    return h[0] if h else None


def oculto(n):
    return n is not None and any(c == 'hide' or (isinstance(c, list) and c[:2] == ['hide', 'yes']) for c in n[1:])


def prop(n, nombre):
    return next((p[2] for p in hijos(n, 'property') if p[1] == nombre), '')


def limpio(t):
    return ' '.join(t.replace('|', '/').split())


def f(v):
    return f'{v:.3f}'.rstrip('0').rstrip('.')


def arco_3p(a, m, b):
    """Centro, radio y ángulos (CCW, grados) del arco que va de a a b pasando por m."""
    (ax, ay), (bx, by), (cx, cy) = a, m, b
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d
    ang = [math.degrees(math.atan2(py - uy, px - ux)) % 360 for px, py in (a, m, b)]
    if (ang[1] - ang[0]) % 360 > (ang[2] - ang[0]) % 360:  # m no queda en el giro CCW de a a b
        ang[0], ang[2] = ang[2], ang[0]
    return ux, uy, math.hypot(ax - ux, ay - uy), ang[0], ang[2]


def simbolo(lib, nombre, nuevo):
    raiz = parse((KSYM / f'{lib}.kicad_sym').read_text(encoding='utf-8'))
    todos = {c[1]: c for c in hijos(raiz, 'symbol')}
    s = base = todos[nombre]
    while hijo(base, 'extends'):
        base = todos[hijo(base, 'extends')[1]]
    ver_nombre, ver_num = not oculto(hijo(base, 'pin_names')), not oculto(hijo(base, 'pin_numbers'))
    subs = [u for u in hijos(base, 'symbol') if u[1].rsplit('_', 1)[1] in ('0', '1')]  # sin estilo De Morgan
    unidades = max([int(u[1].rsplit('_', 2)[1]) for u in subs] + [1])
    out = [f"SYMBOL|{nuevo}|{limpio(prop(s, 'Description'))}|{unidades}"]
    for u in subs:
        unidad = int(u[1].rsplit('_', 2)[1])
        parte = unidad if unidades > 1 else 1
        for p in hijos(u, 'pin'):
            at, largo = hijo(p, 'at'), float(hijo(p, 'length')[1])
            x, y, a = float(at[1]), float(at[2]), int(float(at[3])) % 360
            bx, by = x + largo * math.cos(math.radians(a)), y + largo * math.sin(math.radians(a))  # borde del cuerpo
            nom = re.sub(r'~\{([^}]*)\}', lambda m: ''.join(c + '\\' for c in m.group(1)), hijo(p, 'name')[1])
            vis = not oculto(p)
            out.append('PIN|' + '|'.join([hijo(p, 'number')[1], nom, TIPOS.get(p[1], 'eElectricPassive'),
                                          f'eRotate{(a + 180) % 360}', f(round(bx * MIL)), f(round(by * MIL)),
                                          str(0 if unidad == 0 and unidades > 1 else parte), f(round(largo * MIL)),
                                          str(int(ver_nombre and vis)), str(int(ver_num and vis))]))
        for g in u[1:]:
            if not isinstance(g, list) or g[0] not in ('rectangle', 'polyline', 'circle', 'arc'):
                continue
            relleno = hijo(hijo(g, 'fill'), 'type') if hijo(g, 'fill') else None
            solido = int(bool(relleno) and relleno[1] in ('background', 'outline'))
            if g[0] == 'rectangle':
                (x1, y1), (x2, y2) = [(float(hijo(g, k)[1]) * MIL, float(hijo(g, k)[2]) * MIL) for k in ('start', 'end')]
                out.append(f'GRAPHIC|rectangle|{parte}|1|{solido}|{f(x1)}|{f(y1)}|{f(x2)}|{f(y2)}')
            elif g[0] == 'polyline':
                pts = [f'{f(float(q[1]) * MIL)}|{f(float(q[2]) * MIL)}' for q in hijos(hijo(g, 'pts'), 'xy')]
                tipo = f'polygon|{parte}|1|{solido}' if solido else f'polyline|{parte}|1'
                out.append(f"GRAPHIC|{tipo}|{'|'.join(pts)}")
            elif g[0] == 'circle':
                c, r = hijo(g, 'center'), float(hijo(g, 'radius')[1]) * MIL
                out.append(f'GRAPHIC|ellipse|{parte}|1|{solido}|{f(float(c[1]) * MIL)}|{f(float(c[2]) * MIL)}|{f(r)}|{f(r)}')
            else:
                cx, cy, r, a1, a2 = arco_3p(*[(float(hijo(g, k)[1]) * MIL, float(hijo(g, k)[2]) * MIL)
                                              for k in ('start', 'mid', 'end')])
                out.append(f'GRAPHIC|arc|{parte}|1|{f(cx)}|{f(cy)}|{f(r)}|{f(a1)}|{f(a2)}')
    return out


def huella(pretty, nombre, nuevo):
    raiz = parse((KFP / f'{pretty}.pretty' / f'{nombre}.kicad_mod').read_text(encoding='utf-8'))
    P = lambda n: (float(n[1]) * MIL + ORIGEN, -float(n[2]) * MIL + ORIGEN)  # KiCad tiene y hacia abajo
    desc = hijo(raiz, 'descr')
    out = [f"FOOTPRINT|{nuevo}|{limpio(desc[1] if desc else nombre)}"]
    for p in hijos(raiz, 'pad'):
        num, tipo, forma = p[1], p[2], p[3]
        at, size = hijo(p, 'at'), hijo(p, 'size')
        x, y = P(at)
        rot = float(at[3]) if len(at) > 3 else 0
        w, h = float(size[1]) * MIL, float(size[2]) * MIL
        esquina = round(float(hijo(p, 'roundrect_rratio')[1]) * 200) if forma == 'roundrect' else 0
        capa, plat, agujero, tipo_ag, largo_ag, rot_ag = 'Top Layer', 1, 0, 0, 0, 0
        if tipo != 'smd':
            d = hijo(p, 'drill')
            capa, plat = 'Multi Layer', int(tipo != 'np_thru_hole')
            if d[1] == 'oval':  # ranura: diámetro = lado corto, largo = lado largo
                dx, dy = float(d[2]) * MIL, float(d[3]) * MIL
                agujero, largo_ag, tipo_ag, rot_ag = min(dx, dy), max(dx, dy), 2, (0 if dx >= dy else 90)
            else:
                agujero = float(d[1]) * MIL
        campos = [num, f(x), f(y), f(rot), capa, str(plat), f(agujero), str(tipo_ag), f(largo_ag),
                  f(rot_ag), f(w), f(h), str(FORMAS.get(forma, 2)), str(esquina)]
        if capa == 'Multi Layer' and plat:  # pila explícita arriba/medio/abajo: en modo simple el DRC no ve el cobre interno
            campos += ['1'] + [f(w), f(h), str(FORMAS.get(forma, 2))] * 2
        out.append('PAD|' + '|'.join(campos))
    for g in raiz[1:]:
        if not isinstance(g, list) or g[0] not in ('fp_line', 'fp_rect', 'fp_poly', 'fp_circle', 'fp_arc'):
            continue
        capa = CAPAS.get((hijo(g, 'layer') or [None, None])[1])
        if not capa:
            continue
        trazo = hijo(g, 'stroke')
        ancho = f(float(hijo(trazo or g, 'width')[1]) * MIL)
        if g[0] in ('fp_line', 'fp_rect', 'fp_poly'):
            if g[0] == 'fp_line':
                pts = [P(hijo(g, 'start')), P(hijo(g, 'end'))]
            elif g[0] == 'fp_rect':
                (x1, y1), (x2, y2) = P(hijo(g, 'start')), P(hijo(g, 'end'))
                pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
            else:
                pts = [P(q) for q in hijos(hijo(g, 'pts'), 'xy')]
                pts.append(pts[0])
            out += [f'TRACK|{f(a[0])}|{f(a[1])}|{f(b[0])}|{f(b[1])}|{ancho}|{capa}' for a, b in zip(pts, pts[1:])]
        elif g[0] == 'fp_circle':
            (cx, cy), (ex, ey) = P(hijo(g, 'center')), P(hijo(g, 'end'))
            out.append(f'ARC|{f(cx)}|{f(cy)}|{f(math.hypot(ex - cx, ey - cy))}|0|360|{ancho}|{capa}')
        else:
            cx, cy, r, a1, a2 = arco_3p(P(hijo(g, 'start')), P(hijo(g, 'mid')), P(hijo(g, 'end')))
            out.append(f'ARC|{f(cx)}|{f(cy)}|{f(r)}|{f(a1)}|{f(a2)}|{ancho}|{capa}')
    out.append(f'TEXT|{ORIGEN - 20}|{ORIGEN - 4}|9.842|1.968|0|Mechanical Layer 29|0|0|.Designator')
    return out


def test():
    cx, cy, r, a1, a2 = arco_3p((1, 0), (0, 1), (-1, 0))  # semicírculo superior, CCW de 0° a 180°
    assert (round(cx, 6), round(cy, 6), round(r, 6), round(a1), round(a2)) == (0, 0, 1, 0, 180)
    cx, cy, r, a1, a2 = arco_3p((-1, 0), (0, 1), (1, 0))  # mismo arco recorrido al revés
    assert (round(a1), round(a2)) == (0, 180)
    pin = [l for l in simbolo('Regulator_Linear', 'TLV75533PDBV', 'T') if l.startswith('PIN|1|')][0]
    assert pin.split('|')[2:4] == ['IN', 'eElectricPower'], pin
    pads = [l for l in huella('Package_TO_SOT_SMD', 'SOT-23-5', 'T') if l.startswith('PAD|')]
    assert len(pads) == 5 and all('|Top Layer|' in l for l in pads)
    print('kicad2altium: autochequeo OK')


if __name__ == '__main__':
    if sys.argv[1] == 'test':
        test()
    else:
        print('\n'.join((simbolo if sys.argv[1] == 'sym' else huella)(*sys.argv[2:5])))
