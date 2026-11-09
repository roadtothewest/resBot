# ELO301 — Módulo de control secundario (Grupo 1)

Esquemático y PCB en Altium Designer 26 del módulo de control secundario del resBot: la placa de expansión que va sobre la
motherboard junto a la Radxa Zero 3W. Implementa el [Documento de Diseño v6](docs/Documento_de_Diseno_ELO301_Grupo1_v6.pdf)
(revisión 1.4; [`.docx`](docs/Documento_de_Diseno_ELO301_Grupo1_v6.docx)).

## Estado (09/11/2026)

| Ítem | Estado |
|---|---|
| Esquemático | Jerárquico: hoja superior de módulos + 4 hojas, 71 componentes ([PDF](esquematicos/ELO301_G1_Esquematico.pdf)) |
| ERC | **0 errores y 0 advertencias** (3 pines con No ERC*) |
| Componentes | Cada uno con huella, valor, fabricante, número de parte y código DigiKey (LCSC como segundo proveedor), también en la placa. ActiveBOM en `altium/ELO301_G1.BomDoc`: con internet muestra precio y stock en vivo |
| PCB (`ELO301_G1.PcbDoc`) | 4 capas, 70 x 50 mm, ruteo completo, GND en las capas 2 y 3. **DRC: 0 violaciones**. Serigrafía completa, a 0,24 mm o más del borde |
| Salidas de fabricación | Regeneradas el 09/11, verificadas contra la netlist y revisadas en JLCPCB ([detalle](#salidas-de-fabricación-fabricacion), [verificación](fabricacion/verificacion/)) |

\* PA0 y PA3 del MCU (U4-8, U4-11) son E/S usadas como entrada y las maneja una salida del GNSS (PPS y TX); el RESET_N
del GNSS (U6-9) solo tiene su pull-up R9. Altium avisa en los tres casos, aunque el circuito es correcto.

| Hoja | Contenido |
|---|---|
| [00 Módulos](esquematicos/00_Modulos.png) | Hoja superior: un bloque por hoja (PODER, MCU, SENSORES, CONECTORES) con sus 29 señales entre hojas cableadas como entradas de hoja |
| [01 Alimentación](esquematicos/01_Alimentacion.png) | 12 V con B240A en serie y TVS SMAJ15A, buck AP63205 a 5 V, LDO TLV75533 para MCU y para sensores (con ferrita), LED de encendido, divisor 100k/12k + 100 nF hacia PA1 |
| [02 MCU](esquematicos/02_MCU.png) | STM32G431CBT6 con 31 E/S (Tabla 9), desacoplos, VDDA con ferrita, cristal de 25 MHz (CL 10 pF, 2 × 12 pF), NRST y BOOT0 con pulsadores, LED heartbeat en PB9, UART de depuración (USART1) en PB6/PB7 |
| [03 Sensores](esquematicos/03_Sensores.png) | IMU BMI270 por SPI1, GNSS ATGM336H por USART2 + PPS con antena activa por U.FL (alimentada desde VCC_RF por L2), conector JST del ToF por I2C2 con pull-ups de 4,7k |
| [04 Conectores](esquematicos/04_Conectores.png) | Expansión 1x14 (Tabla 5), SWD 1x5, UART de depuración 1x4 (J9), 4 JST XH 5P para los FOC con 33 Ω en serie, 4 agujeros M3 |

## Pendientes

Están en [TAREAS.md](TAREAS.md), en orden.

## Cambios del 09/11/2026

- **ERC sin advertencias** (`generadores/jerarquia/jerarquia.py unificar`):
  - Las redes con dos o más puertos en una misma hoja quedan con uno solo: NRST, I2C_TOF_SDA/SCL, VIN_12V, SWDIO,
    SWCLK y SPI_FOC_MISO. Los demás tramos recuperan su etiqueta de red, que se une por nombre dentro de la hoja.
  - No ERC en los 3 pines de la nota del estado.
  - `revisar` cuenta solo las violaciones activas, como el panel Messages.
  - Netlist idéntica: 251 pines y 72 redes.
- **Designadores que no quedaban guardados:**
  - `completar.py` movía los textos con `XLocation`. Se ven bien en pantalla y salen bien en los Gerber, pero al reabrir
    el PcbDoc Altium los devolvía a su posición anterior.
  - El PcbDoc del 08/11, abierto en Altium, mostraba 10 designadores fuera de lugar (DRC con 21 violaciones), aunque
    los Gerber subidos estaban bien.
  - Ahora se mueven con `MoveToXY`. Verificado reabriendo el archivo.
- **Serigrafía en el borde** (`generadores/serigrafia/marca_xh.py`):
  - La marca de pin 1 de J3–J6 quedaba a 0,16 mm del borde. Se bajó 0,29 mm, hasta la línea de la carcasa, en la
    huella y en la placa.
  - Ahora toda la serigrafía queda a 0,24 mm o más del borde.
  - `revisar_serigrafia.py` mide hasta el eje del contorno; antes sumaba medio trazo.
- **Bibliotecas genéricas** (`generadores/digikey/huellas_genericas.py`): CAP, RESISTOR, INDUCTOR y DIODE - GENERIC no
  tenían huella, y Altium avisaba al generar salidas. Ahora tienen la que usa la placa (INDUCTOR, las dos).
- **JLCPCB, con cuenta:**
  - **Gerber Viewer:** reconoce las 11 capas (2 internas), el contorno y los 4 M3, y las dos caras se ven bien
    ([captura](fabricacion/verificacion/jlcpcb_visor.png)).
  - **Vista de armado:** 6 huellas tienen otro cero en JLCPCB. `jlcpcb.py` corrige la rotación del CPL (U1 270°, U2 y
    U3 180°, U4 90°, U5 180°, U6 90°), y así el pin 1 de su modelo cae sobre nuestro pad 1
    ([captura](fabricacion/verificacion/jlcpcb_pin1.png)). D1, D2, LED1 y LED2 quedan con la polaridad correcta.
  - La BMI270 solo se arma en «Standard PCBA»: USD 25 por cara y rieles, porque la placa mide menos de 70 mm por lado.
  - C16 sigue sin stock.
  - Los conectores de inserción quedan sin marcar para el armado. JLCPCB asoció J2 y J9 a una tira de 40 pines.
- **ActiveBOM:** abierto en Altium con internet, muestra precio y stock en vivo de cada proveedor. Por ejemplo, la
  línea 1 tiene 260 mil unidades, desde USD 0,1133. El `.BomDoc` no guarda esos datos, igual que el del profesor.
- **CubeMX 6.18.1:**
  - `generadores/cubemx/ELO301_G1.ioc` sale de `ioc.py`, con la Tabla 9.
  - `capturas.py` genera las Ilustraciones 3 y 4 del documento.
  - El documento v6 ya no dice que esas ilustraciones son de la revisión 1.3.
- **Salidas regeneradas:**
  - Esquemático: PDF, y PNG de las hojas 02–04.
  - Gerber: cambia solo la serigrafía, en las 4 marcas.
  - CPL, imagen de la placa y verificación: LVS y serigrafía OK, con prueba de detección.

## Cambios del 08/11/2026

- **Esquemático jerárquico** (`generadores/jerarquia/jerarquia.py`):
  - Las 80 etiquetas que unían hojas pasaron a 68 puertos y 12 símbolos de alimentación (GND y V3V3_MCU de la hoja 04).
  - Cada puerto va en el extremo libre de su cable y con un ancho que no toca otro cable, porque el extremo lejano
    también conecta.
  - `00_Modulos.SchDoc` tiene un bloque por hoja. Los FOC quedan en un solo bloque con su bus compartido y 4 CS; con
    `Repeat` cambiarían designadores y redes.
  - `AllowPortNetNames=1`, para que los nombres de red no cambien.
  - **Netlist idéntica** a la plana: 251 pines y 72 redes, comparados pin a pin.
  - ERC en 0 errores. Los puertos del GNSS van como salida/entrada; el resto, bidireccionales.
  - La placa se re-enlazó a los Unique ID jerárquicos (71 de 71). Así, *Update PCB* no borra ni vuelve a agregar
    componentes.
- **Símbolo del 1x04:** queda uno solo, `BOOMELE 2.54-1x04`, con la descripción corregida («1x4»).
- **Serigrafía completa** (`generadores/serigrafia/completar.py`), sin tocar la del 04/11:
  - Los 10 designadores ocultos ahora se ven: C6, C12, C19, C25, J4, R13 y H1–H4. Van en 1,0 mm, el mínimo de JLCPCB.
  - C19 lleva una línea guía.
  - C23 y R2 se corrieron para dejar lugar a C12 y C25.
  - Nombre de cada módulo, como los bloques de la hoja superior: PODER, MCU, IMU, TOF, GNSS, LDO, SERVICIO, SWD,
    UART, EXPANSION y FOC1–FOC4.
  - Líneas de 0,18 mm que separan los módulos, cortadas donde hay máscara, tinta, vías o tornillos.
  - DRC 0, incluida la regla Silk To Silk de 10 mil.
  - Gerber revisado con `revisar_serigrafia.py`: todo sobre los mínimos de JLCPCB salvo un punto heredado (resuelto el
    09/11).
- **ActiveBOM** (`generadores/digikey/activebom.py`):
  - `ELO301_G1.BomDoc` con las opciones del proyecto del profesor.
  - 36 líneas, con DigiKey como primera opción de compra y LCSC como segunda.
- **Documento de diseño v6** (`generadores/documento/doc_v6.py`): UART de depuración, cristal de 10 pF, L2 bobinada,
  4 M3, 31 E/S, diagrama de bloques, y BOM y costos con códigos DigiKey y precios LCSC. Da USD 34,43 por unidad en un
  lote de 100.
- **Salidas regeneradas:**
  - PDF del esquemático (5 hojas, A4) y PNG de cada hoja y de la placa.
  - Gerber, taladro, Pick & Place, zip, CPL y BOM.
  - Cobre, máscara, pasta y contorno quedan geométricamente idénticos a los del 04/11; cambia solo la serigrafía
    superior.

## Abrir el proyecto

En Altium Designer, abrir `altium/ELO301_G1.PrjPcb`. Las bibliotecas van en la misma carpeta y se cargan solas.

- **`CAP/RESISTOR/INDUCTOR/DIODE - GENERIC.SchLib`, `C0603 - MURATA.PcbLib` y `R0603 - YAGEO.PcbLib`:** bibliotecas
  RCL del profesor (github.com/linitrofe/ELO301.Hw.Altium).
- **`<TIPO> - <MPN>.SchLib`** (por ejemplo `MCU - STM32G431CBT6.SchLib`): un símbolo por pieza, como en el proyecto
  de referencia del profesor, con los parámetros de DigiKey y la huella enlazada. `LED - GENERIC`, `FERRITE - GENERIC` y
  `MOUNTING HOLE - M3` son genéricos: sus datos de fabricante van en cada instancia, igual que en los RCL del profesor.
- **`ELO301_G1.PcbLib`:** 17 huellas convertidas desde las bibliotecas oficiales de KiCad 10 (huellas IPC). Siguen las
  capas del profesor: Mech 13 para ensamble, Mech 15 para courtyard y Mech 29 para el designador.

## Metadatos DigiKey (02/11/2026)

El ramo pide componentes de DigiKey. Cada línea del BOM se buscó en DigiKey y sus datos quedaron en
[`generadores/digikey/metadatos_digikey.tsv`](generadores/digikey/metadatos_digikey.tsv). Desde ahí se escriben en el
símbolo y en cada componente del esquemático: `Supplier 1` = DigiKey y `Supplier Part Number 1` (el código CT-ND), con
descripción, categoría, encapsulado, rango de temperatura, estado y enlaces a la hoja de datos y a DigiKey. LCSC queda
como `Supplier 2`.

- **Excepciones con LCSC como `Supplier 1`:**
  - ATGM336H-5N31: no se vende en DigiKey, igual que en el documento de diseño.
  - J1/J2: tira BOOMELE 2.54-1×40P (C2337), estándar del ramo, en vez de los headers XFCN de la auditoría.
- **Reemplazos por piezas obsoletas en DigiKey** (mismo tamaño 0603):

  | Designadores | Antes (obsoleto) | Ahora | DigiKey |
  |---|---|---|---|
  | 12 × 100 nF | GRM188R71H104KA93D | GCM188R71H104KA57D (50 V X7R) | 490-4779-1-ND |
  | C8–C11, C18 (1 µF) | GRM188R61E105KA12D | GCM188R71E105KA64D (25 V X7R) | 490-10673-1-ND |
  | C16 (4,7 µF) | GRM188R61A475KE15D | GRM188R61C475ME11J (16 V X5R) | 490-GRM188R61C475ME11JCT-ND |

  El 12 pF sigue siendo el Samsung CL10C120JB8NNNC: el GRM1885C1H120JA01D de Murata está como «Not For New Designs».
- **Pinouts revisados contra el fabricante:** STM32G431CBT6 (STM32_open_pin_data de ST), AP63205 (DS41326), TLV755P
  (tabla 4-1), BMI270 (tabla 22) y ATGM336H (manual de ZKW, pág. 10). Todos coinciden.
  - **Cambios:** se agregaron los nombres de ST a los pines con función fija (`PG10-NRST`, `PB8-BOOT0`, `PF0-OSC_IN`…),
    VSS 35/47 pasaron a alimentación, Y1 pasó a llamarse ABM8-25.000MHZ-10-D1G-T y se asignó el designador de cada tipo.
- **Verificación:** el proyecto compila y la netlist aplanada es idéntica a la del commit anterior (72 redes, 247 pines).

Para regenerar todo, con Altium abierto: `correr.ps1 -Proc CrearBibliotecas`, `correr.ps1 -Proc ActualizarEsquematico`
y `proyecto_bibliotecas.ps1`. Los scripts están en `generadores/digikey/`.

**Pendiente:**
- ~~Regenerar el BOM de `fabricacion/`~~: hecho el 04/11.
  - Se agregaron los LCSC de los 3 capacitores reemplazados: C85864, C85862 y C6565408.
  - Se agregó una fila para J9.
- Pasar el documento de diseño a DigiKey (la v5 cotiza en Mouser).

## Cambios de placa (02/11/2026)

- **Update PCB:** los parámetros de DigiKey ya están en la placa.
  - El ECO vuelve a proponer «Remove Net Classes» (Potencia y Alimentacion). Si se ejecuta,
    `generadores/digikey/Placa.pas` (`ClasesDeRed`) las repone en 2 s.
- **GND en la capa 3 (Senal-Potencia):** antes estaba vacía. Ahora las pistas de Bottom tienen referencia a 0,21 mm
  y no a 1,27 mm.
- **Perforaciones H3 y H4 (M3) en (3,3 ; 38,6) y (66,7 ; 38,6) mm desde el origen:**
  - Quedan a 35 mm sobre H1/H2 y bajan el voladizo del borde de los FOC de 46 a ~11 mm.
  - Se quitaron 5 vías de costura bajo los separadores.
- **C3 (10 µF):** pasa a estar entre VIN (pin 3) y GND (pin 4) del AP63205, con el lazo de entrada mínimo. C1 y C2
  quedan como capacidad de entrada.
- **LDO de sensores (U3, FB1, C10, C11) entre la IMU y el GNSS:**
  - V3V3_SENS bajó de 113 mm a ~48 mm y el GNSS queda a 3 mm del LDO.
  - La rama de la IMU sigue por el borde superior: el abanico SPI del MCU bloquea el camino directo en las 3 capas.
  - GND de C10/U3 con vías propias al plano. Los designadores del grupo quedan ocultos.
- **Sin cambios:** la IMU y R10–R15. Con H3/H4 la IMU ya no está en voladizo, y el bus FOC es lento.
- **Verificación:** DRC completo en 0 (incluye no ruteadas, antenas, slivers y serigrafía); el ECO solo muestra
  las clases de red.
- **Situs:** no usar «Connections on selected components» sin bloquear antes las rutas existentes. Corre sus pasadas
  sobre toda la placa: borró vías de otras redes y agregó vías de fanout pegadas a pads. Las rutas del LDO se
  agregaron a mano (`RutasLDO`).

## Cambios de placa (04/11/2026)

La lista de lo que falta para la entrega está en [TAREAS.md](TAREAS.md).

- **UART de depuración (PR #2):**
  - USART1 con TX en PB6 y RX en PB7. El LED de heartbeat pasa a PB9.
  - Header J9 1x4 BOOMELE: 1 V3V3_MCU (referencia, no alimenta), 2 TX del MCU, 3 RX del MCU, 4 GND.
  - La programación sigue por SWD: J2, o J1 desde la Radxa.
- **J9 corrido 1,45 mm a la derecha:** su courtyard se metía 1,33 mm en la zona del tornillo de H1 (radio de 3,45 mm).
  - El DRC no lo veía porque no revisa courtyards.
  - Se ajustaron sus pistas en Bottom.
  - La pista de VIN_12V en Top (D1 → J1-1) ahora pasa por fuera del J9: horizontal, 45° y bajada vertical a J1-1.
- **Serigrafía por encima de los mínimos de JLCPCB:**

  | | Antes | Ahora | Mínimo JLCPCB |
  |---|---|---|---|
  | Ancho de línea | 0,10–0,12 mm | 0,18 mm | 0,15 mm |
  | Alto de texto | 0,8 mm (1,0 mm el de la cara inferior) | 1,2 mm, trazo de 0,2 mm (1:6) | 1,0 mm |
  | Serigrafía a cobre de pad | 0,15 mm | 0,2 mm o más | 0,15 mm |

  - **Recorte de las líneas:** se recortaron donde quedaban a menos de 0,2 mm del cobre, con la forma real de cada pad
    (rectángulo redondeado). Se mantienen las marcas de pin 1 y de polaridad.
  - **Bibliotecas:** las de `ELO301_G1.PcbLib` y las dos del profesor (`C0603 - MURATA`, `R0603 - YAGEO`) quedaron igual
    que en la placa, para que un *Update From PCB Libraries* no revierta el cambio.
  - **Designadores:**
    - Reubicados con `generadores/serigrafia/designadores.py`: a 0,25 mm o más de los pads, a 0,26 mm o más de otra
      serigrafía, fuera de los cuerpos y de la zona de los tornillos.
    - Cada uno queda más cerca de su pieza que de otra del mismo tipo.
    - Quedan 61 visibles.
    - Ocultos: C6, C12, C19, C25, J4 y R13, que no caben (J4 tiene 1,3 mm libres y el texto ocupa 1,6 mm), y H1–H4.
  - **Identificación de la cara inferior:** «ELO301 G1 v1.2 2026-11».
- **Verificación:**
  - DRC completo en 0.
  - Sin choques de courtyard.
  - Serigrafía medida sobre el archivo con `generadores/serigrafia/verificar_seda.py`.
- **Regla *Silk To Solder Mask*:** pasó de 0,1 a 0,15 mm. Con la máscara de 0,05 mm, el DRC exige ahora 0,2 mm entre la
  serigrafía y el cobre.
- **Vías del PR #2 tapadas:** las 3 vías nuevas junto al MCU (UART TX, RX y LED) venían sin máscara encima. Ahora están
  tapadas como las otras 182 (`Placa.pas`, `TaparVias`).
- **Esquemático:**
  - `ActualizarEsquematico` volvió a escribir los metadatos.
  - Volvieron los parámetros «Description» que el PR #2 había quitado en la hoja 02.
  - La descripción del J9 dice «1x4».
  - Se cargaron los LCSC de los capacitores reemplazados.
  - Las conexiones quedaron idénticas, comparadas hoja por hoja.

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
   Se revierten partiendo de la etapa 4 del paquete por etapas, con el `Fabricacion.OutJob` de la etapa 5.

## PCB

![PCB](esquematicos/05_PCB.png)

- **Placa:** 70 x 50 mm, 4 capas (Top / GND plano / Señal-Potencia / Bottom), 4 agujeros M3. Apilado tipo JLC04161H-7628
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
- **Serigrafía:** los 71 designadores visibles: 61 de 1,2 mm y 10 de 1,0 mm (ver los [cambios del 08/11](#cambios-del-08112026)).
  Lleva el nombre de cada módulo y separadores entre módulos. La cara inferior lleva la identificación «ELO301 G1 v1.2 2026-11».

### Salidas de fabricación (`fabricacion/`)

Regeneradas el 08/11/2026 con `altium/Fabricacion.OutJob` (contenedor «Fabrication Files»), desde la placa con DRC 0.
Las armó `generadores/herramientas/jlcpcb.py`. En [`fabricacion/verificacion/`](fabricacion/verificacion/) queda la
comparación del zip contra la netlist del esquemático (`lvs.txt`, `lvs_gerber.py`: sin abiertos ni cortos, y con la prueba
de detección) y la revisión de la serigrafía (`serigrafia.txt`).

- **`ELO301_G1_Gerber_JLCPCB.zip`, lo que se sube a JLCPCB:** 11 Gerber y el taladro. El plano GND va en positivo como
  `.G2L` (capa 2), Señal-Potencia como `.G3L` (capa 3) y el contorno como `.GKO`, los nombres que JLCPCB documenta para 4 capas.
- **`BOM_ELO301_G1.csv`:** lo genera `generadores/digikey/bom_digikey.py` directamente desde los esquemáticos y la placa.
  - 35 líneas y 67 piezas, sin los agujeros M3, agrupadas por número de parte, valor y huella.
  - Columnas: fabricante, MPN, código DigiKey y código LCSC. Lleva además las columnas que pide JLCPCB para armar
    (Comment, Designator, Footprint, LCSC Part #).
  - **Sin código DigiKey:** la tira BOOMELE (J1, J2, J9) y el GNSS ATGM336H, excepciones documentadas en la columna Nota.
  - **Verificación del 04/11/2026:** los 35 códigos LCSC se revisaron contra la API de piezas de JLCPCB. Todos coinciden
    con su MPN y tienen stock, menos el **C16 (GRM188R61C475ME11J, C6565408): sin stock**. El equivalente con stock es
    Samsung CL10A475KO8NNNC (C19666, pieza «Basic»), anotado en la columna Nota. Hay que decidir si se reemplaza para
    el armado en JLCPCB.
  - La única pieza «Basic» del BOM actual es C22/C23. Las demás son «Extended»: JLCPCB cobra un cargo fijo por cada tipo.
- **`CPL_ELO301_G1_JLCPCB.csv`:** posición (mm) y rotación de las 67 piezas. En 6 huellas, la rotación va llevada al
  cero de JLCPCB (`ROT_JLC` en `jlcpcb.py`, revisado en su vista de armado el 09/11).
- **`Gerber/`, `NC Drill/` y `Pick Place/`:** salida directa del OutJob, para otros fabricantes (ahí el plano `.GP1` es negativo).
- **Taladro:** en un solo archivo con `;TYPE=PLATED` / `;TYPE=NON_PLATED`.
  - Metalizados: 185 × 0,3 mm (vías), 24 × 0,95 mm y 23 × 1,0 mm.
  - Sin metalizar: 4 × 3,2 mm (M3).
- **Revisión de los Gerber:**
  - Serigrafía solo de 0,18 y 0,2 mm.
  - Las 185 vías tapadas en ambas caras. Las 3 que agregó el PR #2 junto al MCU venían destapadas; se taparon.
  - Los 236 agujeros con su antipad o alivio en el plano.
  - Contorno de 70 × 50 mm en (0,0).

Al pedir: 4 capas, 1,6 mm, apilado JLC04161H-7628, cobre exterior de 1 oz. El orden queda L1 `.GTL` · L2 `.G2L` (GND) ·
L3 `.G3L` · L4 `.GBL`.

**En el cotizador de JLCPCB (01/11/2026):**
- **Reconoció:** 4 capas de 70 × 50 mm, los 12 archivos (como salida de Altium) y 233 agujeros. El agujero mínimo es de
  0,30 mm, la pista mínima de 0,20 mm y la separación mínima de 0,156 mm. Sin observaciones (`RES_OK`).
- **A revisar:** contó 4 agujeros sin metalizar cuando el taladro tenía 2 M3. Desde el 04/11 son 4 M3, y el
  «Gerber Viewer» los muestra (revisado el 09/11).
- **Render independiente (PyGerber) de `.G2L`:** plano macizo, 97 agujeros de otras redes despejados y los 136 de GND
  unidos al plano. PyGerber no dibuja la primitiva de alivio térmico, así que ahí se ven como conexión directa.

**Para regenerarlas:** con el proyecto abierto, ejecutar «Fabrication Files» de `Fabricacion.OutJob`. El OutJob está
dentro del proyecto: si se abre suelto, Altium lo deja en «Free Documents» y no genera nada. Después correr
`python3 generadores/herramientas/jlcpcb.py altium/Fabricacion fabricacion/`. El script no arma el zip en estos casos:
- el contorno no parte en (0,0);
- algún agujero no tiene su pad, o su antipad o alivio en el plano;
- una pista llega a un agujero sin pad en esa capa;
- las capas vienen mezcladas.

### Scripts de la placa

Los nodos críticos se rehacen con `criticas_preparar.py` (respaldo, giro de L1, borra el cobre viejo) →
`ruteo_astar.py` (solo Top) → `aplicar_rutas.py` → `fix_netl2.py`; `volcar.py` exporta la geometría para medir.

El flujo que recrea la placa desde cero está en `generadores/pcb/` (`rehacer1.py` → `situs.py` → `fanout_altium.py` →
`aplicar_rutas.py` → `post6.py` → `designadores2.py`). Necesita la VM de Altium y `generadores/herramientas/` (`boton.*`,
`teclas.py`, `qga.py`, `mcpc.py`). `huellas_todas.txt` es la especificación de las 17 huellas ya con los THT corregidos.
La auditoría quedó en `auditoria.py` (placa y esquemático) y `auditoria_salidas.py` (OutJob y salidas). Además:
- `lcsc_esquematico.py` escribe los LCSC del BOM en el esquemático.
- `clases_red.py` repone las clases de red de la placa (ver la nota sobre «Update PCB»).

## Auditoría (01/11/2026)

Revisión completa del esquemático, la placa y las salidas contra el documento de diseño, las hojas de datos y las
capacidades de JLCPCB. Hallazgos, de más a menos grave:

| # | Hallazgo | Corrección |
|---|---|---|
| 1 | **Gerber inservibles.** `Fabricacion.OutJob` tenía «Add to all plots» con todas las capas eléctricas: cada Gerber de cobre, plano y serigrafía llevaba las pistas de las tres capas de ruteo y el pour de Top; máscara, pasta y cobre llevaban los designadores. | OutJob reescrito con las claves de los OutJob de ejemplo de Altium 26. Verificado capa por capa: cada una lleva solo lo suyo. |
| 2 | **Taladro desalineado.** Los Gerber salían centrados en el film (x ≈ 219 mm) y el taladro relativo al origen (0–70 mm): ninguna de las 188 vías calzaba con su pad. | `CentrePlots=False` y origen relativo: los 233 agujeros calzan con su pad. |
| 3 | **Plano GND negativo y nombres ambiguos.** JLCPCB no busca `.GP1` ni procesa bien Gerber negativos, y `.G1` + `.GP1` no deja claro el orden. La opción de Altium para plano positivo lo dibuja sin antipads (cortocircuito). | `jlcpcb.py` pasa el plano a positivo y lo nombra `.G2L`; Señal-Potencia `.G3L`. Verificado: 97 agujeros de otras redes despejados y 136 de GND con alivio. |
| 4 | **Pista interna sin anillo en J1-1.** La pista de 12 V (0,6 mm) de Señal-Potencia une J1-1 con J1-2 y es la única conexión de J1-2. Al generar las salidas, Altium dio por desconectado el pad interno de J1-1 y lo omitió del `.G1`: el taladro de 1,0 mm habría cortado la pista y J1-2 podía quedar abierto. | Tras recalcular la conectividad (Update PCB), el Gerber trae el anillo. `jlcpcb.py` ahora rechaza todo agujero al que llegue una pista sin pad en esa capa (el paquete anterior no pasa). |
| 5 | **Cristal fuera de especificación.** ABM8 de 18 pF a 25 MHz: gm crítico de 2,18 mA/V con ESR 50 Ω y C0 3 pF (peor caso de Abracon), sobre el máximo de 1,5 mA/V del oscilador HSE (DS12589, tabla 42); además puede pasar el nivel de excitación máximo de 100 µW. | ABM8-25.000MHZ-10-D1G-T (CL 10 pF, −40…85 °C): 0,83 mA/V, margen de 1,8×. C22/C23 de 27 pF a 12 pF C0G: Samsung CL10C120JB8NNNC, porque el GRM1885C1H120JA01D equivalente no tiene stock en JLCPCB. |
| 6 | **L2 (alimentación de la antena) resuena bajo la banda GPS.** LQG18HN47NJ00D tiene SRF ≥ 1,2 GHz: a 1,575 GHz puede ser capacitiva y cargar RF_IN. | LQW18AN47NJ00D: bobinada, mismos 47 nH del circuito de ZKW y misma huella 0603, SRF ≥ 2,6 GHz. |
| 7 | **Ranuras en el plano GND.** Antipads de 0,508 mm desde el agujero: 8 grupos de antipads unidos bajo el MCU (hasta 3,3 × 2,1 mm). | Power Plane Clearance de 0,3 mm (JLCPCB pide ≥ 0,2 mm en vías y 0,3 mm en pads): quedan 2 grupos. |
| 8 | **DRC incompleto.** El designador de L2 tocaba la máscara de los pads 14 y 15 de U6; el «DRC 0» anterior no lo mostraba. | Designador movido sobre L2; DRC 0 completo. |
| 9 | **OutJob fuera del proyecto.** `Fabricacion.OutJob` y `Documentacion.OutJob` no estaban en el `.PrjPcb`: abiertos sueltos quedan en «Free Documents» y «Generate» termina «bien» sin escribir ningún archivo. | Agregados al proyecto. |
| 10 | **BOM sin fabricante, MPN ni LCSC.** J1/J2 eran tiras BOOMELE de 40 pines, que JLCPCB no puede cortar ni armar. | BOM agrupado por número de parte, con fabricante, MPN y LCSC (también en el esquemático y en la placa). J1/J2: headers XFCN PZ254V-11-14P y PZ254V-11-05P. |
| 11 | **RF_IN: el «≈ 49 Ω» publicado salió de una interpolación mal hecha.** | Resolviendo el campo 2D (diferencias finitas, validado contra Hammerstad): 51,3 Ω como microstrip desnuda y **48,1 Ω reales** con máscara y el GND de Top a 0,39 mm. Con 5 mm (≈ 0,05 λ) la pérdida de retorno es > 39 dB: queda como está. |
| 12 | Sin identificación de placa. | «ELO301 G1 v1.1 2026-11» en la serigrafía inferior. |

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
- **PB4 (SPI3_MISO) y PB6 (TX de USART1 desde el 04/11):** tienen activo desde el reset el pull-down de 5,1 kΩ de «dead battery» del UCPD. Para
  quitarlo hay que poner UCPD1_DBDIS = 1 en PWR_CR3 al arrancar; en HAL es `HAL_PWREx_DisableUCPDDeadBattery()`.
- **«Update PCB» y las clases de red:** la placa ya guarda fabricante, MPN y LCSC (se sincronizó el 01/11/2026).
  - **Riesgo:** las clases «Alimentacion» y «Potencia» existen solo en la placa y las usan las reglas `Ancho_*`, así que
    el ECO propone borrarlas («Remove Net Classes»). Si se borran, el DRC sigue en 0 pero esas reglas dejan de aplicar.
  - **Qué hacer:** desmarcar ese grupo en el ECO. Si igual se borran, `generadores/pcb/clases_red.py` las repone.
  - **Y1:** su símbolo sigue llamándose ABM8-25.000MHZ-B2-T.

**Fuentes:** [capacidades de JLCPCB](https://jlcpcb.com/capabilities/pcb-capabilities),
[nombres de archivo de JLCPCB](https://jlcpcb.com/help/article/suggested-naming-patterns),
[Abracon ABM8](https://abracon.com/Resonators/abm8.pdf),
[ZKW ATGM336H-5N](https://atta.szlcsc.com/upload/public/pdf/source/20161226/1482720799860.pdf),
[LQG18HN47NJ00D](https://es.farnell.com/en-ES/murata/lqg18hn47nj00d/inductor-47nh-0603-case/dp/1515390),
[LQW18AN47NJ00D](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/6/47nH_5F00_LQW18AN47NJ00.PDF),
[STM32G431, DS12589 tabla 42](https://www.st.com/resource/en/datasheet/stm32g431cb.pdf),
[piezas de JLCPCB](https://jlcpcb.com/parts),
[TFmini-S](https://waveshare.com/wiki/TFmini-S_LiDAR_Range_Sensor),
[UCPD dead battery](https://community.st.com/t5/stm32-mcus-products/gpio-status-during-bootmode/td-p/827730).

### Para revisar antes de mandar a fabricar

1. ~~Revisar el zip en el «Gerber Viewer» de JLCPCB~~: hecho el 09/11 (11 capas, contorno y 4 M3).
2. ~~Revisar las rotaciones del CPL en la vista previa de armado~~: hecho el 09/11; 6 huellas corregidas en `jlcpcb.py`.
   Al pedir, marcar «Confirm Parts Placement» para que JLCPCB envíe la colocación antes de armar (J7 incluido).
3. ~~Exportar el esquemático a PDF~~: hecho el 08/11 (`esquematicos/ELO301_G1_Esquematico.pdf`).

## Generadores

`generadores/` contiene lo que se usó para generar el esquemático, con altium-mcp desde Claude Code y Altium corriendo
en una VM:

- `lote*_*.txt` y `fix_*.txt`: especificaciones de símbolos y huellas.
- `hoja_0N_*.py`: un generador por hoja.
- `herramientas/`: el conversor KiCad → Altium, los scripts de construcción y verificación pin a pin, `jlcpcb.py`,
  `lvs_gerber.py` (Gerber contra netlist), `netlist_altium.py`, `placa_kicad.py` (pads desde KiCad),
  `render_gerber.py` y `revisar_serigrafia.py`.
- `jerarquia/`, `serigrafia/completar.py`, `digikey/activebom.py` y `documento/`: los cambios del 08/11.
- `cubemx/` (`.ioc` y figuras), `serigrafia/marca_xh.py` y `digikey/huellas_genericas.py`: los del 09/11.

**Ojo:** si una hoja se edita a mano en Altium, no hay que volver a correr su generador, porque se perderían esos
cambios.

## Siguientes pasos

1. Revisión en grupo de los cambios del 08/11 y del 09/11, y de las decisiones de arriba.
2. Los pendientes de [TAREAS.md](TAREAS.md).
3. Pedido de prueba (puntos de «Para revisar antes de mandar a fabricar»).

## Paquete Altium por etapas (para revisar y modificar)

`ELO301_G1_Altium_por_etapas.zip`: 5 proyectos Altium completos (esquemático → PCB ruteado → nodos críticos → costura de
GND → auditoría y fabricación), con su `LEEME.md` de importación. **Quedó desactualizado:** la versión vigente es la de
`altium/` (UART J9, serigrafía completa y esquemático jerárquico).
