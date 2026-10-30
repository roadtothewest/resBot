# ELO301 — Módulo de control secundario (Grupo 1)

Esquemático en Altium Designer 26 del módulo de control secundario del resBot: la placa de expansión que va sobre la
motherboard junto a la Radxa Zero 3W. Implementa el [Documento de Diseño v5](docs/Documento_de_Diseno_ELO301_Grupo1_v5.pdf).

## Estado (30/10/2026)

| Ítem | Estado |
|---|---|
| Esquemático | 4 hojas, 68 componentes |
| ERC | **0 errores**, 3 advertencias esperadas* |
| Componentes | Cada uno con huella, valor, fabricante y número de parte (el BOM sale directo de Altium) |
| PCB (`ELO301_G1.PcbDoc`) | Vacío, es el siguiente paso |

\* GNSS_PPS y UART_GNSS_RX llevan salidas del GNSS a pines E/S del MCU, y el nRESET del GNSS solo tiene su pull-up.

| Hoja | Contenido |
|---|---|
| [01 Alimentación](esquematicos/01_Alimentacion.png) | 12 V con B240A en serie y TVS SMAJ15A, buck AP63205 a 5 V, LDO TLV75533 para MCU y para sensores (con ferrita), LED de encendido, divisor 100k/12k + 100 nF hacia PA1 |
| [02 MCU](esquematicos/02_MCU.png) | STM32G431CBT6 con los 29 pines de la Tabla 9, desacoplos, VDDA con ferrita, cristal de 25 MHz, NRST y BOOT0 con pulsadores, LED heartbeat en PB6 |
| [03 Sensores](esquematicos/03_Sensores.png) | IMU BMI270 por SPI1, GNSS ATGM336H por USART2 + PPS con antena activa por U.FL, conector JST del ToF por I2C2 con pull-ups de 4,7k |
| [04 Conectores](esquematicos/04_Conectores.png) | Expansión 1x14 (Tabla 5), SWD 1x5, 4 JST XH 5P para los FOC con 33 Ω en serie, 2 agujeros M3 |

## Abrir el proyecto

En Altium Designer, abrir `altium/ELO301_G1.PrjPcb`. Las bibliotecas van en la misma carpeta y se cargan solas.

- **`CAP/RESISTOR/INDUCTOR/DIODE - GENERIC.SchLib`, `C0603 - MURATA.PcbLib` y `R0603 - YAGEO.PcbLib`:** bibliotecas
  RCL del profesor (github.com/linitrofe/ELO301.Hw.Altium).
- **`ELO301_G1.SchLib` / `ELO301_G1.PcbLib`:** 16 símbolos y 17 huellas convertidos desde las bibliotecas oficiales de
  KiCad 10 (huellas IPC). Siguen las capas del profesor: Mech 13 para ensamble, Mech 15 para courtyard y Mech 29 para
  el designador.
  - La BMI270 se verificó contra la hoja de datos de Bosch (tabla 22).
  - El ATGM336H se verificó contra el manual de ZKW: usa la huella del u-blox MAX y pines propios.

## Decisiones para revisar en grupo

El documento de diseño no define estos puntos:

1. **SWD 1x5:** orden VDD, SWCLK, GND, SWDIO, NRST, igual que el CN4 de las Nucleo.
2. **Resistencias de 33 Ω del bus de los FOC:** una en SCK y otra en MOSI (compartidas), más una por cada CS (6 en total).
3. **Pull-ups del I2C del ToF:** a V3V3_MCU.
4. **GNSS:** ON/OFF fijo en alto; VBAT a VCC (sin batería de respaldo, no hay arranque en caliente); pull-up de 10k en nRESET.
5. **BMI270:** ASDx, ASCx, INT2, OCSB y OSDO sin conectar, como permite Bosch.
6. **Desacoplos:**
   - VDD: 3 x 100 nF + 4,7 µF.
   - VBAT: 100 nF.
   - VDDA: ferrita + 1 µF + 2 x 100 nF.
   - LDO: 1 µF en la entrada y en la salida.
   - GNSS: 10 µF + 100 nF.
7. **Inductor del buck (SRN4018-4R7M):** según Bourns, Irms = 1,9 A e Isat = 2,0 A. El documento dice «1,9 A de
   saturación».
8. **Protección de entrada:** el TVS va después del diodo serie, y el divisor de monitoreo mide la tensión ya protegida
   (VIN_PROT).

## Generadores

`generadores/` contiene lo que se usó para generar el esquemático, con altium-mcp desde Claude Code y Altium corriendo
en una VM:

- `lote*_*.txt` y `fix_*.txt`: especificaciones de símbolos y huellas.
- `hoja_0N_*.py`: un generador por hoja.
- `herramientas/`: el conversor KiCad → Altium y los scripts de construcción y verificación pin a pin.

**Ojo:** si una hoja se edita a mano en Altium, no hay que volver a correr su generador, porque se perderían esos
cambios.

## Siguientes pasos

1. *Design » Update PCB Document* para traer los 68 componentes al PCB.
2. Contorno de la placa, agujeros M3 y stackup.
3. Ubicación por bloques. Cristal junto a OSC_IN/OUT con anillo de GND; buck con lazo de entrada corto; U.FL con
   línea de 50 Ω.
4. Ruteo, DRC y salidas de fabricación (Gerber, BOM, pick and place).
5. Exportar el esquemático a PDF.
