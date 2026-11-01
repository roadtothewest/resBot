# ELO301 — Módulo de control secundario (Grupo 1)

Esquemático y PCB en Altium Designer 26 del módulo de control secundario del resBot: la placa de expansión que va sobre la
motherboard junto a la Radxa Zero 3W. Implementa el [Documento de Diseño v5](docs/Documento_de_Diseno_ELO301_Grupo1_v5.pdf)
con los cambios de la [auditoría del 01/11/2026](#auditoría-01112026).

## Estado (01/11/2026)

| Ítem | Estado |
|---|---|
| Esquemático | 4 hojas, 68 componentes |
| ERC | **0 errores**, 3 advertencias esperadas* |
| Componentes | Cada uno con huella, valor, fabricante y número de parte |
| PCB (`ELO301_G1.PcbDoc`) | 4 capas, 70 x 50 mm, 68 componentes colocados, ruteo completo, plano y pours de GND. **DRC: 0 violaciones** |
| Salidas de fabricación | Regeneradas y verificadas: paquete para JLCPCB, BOM con número de parte y CPL ([detalle](#salidas-de-fabricación-fabricacion)) |

\* GNSS_PPS y UART_GNSS_RX llevan salidas del GNSS a pines E/S del MCU, y el nRESET del GNSS solo tiene su pull-up.

| Hoja | Contenido |
|---|---|
| [01 Alimentación](esquematicos/01_Alimentacion.png) | 12 V con B240A en serie y TVS SMAJ15A, buck AP63205 a 5 V, LDO TLV75533 para MCU y para sensores (con ferrita), LED de encendido, divisor 100k/12k + 100 nF hacia PA1 |
| [02 MCU](esquematicos/02_MCU.png) | STM32G431CBT6 con los 29 pines de la Tabla 9, desacoplos, VDDA con ferrita, cristal de 25 MHz (CL 10 pF, 2 × 12 pF), NRST y BOOT0 con pulsadores, LED heartbeat en PB6 |
| [03 Sensores](esquematicos/03_Sensores.png) | IMU BMI270 por SPI1, GNSS ATGM336H por USART2 + PPS con antena activa por U.FL (alimentada desde VCC_RF por L2), conector JST del ToF por I2C2 con pull-ups de 4,7k |
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
9. **Cambios de la auditoría** (cristal de 10 pF, L2 bobinada, antipads de 0,3 mm): ver la [auditoría](#auditoría-01112026).
   Se revierten partiendo de la etapa 4 del paquete por etapas.

## PCB

![PCB](esquematicos/05_PCB.png)

- **Placa:** 70 x 50 mm, 4 capas (Top / GND plano / Señal-Potencia / Bottom), 2 agujeros M3. Apilado tipo JLC04161H-7628
  (prepreg 0,21 mm, núcleo 1,065 mm, prepreg 0,21 mm; cobre 35 µm fuera, 15 µm dentro; ≈ 1,6 mm).
- **Colocación:** `generadores/pcb/colocacion.py` define las 68 posiciones y verifica sin Altium que no haya choques de
  courtyard. La expansión J1 va en la cara inferior hacia la motherboard; el cristal junto a PF0/PF1; los desacoplos
  pegados a cada pin de alimentación del MCU.
- **Reglas:** clases de red (potencia, RF, osciladores, señal), anchos por clase (RF_IN 0,35 mm, SW 0,6 mm, 3V3 0,3 mm),
  holgura 0,15 mm, antipads del plano GND de 0,3 mm, máscara y serigrafía según JLCPCB.
- **Ruteo:** Situs con las pre-rutas bloqueadas, 49 vías de GND al plano (`fanout_gnd.py`, tapadas) y un A* propio
  (`ruteo_astar.py`) para las conexiones que Situs deja sin cerrar. Pours de GND en Top y Bottom.
  Resultado: 682 pistas, 188 vías (63 de ellas de costura de GND cada ≥ 5 mm, `costura.py`), todas con máscara encima.
- **Nodos críticos** (rehechos en Top, sin vías): SW 6,0 mm, BST 2,7 mm, OSC_IN 7,4 mm, OSC_OUT 6,4 mm,
  RF_IN 5,0 mm a 0,35 mm (≈ 48 Ω, ver la auditoría) con un stub de 0,4 mm hacia L2. L1 se giró 180° para que su pad SW
  mire a U1/C4, y L2 (47 nH, VCC_RF) quedó pegada a la línea de RF.
- **Pads THT** con pila explícita (arriba / medio / abajo): en modo simple el DRC no ve el cobre de las capas internas.
- **Designadores:** 60 visibles y el resto ocultos porque no caben sin chocar con serigrafía o pads. La serigrafía
  inferior lleva la identificación «ELO301 G1 v1.1 2026-11».

### Salidas de fabricación (`fabricacion/`)

Generadas con `altium/Fabricacion.OutJob` (contenedor «Fabrication Files») desde la placa con DRC 0 y armadas con
`generadores/herramientas/jlcpcb.py`:

- **`ELO301_G1_Gerber_JLCPCB.zip`, lo que se sube a JLCPCB:** 11 Gerber y el taladro. El plano GND va en positivo como
  `.G2L` (capa 2), Señal-Potencia como `.G3L` (capa 3) y el contorno como `.GKO`, los nombres que JLCPCB documenta para 4 capas.
- **`BOM_ELO301_G1.csv`:** 34 líneas y 66 piezas (sin los agujeros M3), agrupadas por número de parte, con fabricante y
  MPN. LCSC solo del GNSS (C90770).
- **`CPL_ELO301_G1_JLCPCB.csv`:** posición (mm) y rotación de las 66 piezas.
- **`Gerber/`, `NC Drill/` y `Pick Place/`:** salida directa del OutJob, para otros fabricantes (ahí el plano `.GP1` es negativo).
- **Taladro:** 188 × 0,3 mm (vías), 24 × 0,95 mm y 19 × 1,0 mm metalizados, y 2 × 3,2 mm sin metalizar (M3), en un solo
  archivo con `;TYPE=PLATED` / `;TYPE=NON_PLATED`.

Al pedir: 4 capas, 1,6 mm, apilado JLC04161H-7628, cobre exterior de 1 oz. El orden queda L1 `.GTL` · L2 `.G2L` (GND) ·
L3 `.G3L` · L4 `.GBL`.

**Para regenerarlas:** en Altium, ejecutar «Fabrication Files» de `Fabricacion.OutJob`; después,
`python3 generadores/herramientas/jlcpcb.py altium/Fabricacion fabricacion/`. El script no arma el zip si el contorno no
parte en (0,0), si algún agujero no tiene su pad o su antipad/alivio en el plano, o si las capas vienen mezcladas.

### Scripts de la placa

Los nodos críticos se rehacen con `criticas_preparar.py` (respaldo, giro de L1, borra el cobre viejo) →
`ruteo_astar.py` (solo Top) → `aplicar_rutas.py` → `fix_netl2.py`; `volcar.py` exporta la geometría para medir.

El flujo que recrea la placa desde cero está en `generadores/pcb/` (`rehacer1.py` → `situs.py` → `fanout_altium.py` →
`aplicar_rutas.py` → `post6.py` → `designadores2.py`). Necesita la VM de Altium y `generadores/herramientas/` (`boton.*`,
`teclas.py`, `qga.py`, `mcpc.py`). `huellas_todas.txt` es la especificación de las 17 huellas ya con los THT corregidos.
La auditoría quedó en `auditoria.py` (placa y esquemático) y `auditoria_salidas.py` (OutJob y salidas).

## Auditoría (01/11/2026)

Revisión completa del esquemático, la placa y las salidas contra el documento de diseño, las hojas de datos y las
capacidades de JLCPCB. Hallazgos, de más a menos grave:

| # | Hallazgo | Corrección |
|---|---|---|
| 1 | **Gerber inservibles.** `Fabricacion.OutJob` tenía «Add to all plots» con todas las capas eléctricas: cada Gerber de cobre, plano y serigrafía llevaba las pistas de las tres capas de ruteo y el pour de Top; máscara, pasta y cobre llevaban los designadores. | OutJob reescrito con las claves de los OutJob de ejemplo de Altium 26. Verificado capa por capa: cada una lleva solo lo suyo. |
| 2 | **Taladro desalineado.** Los Gerber salían centrados en el film (x ≈ 219 mm) y el taladro relativo al origen (0–70 mm): ninguna de las 188 vías calzaba con su pad. | `CentrePlots=False` y origen relativo: los 233 agujeros calzan con su pad. |
| 3 | **Plano GND negativo y nombres ambiguos.** JLCPCB no busca `.GP1` ni procesa bien Gerber negativos, y `.G1` + `.GP1` no deja claro el orden. La opción de Altium para plano positivo lo dibuja sin antipads (cortocircuito). | `jlcpcb.py` pasa el plano a positivo y lo nombra `.G2L`; Señal-Potencia `.G3L`. Verificado: 97 agujeros de otras redes despejados y 136 de GND con alivio. |
| 4 | **Cristal fuera de especificación.** ABM8 de 18 pF a 25 MHz: gm crítico de 2,18 mA/V con ESR 50 Ω y C0 3 pF (peor caso de Abracon), sobre el máximo de 1,5 mA/V del oscilador HSE (AN2867); además puede pasar el nivel de excitación máximo de 100 µW. | ABM8-25.000MHZ-10-D1G-T (CL 10 pF, −40…85 °C): 0,83 mA/V. C22/C23 de 27 pF a 12 pF (GRM1885C1H120JA01D). |
| 5 | **L2 (alimentación de la antena) resuena bajo la banda GPS.** LQG18HN47NJ00D tiene SRF ≥ 1,2 GHz: a 1,575 GHz puede ser capacitiva y cargar RF_IN. | LQW18AN47NJ00D: bobinada, mismos 47 nH del circuito de ZKW y misma huella 0603, SRF ≥ 2,6 GHz. |
| 6 | **Ranuras en el plano GND.** Antipads de 0,508 mm desde el agujero: 8 grupos de antipads unidos bajo el MCU (hasta 3,3 × 2,1 mm). | Power Plane Clearance de 0,3 mm (JLCPCB pide ≥ 0,2 mm en vías y 0,3 mm en pads): quedan 2 grupos. |
| 7 | **DRC incompleto.** El designador de L2 tocaba la máscara de los pads 14 y 15 de U6; el «DRC 0» anterior no lo mostraba. | Designador movido sobre L2; DRC 0 completo. |
| 8 | **BOM sin fabricante ni MPN.** | BOM agrupado por número de parte, con fabricante y MPN. |
| 9 | **RF_IN: el «≈ 49 Ω» publicado salió de una interpolación mal hecha.** | Resolviendo el campo 2D (diferencias finitas, validado contra Hammerstad): 51,3 Ω como microstrip desnuda y **48,1 Ω reales** con máscara y el GND de Top a 0,39 mm. Con 5 mm (≈ 0,05 λ) la pérdida de retorno es > 39 dB: queda como está. |
| 10 | Sin identificación de placa. | «ELO301 G1 v1.1 2026-11» en la serigrafía inferior. |

**Revisado sin cambios:**
- **Conexiones:** los 48 pines del MCU contra la Tabla 9 y el J1 contra la Tabla 5.
- **Pines:** AP63205, TLV75533, BMI270 y ATGM336H.
- **Tensión nominal de cada capacitor:** 25 V en la entrada de 12 V.
- **Anchos contra corriente:** 0,25 A en 5 V.
- **Reglas contra JLCPCB:** pista y espacio de 0,15 mm, vías 0,3/0,6 mm, anillo THT ≥ 0,5 mm, cobre a 0,3 mm del borde, máscara de 0,05 mm, serigrafía de 0,15 mm.
- **Agujero a agujero mínimo:** 0,40 mm, entre una vía y un pad, ambos de GND.
- **Vías:** todas tapadas.
- **Desacoplos:** a ≤ 3,5 mm de cada VDD del MCU.

**Notas para firmware e integración:**
- **TFmini-S:** viene configurado en UART. Para usarlo por I2C hay que configurarlo una vez con un adaptador USB-serie
  (`5A 05 0A 01 6A` y guardar con `5A 04 11 6F`) y después revisar su dirección con un escaneo I2C.
- **PB4 (SPI3_MISO) y PB6 (LED):** tienen activo desde el reset el pull-down de 5,1 kΩ de «dead battery» del UCPD. Para
  quitarlo hay que poner UCPD1_DBDIS = 1 en PWR_CR3 al arrancar; en HAL es `HAL_PWREx_DisableUCPDDeadBattery()`.
- **Parámetros MPN en la PCB:** la placa todavía guarda los MPN viejos de Y1, C22, C23 y L2. «Design ▸ Update PCB Document»
  los sincroniza, y no afectan las salidas. El símbolo de Y1 sigue llamándose ABM8-25.000MHZ-B2-T.

**Fuentes:** [capacidades de JLCPCB](https://jlcpcb.com/capabilities/pcb-capabilities),
[nombres de archivo de JLCPCB](https://jlcpcb.com/help/article/suggested-naming-patterns),
[Abracon ABM8](https://abracon.com/Resonators/abm8.pdf),
[ZKW ATGM336H-5N](https://atta.szlcsc.com/upload/public/pdf/source/20161226/1482720799860.pdf),
[LQG18HN47NJ00D](https://es.farnell.com/en-ES/murata/lqg18hn47nj00d/inductor-47nh-0603-case/dp/1515390),
[LQW18AN47NJ00D](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/6/47nH_5F00_LQW18AN47NJ00.PDF),
[Gm_crit_max de ST](https://community.st.com/s/question/0D50X0000A1mqBf/to-wich-parameter-refers-hse-oscillator-characteristic-gm-in-stm32l443-datasheet-on-page-123-does-it-refer-to-an2867-parameter-gm-or-to-gmcritmax),
[TFmini-S](https://waveshare.com/wiki/TFmini-S_LiDAR_Range_Sensor),
[UCPD dead battery](https://community.st.com/t5/stm32-mcus-products/gpio-status-during-bootmode/td-p/827730).

### Para revisar antes de mandar a fabricar

1. Subir `ELO301_G1_Gerber_JLCPCB.zip` a JLCPCB y revisar el visor: la capa 2 debe verse como plano GND con antipads.
2. Confirmar el Gm_critmax del STM32G431 en la tabla HSE de su hoja de datos (no se pudo descargar; 1,5 mA/V es el de la familia).
3. Completar los LCSC del BOM y revisar las rotaciones del CPL en la vista previa, si se arma en JLCPCB.
4. Exportar el esquemático a PDF (`Documentacion.OutJob`; Altium se colgó al publicarlo).

## Generadores

`generadores/` contiene lo que se usó para generar el esquemático, con altium-mcp desde Claude Code y Altium corriendo
en una VM:

- `lote*_*.txt` y `fix_*.txt`: especificaciones de símbolos y huellas.
- `hoja_0N_*.py`: un generador por hoja.
- `herramientas/`: el conversor KiCad → Altium, los scripts de construcción y verificación pin a pin, y `jlcpcb.py`.

**Ojo:** si una hoja se edita a mano en Altium, no hay que volver a correr su generador, porque se perderían esos
cambios.

## Siguientes pasos

1. Revisión en grupo de los cambios de la auditoría y de las decisiones de arriba.
2. Pedido de prueba en JLCPCB (puntos de «Para revisar antes de mandar a fabricar»).
3. Exportar el esquemático a PDF.

## Paquete Altium por etapas (para revisar y modificar)

`ELO301_G1_Altium_por_etapas.zip`: 5 proyectos Altium completos (esquemático → PCB ruteado → nodos críticos → costura y
fabricación → auditoría), con su `LEEME.md` de importación. Abrir `ELO301_G1.PrjPcb` de la etapa deseada; **la etapa 5
es la vigente**.
