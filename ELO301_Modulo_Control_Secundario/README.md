# ELO301 — Módulo de control secundario (Grupo 1)

Esquemático en Altium Designer 26 del módulo de control secundario del resBot: la placa de expansión que va sobre la
motherboard junto a la Radxa Zero 3W. Implementa el [Documento de Diseño v5](docs/Documento_de_Diseno_ELO301_Grupo1_v5.pdf).

## Estado (30/10/2026)

| Ítem | Estado |
|---|---|
| Esquemático | 4 hojas, 68 componentes |
| ERC | **0 errores**, 3 advertencias esperadas* |
| Componentes | Cada uno con huella, valor, fabricante y número de parte (el BOM sale directo de Altium) |
| PCB (`ELO301_G1.PcbDoc`) | 4 capas, 70 x 50 mm, 68 componentes colocados, ruteo completo, planos y pours de GND. **DRC: 0 violaciones** |
| Salidas de fabricación | Pendientes (Gerber, taladros, pick and place, BOM) |

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

## PCB

![PCB](esquematicos/05_PCB.png)

- **Placa:** 70 x 50 mm, 4 capas (Top / GND plano / Señal-Potencia / Bottom), 2 agujeros M3. Apilado tipo JLC04161H-7628
  (prepreg 0,21 mm, núcleo 1,065 mm, prepreg 0,21 mm; cobre 35 µm fuera, 15 µm dentro; ≈ 1,6 mm).
- **Colocación:** `generadores/pcb/colocacion.py` define las 68 posiciones y verifica sin Altium que no haya choques de
  courtyard. La expansión J1 va en la cara inferior hacia la motherboard; el cristal junto a PF0/PF1; los desacoplos
  pegados a cada pin de alimentación del MCU.
- **Reglas:** clases de red (potencia, RF, osciladores, señal), anchos por clase (RF_IN 0,35 mm, SW 0,6 mm, 3V3 0,3 mm),
  holgura 0,15 mm, máscara y serigrafía según JLCPCB.
- **Ruteo:** Situs con las pre-rutas bloqueadas, 49 vías de GND al plano (`fanout_gnd.py`, tapadas) y un A* propio
  (`ruteo_astar.py`) para las conexiones que Situs deja sin cerrar. Pours de GND en Top y Bottom.
  Resultado: 682 pistas, 125 vías, todas con máscara encima.
- **Nodos críticos** (rehechos en Top, sin vías): SW 6,0 mm, BST 2,7 mm, OSC_IN 7,4 mm, OSC_OUT 6,4 mm,
  RF_IN 5,0 mm a 0,35 mm (≈ 50 Ω sobre el prepreg de 0,21 mm) con un stub de 0,4 mm hacia L2. L1 se giró 180° para
  que su pad SW mire a U1/C4, y L2 (47 nH, VCC_RF) quedó pegada a la línea de RF.
- **Pads THT** con pila explícita (arriba / medio / abajo): en modo simple el DRC no ve el cobre de las capas internas.
- **Designadores:** 60 visibles y el resto ocultos porque no caben sin chocar con serigrafía o pads.

### Para revisar antes de mandar a fabricar

1. Faltan vías de costura de GND más allá del fanout.
2. Confirmar los 50 Ω de RF_IN con la calculadora de impedancia de la fábrica.
3. Revisar los Gerber y el taladro con el visor de la fábrica (JLCPCB/PCBWay) antes de pedir.
4. El PDF del esquemático (`Documentacion.OutJob`) no se pudo regenerar: Altium se colgó al publicarlo.
5. El BOM no trae números de parte de proveedor (LCSC): se arma solo con valor y huella.

### Salidas de fabricación (`fabricacion/`)

Generadas con `altium/Fabricacion.OutJob` desde la placa con DRC 0:
- `ELO301_G1_Gerber_JLCPCB.zip`: 11 capas Gerber (cobre Top/Mid/GND/Bottom, máscara, serigrafía, pasta, contorno 70 x 50 mm)
  más el taladro `NC Drill/ELO301_G1.TXT` (4 diámetros: 0,3 / 0,95 / 1,0 mm chapados y 3,2 mm de los agujeros M3).
- `Pick Place/` (68 piezas, mil) y `BOM_ELO301_G1.csv` (35 líneas, agrupado por valor y huella).

Los nodos críticos se rehacen con `criticas_preparar.py` (respaldo, giro de L1, borra el cobre viejo) →
`ruteo_astar.py` (solo Top) → `aplicar_rutas.py` → `fix_netl2.py`; `volcar.py` exporta la geometría para medir.

El flujo que recrea la placa desde cero está en `generadores/pcb/` (`rehacer1.py` → `situs.py` → `fanout_altium.py` →
`aplicar_rutas.py` → `post6.py` → `designadores2.py`). Necesita la VM de Altium y `generadores/herramientas/` (`boton.*`,
`teclas.py`, `qga.py`, `mcpc.py`). `huellas_todas.txt` es la especificación de las 17 huellas ya con los THT corregidos.

## Generadores

`generadores/` contiene lo que se usó para generar el esquemático, con altium-mcp desde Claude Code y Altium corriendo
en una VM:

- `lote*_*.txt` y `fix_*.txt`: especificaciones de símbolos y huellas.
- `hoja_0N_*.py`: un generador por hoja.
- `herramientas/`: el conversor KiCad → Altium y los scripts de construcción y verificación pin a pin.

**Ojo:** si una hoja se edita a mano en Altium, no hay que volver a correr su generador, porque se perderían esos
cambios.

## Siguientes pasos

1. Corregir los puntos de revisión del PCB (arriba).
2. Salidas de fabricación: Gerber, taladros NC, pick and place y BOM.
3. Exportar el esquemático a PDF.
