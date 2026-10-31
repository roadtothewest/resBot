#!/usr/bin/env python3
"""Ubicación de los 68 componentes de ELO301_G1 en la placa de 70 x 50 mm (origen abajo a la izquierda, mm).
Verifica sin Altium que ningún courtyard choque con otro de la misma cara ni salga de la placa, y escribe los
argumentos de place_components (mils). Los THT (conectores) ocupan ambas caras.
Uso: colocacion.py > colocacion.json"""
import json
import sys
from pathlib import Path

from huellas import caja

AQUI = Path(__file__).resolve().parent
ANCHO, ALTO = 70.0, 50.0
THT = {'B4B-XH-A - JST', 'B5B-XH-A - JST', 'HDR 1x14 2.54 - BOOMELE', 'HDR 1x05 2.54 - BOOMELE', 'M3 - HOLE'}

# designador -> huella, desde los generadores de las hojas
sys.path.insert(0, str(AQUI.parent / 'specs'))
import hojas_comun  # noqa: E402
for g in sorted((AQUI.parent / 'specs').glob('hoja_0*.py')):
    import contextlib, io  # noqa: E401
    with contextlib.redirect_stdout(io.StringIO()):
        exec(g.read_text(encoding='utf-8'), {'__name__': 'gen'})
HUELLA = {p['designator']: p['footprint'] for p in hojas_comun.partes}

# Pads del LQFP-48 (mm desde el centro), para pegar los desacoplos a cada pin de alimentación
PAD_MCU = {}
for linea in (AQUI.parent / 'specs' / 'huellas_todas.txt').read_text().splitlines():
    c = linea.split('|')
    if c[0] == 'FOOTPRINT':
        actual = c[1]
    elif c[0] == 'PAD' and actual == 'LQFP-48 - ST':
        PAD_MCU[c[1]] = (float(c[2]) * 0.0254, float(c[3]) * 0.0254)

X = {}   # designador -> (x, y, rotación, cara)


def pon(des, x, y, rot=0, cara='top'):
    X[des] = (round(x, 3), round(y, 3), rot % 360, cara)


# ---------------- bordes ----------------
pon('J1', 18.49, 2.6, 270, 'bottom')                    # expansión 1x14 hacia la motherboard (cara inferior), pin 1 a la izquierda
pon('H1', 3.6, 3.6)
pon('H2', 66.4, 3.6)
for k, des in enumerate(('J3', 'J4', 'J5', 'J6')):      # FOC1-4, pin 1 a la izquierda
    pon(des, 3.75 + 17.5 * k, 47.0)
pon('J7', 3.2, 22.0, 90)                                # ToF, borde izquierdo
pon('J2', 67.5, 24.0)                                   # SWD, borde derecho
pon('U6', 57.0, 33.0)                                   # GNSS
pon('J8', 67.3, 31.0)                                   # U.FL al borde, junto a RF_IN

# ---------------- MCU y lo que va pegado a sus pines ----------------
MCU = (33.0, 24.0, 180)
pon('U4', *MCU)


def junto_a_pin(pin, dist=6.9, lateral=0.0):
    """Punto a `dist` mm del centro del MCU, frente al pin (girado con el MCU)."""
    px, py = PAD_MCU[pin]
    if MCU[2] == 180:
        px, py = -px, -py
    if abs(px) > abs(py):                                # pin en un costado izquierdo/derecho
        return MCU[0] + (dist if px > 0 else -dist), MCU[1] + py + lateral, 0
    return MCU[0] + px + lateral, MCU[1] + (dist if py > 0 else -dist), 90


# lado superior (VDD 24, VDDA 21, VREF+ 20 a 0,5 mm entre sí): condensadores cada 2 mm, segunda fila 1 uF y ferrita
pon('C13', 29.0, 30.9, 90)                              # VDD (24)
pon('C19', 31.0, 30.9, 90)                              # VDDA (21)
pon('C20', 33.0, 30.9, 90)                              # VREF+ (20)
pon('C18', 31.0, 34.4, 90)                              # 1 uF de VDDA
pon('FB2', 31.0, 37.75, 90)                              # ferrita de VDDA
pon('C14', *junto_a_pin('36'))                          # VDD (36), lado izquierdo
pon('C16', 26.1, 23.3, 0)                               # 4,7 uF de VDD
pon('C15', *junto_a_pin('48'))                          # VDD (48), abajo
# lado derecho: el cristal frente a PF0/PF1 (pines 5-6) y VBAT/NRST arriba y abajo de él
pon('Y1', 40.6, 23.5, 90)
pon('C22', 44.25, 22.4, 0)
pon('C23', 44.25, 24.6, 0)
pon('C17', 39.9, 19.8, 0)                               # VBAT (1)
pon('C21', 39.9, 26.6, 0)                               # NRST (7)

# ---------------- alimentación (abajo a la izquierda, junto a VIN de J1) ----------------
pon('D1', 12.0, 9.0)
pon('D2', 12.0, 13.0)
for i, des in enumerate(('C1', 'C2', 'C3')):
    pon(des, 17.5, 8.6 + 2.0 * i)
pon('U1', 22.5, 10.5)
pon('C4', 22.5, 14.2)
pon('L1', 22.5, 18.0, 180)                             # pad SW (1) a la derecha, hacia U1-5; pad de 5 V hacia C5-C7
for i, des in enumerate(('C5', 'C6', 'C7')):
    pon(des, 17.5, 15.6 + 2.0 * i)
pon('U2', 12.0, 17.5)                                   # LDO del MCU
pon('C8', 12.0, 21.0)
pon('C9', 12.0, 23.0)
pon('LED1', 12.0, 25.2)
pon('R3', 12.0, 27.2)
pon('R1', 42.5, 28.5)                                   # divisor de VIN hacia PA1 (pin 9)
pon('R2', 42.5, 30.6)
pon('C12', 46.0, 29.5, 90)
pon('U3', 46.0, 10.5)                                   # LDO de sensores
pon('FB1', 41.5, 10.5)
pon('C10', 41.5, 13.0)
pon('C11', 50.0, 10.5, 90)

# ---------------- sensores ----------------
pon('U5', 21.5, 33.5)                                   # IMU arriba a la izquierda del MCU, ejes alineados
pon('C26', 21.5, 36.3)
pon('C27', 18.2, 33.5, 90)
pon('C24', 49.0, 36.5, 90)                              # desacoplo del GNSS
pon('C25', 49.0, 33.0, 90)
pon('R9', 49.0, 29.5, 90)                               # pull-up de nRESET del GNSS
pon('L2', 63.83, 32.6, 270)                             # 47 nH VCC_RF -> RF_IN, entre U6 y J8 pegada a la línea RF
pon('R7', 9.2, 31.0)                                    # pull-ups I2C del ToF
pon('R8', 9.2, 33.0)

# ---------------- servicio ----------------
pon('SW1', 57.5, 10.0)                                  # reset
pon('SW2', 57.5, 15.5)                                  # boot
pon('R4', 52.6, 15.5, 90)                               # pull-down de BOOT0
pon('R5', 52.6, 19.6, 90)                               # LED heartbeat
pon('LED2', 54.6, 19.6, 90)

# ---------------- resistencias serie del bus de los FOC ----------------
for i, des in enumerate(('R10', 'R11', 'R12', 'R13', 'R14', 'R15')):
    pon(des, 20.0 + 3.6 * i, 40.6)


def caja_colocada(des):
    x, y, r, cara = X[des]
    x0, x1, y0, y1 = caja(HUELLA[des])
    for _ in range(int(r) // 90):                        # giro antihorario de 90°
        x0, x1, y0, y1 = -y1, -y0, x0, x1
    if cara == 'bottom':                                 # en la cara inferior Altium gira y después refleja en x
        x0, x1 = -x1, -x0
    return x + x0, x + x1, y + y0, y + y1


def chequeo(margen=0.1):
    faltan = sorted(set(HUELLA) - set(X))
    problemas = [f'sin ubicar: {faltan}'] if faltan else []
    cajas = {d: caja_colocada(d) for d in X}
    for d, (x0, x1, y0, y1) in cajas.items():
        if x0 < -0.01 or y0 < -0.01 or x1 > ANCHO + 0.01 or y1 > ALTO + 0.01:
            problemas.append(f'{d} fuera de la placa: x {x0:.2f}..{x1:.2f} y {y0:.2f}..{y1:.2f}')
    ds = sorted(cajas)
    for i, a in enumerate(ds):
        for b in ds[i + 1:]:
            ca, cb = X[a][3], X[b][3]
            mismo_lado = ca == cb or HUELLA[a] in THT or HUELLA[b] in THT
            (ax0, ax1, ay0, ay1), (bx0, bx1, by0, by1) = cajas[a], cajas[b]
            if mismo_lado and ax0 < bx1 + margen and bx0 < ax1 + margen and ay0 < by1 + margen and by0 < ay1 + margen:
                problemas.append(f'choque {a}-{b}')
    return problemas


if __name__ == '__main__':
    p = chequeo()
    print('\n'.join(p) or 'colocación: sin choques ni piezas fuera de la placa', file=sys.stderr)
    mil = 1 / 0.0254
    print(json.dumps({'placements': [{'designator': d, 'x': round(x * mil, 1), 'y': round(y * mil, 1),
                                      'rotation': r, 'layer': cara} for d, (x, y, r, cara) in sorted(X.items())]}))
    sys.exit(1 if p else 0)
