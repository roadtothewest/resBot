#!/usr/bin/env python3
"""Hoja 01_Alimentacion de ELO301_G1 (documento de diseño v5, §4.2): entrada 12 V con B240A + SMAJ15A, buck AP63205
a 5 V, dos LDO TLV75533 (MCU y sensores, este con ferrita), LED de encendido y divisor de monitoreo de VIN hacia PA1.
Imprime los argumentos JSON de build_schematic. Cada extremo de cable que toca un pin sale de la geometría del
símbolo (extremo eléctrico = Location + largo), así que no puede quedar desalineado."""
from hojas_comun import (cajetin, P, PINES, R0603, REPETIDOS, cap, cable, derivacion, etiqueta, gnd, nota, parte, pos, riel,  # noqa: F401
                         salida, uniones)

C10U = cap('10uF', '25V', 'GRM188R61E106MA73D')
C22U = cap('22uF', '10V', 'GRM188R61A226ME15D')
C1U = cap('1uF', '25V', 'GRM188R61E105KA12D')
C100N = cap('100nF', '50V', 'GRM188R71H104KA93D')


# ---- Entrada 12 V: protección contra polaridad inversa y transitorios ----
parte('D1', 'B240A-13-F', 1450, 5000, 2, 'B240A', 'SMA - DIODES', 'Diodes Inc.', 'B240A-13-F')
parte('D2', 'SMAJ15A-13-F', 1900, 4750, 3, 'SMAJ15A', 'SMA - DIODES', 'Diodes Inc.', 'SMAJ15A-13-F')
for i, x in enumerate((2400, 2800, 3200), 1):
    parte(f'C{i}', 'CAP - GENERIC', x, 4700, 3, *C10U)
parte('U1', 'AP63205WU-7', 4300, 4900, 0, 'AP63205', 'TSOT-23-6 - DIODES', 'Diodes Inc.', 'AP63205WU-7')
parte('C4', 'CAP - GENERIC', 5100, 5300, 0, *C100N)
parte('L1', 'INDUCTOR - GENERIC', 5900, 5000, 0, 'SRN4018-4R7M', 'SRN4018 - BOURNS', 'Bourns', 'SRN4018-4R7M',
      {'Value': '4.7uH', 'RMS Current (Irms)': '1.9A', 'Max DC Current': '2.0A'})  # Isat 2,0 A según Bourns
for i, x in enumerate((6500, 6900, 7300), 5):
    parte(f'C{i}', 'CAP - GENERIC', x, 4700, 3, *C22U)

cable((700, 5000), P('D1', 'A'))
etiqueta(750, 5000, 'VIN_12V')
cable(P('D1', 'K'), P('U1', 'IN'))                       # riel VIN_PROT
etiqueta(1650, 5000, 'VIN_PROT')
derivacion('D2', 'K', 'A', 5000)
for c in ('C1', 'C2', 'C3'):
    derivacion(c, '1', '2', 5000)
en = P('U1', 'EN')
cable(en, (3700, en[1]), (3700, 5000))                   # EN a VIN, riser a 200 mil de la columna de pines
uniones.append({'x': 3700, 'y': 5000})
gnd(P('U1', 'GND'))
fb = P('U1', 'FB')
cable(fb, (fb[0] + 200, fb[1]))                          # FB de la versión fija va directo a 5 V
riel(fb[0] + 200, fb[1], 'V_5V')
bst = P('U1', 'BST')
cable(bst, (bst[0] + 200, bst[1]))
etiqueta(bst[0] + 100, bst[1], 'BST')
c4a, c4b = P('C4', '1'), P('C4', '2')
cable(c4a, (c4a[0] - 200, c4a[1]))
etiqueta(c4a[0] - 100, c4a[1], 'BST')
cable(P('U1', 'SW'), P('L1', '1'))                       # nodo SW
etiqueta(5400, 5000, 'SW')
cable(c4b, (c4b[0], 5000))
uniones.append({'x': c4b[0], 'y': 5000})
cable(P('L1', '2'), (7600, 5000))                        # riel V_5V
riel(7600, 5000, 'V_5V')
for c in ('C5', 'C6', 'C7'):
    derivacion(c, '1', '2', 5000)

# ---- LDO 3,3 V para el MCU + LED de encendido ----
parte('U2', 'TLV75533PDBVR', 6500, 3600, 0, 'TLV75533', 'SOT-23-5 - TI', 'Texas Instruments', 'TLV75533PDBVR')
parte('C8', 'CAP - GENERIC', 5600, 3400, 3, *C1U)
parte('C9', 'CAP - GENERIC', 7300, 3400, 3, *C1U)
parte('R3', 'RESISTOR - GENERIC', 7700, 3400, 1, '1k', 'R0603 - YAGEO', 'Yageo', 'RC0603FR-071KL', R0603)
parte('LED1', 'LED - GENERIC', 7700, 2950, 1, 'Verde', 'LED0603 - LITEON', 'Lite-On', 'LTST-C191KGKT')
riel(5300, 3700, 'V_5V', 2)
cable((5300, 3700), P('U2', 'IN'))
derivacion('C8', '1', '2', 3700)
en = P('U2', 'EN')
cable(en, (5800, en[1]), (5800, 3700))
uniones.append({'x': 5800, 'y': 3700})
gnd(P('U2', 'GND'))
cable(P('U2', 'OUT'), (8000, 3700))
riel(8000, 3700, 'V3V3_MCU')
derivacion('C9', '1', '2', 3700)
r3 = P('R3', '2')
cable(r3, (r3[0], 3700))
uniones.append({'x': r3[0], 'y': 3700})
cable(P('R3', '1'), P('LED1', 'A'))
gnd(P('LED1', 'K'))

# ---- LDO 3,3 V para sensores, con ferrita a la entrada ----
parte('U3', 'TLV75533PDBVR', 6500, 2000, 0, 'TLV75533', 'SOT-23-5 - TI', 'Texas Instruments', 'TLV75533PDBVR')
parte('FB1', 'FERRITE - GENERIC', 5100, 2100, 1, '220R@100MHz', 'L0603 - GENERIC', 'Murata', 'BLM18PG221SN1D')
parte('C10', 'CAP - GENERIC', 5600, 1800, 3, *C1U)
parte('C11', 'CAP - GENERIC', 7300, 1800, 3, *C1U)
riel(4700, 2100, 'V_5V', 2)
cable((4700, 2100), P('FB1', '1'))
cable(P('FB1', '2'), P('U3', 'IN'))
etiqueta(5300, 2100, 'V5_SENS')
derivacion('C10', '1', '2', 2100)
en = P('U3', 'EN')
cable(en, (5800, en[1]), (5800, 2100))
uniones.append({'x': 5800, 'y': 2100})
gnd(P('U3', 'GND'))
cable(P('U3', 'OUT'), (8000, 2100))
riel(8000, 2100, 'V3V3_SENS')
derivacion('C11', '1', '2', 2100)

# ---- Monitoreo de VIN: 100k / 12k + 100 nF hacia PA1 (ADC1_IN2) ----
parte('R1', 'RESISTOR - GENERIC', 2000, 2800, 1, '100k', 'R0603 - YAGEO', 'Yageo', 'RC0603FR-07100KL', R0603)
parte('R2', 'RESISTOR - GENERIC', 2000, 2000, 1, '12k', 'R0603 - YAGEO', 'Yageo', 'RC0603FR-0712KL', R0603)
parte('C12', 'CAP - GENERIC', 2400, 2100, 3, *C100N)
r1 = P('R1', '2')
cable(r1, (r1[0], 3200), (1600, 3200))
etiqueta(1700, 3200, 'VIN_PROT')
cable(P('R1', '1'), P('R2', '2'))
cable((2000, 2400), (2900, 2400))
uniones += [{'x': 2000, 'y': 2400}, {'x': 2400, 'y': 2400}]
cable(P('C12', '1'), (2400, 2400))
etiqueta(2700, 2400, 'VIN_SENSE')
gnd(P('R2', '1'))
gnd(P('C12', '2'))

nota(700, 5600, 'ENTRADA 12 V (conector de expansion): B240A serie + TVS SMAJ15A')
nota(4000, 5800, 'BUCK 12 V -> 5 V: AP63205 a 1,1 MHz, L = 4,7 uH')
nota(5100, 4100, 'LDO 3,3 V MCU (TLV75533) + LED de encendido')
nota(4700, 2500, 'LDO 3,3 V SENSORES (ferrita + TLV75533)')
nota(1000, 3600, 'MONITOREO VIN -> PA1 (ADC1_IN2): 100k / 12k + 100 nF')

cajetin(1, 'Alimentacion: entrada 12 V, buck 5 V, LDO 3,3 V')
salida()
