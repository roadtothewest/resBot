#!/usr/bin/env python3
"""Hoja 04_Conectores de ELO301_G1 (documento de diseño v5): conector de expansión 1x14 hacia la motherboard (Tabla 5),
header SWD 1x5 para ST-LINK, cuatro JST XH de 5 pines para los FOC en un bus SPI2 compartido con resistencias serie
de 33 ohm en SCK, MOSI y cada CS, y dos agujeros M3. Las tierras de los conectores se nombran con la etiqueta GND."""
from hojas_comun import (cajetin, P, PINES, REPETIDOS, R0603, cable, etiqueta, nota, parte, pos, salida)  # noqa: F401

def stub(des, pin, red, largo=1000):
    x, y = P(des, pin)
    cable((x, y), (x - largo, y))
    etiqueta(x - largo + 50, y, red)


# ---- J1: conector de expansión (header 2,54 mm 1x14 cortado de BOOMELE 1x40), Tabla 5 ----
parte('J1', 'CONN - 1x14', 2500, 5000, 0, 'HDR 1x14', 'HDR 1x14 2.54 - BOOMELE', 'BOOMELE', '2.54-1*40P (1x14)')
for pin, red in enumerate(('VIN_12V', 'VIN_12V', 'GND', 'GND', 'SPI_SUP_SCK', 'SPI_SUP_MOSI', 'SPI_SUP_MISO',
                           'SPI_SUP_NSS', 'SUP_IRQ', 'GND', 'SWDIO', 'SWCLK', 'NRST', 'GND'), 1):
    stub('J1', str(pin), red)
nota(1300, 6150, 'J1 EXPANSION (motherboard / Radxa Zero 3W)')
nota(1300, 5950, '12 V, SPI3 esclavo + IRQ, SWD (Tabla 5)')

# ---- J2: SWD para ST-LINK (orden de CN4 en placas Nucleo, sin SWO) ----
parte('J2', 'CONN - 1x05', 2500, 2800, 0, 'HDR 1x05', 'HDR 1x05 2.54 - BOOMELE', 'BOOMELE', '2.54-1*40P (1x5)')
for pin, red in enumerate(('V3V3_MCU', 'SWCLK', 'GND', 'SWDIO', 'NRST'), 1):
    stub('J2', str(pin), red)
nota(1300, 3300, 'J2 SWD (ST-LINK): 1 VDD, 2 SWCLK, 3 GND, 4 SWDIO, 5 NRST')

# ---- Bus SPI2 a los FOC: 33 ohm en serie en SCK, MOSI y cada CS (lado MCU -> lado conectores) ----
for i, (des, y, mcu, bus) in enumerate((('R10', 6400, 'SPI_FOC_SCK', 'FOC_BUS_SCK'), ('R11', 5900, 'SPI_FOC_MOSI', 'FOC_BUS_MOSI'),
                                        ('R12', 5400, 'FOC_CS1', 'FOC1_CS'), ('R13', 4900, 'FOC_CS2', 'FOC2_CS'),
                                        ('R14', 4400, 'FOC_CS3', 'FOC3_CS'), ('R15', 3900, 'FOC_CS4', 'FOC4_CS'))):
    parte(des, 'RESISTOR - GENERIC', 5000, y, 0, '33R', 'R0603 - YAGEO', 'Yageo', 'RC0603FR-0733RL', R0603)
    a, b = P(des, '1'), P(des, '2')
    cable(a, (a[0] - 800, a[1]))
    etiqueta(a[0] - 750, a[1], mcu)
    cable(b, (b[0] + 800, b[1]))
    etiqueta(b[0] + 50, b[1], bus)
nota(4000, 6900, 'BUS SPI2 A LOS FOC: R serie 33 ohm en SCK, MOSI y CS (cable a 4 destinos); MISO directo')

# ---- J3-J6: JST XH 5 pines por FOC (SCK, MOSI, MISO, CS, GND) ----
for k, (des, y) in enumerate((('J3', 6300), ('J4', 5500), ('J5', 4700), ('J6', 3900)), 1):
    parte(des, 'CONN - 1x05', 8500, y, 0, f'FOC{k}', 'B5B-XH-A - JST', 'JST', 'B5B-XH-A(LF)(SN)')
    for pin, red in enumerate(('FOC_BUS_SCK', 'FOC_BUS_MOSI', 'SPI_FOC_MISO', f'FOC{k}_CS', 'GND'), 1):
        stub(des, str(pin), red)
nota(6800, 7100, 'J3-J6: FOC 1-4 (JST XH 5P); PA11/PA12 libres para FDCAN1')

# ---- Montaje: dos M3 con separadores (el conector no soporta la vibracion) ----
parte('H1', 'MOUNTING HOLE - M3', 7600, 2500, 0, 'M3', 'M3 - HOLE', '-', 'M3')
parte('H2', 'MOUNTING HOLE - M3', 8400, 2500, 0, 'M3', 'M3 - HOLE', '-', 'M3')
nota(7000, 2900, 'H1, H2: perforaciones M3 con separadores')

cajetin(4, 'Conectores: expansion, SWD y FOC')
salida()
