#!/usr/bin/env python3
"""Hoja 03_Sensores de ELO301_G1 (documento de diseño v5, bloque de sensores): IMU BMI270 por SPI1 con INT1, GNSS
ATGM336H-5N31 por USART2 + PPS con antena activa por U.FL (VCC_RF -> 47 nH -> RF_IN, circuito de aplicación de ZKW)
y conector JST XH de 4 pines para el ToF TFmini-S por I2C2 con pull-ups de 4,7k."""
from hojas_comun import (cajetin, P, PINES, REPETIDOS, R0603, cap, cable, derivacion, etiqueta, gnd, nota, parte,  # noqa: F401
                         pos, riel, salida, uniones)

C100N = cap('100nF', '50V', 'GRM188R71H104KA93D')
C10U = cap('10uF', '25V', 'GRM188R61E106MA73D')


def stub_izq(des, pin, red, largo=900):
    x, y = P(des, pin)
    cable((x, y), (x - largo, y))
    etiqueta(x - largo + 50, y, red)


# ---- IMU BMI270 (SPI 4 hilos). Bosch, tabla 22: ASDx/ASCx sin conectar (o a VDDIO, nunca a GND); INT2, OCSB, OSDO: DNC
parte('U5', 'BMI270', 3000, 5800, 0, 'BMI270', 'LGA-14 2.5x3.0 - BOSCH', 'Bosch Sensortec', 'BMI270')
for pin, red in (('SDO', 'SPI_IMU_MISO'), ('SDx', 'SPI_IMU_MOSI'), ('SCx', 'SPI_IMU_SCK'), ('CSB', 'SPI_IMU_CS'),
                 ('INT1', 'IMU_INT1')):
    stub_izq('U5', pin, red)
riel_imu = 6600
for pin in ('VDDIO', 'VDD'):
    x, y = P('U5', pin)
    cable((x, y), (x, riel_imu))
    uniones.append({'x': x, 'y': riel_imu})
cable((2400, riel_imu), (4800, riel_imu))
riel(2400, riel_imu, 'V3V3_SENS', 2)
parte('C26', 'CAP - GENERIC', 4200, 6300, 3, *C100N)    # VDD
parte('C27', 'CAP - GENERIC', 4500, 6300, 3, *C100N)    # VDDIO
derivacion('C26', '1', '2', riel_imu)
derivacion('C27', '1', '2', riel_imu)
gio, g = P('U5', 'GNDIO'), P('U5', 'GND')
gnd(g)
cable(gio, (gio[0], g[1] - 100), (g[0], g[1] - 100))
nota(1400, 6900, 'IMU BMI270 por SPI1 (4 hilos): ASDx, ASCx, INT2, OCSB y OSDO sin conectar (Bosch, tabla 22)')

# ---- GNSS ATGM336H-5N31: USART2 + PPS a TIM2, antena activa por U.FL ----
parte('U6', 'ATGM336H-5N31', 7000, 4300, 0, 'ATGM336H-5N31', 'LCC-18 9.7x10.1 - ZKW', 'ZKW (Hangzhou ZhongKe)',
      'ATGM336H-5N31')
stub_izq('U6', 'RXD', 'UART_GNSS_TX')                    # TX del MCU -> RXD del módulo
stub_izq('U6', 'TXD', 'UART_GNSS_RX')
onoff = P('U6', 'ON/OFF')
cable(onoff, (onoff[0] - 1200, onoff[1]))                # ON/OFF activo en bajo: fijo en alto
riel(onoff[0] - 1200, onoff[1], 'V3V3_SENS', 2)
parte('R9', 'RESISTOR - GENERIC', 6000, 3900, 0, '10k', 'R0603 - YAGEO', 'Yageo', 'RC0603FR-0710KL', R0603)
cable(P('U6', '9'), P('R9', '2'))                        # nRESET con pull-up
r9 = P('R9', '1')
cable(r9, (r9[0] - 200, r9[1]))
riel(r9[0] - 200, r9[1], 'V3V3_SENS', 2)
riel_gnss = 5400
vcc, vbat = P('U6', 'VCC'), P('U6', 'VBAT')
cable(vcc, (vcc[0], riel_gnss))
uniones.append({'x': vcc[0], 'y': riel_gnss})
cable(vbat, (vbat[0], riel_gnss), (4600, riel_gnss))     # VBAT a VCC (sin batería de respaldo)
riel(4600, riel_gnss, 'V3V3_SENS', 2)
parte('C24', 'CAP - GENERIC', 4900, 5100, 3, *C10U)
parte('C25', 'CAP - GENERIC', 5200, 5100, 3, *C100N)
derivacion('C24', '1', '2', riel_gnss)
derivacion('C25', '1', '2', riel_gnss)
gnd(P('U6', '1'))
pps = P('U6', '1PPS')
cable(pps, (pps[0] + 800, pps[1]))
etiqueta(pps[0] + 300, pps[1], 'GNSS_PPS')
parte('J8', 'U.FL-R-SMT-1(10)', 8800, 4300, 0, 'U.FL', 'U.FL - HIROSE', 'Hirose', 'U.FL-R-SMT-1(10)')
parte('L2', 'INDUCTOR - GENERIC', 8500, 4800, 3, 'LQG18HN47NJ00D', 'L0603 - GENERIC', 'Murata', 'LQG18HN47NJ00D',
      {'Value': '47nH', 'RMS Current (Irms)': '400mA', 'Max DC Current': '400mA'})
rf = P('U6', 'RF_IN')
cable(rf, P('J8', 'In'))
etiqueta(rf[0] + 300, rf[1], 'RF_IN')
cable(P('L2', '2'), (8500, rf[1]))
uniones.append({'x': 8500, 'y': rf[1]})
vrf = P('U6', 'VCC_RF')
cable(vrf, (vrf[0], 5200), (8500, 5200), P('L2', '1'))
gnd(P('J8', 'Ext'))
nota(4600, 5800, 'GNSS ATGM336H-5N31 (USART2 + PPS a TIM2). Antena activa por U.FL, linea de 50 ohm')
nota(7300, 5500, 'VCC_RF -> L2 47 nH -> RF_IN (aplicacion ZKW)')

# ---- ToF TFmini-S: JST XH 4 pines (5 V, SDA, SCL, GND) por I2C2, pull-ups de 4,7k a 3,3 V ----
parte('J7', 'CONN - 1x04', 2500, 2500, 0, 'B4B-XH-A', 'B4B-XH-A - JST', 'JST', 'B4B-XH-A(LF)(SN)')
p1, p2, p3, p4 = (P('J7', str(n)) for n in (1, 2, 3, 4))
cable(p1, (p1[0] - 200, p1[1]), (p1[0] - 200, p1[1] + 200))
riel(p1[0] - 200, p1[1] + 200, 'V_5V', 1)
cable(p2, (1100, p2[1]))
etiqueta(1150, p2[1], 'I2C_TOF_SDA')
cable(p3, (1100, p3[1]))
etiqueta(1150, p3[1], 'I2C_TOF_SCL')
cable(p4, (p4[0] - 200, p4[1]))
gnd((p4[0] - 200, p4[1]))
for des, x, red in (('R7', 3300, 'I2C_TOF_SDA'), ('R8', 4300, 'I2C_TOF_SCL')):
    parte(des, 'RESISTOR - GENERIC', x, 2900, 1, '4.7k', 'R0603 - YAGEO', 'Yageo', 'RC0603FR-074K7L', R0603)
    abajo, arriba = P(des, '1'), P(des, '2')
    cable(arriba, (arriba[0], 3200))
    cable(abajo, (abajo[0], 2400), (abajo[0] + 600, 2400))
    etiqueta(abajo[0] + 50, 2400, red)
cable((3000, 3200), (4300, 3200))
uniones.append({'x': 3300, 'y': 3200})
riel(3000, 3200, 'V3V3_MCU', 2)
nota(1100, 3500, 'ToF TFmini-S (externo) por I2C2: JST XH 4P, adaptador a GH en el arnes; pull-ups R7/R8 4,7k')

cajetin(3, 'Sensores: IMU BMI270, GNSS ATGM336H y ToF')
salida()
