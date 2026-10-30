#!/usr/bin/env python3
"""Hoja 02_MCU de ELO301_G1: STM32G431CBT6 con desacoplos, VDDA filtrada, cristal HSE de 25 MHz, NRST, BOOT0,
LED de heartbeat y una etiqueta de red por cada E/S asignada en la Tabla 9 del documento de diseño (v5)."""
from hojas_comun import (cajetin, P, PINES, R0603, REPETIDOS, cap, cable, derivacion, etiqueta, gnd, nota, parte, pos, riel,  # noqa: F401
                         salida, uniones)

C100N = cap('100nF', '50V', 'GRM188R71H104KA93D')
C1U = cap('1uF', '25V', 'GRM188R61E105KA12D')
C4U7 = cap('4.7uF', '10V', 'GRM188R61A475KE15D')
C27P = cap('27pF C0G', '50V', 'GRM1885C1H270JA01D')
PTS810 = ('PTS810', 'PTS810 - CK', 'C&K', 'PTS810 SJM 250 SMTR LFS')

# ---- MCU y sus E/S (Tabla 9) ----
parte('U4', 'STM32G431CBT6', 5000, 4400, 0, 'STM32G431CBT6', 'LQFP-48 - ST', 'STMicroelectronics', 'STM32G431CBT6')
IZQ = {'PG10': 'NRST', 'PF0': 'OSC_IN', 'PF1': 'OSC_OUT', 'PB0': 'IMU_INT1', 'PB1': 'FOC_CS1', 'PB2': 'FOC_CS2',
       'PB3': 'SPI_SUP_SCK', 'PB4': 'SPI_SUP_MISO', 'PB5': 'SPI_SUP_MOSI', 'PB6': 'LED_HB', 'PB8': 'BOOT0',
       'PB10': 'FOC_CS3', 'PB11': 'FOC_CS4', 'PB13': 'SPI_FOC_SCK', 'PB14': 'SPI_FOC_MISO', 'PB15': 'SPI_FOC_MOSI',
       'VREF+': 'VDDA'}
DER = {'PA0': 'GNSS_PPS', 'PA1': 'VIN_SENSE', 'PA2': 'UART_GNSS_TX', 'PA3': 'UART_GNSS_RX', 'PA4': 'SPI_IMU_CS',
       'PA5': 'SPI_IMU_SCK', 'PA6': 'SPI_IMU_MISO', 'PA7': 'SPI_IMU_MOSI', 'PA8': 'I2C_TOF_SDA', 'PA9': 'I2C_TOF_SCL',
       'PA10': 'SUP_IRQ', 'PA13': 'SWDIO', 'PA14': 'SWCLK', 'PA15': 'SPI_SUP_NSS'}
for pin, red in IZQ.items():
    x, y = P('U4', pin)
    cable((x, y), (x - 1000, y))
    etiqueta(x - 950, y, red)
for pin, red in DER.items():
    x, y = P('U4', pin)
    cable((x, y), (x + 1000, y))
    etiqueta(x + 300, y, red)      # deja libre el número de pin

# ---- VDD y VBAT a V3V3_MCU: 3 x 100 nF + 4,7 uF en VDD y 100 nF en VBAT ----
riel_y = 6300
vbat = P('U4', '1')
for i, pin in enumerate(('1', '24', '36', '48')):           # VBAT y los tres VDD, por número de pin
    x, y = P('U4', pin)
    cable((x, y), (x, riel_y))
    if pin != '48':
        uniones.append({'x': x, 'y': riel_y})
cable(P('U4', '48')[:1] + (riel_y,), (1500, riel_y))
riel(1500, riel_y, 'V3V3_MCU', 2)
for des, x, valor in (('C17', 1800, C100N), ('C13', 2100, C100N), ('C14', 2400, C100N), ('C15', 2700, C100N),
                      ('C16', 3000, C4U7)):
    parte(des, 'CAP - GENERIC', x, 6000, 3, *valor)
    derivacion(des, '1', '2', riel_y)
nota(1500, 6600, 'DESACOPLO: C13-C15 100 nF (uno por VDD), C16 4,7 uF, C17 100 nF en VBAT')

# ---- VDDA y VREF+: ferrita desde V3V3_MCU + 1 uF + 2 x 100 nF ----
vdda = P('U4', 'VDDA')
cable(vdda, (vdda[0], 6700), (6300, 6700))
etiqueta(5250, 6700, 'VDDA')
parte('FB2', 'FERRITE - GENERIC', 6400, 6700, 1, '220R@100MHz', 'L0603 - GENERIC', 'Murata', 'BLM18PG221SN1D')
cable(P('FB2', '2'), (6900, 6700))
riel(6900, 6700, 'V3V3_MCU')
for des, x, valor in (('C18', 5500, C1U), ('C19', 5800, C100N), ('C20', 6100, C100N)):
    parte(des, 'CAP - GENERIC', x, 6400, 3, *valor)
    derivacion(des, '1', '2', 6700)
nota(5200, 7000, 'VDDA / VREF+: ferrita + 1 uF + 100 nF (C20 junto al pin VREF+)')

# ---- VSS y VSSA a GND ----
vss, vssa = P('U4', '23'), P('U4', 'VSSA')   # VSS (23, con 35 y 47 apilados)
gnd(vss)
cable(vssa, (vssa[0], vss[1] - 100), (vss[0], vss[1] - 100))

# ---- Cristal HSE 25 MHz (ABM8) con 2 x 27 pF C0G ----
parte('Y1', 'ABM8-25.000MHZ-B2-T', 1700, 4700, 0, '25MHz', 'ABM8 - ABRACON', 'Abracon', 'ABM8-25.000MHZ-B2-T')
parte('C22', 'CAP - GENERIC', 1100, 4400, 3, *C27P)
parte('C23', 'CAP - GENERIC', 2300, 4400, 3, *C27P)
cable(P('Y1', '1'), (700, 4700))
etiqueta(750, 4700, 'OSC_IN')
cable(P('Y1', '3'), (3000, 4700))
etiqueta(2450, 4700, 'OSC_OUT')
derivacion('C22', '1', '2', 4700)
derivacion('C23', '1', '2', 4700)
gnd(P('Y1', '2'))
nota(700, 5000, 'HSE 25 MHz (ABM8) + 2 x 27 pF C0G, pistas cortas con anillo de GND')

# ---- NRST: 100 nF + pulsador SW1 a GND ----
parte('C21', 'CAP - GENERIC', 1300, 3200, 3, *C100N)
parte('SW1', 'PTS810 SJM 250 SMTR LFS', 2000, 3200, 1, *PTS810)
cable((700, 3500), (2000, 3500), P('SW1', '2'))
etiqueta(750, 3500, 'NRST')
derivacion('C21', '1', '2', 3500)
gnd(P('SW1', '1'))
nota(700, 3700, 'RESET: 100 nF + pulsador SW1 (PTS810)')

# ---- BOOT0 (PB8): pull-down 10k + pulsador SW2 a 3,3 V ----
parte('R4', 'RESISTOR - GENERIC', 1300, 1700, 1, '10k', 'R0603 - YAGEO', 'Yageo', 'RC0603FR-0710KL', R0603)
parte('SW2', 'PTS810 SJM 250 SMTR LFS', 2500, 2200, 1, *PTS810)
cable((700, 2000), P('SW2', '1'))
etiqueta(750, 2000, 'BOOT0')
derivacion('R4', '2', '1', 2000)
sw2 = P('SW2', '2')
cable(sw2, (sw2[0], sw2[1] + 100))
riel(sw2[0], sw2[1] + 100, 'V3V3_MCU', 1)
nota(2900, 1750, 'BOOT0 (PB8): pull-down 10k + pulsador SW2 a 3,3 V')

# ---- LED de heartbeat (PB6) ----
parte('R5', 'RESISTOR - GENERIC', 6700, 3500, 0, '1k', 'R0603 - YAGEO', 'Yageo', 'RC0603FR-071KL', R0603)
parte('LED2', 'LED - GENERIC', 7000, 3250, 1, 'Rojo', 'LED0603 - LITEON', 'Lite-On', 'LTST-C191KRKT')
cable((6000, 3500), P('R5', '1'))
etiqueta(6050, 3500, 'LED_HB')
cable(P('R5', '2'), (7000, 3500), P('LED2', 'A'))
gnd(P('LED2', 'K'))
nota(6000, 3800, 'LED heartbeat (PB6)')
nota(5800, 2400, 'Libres: PC13-PC15, PB7, PB9, PB12, PA11, PA12 (FDCAN1 si los FOC migran a CAN)')

cajetin(2, 'MCU STM32G431CBT6')
salida()
