"""Courtyard de cada huella de ELO301_G1 (mm, ejes de Altium: x a la derecha, y hacia arriba, origen de la huella),
leído de las huellas de KiCad 10 de las que se convirtieron; las 0603 del profesor van con sus medidas."""
import sys
from pathlib import Path

sys.path.insert(0, '/mnt/sda3/vms/altium')
from kicad2altium import KFP, hijo, hijos, parse  # noqa: E402

ORIGEN_KICAD = {
    'LQFP-48 - ST': ('Package_QFP', 'LQFP-48_7x7mm_P0.5mm'),
    'TSOT-23-6 - DIODES': ('Package_TO_SOT_SMD', 'TSOT-23-6'),
    'SOT-23-5 - TI': ('Package_TO_SOT_SMD', 'SOT-23-5'),
    'ABM8 - ABRACON': ('Crystal', 'Crystal_SMD_Abracon_ABM8G-4Pin_3.2x2.5mm'),
    'LED0603 - LITEON': ('LED_SMD', 'LED_0603_1608Metric'),
    'L0603 - GENERIC': ('Inductor_SMD', 'L_0603_1608Metric'),
    'SRN4018 - BOURNS': ('Inductor_SMD', 'L_Bourns-SRN4018'),
    'SMA - DIODES': ('Diode_SMD', 'D_SMA'),
    'PTS810 - CK': ('Button_Switch_SMD', 'SW_SPST_PTS810'),
    'B4B-XH-A - JST': ('Connector_JST', 'JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical'),
    'B5B-XH-A - JST': ('Connector_JST', 'JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical'),
    'HDR 1x14 2.54 - BOOMELE': ('Connector_PinHeader_2.54mm', 'PinHeader_1x14_P2.54mm_Vertical'),
    'HDR 1x05 2.54 - BOOMELE': ('Connector_PinHeader_2.54mm', 'PinHeader_1x05_P2.54mm_Vertical'),
    'U.FL - HIROSE': ('Connector_Coaxial', 'U.FL_Hirose_U.FL-R-SMT-1_Vertical'),
    'M3 - HOLE': ('MountingHole', 'MountingHole_3.2mm_M3'),
    'LGA-14 2.5x3.0 - BOSCH': ('Package_LGA', 'Bosch_LGA-14_3x2.5mm_P0.5mm'),
    'LCC-18 9.7x10.1 - ZKW': ('RF_GPS', 'ublox_MAX'),
}
CAJA_0603 = (-1.5, 1.5, -0.8, 0.8)          # R0603 - YAGEO y C0603 - MURATA (bibliotecas del profesor)


def caja(huella):
    """(xmin, xmax, ymin, ymax) del courtyard en mm."""
    if huella not in ORIGEN_KICAD:
        return CAJA_0603
    pretty, nombre = ORIGEN_KICAD[huella]
    raiz = parse((KFP / f'{pretty}.pretty' / f'{nombre}.kicad_mod').read_text(encoding='utf-8'))
    xs, ys = [], []
    for g in raiz[1:]:
        if isinstance(g, list) and g[0].startswith('fp_') and (hijo(g, 'layer') or [None, None])[1] == 'F.CrtYd':
            if g[0] == 'fp_circle':
                c, e = hijo(g, 'center'), hijo(g, 'end')
                r = ((float(e[1]) - float(c[1])) ** 2 + (float(e[2]) - float(c[2])) ** 2) ** 0.5
                xs += [float(c[1]) - r, float(c[1]) + r]
                ys += [float(c[2]) - r, float(c[2]) + r]
            else:
                for k in ('start', 'end', 'mid'):
                    p = hijo(g, k)
                    if p:
                        xs.append(float(p[1]))
                        ys.append(float(p[2]))
                for q in hijos(hijo(g, 'pts') or ['pts'], 'xy'):
                    xs.append(float(q[1]))
                    ys.append(float(q[2]))
    return min(xs), max(xs), -max(ys), -min(ys)          # KiCad tiene y hacia abajo


if __name__ == '__main__':
    for h in list(ORIGEN_KICAD) + ['R0603 - YAGEO']:
        x0, x1, y0, y1 = caja(h)
        print(f'{h:26s} x {x0:6.2f}..{x1:6.2f}  y {y0:6.2f}..{y1:6.2f}  ({x1 - x0:.2f} x {y1 - y0:.2f})')
