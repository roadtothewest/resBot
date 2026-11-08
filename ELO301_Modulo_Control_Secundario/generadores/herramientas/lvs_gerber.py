#!/usr/bin/env python3
"""Compara el paquete de fabricación con la netlist del esquemático, sin pasar por Altium.

Uso: python3 lvs_gerber.py <zip JLCPCB> <pads.json> <netlist.json> [--prueba]

Reconstruye con shapely el cobre de cada capa desde los Gerber (.GTL/.G2L/.G3L/.GBL), une las capas por los agujeros
metalizados del taladro y comprueba, pad por pad, que cada red quede en una sola pieza de cobre (sin abiertos) y que cada
pieza lleve una sola red (sin cortos). También mide separaciones, cobre flotante, agujeros que rozan cobre ajeno y
aperturas de máscara. Es lo que el DRC de Altium no ve: revisa los archivos que se mandan a fabricar.

- pads.json: pads de la placa, importada a KiCad (kicad-cli pcb import + pcbnew), en mm desde el origen de la placa.
- netlist.json: {"U4-1": "V3V3_MCU", ...}, netlist aplanada que entrega Altium al compilar.
- --prueba: además rompe la placa a propósito (quita vías, agrega un puente) y exige que se detecte.
"""
import collections, json, math, os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shapely
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import nearest_points
from shapely.strtree import STRtree
from jlcpcb import taladro

COBRE = ['GTL', 'G2L', 'G3L', 'GBL']
UNION = 0.001  # mm: cierra microrrendijas numéricas entre regiones contiguas (muy por debajo de la separación mínima)


def forma(tipo, p, macros):
    if tipo == 'C': return Point(0, 0).buffer(p[0] / 2, quad_segs=8)
    if tipo == 'R': return box(-p[0] / 2, -p[1] / 2, p[0] / 2, p[1] / 2)
    if tipo == 'O':
        w, h = p
        return LineString([(-(w - h) / 2, 0), ((w - h) / 2, 0)]).buffer(h / 2, quad_segs=8) if w > h else LineString([(0, -(h - w) / 2), (0, (h - w) / 2)]).buffer(w / 2, quad_segs=8)
    partes = []
    for s in macros[tipo]:
        v = s.split(',')
        if v[0] == '1':  # círculo: exposición, diámetro, x, y
            partes.append(Point(float(v[3]), float(v[4])).buffer(float(v[2]) / 2, quad_segs=8))
        elif v[0] == '21':  # rectángulo centrado: exposición, ancho, alto, x, y, giro
            w, h, x, y, g = map(float, v[2:7])
            partes.append(affinity.rotate(box(x - w / 2, y - h / 2, x + w / 2, y + h / 2), g, origin=(0, 0)))
        elif v[0] == '7':  # alivio térmico: x, y, diámetro exterior e interior, separación, giro
            x, y, de, di, sep, g = map(float, v[1:7])
            ani = Point(x, y).buffer(de / 2, quad_segs=16).difference(Point(x, y).buffer(di / 2, quad_segs=16))
            cruz = box(x - de, y - sep / 2, x + de, y + sep / 2).union(box(x - sep / 2, y - de, x + sep / 2, y + de))
            partes.append(ani.difference(affinity.rotate(cruz, g, origin=(x, y))))
        elif v[0] != '0':
            raise ValueError(f'primitiva de macro no implementada: {s}')
    return shapely.union_all(partes)


def capa(texto):
    """Geometría (shapely) de un Gerber RS-274X de Altium: líneas, destellos y regiones, respetando la polaridad."""
    if '%MOMM' not in texto: raise ValueError('el Gerber no está en mm')
    esc = 10 ** int(re.search(r'%FSLAX\d(\d)', texto).group(1))
    macros = {n: [s.strip() for s in b.split('*') if s.strip()] for n, b in re.findall(r'%AM([^*]+)\*(.*?)%', texto, re.S)}
    ap = {}
    for d, tipo, par in re.findall(r'%ADD(\d+)([^,*]+)(?:,([^*]*))?\*%', texto):
        ap[int(d)] = forma(tipo, [float(x) for x in par.split('X')] if par else [], macros)
    base, bloque, oscura, act, x, y, reg, cont = Polygon(), [], True, None, 0, 0, None, []

    def volcar():
        nonlocal base
        if bloque:
            u = shapely.union_all(bloque)
            base = base.union(u) if oscura else base.difference(u)
            bloque.clear()

    def cerrar():
        if len(cont) >= 3: reg.append(shapely.make_valid(Polygon(cont)))
        cont.clear()

    for c in texto.split('*'):
        c = c.strip().lstrip('%').strip()
        if c in ('LPD', 'LPC'):
            volcar(); oscura = c == 'LPD'
        elif c == 'G36':
            reg = []
        elif c == 'G37':
            cerrar(); bloque.extend(reg); reg = None
        elif re.fullmatch(r'(?:G54)?D[1-9]\d+', c):
            act = int(c.split('D')[1])
        else:
            m = re.fullmatch(r'(?:G0?1)?(?:X(-?\d+))?(?:Y(-?\d+))?D0?([123])', c)
            if not m:
                if re.fullmatch(r'(?:G0?[23])?(?:X-?\d+)?(?:Y-?\d+)?(?:I-?\d+)?(?:J-?\d+)?D0?[123]', c): raise ValueError(f'arco no implementado: {c}')
                continue
            x0, y0 = x, y
            x = int(m.group(1)) / esc if m.group(1) else x
            y = int(m.group(2)) / esc if m.group(2) else y
            d = int(m.group(3))
            if reg is not None:
                if d == 2: cerrar(); cont.append((x, y))
                elif d == 1: cont.append((x, y))
            elif d == 3:
                bloque.append(affinity.translate(ap[act], x, y))
            elif d == 1:
                bloque.append(shapely.union_all([affinity.translate(ap[act], x0, y0), affinity.translate(ap[act], x, y)]).convex_hull)
    volcar()
    return base


def piezas(g):
    return [p for p in (g.geoms if hasattr(g, 'geoms') else [g]) if p.geom_type == 'Polygon' and p.area > 1e-6]


def analizar(capas, agujeros, pads, red):
    """capas: geometría por capa; agujeros: (x, y, d, metalizado); pads: de pads.json; red: {"U4-1": "V3V3_MCU"}."""
    # el pad M3 «sin anillo» es un disco del tamaño del agujero: el taladro lo elimina, así que no cuenta como cobre
    npth = [Point(h[0], h[1]).buffer(h[2] / 2 + 0.02, quad_segs=16) for h in agujeros if not h[3]]
    partes = [[q for q in piezas(g.buffer(UNION)) if not any(q.within(n) for n in npth)] for g in capas]
    arboles = [STRtree(p) for p in partes]
    padre = {}

    def raiz(n):
        padre.setdefault(n, n)
        while padre[n] != n:
            padre[n] = padre[padre[n]]; n = padre[n]
        return n

    def en(c, x, y):
        i = arboles[c].query(Point(x, y), predicate='intersects')
        return (c, int(i[0])) if len(i) else None

    nodos_h = {}
    for h in agujeros:
        if not h[3]: continue
        ns = [n for n in (en(c, h[0], h[1]) for c in range(len(capas))) if n]
        for n in ns: padre[raiz(n)] = raiz(ns[0])
        nodos_h[(round(h[0], 2), round(h[1], 2))] = ns
    pieza_pad, r = {}, {'sin_cobre': [], 'solo_sch': sorted(set(red) - {f"{p['ref']}-{p['pin']}" for p in pads})}
    for p in pads:
        k = f"{p['ref']}-{p['pin']}"
        if p['th'] and p['net'] == '' and k not in red: continue  # agujero M3 sin metalizar
        if p['th']:
            ns = nodos_h.get((round(p['px'], 2), round(p['py'], 2)))
            n = ns[0] if ns else None
        else:
            n = en(0 if p['top'] else 3, p['x'], p['y'])
        if n is None:
            r['sin_cobre'].append(k); continue
        pieza_pad[k] = raiz(n)
    # abiertos y cortos: partición de pads según el cobre contra partición según la netlist
    por_red, por_pieza = collections.defaultdict(set), collections.defaultdict(set)
    for k, n in pieza_pad.items():
        if red.get(k): por_red[red[k]].add(n); por_pieza[n].add(red[k])
    r['abiertos'] = {a: len(b) for a, b in por_red.items() if len(b) > 1}
    r['cortos'] = [sorted(v) for v in por_pieza.values() if len(v) > 1]
    r['redes'] = len(por_red); r['pines'] = sum(1 for k in pieza_pad if red.get(k))
    r['pads_fuera_de_netlist'] = sorted(k for k in pieza_pad if k not in red)
    # cobre flotante: piezas sin ningún pad
    con_pad = set(por_pieza) | {raiz(n) for n in pieza_pad.values()}
    r['flotante'] = []
    for c, ps in enumerate(partes):
        for i, g in enumerate(ps):
            if raiz((c, i)) not in con_pad:
                r['flotante'].append((COBRE[c], round(g.area, 3), round(g.centroid.x, 2), round(g.centroid.y, 2)))
    # separaciones entre cobre de redes distintas y de agujeros a cobre ajeno
    etiqueta = {n: next(iter(v)) for n, v in por_pieza.items() if len(v) == 1}
    r['sep_min'], r['agujero_min'], r['roces'] = {}, {}, []
    for c, ps in enumerate(partes):
        mejor = (9e9, None)
        for i, a in enumerate(ps):
            ra = etiqueta.get(raiz((c, i)))
            for j in arboles[c].query(a, predicate='dwithin', distance=0.3):
                if j <= i: continue
                if ra != etiqueta.get(raiz((c, int(j)))) or ra is None:
                    d = a.distance(ps[j])
                    if d < mejor[0]:
                        q = nearest_points(a, ps[j])[0]
                        mejor = (d, (round(q.x, 2), round(q.y, 2)))
        if mejor[1]: r['sep_min'][COBRE[c]] = (round(mejor[0] + 2 * UNION, 3), mejor[1])
    for h in agujeros:
        disco = Point(h[0], h[1]).buffer(h[2] / 2, quad_segs=16)
        mias = {raiz(n) for n in nodos_h.get((round(h[0], 2), round(h[1], 2)), [])}
        for c, ps in enumerate(partes):
            for j in arboles[c].query(disco, predicate='dwithin', distance=0.5):
                if raiz((c, int(j))) in mias: continue
                d = disco.distance(ps[j]) + UNION
                clase = 'metalizado' if h[3] else 'sin metalizar'
                if d < r['agujero_min'].get(clase, (9e9,))[0]: r['agujero_min'][clase] = (round(d, 3), COBRE[c], round(h[0], 2), round(h[1], 2))
                if d <= UNION * 2: r['roces'].append((COBRE[c], round(h[0], 2), round(h[1], 2), h[2]))
    return r


def mascara(archivos, pads, vias):
    """Máscara y pasta: pads abiertos, vías tapadas, THT abiertos en ambas caras."""
    g = {e: capa(archivos[e]) for e in ('GTS', 'GBS', 'GTP', 'GBP')}
    punto = lambda e, x, y: g[e].intersects(Point(x, y))
    r = collections.defaultdict(list)
    for p in pads:
        k = f"{p['ref']}-{p['pin']}"
        if p['th']:
            for e in ('GTS', 'GBS'):
                if not punto(e, p['px'], p['py']) and p['net']: r['THT sin apertura'].append(k + ' ' + e)
        else:
            lado = 'T' if p['top'] else 'B'
            if not punto(f'G{lado}S', p['x'], p['y']): r['SMD sin apertura'].append(k)
            if not punto(f'G{lado}P', p['x'], p['y']): r['SMD sin pasta'].append(k)
    for v in vias:
        for e in ('GTS', 'GBS'):
            if punto(e, v['x'], v['y']): r['vía destapada'].append(f"{v['x']:.2f},{v['y']:.2f} {e}")
    return dict(r)


def prueba(capas, agujeros, pads, red, vias):
    """Rompe la placa a propósito: si el verificador no lo detecta, no sirve."""
    malas = 0
    for v in [v for v in vias if v['net'] != 'GND'][:40]:
        sin = [h for h in agujeros if not (abs(h[0] - v['x']) < 0.01 and abs(h[1] - v['y']) < 0.01)]
        assert len(sin) == len(agujeros) - 1
        if analizar(capas, sin, pads, red)['abiertos']:
            malas += 1
    assert malas >= 5, f'solo {malas} vías quitadas se detectaron como abiertos'
    a, b = [p for p in pads if p['ref'] == 'U4' and p['pin'] in ('1', '2')]
    puente = capas[0].union(LineString([(a['x'], a['y']), (b['x'], b['y'])]).buffer(0.05))
    assert analizar([puente] + capas[1:], agujeros, pads, red)['cortos'], 'un puente entre U4-1 y U4-2 no se detectó'
    print(f'Prueba: al quitar una por una 40 vías de señal, {malas} dieron abierto; el puente U4-1/U4-2 dio corto.')


def main(zp, fpads, fred, probar):
    z = zipfile.ZipFile(zp)
    archivos = {os.path.splitext(n)[1][1:].upper(): z.read(n).decode('latin-1') for n in z.namelist()}
    capas = [capa(archivos[e]) for e in COBRE]
    agujeros = taladro(archivos['TXT'])
    d = json.load(open(fpads))
    pads, vias = [p for p in d['pads'] if p['pin']], d['vias']
    red = json.load(open(fred))
    r = analizar(capas, agujeros, pads, red)
    r['mascara'] = mascara(archivos, pads, vias)
    r['agujeros'] = {f'{k[0]} {k[1]}': v for k, v in collections.Counter((h[2], 'PTH' if h[3] else 'NPTH') for h in agujeros).items()}
    placa = box(0, 0, d['w'], d['h']).area
    r['cobertura'] = {e: round(g.area / placa * 100, 1) for e, g in zip(COBRE, capas)}
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if probar: prueba(capas, agujeros, pads, red, vias)
    malo = r['abiertos'] or r['cortos'] or r['sin_cobre'] or r['solo_sch'] or r['roces']
    print('RESULTADO:', 'FALLA' if malo else f"OK: {r['pines']} pines en {r['redes']} redes coinciden con el cobre de los Gerber; sin abiertos ni cortos.")
    return 1 if malo else 0


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if x != '--prueba']
    sys.exit(main(*a[:3], '--prueba' in sys.argv))
