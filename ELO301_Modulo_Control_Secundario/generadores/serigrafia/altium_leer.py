"""Lectura directa de archivos binarios de Altium (SchDoc y PcbDoc) sin abrir Altium.
SchDoc: registros |CLAVE=VALOR| del stream FileHeader y netlist geométrica por hoja.
PcbDoc: componentes, pistas, arcos y textos (formato de los Data binarios, según el importador de KiCad)."""
import math
import struct
import sys
from collections import defaultdict

import olefile


# ---------------- esquemático ----------------
def registros_sch(ruta):
    ole = olefile.OleFileIO(ruta)
    d = ole.openstream('FileHeader').read()
    out, i = [], 0
    while i + 4 <= len(d):
        n = struct.unpack_from('<I', d, i)[0]
        largo, tipo = n & 0xFFFFFF, n >> 24
        cuerpo = d[i + 4:i + 4 + largo]
        i += 4 + largo
        if tipo != 0:
            out.append({'_binario': tipo, '_crudo': cuerpo})
            continue
        txt = cuerpo.rstrip(b'\0').decode('latin-1')
        r = {}
        for campo in txt.split('|'):
            if '=' in campo:
                k, v = campo.split('=', 1)
                r[k.upper()] = v
        out.append(r)
    return out[1:] if out and 'HEADER' in out[0] else out   # el primero es la cabecera; los índices de OWNERINDEX parten en 0 tras ella


def coord(r, k):
    """Coordenada en mils (Altium guarda unidades de 10 mil más una fracción de 1/100000)."""
    return int(r.get(k, 0)) * 10 + int(r.get(k + '_FRAC', 0)) / 10000


def netlist_sch(ruta):
    regs = registros_sch(ruta)
    comps = {}
    for idx, r in enumerate(regs):
        if r.get('RECORD') == '1':
            comps[idx] = {'lib': r.get('LIBREFERENCE', ''), 'parte': r.get('CURRENTPARTID', '1'),
                          'modo': r.get('DISPLAYMODE', '0'), 'des': '?', 'x': coord(r, 'LOCATION.X'), 'y': coord(r, 'LOCATION.Y')}
    for r in regs:
        if r.get('RECORD') == '34' and int(r.get('OWNERINDEX', -1)) in comps:
            comps[int(r['OWNERINDEX'])]['des'] = r.get('TEXT', '?')
    for r in regs:
        if r.get('RECORD') == '41' and int(r.get('OWNERINDEX', -1)) in comps:
            comps[int(r['OWNERINDEX'])].setdefault('param', {})[r.get('NAME', '')] = r.get('TEXT', '')
    pines, cables, etiquetas, union = [], [], [], []
    for r in regs:
        t = r.get('RECORD')
        if t == '2':
            c = comps.get(int(r.get('OWNERINDEX', -1)))
            if not c or r.get('OWNERPARTID', '1') not in (c['parte'], '-1', '0') or r.get('OWNERPARTDISPLAYMODE', '0') != c['modo']:
                continue
            x, y, L = coord(r, 'LOCATION.X'), coord(r, 'LOCATION.Y'), coord(r, 'PINLENGTH')
            o = int(r.get('PINCONGLOMERATE', 0)) & 3
            dx, dy = ((1, 0), (0, 1), (-1, 0), (0, -1))[o]
            pines.append((round(x + dx * L, 1), round(y + dy * L, 1), c['des'], r.get('DESIGNATOR', ''), r.get('NAME', '')))
        elif t == '27':
            pts = [(round(coord(r, f'X{k}'), 1), round(coord(r, f'Y{k}'), 1)) for k in range(1, int(r.get('LOCATIONCOUNT', 0)) + 1)]
            cables.extend(zip(pts, pts[1:]))
        elif t in ('25', '17', '18'):
            etiquetas.append((round(coord(r, 'LOCATION.X'), 1), round(coord(r, 'LOCATION.Y'), 1), r.get('TEXT', r.get('NAME', '')),
                              {'25': 'etiqueta', '17': 'poder', '18': 'puerto'}[t]))
        elif t == '29':
            union.append((round(coord(r, 'LOCATION.X'), 1), round(coord(r, 'LOCATION.Y'), 1)))
    # unión-búsqueda sobre puntos
    padre = {}

    def raiz(a):
        padre.setdefault(a, a)
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a

    def unir(a, b):
        padre[raiz(a)] = raiz(b)

    def sobre(p, s):
        (x1, y1), (x2, y2) = s
        if abs((x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1)) > 0.5:
            return False
        return min(x1, x2) - 0.5 <= p[0] <= max(x1, x2) + 0.5 and min(y1, y2) - 0.5 <= p[1] <= max(y1, y2) + 0.5

    for a, b in cables:
        unir(('p',) + a, ('p',) + b)
    extremos = {p for s in cables for p in s}
    puntos = list(extremos) + [p[:2] for p in pines] + [e[:2] for e in etiquetas] + union
    for p in puntos:                       # un punto sobre el tramo de un cable queda conectado a ese cable
        for s in cables:
            if sobre(p, s):
                unir(('p',) + p, ('p',) + s[0])
    for x, y, des, num, nom in pines:
        unir(('pin', des, num), ('p', x, y))
    nombres = defaultdict(set)
    for x, y, txt, tipo in etiquetas:
        unir(('n', txt), ('p', x, y))
    redes = defaultdict(set)
    for x, y, des, num, nom in pines:
        redes[raiz(('pin', des, num))].add(f'{des}-{num}')
    for k in list(padre):
        if k[0] == 'n':
            nombres[raiz(k)].add(k[1])
    res = {}
    for rz, miembros in redes.items():
        nom = '/'.join(sorted(nombres.get(rz, []))) or f'(sin nombre:{sorted(miembros)[0]})'
        res.setdefault(nom, set()).update(miembros)
    return comps, res, etiquetas, regs


# ---------------- placa ----------------
MIL_A_MM = 0.0254
U = 1e-4 * MIL_A_MM                        # unidad interna de Altium en mm
CAPAS = {1: 'Top', 32: 'Bottom', 33: 'TopOverlay', 34: 'BottomOverlay', 37: 'TopSolder', 38: 'BottomSolder'}


def flujo(ole, nombre):
    return ole.openstream(nombre + '/Data').read() if ole.exists(nombre + '/Data') else b''


def textos_pcb(d):
    """Registros |CLAVE=VALOR| con prefijo de largo (Components6, Nets6, Board6...)."""
    out, i = [], 0
    while i + 4 <= len(d):
        n = struct.unpack_from('<I', d, i)[0]
        txt = d[i + 4:i + 4 + n].rstrip(b'\0').decode('latin-1')
        i += 4 + n
        r = {}
        for campo in txt.split('|'):
            if '=' in campo:
                k, v = campo.split('=', 1)
                r[k.upper()] = v
        out.append(r)
    return out


def binarios(d, tipo):
    """Divide un Data binario en registros: byte de tipo y subregistros con largo de 4 bytes."""
    out, i = [], 0
    nsub = {4: 1, 1: 1, 5: 2, 6: 1, 3: 1}.get(tipo, 1)
    while i < len(d):
        t = d[i]; i += 1
        subs = []
        for _ in range(nsub):
            n = struct.unpack_from('<I', d, i)[0]; i += 4
            subs.append(d[i:i + n]); i += n
        out.append((t, subs))
    return out


def leer_pcb(ruta):
    ole = olefile.OleFileIO(ruta)
    comps = textos_pcb(flujo(ole, 'Components6'))
    redes = [r.get('NAME', '') for r in textos_pcb(flujo(ole, 'Nets6'))]
    pistas = []
    for t, (s,) in binarios(flujo(ole, 'Tracks6'), 4):
        capa, red, poli, comp = s[0], *struct.unpack_from('<HHH', s, 3)
        x1, y1, x2, y2, w = struct.unpack_from('<iiiii', s, 13)
        pistas.append({'capa': capa, 'red': redes[red] if red < len(redes) else None, 'comp': comp if comp != 0xFFFF else None,
                       'poli': poli != 0xFFFF, 'x1': x1 * U, 'y1': y1 * U, 'x2': x2 * U, 'y2': y2 * U, 'w': w * U})
    arcos = []
    for t, (s,) in binarios(flujo(ole, 'Arcs6'), 1):
        capa, red, poli, comp = s[0], *struct.unpack_from('<HHH', s, 3)
        cx, cy, r = struct.unpack_from('<iii', s, 13)
        a0, a1 = struct.unpack_from('<dd', s, 25)
        w = struct.unpack_from('<i', s, 41)[0]
        arcos.append({'capa': capa, 'comp': comp if comp != 0xFFFF else None, 'poli': poli != 0xFFFF,
                      'cx': cx * U, 'cy': cy * U, 'r': r * U, 'a0': a0, 'a1': a1, 'w': w * U})
    textos = []
    for t, (s, s2) in binarios(flujo(ole, 'Texts6'), 5):
        capa = s[0]
        comp = struct.unpack_from('<H', s, 7)[0]
        x, y, h = struct.unpack_from('<iii', s, 13)
        rot = struct.unpack_from('<d', s, 27)[0]
        espejo = s[35]
        trazo = struct.unpack_from('<i', s, 36)[0]
        es_comentario, es_des = (s[40], s[41]) if len(s) > 42 else (0, 0)
        tipo_fuente = s[43] if len(s) > 43 else 0
        cadena = s2[1:1 + s2[0]].decode('latin-1', 'replace') if s2 else ''
        textos.append({'capa': capa, 'comp': comp if comp != 0xFFFF else None, 'x': x * U, 'y': y * U, 'h': h * U,
                       'rot': rot, 'trazo': trazo * U, 'des': es_des, 'coment': es_comentario, 'fuente': tipo_fuente,
                       'texto': cadena.strip('\0')})
    tablero = textos_pcb(flujo(ole, 'Board6'))
    return comps, redes, pistas, arcos, textos, tablero


if __name__ == '__main__':
    print(registros_sch(sys.argv[1])[:3])


def pads_vias(ruta):
    """Pads (centro, tamaños, agujero, capa, red, componente) y vías (centro, diámetro, agujero, red)."""
    ole = olefile.OleFileIO(ruta)
    redes = [r.get('NAME', '') for r in textos_pcb(flujo(ole, 'Nets6'))]
    comps = textos_pcb(flujo(ole, 'Components6'))
    d = flujo(ole, 'Pads6')
    pads, i = [], 0
    while i < len(d):
        i += 1
        subs = []
        for _ in range(6):
            n = struct.unpack_from('<I', d, i)[0]; i += 4
            subs.append(d[i:i + n]); i += n
        nom = subs[0][1:1 + subs[0][0]].decode('latin-1') if subs[0] else ''
        s = subs[4]
        capa, red, comp = s[0], struct.unpack_from('<H', s, 3)[0], struct.unpack_from('<H', s, 7)[0]
        x, y, tx, ty, mx, my, bx, by, h = struct.unpack_from('<iiiiiiiii', s, 13)
        forma = s[49]
        rot = struct.unpack_from('<d', s, 52)[0]
        # subregistro 6 (tamaño y forma por capa): forma alternativa y radio de esquina en % de la mitad del lado menor
        s6, alt, radio = subs[5], 0, 0.0
        if len(s6) >= 596:
            alt, pct = s6[532], s6[564]
            if alt == 9:
                radio = min(tx, ty) * U * pct / 200
        pads.append({'nombre': nom, 'capa': capa, 'red': redes[red] if red < len(redes) else None,
                     'comp': comps[comp].get('SOURCEDESIGNATOR') if comp < len(comps) else None,
                     'x': x * U, 'y': y * U, 'tx': tx * U, 'ty': ty * U, 'bx': bx * U, 'by': by * U, 'h': h * U, 'forma': forma, 'rot': rot,
                     'alt': alt, 'radio': radio})
    d = flujo(ole, 'Vias6')
    vias, i = [], 0
    while i < len(d):
        i += 1
        n = struct.unpack_from('<I', d, i)[0]; i += 4
        s = d[i:i + n]; i += n
        red = struct.unpack_from('<H', s, 3)[0]
        x, y, dia, h = struct.unpack_from('<iiii', s, 13)
        vias.append({'red': redes[red] if red < len(redes) else None, 'x': x * U, 'y': y * U, 'dia': dia * U, 'h': h * U})
    return pads, vias


def forma_pad(p, lado, O=25.4):
    """Cobre de un pad en una cara ('top' o 'bot') como polígono de shapely, en mm desde el origen O.
    Redondo u oblongo (forma 1 sin forma alternativa), rectángulo redondeado (alternativa 9) o rectángulo."""
    from shapely.geometry import Point, box
    from shapely import affinity
    tx, ty = (p['tx'], p['ty']) if (lado == 'top' or p['h'] == 0) else (p['bx'], p['by'])
    if p.get('alt') == 9 and p.get('radio', 0) > 0:
        r = min(p['radio'], min(tx, ty) / 2)
        g = box(-tx / 2 + r, -ty / 2 + r, tx / 2 - r, ty / 2 - r).buffer(r, 16)
    elif p['forma'] == 1:
        r = min(tx, ty) / 2
        g = box(-tx / 2 + r, -ty / 2 + r, tx / 2 - r, ty / 2 - r).buffer(r, 32) if abs(tx - ty) > 1e-6 else Point(0, 0).buffer(r, 64)
    else:
        g = box(-tx / 2, -ty / 2, tx / 2, ty / 2)
    return affinity.translate(affinity.rotate(g, p['rot'], origin=(0, 0)), p['x'] - O, p['y'] - O)
