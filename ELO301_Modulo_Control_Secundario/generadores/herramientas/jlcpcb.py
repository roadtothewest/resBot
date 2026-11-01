#!/usr/bin/env python3
"""Arma y verifica el paquete para JLCPCB desde las salidas de Fabricacion.OutJob (Altium).

Uso: python3 jlcpcb.py <carpeta Fabricacion de Altium> <carpeta destino>

- El plano GND (.GP1) sale negativo de Altium y JLCPCB no procesa bien los Gerber negativos: se pasa a positivo (cobre en
  toda la placa y el contenido original en polaridad clara) y se nombra .G2L. La capa Señal-Potencia (.G1) pasa a .G3L y el
  contorno (.GM) a .GKO, los nombres que JLCPCB documenta para 4 capas.
- Verifica que el contorno parta en (0,0) igual que el taladro, que cada agujero metalizado tenga su pad en Top y Bottom y
  su antipad o alivio en el plano, y que las capas no se repitan entre sí (el OutJob viejo las mezclaba).
- Escribe el CPL (Designator, Mid X, Mid Y, Layer, Rotation) desde el Pick and Place en CSV y mm.
"""
import csv, glob, os, re, sys, zipfile

BASE = 'ELO301_G1'
NOMBRES = {'GTL': 'GTL', 'GTS': 'GTS', 'GTO': 'GTO', 'GTP': 'GTP', 'GP1': 'G2L', 'G1': 'G3L', 'GBL': 'GBL', 'GBS': 'GBS', 'GBO': 'GBO', 'GBP': 'GBP', 'GM': 'GKO'}


def comandos(texto):
    """(x, y, código D, apertura activa, dentro de una región) de cada operación."""
    esc = 10 ** int(re.search(r'%FSLAX\d(\d)', texto).group(1))
    ap, x, y, ops, reg = None, 0, 0, [], False
    for c in texto.split('*'):
        c = c.strip().lstrip('%').strip()
        if c in ('G36', 'G37'):
            reg = c == 'G36'
            continue
        m = re.fullmatch(r'(?:G54)?D(\d+)', c)
        if m and int(m.group(1)) >= 10:
            ap = int(m.group(1))
            continue
        m = re.fullmatch(r'(?:G0?[123])?(?:X(-?\d+))?(?:Y(-?\d+))?(?:I-?\d+)?(?:J-?\d+)?D0?([123])', c)
        if m:
            x = int(m.group(1)) / esc if m.group(1) else x
            y = int(m.group(2)) / esc if m.group(2) else y
            ops.append((x, y, int(m.group(3)), ap, reg))
    return ops


def taladro(texto):
    """Agujeros (x, y, diámetro, metalizado) de un Excellon de Altium (formato 4:4 con ceros a la izquierda o decimal)."""
    herr, chapado, act, x, y, hs = {}, True, None, 0.0, 0.0, []
    leer = lambda s: float(s) if '.' in s else (-1 if s[0] == '-' else 1) * int(s.lstrip('-').ljust(8, '0')) / 1e4
    for l in texto.splitlines():
        if l.startswith(';TYPE='): chapado = l.strip() == ';TYPE=PLATED'
        m = re.match(r'T(\d+)F\d+S\d+C([\d.]+)', l)
        if m: herr[int(m.group(1))] = (float(m.group(2)), chapado); continue
        m = re.fullmatch(r'T(\d+)', l.strip())
        if m: act = herr.get(int(m.group(1))); continue
        m = re.fullmatch(r'(?:X(-?[\d.]+))?(?:Y(-?[\d.]+))?', l.strip())
        if m and l.strip() and act:
            x = leer(m.group(1)) if m.group(1) else x
            y = leer(m.group(2)) if m.group(2) else y
            hs.append((x, y) + act)
    return hs


def positivo(texto, x1, y1):
    """Gerber negativo -> positivo: región de cobre del tamaño de la placa y luego todo lo original con polaridad invertida."""
    esc = 10 ** int(re.search(r'%FSLAX\d(\d)', texto).group(1))
    X, Y = round(x1 * esc), round(y1 * esc)
    caja = f'%LPD*%\nG36*\nX0Y0D02*\nX{X}Y0D01*\nX{X}Y{Y}D01*\nX0Y{Y}D01*\nX0Y0D01*\nG37*\n%LPC*%\n'
    i = re.search(r'^(?:G54)?D(?:[1-9]\d+)\*|^G36\*|^[XY]-?\d', texto, re.M).start()
    cuerpo = texto[i:].replace('%LPD*%', '%LP_*%').replace('%LPC*%', '%LPD*%').replace('%LP_*%', '%LPC*%')
    return texto[:i].replace('FilePolarity,Negative', 'FilePolarity,Positive') + caja + cuerpo


def main(origen, destino):
    g = {e: open(os.path.join(origen, 'Gerber', f'{BASE}.{e}')).read() for e in NOMBRES}
    txt = open(glob.glob(os.path.join(origen, 'NC Drill', '*.TXT'))[0]).read()
    fallas = []
    cont = [o[:2] for o in comandos(g['GM'])]
    x0, y0, x1, y1 = min(p[0] for p in cont), min(p[1] for p in cont), max(p[0] for p in cont), max(p[1] for p in cont)
    if abs(x0) > 0.01 or abs(y0) > 0.01: fallas.append(f'el contorno no parte en (0,0): ({x0}, {y0}); revisar CentrePlots/OriginPosition del OutJob')
    if 'FilePolarity,Negative' not in g['GP1']: fallas.append('el plano no salió negativo (PlotPositivePlaneLayers debe ser False)')
    hs = taladro(txt)
    for e in ('GTL', 'GBL', 'GP1'):
        p = [o[:2] for o in comandos(g[e]) if o[2] == 3]
        sin = [h for h in hs if (h[3] or e == 'GP1') and not any(abs(h[0] - q[0]) < 0.01 and abs(h[1] - q[1]) < 0.01 for q in p)]
        if sin: fallas.append(f'{len(sin)} agujeros sin pad/antipad en {e}, p. ej. {sin[:3]}')
    lineas = {e: {(round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)) for a, b in zip(comandos(g[e]), comandos(g[e])[1:]) if b[2] == 1 and not b[4] and a[:2] != b[:2]} for e in ('GTL', 'G1', 'GBL', 'GTO', 'GBO')}
    for a in lineas:
        for b in lineas:
            if a < b and len(lineas[a] & lineas[b]) > 5: fallas.append(f'{a} y {b} comparten {len(lineas[a] & lineas[b])} trazos: capas mezcladas')
    if fallas:
        sys.exit('NO apto para fabricar:\n- ' + '\n- '.join(fallas))
    os.makedirs(destino, exist_ok=True)
    g['GP1'] = positivo(g['GP1'], x1, y1)
    zp = os.path.join(destino, f'{BASE}_Gerber_JLCPCB.zip')
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for e, n in NOMBRES.items(): z.writestr(f'{BASE}.{n}', g[e])
        z.writestr(f'{BASE}.TXT', txt)
    filas = list(csv.reader(open(glob.glob(os.path.join(origen, 'Pick Place', '*.csv'))[0], encoding='latin-1')))
    i = next(k for k, f in enumerate(filas) if f and f[0] == 'Designator')
    col = {n: filas[i].index(n) for n in ('Designator', 'Layer', 'Center-X(mm)', 'Center-Y(mm)', 'Rotation')}
    cpl = [[f[col['Designator']], f[col['Center-X(mm)']] + 'mm', f[col['Center-Y(mm)']] + 'mm', 'Bottom' if 'Bottom' in f[col['Layer']] else 'Top', f[col['Rotation']]]
           for f in filas[i + 1:] if f and not f[0].startswith('H')]
    with open(os.path.join(destino, f'CPL_{BASE}_JLCPCB.csv'), 'w', newline='') as fo:
        csv.writer(fo).writerows([['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation']] + cpl)
    print(f'OK: contorno {x1:.2f} x {y1:.2f} mm en (0,0); {len(hs)} agujeros con pad y antipad/alivio; capas sin mezclar; plano en positivo.')
    print(f'{zp} ({len(NOMBRES) + 1} archivos) y CPL con {len(cpl)} piezas.')


if __name__ == '__main__':
    main(*sys.argv[1:3])
