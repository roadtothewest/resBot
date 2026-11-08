"""Completa la serigrafía de la placa sin tocar la que ya tiene (commit 7875a52: líneas de 0,18 mm, 61 designadores de 1,2 mm):
- muestra los designadores que quedaron ocultos (a 1,0 mm, el mínimo de JLCPCB), con el componente identificado;
- agrega el nombre de cada módulo, como las hojas del esquemático, y líneas que separan los módulos.
Lo existente (tinta, aberturas de máscara, cuerpos, vías, tornillos) es obstáculo; un cálculo sobre una grilla de 0,05 mm
ubica cada texto nuevo lo más cerca de su pieza y dentro de su módulo.

  python3 completar.py volcar                  lee de Altium la serigrafía y las piezas a completar_dump.txt (solo sobre la placa
                                               sin completar: el volcado es la referencia de lo que ya había)
  python3 completar.py plan <zip> <pads.json>  calcula completar_plan.json (no toca Altium)
  python3 completar.py placa                   aplica el plan a la placa abierta, sin guardar
  python3 completar.py guardar                 rehace polígonos, corre el DRC y guarda
Se verifica con herramientas/revisar_serigrafia.py <zip> completar_plan.json sobre los Gerber nuevos."""
import json, math, random, sys, zipfile
from pathlib import Path
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / 'herramientas')); sys.path.insert(0, str(AQUI.parent / 'pcb'))
DUMP, PLAN, MEDIDAS = AQUI / 'completar_dump.txt', AQUI / 'completar_plan.json', AQUI / 'completar_anchos.json'
W, H = 70.0, 50.0
LINEA, TXT, TIT = 0.18, (1.0, 0.17), (1.2, 0.20)
C_MASK, C_SILK, C_TEXTO, BORDE, R_M3 = 0.16, 0.26, 0.3, 0.25, 3.48

# Módulos (polígonos en mm desde el origen de la placa): cada texto nuevo queda dentro del suyo.
REG = {
    'FOC': [(.25, 41.1), (17.5, 41.1), (17.5, 38.1), (30, 38.1), (30, 39.5), (33.2, 39.5), (33.2, 38.0), (39.8, 38.0), (39.8, 41.1), (69.75, 41.1), (69.75, 49.75), (.25, 49.75)],
    'EXP': [(17.35, .25), (62.9, .25), (62.9, 6.5), (17.35, 6.5)],
    'UART': [(.25, .25), (17.35, .25), (17.35, 6.5), (.25, 6.5)],
    'PODER': [(.25, 6.5), (25.5, 6.5), (25.5, 20.54), (24.25, 20.54), (24.25, 28.6), (8, 28.6), (8, 18.7), (.25, 18.7)],
    'TOF': [(.25, 18.7), (8, 18.7), (8, 28.6), (13.4, 28.6), (13.4, 34.9), (.25, 34.9)],
    'IMU': [(13.4, 28.6), (25.5, 28.6), (25.5, 38.1), (17.5, 38.1), (17.5, 41.1), (.25, 41.1), (.25, 34.9), (13.4, 34.9)],
    'MCU': [(25.5, 6.5), (50.5, 6.5), (50.5, 27.3), (47.85, 27.3), (47.85, 25.55), (41.7, 25.55), (41.7, 27.45), (40.95, 27.45), (40.95, 28.9), (37.15, 28.9), (37.15, 38.0), (33.2, 38.0), (33.2, 39.5), (30, 39.5), (30, 38.1), (25.5, 38.1), (25.5, 28.6), (24.25, 28.6), (24.25, 20.54), (25.5, 20.54)],
    'LDO': [(37.15, 28.9), (40.95, 28.9), (40.95, 27.45), (41.7, 27.45), (41.7, 25.55), (47.85, 25.55), (47.85, 41.1), (39.8, 41.1), (39.8, 38.0), (37.15, 38.0)],
    'GNSS': [(47.85, 27.3), (69.75, 27.3), (69.75, 41.1), (47.85, 41.1)],
    'SERV': [(50.5, 6.5), (69.75, 6.5), (69.75, 27.3), (50.5, 27.3)],
}
# Líneas que separan los módulos; se cortan solas donde hay máscara, tinta, tornillos o vías.
TRAZOS = [
    [(.33, 41.1), (17.5, 41.1), (17.5, 38.1), (30, 38.1), (30, 39.5), (33.2, 39.5), (33.2, 38.0), (39.8, 38.0), (39.8, 41.1), (69.67, 41.1)],
    [(.33, 6.5), (69.67, 6.5)], [(17.35, .33), (17.35, 6.5)],
    [(8, 18.7), (8, 28.6), (24.25, 28.6)], [(.33, 18.7), (8, 18.7)], [(13.4, 28.6), (13.4, 34.9), (.33, 34.9)],
    [(25.5, 6.5), (25.5, 20.54), (24.25, 20.54), (24.25, 28.6), (25.5, 28.6), (25.5, 38.1)],
    [(37.15, 38.0), (37.15, 28.9), (40.95, 28.9), (40.95, 27.45), (41.7, 27.45), (41.7, 25.55), (47.85, 25.55)], [(47.85, 25.55), (47.85, 41.1)], [(47.85, 27.3), (69.67, 27.3)], [(50.5, 6.5), (50.5, 27.3)],
]
MODULO = {'PODER': 'D1 D2 C1 C2 C3 C4 C5 C6 C7 C8 C9 U1 U2 L1 LED1 R3', 'TOF': 'J7 R7 R8', 'IMU': 'U5 C26 C27', 'MCU': 'U4 Y1 C13 C14 C15 C16 C17 C18 C19 C20 C21 C22 C23 FB2',
          'LDO': 'U3 C10 C11 FB1 R1 R2 C12', 'GNSS': 'U6 C24 C25 R9 L2 J8', 'SERV': 'SW1 SW2 R4 R5 LED2 J2', 'FOC': 'J3 J4 J5 J6 R10 R11 R12 R13 R14 R15', 'UART': 'J9'}
# Nombre de cada módulo (como el bloque de la hoja superior) y funciones que no dice el designador: texto, tamaño, punto deseado, módulo.
ETIQ = [('PODER', TIT, (4, 15.5), 'PODER'), ('MCU', TIT, (28, 37), 'MCU'), ('IMU', TIT, (15.4, 36.5), 'IMU'), ('TOF', TIT, (4.6, 33.8), 'TOF'),
        ('GNSS', TIT, (56.5, 39.6), 'GNSS'), ('LDO SENS', TXT, (38.1, 33.5), 'LDO'), ('SERVICIO', TIT, (56, 24.8), 'SERV'), ('SWD', TXT, (63.6, 19), 'SERV'),
        ('UART', TXT, (14.8, 5.5), 'UART'), ('EXPANSION', TXT, (35.8, 5.5), 'EXP'),
        ('FOC1', TIT, (11.8, 42.1), 'FOC'), ('FOC2', TIT, (25.5, 42.1), 'FOC'), ('FOC3', TIT, (45.5, 42.1), 'FOC'), ('FOC4', TIT, (60, 42.1), 'FOC')]
CORTO = {'LDO SENS': ['LDO'], 'SERVICIO': ['SERV'], 'EXPANSION': ['EXP']}  # si el nombre largo no cabe cerca
MAX_LEJOS = 6.0
SEP_TEXTO = 0.40  # separador a texto: regla Silk To Silk de la placa (10 mil) + medio ancho de línea + margen
GUIA_DESDE = 1.5  # designador a más de esto de su pieza: lleva línea guía  # puntaje máximo (≈ mm desde su punto o pieza): más lejos, el texto confunde más de lo que identifica
MOVER = ['C23', 'R2']  # ocupaban el único lugar junto a C12 y a C25; se corren junto a su pieza
# Zona LDO/GNSS, la más densa: caja de tinta fija (x0, y0, giro) medida a mano; la revisión de los Gerber confirma las distancias.
FIJO = {'C12': (45.6, 26.8, 0), 'C23': (45.8, 23.0, 0), 'R2': (44.25, 31.4, 0), 'C25': (46.72, 30.7, 90)}
OBJ = {'J4': (21.2, 42), 'R13': (31.6, 42)}  # punto deseado en vez del courtyard (J4 es grande: junto a su pin 1)


def cargar():
    n = lambda v: float(v.replace(',', '.'))
    d = {'T': [], 'X': [], 'C': {}}
    for l in DUMP.read_text().split('\n'):
        l = l.split(';')
        if l[0] == 'T': d['T'].append(dict(capa=l[1], ref=l[2], p=[n(v) for v in l[7:11]], w=n(l[11])))
        elif l[0] == 'X': d['X'].append(dict(capa=l[1], ref=l[2], bb=[n(v) for v in l[3:7]], s=(n(l[10]), n(l[11])), t=l[12], des=l[13] != '0', com=l[14] != '0'))
        elif l[0] == 'C': d['C'][l[1]] = dict(capa=l[2], x=n(l[3]), y=n(l[4]), rot=n(l[5]), fp=l[6], nombre=l[7] != '0', comentario=l[8] != '0', bb=[n(v) for v in l[9:13]])
    return d


def volcar():
    from drc_comun import correr, VARS, ABRIR
    r = correr(f"""{VARS}    BB : TCoordRect;
    dueno : String;
    G : IDispatch;
{ABRIR}s := '';
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eTrackObject, eArcObject, eTextObject)); It.AddFilter_LayerSet(MkSet(eTopOverlay, eBottomOverlay)); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do
begin
    dueno := '';
    if X.InComponent then if X.Component <> nil then dueno := X.Component.Name.Text;
    BB := X.BoundingRectangle;
    nom := Layer2String(X.Layer) + ';' + dueno + ';' + FloatToStr(CoordToMMs(BB.Left - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Bottom - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Right - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(BB.Top - Board.YOrigin));
    if X.ObjectId = eTrackObject then
        s := s + 'T;' + nom + ';' + FloatToStr(CoordToMMs(X.x1 - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(X.y1 - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(X.x2 - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(X.y2 - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(X.Width)) + #10
    else if X.ObjectId = eArcObject then
        s := s + 'A;' + nom + #10
    else
        s := s + 'X;' + nom + ';' + FloatToStr(CoordToMMs(X.XLocation - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(X.YLocation - Board.YOrigin)) + ';' + FloatToStr(X.Rotation) + ';' + FloatToStr(CoordToMMs(X.Size)) + ';' + FloatToStr(CoordToMMs(X.Width)) + ';' + X.Text + ';' + BoolToStr(X.IsDesignator) + ';' + BoolToStr(X.IsComment) + #10;
    X := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eComponentObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
C := It.FirstPCBObject;
while C <> nil do
begin
    x0 := 2147483647; y0 := 2147483647; x1 := -2147483647; y1 := -2147483647;
    G := C.GroupIterator_Create; G.AddFilter_ObjectSet(MkSet(ePadObject, eTrackObject, eArcObject, eFillObject, eRegionObject));
    V := G.FirstPCBObject;
    while V <> nil do
    begin
        if (V.Layer <> eTopOverlay) and (V.Layer <> eBottomOverlay) then
        begin
            BB := V.BoundingRectangle;
            if BB.Left < x0 then x0 := BB.Left; if BB.Bottom < y0 then y0 := BB.Bottom; if BB.Right > x1 then x1 := BB.Right; if BB.Top > y1 then y1 := BB.Top;
        end;
        V := G.NextPCBObject;
    end;
    C.GroupIterator_Destroy(G);
    s := s + 'C;' + C.Name.Text + ';' + Layer2String(C.Layer) + ';' + FloatToStr(CoordToMMs(C.x - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(C.y - Board.YOrigin)) + ';' + FloatToStr(C.Rotation) + ';' + C.Pattern + ';' + BoolToStr(C.NameOn) + ';' + BoolToStr(C.CommentOn) + ';' + FloatToStr(CoordToMMs(x0 - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(y0 - Board.YOrigin)) + ';' + FloatToStr(CoordToMMs(x1 - Board.XOrigin)) + ';' + FloatToStr(CoordToMMs(y1 - Board.YOrigin)) + #10;
    C := It.NextPCBObject;
end;
Board.BoardIterator_Destroy(It);
ResultText := s;""", 300)
    DUMP.write_text(r)
    d = cargar()
    print(len(r), 'bytes;', len(d['T']), 'líneas,', len(d['X']), 'textos,', len(d['C']), 'piezas; ocultos:', sorted(r for r, c in d['C'].items() if not c['nombre']),
          '; arcos:', r.count('\nA;'))


def medir(pares):
    """Tinta (ancho, alto) de cada texto, medida en Altium sin guardar: la caja de Altium es la tinta más medio trazo por lado."""
    from drc_comun import correr, VARS, ABRIR
    bloque = ''.join(f"""T := PCBServer.PCBObjectFactory(eTextObject, eNoDimension, eCreate_Default);
T.XLocation := Board.XOrigin + MMsToCoord(10); T.YLocation := Board.YOrigin + MMsToCoord(10); T.Layer := eTopOverlay; T.Text := '{t}'; T.Size := MMsToCoord({h}); T.Width := MMsToCoord({w});
Board.AddPCBObject(T); BB := T.BoundingRectangle; s := s + FloatToStr(CoordToMMs(BB.Right - BB.Left)) + ';' + FloatToStr(CoordToMMs(BB.Top - BB.Bottom)) + #10; Board.RemovePCBObject(T);
""" for t, h, w in pares)
    r = correr(f"""{VARS}    T : IDispatch;
    BB : TCoordRect;
{ABRIR}s := '';
{bloque}ResultText := s;""", 200)
    n = lambda v: float(v.replace(',', '.'))
    return {f'{t}|{h}|{w}': (n(l.split(';')[0]) - w, n(l.split(';')[1]) - w) for (t, h, w), l in zip(pares, r.strip().split('\n'))}


def plan(zip_gerber, fpads):
    import numpy as np
    from PIL import Image, ImageDraw
    from shapely.geometry import LineString, Point, Polygon, box
    from shapely.ops import unary_union
    from lvs_gerber import capa, piezas
    d = cargar()
    z = zipfile.ZipFile(zip_gerber); a = {n.rsplit('.', 1)[-1].upper(): z.read(n).decode('latin1') for n in z.namelist()}
    mask = capa(a['GTS'])
    pads = json.load(open(fpads))
    arriba = lambda o: o['capa'] == 'Top Overlay'
    lineas = [LineString([t['p'][:2], t['p'][2:]]).buffer(t['w'] / 2) for t in d['T'] if arriba(t)]
    textos = [box(*x['bb']) for x in d['X'] if arriba(x) and not (x['des'] and not d['C'][x['ref']]['nombre']) and not (x['com'] and not d['C'][x['ref']]['comentario'])
              and not (x['des'] and x['ref'] in MOVER)]
    tinta = unary_union(lineas + textos)
    m3 = [Point(c['x'], c['y']).buffer(R_M3) for r, c in d['C'].items() if r[0] == 'H']
    vias = [Point(v['x'], v['y']).buffer(.3 + LINEA / 2 + .02, quad_segs=6) for v in pads['vias']]
    # separadores de módulo: cortados donde hay máscara, tinta, tornillos o vías
    RES = 0.05
    PX, PY = int(W / RES) + 1, int(H / RES) + 1
    def raster(geoms):
        im = Image.new('1', (PX, PY), 0); dr = ImageDraw.Draw(im)
        for g in geoms:
            for p in piezas(g):
                if p.is_empty: continue
                dr.polygon([(x / RES, y / RES) for x, y in p.exterior.coords], fill=1, outline=1)
                for i in p.interiors: dr.polygon([(x / RES, y / RES) for x, y in i.coords], fill=0)
        return np.array(im, dtype=np.int32)
    integral = lambda m: np.pad(m, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    cuerpos = [box(*c['bb']).buffer(-.2, join_style=2) for r, c in d['C'].items() if c['capa'] == 'Top Layer' and r[0] != 'H'] + m3
    base = raster([mask.buffer(C_MASK + RES / 2, quad_segs=4), unary_union(lineas).buffer(C_SILK + RES / 2, quad_segs=3), unary_union(textos).buffer(C_TEXTO + RES / 2, join_style=2)]
                  + cuerpos)
    # etiqueta de módulo que no cabe: último intento con 0,20 mm a las líneas de huella (el DRC de la placa lo acepta)
    base_flojo = raster([mask.buffer(C_MASK + RES / 2, quad_segs=4), unary_union(lineas).buffer(0.20 + RES / 2, quad_segs=3), unary_union(textos).buffer(C_TEXTO + RES / 2, join_style=2)]
                        + cuerpos)
    k = int(BORDE / RES) + 1
    for b_ in (base, base_flojo): b_[:k, :] = 1; b_[-k:, :] = 1; b_[:, :k] = 1; b_[:, -k:] = 1
    Iv = integral(raster([Point(v['x'], v['y']).buffer(.32, quad_segs=6) for v in pads['vias']]))
    xs, ys = np.arange(PX) * RES, np.arange(PY) * RES
    ocultos = sorted(r for r, c in d['C'].items() if not c['nombre'] and c['capa'] == 'Top Layer')
    var_ = lambda t, s: [(t, s)] + ([(t, TXT)] if s == TIT else []) + [(c, TXT) for c in CORTO.get(t, [])]
    pares = sorted({(v[0], v[1][0], v[1][1]) for t, s, _, _ in ETIQ for v in var_(t, s)} | {(r, *TXT) for r in ocultos}
                   | {(x['ref'], *x['s']) for x in d['X'] if x['des'] and x['ref'] in MOVER})
    med = json.loads(MEDIDAS.read_text()) if MEDIDAS.exists() else {}
    falta = [p for p in pares if f'{p[0]}|{p[1]}|{p[2]}' not in med]
    if falta:
        med.update(medir(falta)); MEDIDAS.write_text(json.dumps(med, indent=0, ensure_ascii=False))
    MOD = {r: m for m, rs in MODULO.items() for r in rs.split()}
    items = [dict(id='L:' + t, var=var_(t, s), caja=(o[0], o[1], o[0], o[1]), reg=reg) for t, s, o, reg in ETIQ]
    for r in ocultos:
        c = d['C'][r]
        bb = (c['x'] - R_M3, c['y'] - R_M3, c['x'] + R_M3, c['y'] + R_M3) if r[0] == 'H' else OBJ[r] * 2 if r in OBJ else tuple(c['bb'])
        items.append(dict(id=r, var=[(r, TXT)], caja=bb, reg=MOD.get(r)))
    for r in MOVER:  # designadores existentes que se corren para dejar lugar; conservan su tamaño
        s0 = next(x['s'] for x in d['X'] if x['des'] and x['ref'] == r)
        items.append(dict(id=r, var=[(r, s0)], caja=tuple(d['C'][r]['bb']), reg=MOD.get(r)))
    for it in items:
        it['var'] = [(t_, s_, *med[f'{t_}|{s_[0]}|{s_[1]}']) for t_, s_ in it['var']]
        im = Image.new('1', (PX, PY), 1)
        if it['reg']: ImageDraw.Draw(im).polygon([(x / RES, y / RES) for x, y in Polygon(REG[it['reg']]).buffer(-(C_SILK + LINEA / 2) + 0.2).exterior.coords], fill=0)
        else: im = Image.new('1', (PX, PY), 0)
        it['fuera'] = np.array(im, dtype=np.int32)
    def puntuar(it, I, rot, w, h):
        w, h = (w, h) if rot == 0 else (h, w)
        a_, c_ = int(math.ceil(w / RES)) + 1, int(math.ceil(h / RES)) + 1
        L = (I[c_:, a_:] - I[:-c_, a_:] - I[c_:, :-a_] + I[:-c_, :-a_]) == 0
        ny, nx = L.shape
        X, Y = np.meshgrid(xs[:nx], ys[:ny])
        b = it['caja']
        dist = np.hypot(np.maximum(np.maximum(b[0] - (X + w), X - b[2]), 0), np.maximum(np.maximum(b[1] - (Y + h), Y - b[3]), 0))
        S = dist + 0.04 * (np.abs(X + w / 2 - (b[0] + b[2]) / 2) + np.abs(Y + h / 2 - (b[1] + b[3]) / 2)) + (0.5 if rot else 0.0)
        S = S + ((Iv[c_:, a_:] - Iv[:-c_, a_:] - Iv[c_:, :-a_] + Iv[:-c_, :-a_]) > 0) * 3.0
        S[~L] = np.inf
        return S
    def resolver(orden, pos):
        puesto = dict(pos)
        for it in orden:
            puesto.pop(it['id'], None)
            if it['id'] in FIJO:
                x0, y0, rot = FIJO[it['id']]; t_, s_, w0, h0 = it['var'][0]
                w, h = (w0, h0) if rot == 0 else (h0, w0)
                puesto[it['id']] = (x0, y0, x0 + w, y0 + h, rot, 0.0, t_, s_)
                continue
            F, Ff = base.copy(), base_flojo.copy()
            for c in puesto.values():
                x0, y0, x1, y1 = max(int((c[0] - C_TEXTO) / RES) - 1, 0), max(int((c[1] - C_TEXTO) / RES) - 1, 0), int((c[2] + C_TEXTO) / RES) + 2, int((c[3] + C_TEXTO) / RES) + 2
                F[y0:y1, x0:x1] = 1; Ff[y0:y1, x0:x1] = 1
            I = integral(F | it['fuera'])
            # designador: si no cabe en su módulo, cerca de su pieza aunque cruce el separador (que se corta); etiqueta: margen flojo
            I2 = integral(F) if not it['id'].startswith('L:') else integral(Ff | it['fuera'])
            for k_, (t_, s_, w0, h0, *_) in enumerate(it['var'] + ([(*it['var'][0], 'libre')] if not it['id'].startswith('L:') else [(*v, 'flojo') for v in it['var']])):  # la primera variante que quede cerca de su punto
                mejor = None
                for rot in (0, 90):
                    S = puntuar(it, I2 if k_ >= len(it['var']) else I, rot, w0, h0)
                    if np.isfinite(S).any():
                        i = np.unravel_index(np.argmin(S), S.shape)
                        if mejor is None or S[i] < mejor[0]: mejor = (float(S[i]), i, rot)
                if mejor and mejor[0] <= MAX_LEJOS:
                    sc, (iy, ix), rot = mejor
                    w, h = (w0, h0) if rot == 0 else (h0, w0)
                    puesto[it['id']] = (float(xs[ix]), float(ys[iy]), float(xs[ix]) + w, float(ys[iy]) + h, rot, sc + 2 * k_, t_, s_)
                    break
        return puesto
    des = [i for i in items if not i['id'].startswith('L:')]
    eti = [i for i in items if i['id'].startswith('L:')]
    pos = resolver(des + eti, {})  # primero los designadores: identificar cada pieza manda
    costo = lambda p: sum(v[5] for v in p.values()) + 100 * sum(i['id'] not in p for i in items)
    random.seed(1)
    for _ in range(12):
        p = resolver(sorted(items, key=lambda i: (i['id'] in pos, i['id'].startswith('L:'), random.random())), pos)
        if costo(p) < costo(pos): pos = p
    print('sin lugar:', [i['id'] for i in items if i['id'] not in pos], 'costo', round(costo(pos), 1))
    lejos = {k: round(v[5], 2) for k, v in pos.items() if v[5] > 1.5}
    print('lejos de su punto (mm aprox.):', lejos)
    # designadores lejos de su pieza: se reubican donde una línea guía recta llegue a la pieza sin cruzar pads, tinta ni otras piezas
    from shapely.geometry import Polygon as Pg
    from shapely.ops import nearest_points
    guias = []
    for it in [i for i in items if i['id'] in pos and not i['id'].startswith('L:') and pos[i['id']][5] > GUIA_DESDE]:
        r = it['id']; c = d['C'][r]
        propio = box(*c['bb']).buffer(.3, join_style=2)  # la guía llega hasta al lado de la pieza
        otros = [box(*v[:4]).buffer(C_TEXTO, join_style=2) for k_, v in pos.items() if k_ != r]
        veda = unary_union([mask.buffer(C_MASK + LINEA / 2 + .01, quad_segs=6), tinta.buffer(C_SILK + LINEA / 2, quad_segs=4)]
                           + [b_ for k_, b_ in zip([k for k in d['C'] if d['C'][k]['capa'] == 'Top Layer' and k[0] != 'H'], cuerpos) if k_ != r] + otros + m3 + vias)
        blanco = propio.difference(veda)
        if blanco.is_empty: print('sin espacio junto a', r); continue
        F = base.copy()
        for k_, v in pos.items():
            if k_ == r: continue
            x0, y0, x1, y1 = max(int((v[0] - C_TEXTO) / RES) - 1, 0), max(int((v[1] - C_TEXTO) / RES) - 1, 0), int((v[2] + C_TEXTO) / RES) + 2, int((v[3] + C_TEXTO) / RES) + 2
            F[y0:y1, x0:x1] = 1
        I = integral(F)
        t_, s_, w0, h0 = it['var'][0]
        mejor = None
        for rot in (0, 90):
            w, h = (w0, h0) if rot == 0 else (h0, w0)
            S = puntuar(dict(caja=it['caja']), I, rot, w0, h0)
            for iy, ix in zip(*np.nonzero(np.isfinite(S) & (S < 7))):
                if iy % 4 or ix % 4: continue  # cada 0,2 mm
                bx = box(xs[ix], ys[iy], xs[ix] + w, ys[iy] + h)
                p, q = nearest_points(bx.buffer(.35, join_style=2).exterior, blanco)
                seg = LineString([p, q])
                if seg.length < .4 or seg.buffer(LINEA / 2).intersects(veda.difference(propio)): continue
                sc = seg.length + .3 * S[iy, ix]
                if mejor is None or sc < mejor[0]: mejor = (sc, (float(xs[ix]), float(ys[iy]), float(xs[ix]) + w, float(ys[iy]) + h, rot, sc, t_, s_), seg)
        if mejor:
            pos[r] = mejor[1]; guias.append([round(v, 3) for v in list(mejor[2].coords[0]) + list(mejor[2].coords[1])])
            print('guía', r, 'largo', round(mejor[2].length, 2), 'texto en', [round(v, 2) for v in mejor[1][:4]])
        else: print('sin guía posible para', r)
    for r in FIJO:
        b_ = box(*pos[r][:4]); otros = unary_union([box(*v[:4]) for k_, v in pos.items() if k_ != r])
        print('fijo', r, 'máscara', round(b_.distance(mask), 3), 'líneas', round(b_.distance(unary_union(lineas)), 3), 'textos', round(b_.distance(unary_union([otros] + textos)), 3))
    nuevos = [box(*v[:4]) for v in pos.values()] + [LineString([g[:2], g[2:]]).buffer(LINEA / 2) for g in guias]
    tapa = unary_union([mask.buffer(C_MASK + LINEA / 2, quad_segs=6), tinta.buffer(C_SILK + LINEA / 2, quad_segs=4), unary_union(nuevos).buffer(SEP_TEXTO, join_style=2)] + m3 + vias)
    marcos = []
    for t in TRAZOS:
        g = LineString(t).difference(tapa)
        for s in getattr(g, 'geoms', [g]):
            if s.length >= 0.5: marcos += [LineString(par) for par in zip(s.coords, list(s.coords)[1:])]
    print('separadores:', len(marcos), 'tramos,', round(sum(m.length for m in marcos), 1), 'mm')
    PLAN.write_text(json.dumps(dict(marcos=[list(s.coords[0]) + list(s.coords[-1]) for s in marcos] + guias,
                                    textos=[dict(id=i['id'], t=pos[i['id']][6], s=pos[i['id']][7], caja=pos[i['id']][:4], rot=pos[i['id']][4]) for i in items if i['id'] in pos],
                                    abajo=[]), indent=0, ensure_ascii=False))


def ancla(c, s, rot):
    # La tinta se sale medio trazo del punto de ubicación; girado 90° el punto queda abajo a la derecha.
    return (c[0] + s[1] / 2 if rot == 0 else c[2] - s[1] / 2), c[1] + s[1] / 2


def placa():
    from drc_comun import correr, VARS, ABRIR
    pl = json.loads(PLAN.read_text())
    fx, fy = 'Board.XOrigin + MMsToCoord', 'Board.YOrigin + MMsToCoord'
    reg = "Board.AddPCBObject(T); PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, T.I_ObjectAddress);\n"
    cod = ''
    for m in pl['marcos']:
        cod += (f"T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default); T.Layer := eTopOverlay; T.Width := MMsToCoord({LINEA}); "
                f"T.x1 := {fx}({m[0]}); T.y1 := {fy}({m[1]}); T.x2 := {fx}({m[2]}); T.y2 := {fy}({m[3]}); " + reg)
    for t in pl['textos']:
        x, y = ancla(t['caja'], t['s'], t['rot'])
        if t['id'].startswith('L:'):
            cod += (f"T := PCBServer.PCBObjectFactory(eTextObject, eNoDimension, eCreate_Default); T.Layer := eTopOverlay; T.Text := '{t['t']}'; T.Size := MMsToCoord({t['s'][0]}); "
                    f"T.Width := MMsToCoord({t['s'][1]}); T.Rotation := {t['rot']}; T.XLocation := {fx}({x:.4f}); T.YLocation := {fy}({y:.4f}); " + reg)
        else:
            cod += (f"C := Board.GetPcbComponentByRefDes('{t['id']}'); C.NameOn := True; X := C.Name; X.Size := MMsToCoord({t['s'][0]}); X.Width := MMsToCoord({t['s'][1]}); "
                    f"X.Rotation := {t['rot']}; X.XLocation := {fx}({x:.4f}); X.YLocation := {fy}({y:.4f});\n")
    # J9 con el nombre de símbolo corregido en el esquemático (BOOMELE 2.54-1x04), para que Update PCB no vea diferencias
    cod += "C := Board.GetPcbComponentByRefDes('J9'); C.SourceLibReference := 'BOOMELE 2.54-1x04'; C.SourceCompDesignItemID := 'BOOMELE 2.54-1x04';\n"
    print(correr(f"""{VARS}    T : IDispatch;
{ABRIR}s := '';
Lista := TInterfaceList.Create;  // lo suelto en Top Overlay es de una pasada anterior (la placa original no tenía nada suelto ahí)
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eTrackObject, eTextObject)); It.AddFilter_LayerSet(MkSet(eTopOverlay)); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do begin if not X.InComponent then Lista.Add(X); X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
PCBServer.PreProcess;
try
for i := 0 to Lista.Count - 1 do Board.RemovePCBObject(Lista.Items[i]);
{cod}finally
    PCBServer.PostProcess;
end;
Board.ViewManager_FullUpdate;
ResultText := 'quitados ' + IntToStr(Lista.Count) + ', separadores {len(pl['marcos'])}, textos {len(pl['textos'])}';""", 500))
    print('en memoria, sin guardar: revisar y luego correr «guardar»')


def guardar():
    from drc_comun import correr, resumen, hora_pcb, VARS, ABRIR, RESUMEN, GUARDAR
    r = correr(f"""{VARS}{ABRIR}s := '';
Lista := TInterfaceList.Create;
It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(ePolyObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
X := It.FirstPCBObject;
while X <> nil do begin Lista.Add(X); X := It.NextPCBObject; end;
Board.BoardIterator_Destroy(It);
for i := 0 to Lista.Count - 1 do begin Poly := Lista.Items[i]; Poly.BeginModify; Poly.Rebuild; Poly.EndModify; end;
{RESUMEN}{GUARDAR}ResultText := s;""", 600)
    resumen(r, 'DRC con la serigrafía completa')
    print('guardado:', hora_pcb())


if __name__ == '__main__':
    {'volcar': volcar, 'plan': lambda: plan(sys.argv[2], sys.argv[3]), 'placa': placa, 'guardar': guardar}[sys.argv[1]]()
