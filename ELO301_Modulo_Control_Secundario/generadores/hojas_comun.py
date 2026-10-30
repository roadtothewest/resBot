"""Base común de los generadores de hojas de ELO301_G1 (argumentos de build_schematic de altium-mcp).
La geometría de los pines sale de los mismos archivos lote*_simbolos.txt con que se crearon los símbolos, así que el
extremo eléctrico de cada pin (Location + largo en su orientación) siempre coincide con la biblioteca."""
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
L = 'C:\\Users\\altium\\Documents\\Altium\\ELO301_G1\\'
LIB_PROF = {'CAP - GENERIC', 'RESISTOR - GENERIC', 'INDUCTOR - GENERIC'}   # bibliotecas genéricas del profesor
PINES = {'CAP - GENERIC': {'1': (-200, 0), '2': (100, 0)},                  # leídas con get_symbol_primitives
         'RESISTOR - GENERIC': {'1': (-200, 0), '2': (200, 0)},
         'INDUCTOR - GENERIC': {'1': (-300, 0), '2': (300, 0)}}
DIR = {'eRotate0': (1, 0), 'eRotate90': (0, 1), 'eRotate180': (-1, 0), 'eRotate270': (0, -1)}
REPETIDOS = {}   # símbolo -> números de pin cuyo nombre se repite o está vacío (el pin_map de Altium los colapsa)
for f in sorted(AQUI.glob('lote*_simbolos.txt')):
    simbolo = None
    for linea in f.read_text(encoding='utf-8').splitlines():
        c = linea.split('|')
        if c[0] == 'SYMBOL':
            simbolo, nombres = c[1], {}
            PINES[simbolo], REPETIDOS[simbolo] = {}, set()
        elif c[0] == 'PIN':
            (dx, dy), largo = DIR[c[4]], float(c[8])
            punto = (round(float(c[5]) + largo * dx), round(float(c[6]) + largo * dy))
            PINES[simbolo][c[1]] = punto                       # siempre por número
            nombres.setdefault(c[2], []).append(punto)
            nombres.setdefault('#' + c[2], []).append(c[1])
            if not c[2] or len(nombres['#' + c[2]]) > 1:
                REPETIDOS[simbolo].update(nombres['#' + c[2]])
            if c[2] and len(nombres[c[2]]) == 1:              # y por nombre cuando no se repite
                PINES[simbolo][c[2]] = punto
            elif c[2] in PINES[simbolo] and c[2] != c[1]:
                del PINES[simbolo][c[2]]

# Parámetros que muestran los símbolos genéricos del profesor (sin ellos aparece #NAME?)
def cap(valor, tension, mpn):
    return (valor, 'C0603 - MURATA', 'Murata', mpn, {'Case/Package': '0603', 'Voltage Rating (DC)': tension})


R0603 = {'Case/Package': '0603', 'Tolerance': '1%'}
partes, pos, cables, uniones, etiquetas, puertos, notas = [], {}, [], [], [], [], []


def parte(des, simbolo, x, y, o, valor, huella, fab, mpn, extra=None):
    lib = f'{simbolo}.SchLib' if simbolo in LIB_PROF else 'ELO301_G1.SchLib'
    partes.append({'designator': des, 'symbol_library': L + lib, 'symbol': simbolo,
                   'x': x, 'y': y, 'orientation': o, 'comment': valor, 'footprint': huella,
                   'parameters': {'Manufacturer': fab, 'Manufacturer Part Number': mpn, **(extra or {})}})
    pos[des] = (simbolo, x, y, o)


def P(des, pin):
    """Extremo eléctrico absoluto del pin, con la rotación de la pieza (o = 0..3, pasos de 90° antihorario)."""
    s, x, y, o = pos[des]
    px, py = PINES[s][pin]
    rx, ry = [(px, py), (-py, px), (-px, -py), (py, -px)][o]
    return x + rx, y + ry


def cable(*pts):
    cables.append([v for p in pts for v in p])


def etiqueta(x, y, texto):
    etiquetas.append({'x': x, 'y': y, 'orientation': 0, 'text': texto})


def gnd(p):  # un grid abajo y puerto de tierra (convención 4)
    cable(p, (p[0], p[1] - 100))
    puertos.append({'x': p[0], 'y': p[1] - 100, 'orientation': 3, 'style': 5, 'text': 'GND', 'show_net_name': False})


def riel(x, y, nombre, o=0):
    puertos.append({'x': x, 'y': y, 'orientation': o, 'style': 2, 'text': nombre, 'show_net_name': True})


def derivacion(des, pin_arriba, pin_abajo, y_riel):
    """Pieza en derivación: un grid de cable hasta el riel (convención 3) y su propia tierra abajo."""
    a = P(des, pin_arriba)
    cable(a, (a[0], y_riel))
    uniones.append({'x': a[0], 'y': y_riel})
    gnd(P(des, pin_abajo))


def nota(x, y, texto):
    notas.append({'x': x, 'y': y, 'text': texto})


def cajetin(n, titulo):
    """Textos del cuadro de título estándar de la hoja A de Altium (3500 x 800 mil en la esquina inferior derecha)."""
    nota(5900, 760, titulo)                   # Title
    nota(6400, 450, f'ELO301-G1-0{n}')        # Number
    nota(8400, 450, '1.0')                    # Revision
    nota(8085, 300, str(n))                   # Sheet n
    nota(8270, 300, '4')                      # of 4
    nota(8250, 205, 'Grupo 1')                # Drawn By
    nota(400, 300, 'Autores: V. Andrade, A. Mena, C. Fuentes, A. Avendano - ELO301, USM 2026-2')


def salida():
    """Autochequeo (ningún cable diagonal, toda etiqueta sobre un cable) e impresión de los argumentos JSON."""
    tramos = [(a, b) for c in cables for a, b in zip(list(zip(c[::2], c[1::2])), list(zip(c[::2], c[1::2]))[1:])]
    assert all(a[0] == b[0] or a[1] == b[1] for a, b in tramos), 'cable diagonal'
    for e in etiquetas:
        assert any(min(a[0], b[0]) <= e['x'] <= max(a[0], b[0]) and min(a[1], b[1]) <= e['y'] <= max(a[1], b[1])
                   for a, b in tramos), e
    print(json.dumps({'parts': partes, 'wires': cables, 'junctions': uniones, 'net_labels': etiquetas,
                      'power_ports': puertos, 'notes': notas}, ensure_ascii=False))
