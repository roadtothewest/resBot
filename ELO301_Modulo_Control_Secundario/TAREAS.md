# Tareas pendientes para la entrega (03/11/2026)

Estado al dejar la sesión: no se ha cambiado nada en Altium ni en git. En la carpeta local solo hay:
- `altium/ELO301_G1.PcbDoc` y `.PrjPcb` regrabados por Altium, sin cambios de diseño.
- El zip de tu compañero en la raíz del repo (`../ELO301_G1_Gerber_JLCPCB.zip`), sin commit. Se reemplaza al
  regenerar las salidas (tarea 4).

Altium quedó abierto (X2.EXE). No hay que cerrarlo a la fuerza: bloquea la licencia.

## Lo que ya se revisó

- **Programación:** la placa la tiene.
  - J2 (SWD 1x5: V3V3, SWCLK, GND, SWDIO, NRST).
  - SWD también en J1 (pines 11 a 13), y botones de NRST y BOOT0.
- **Depuración por UART:** la placa **no la tiene**. La única UART en uso es USART2 (PA2/PA3), y la ocupa el GNSS.
  - Pines libres del MCU: PA11, PA12 (reservados para FDCAN1), PB7, PB9, PB12, PC13, PC14 y PC15. Ningún par TX/RX
    completo está libre.
- **Huellas:** las de `ELO301_G1.PcbLib` vienen del conversor KiCad → Altium del flujo anterior
  (`generadores/herramientas/kicad2altium.py`). En la sesión del 02/11 se rehicieron en Altium los **símbolos** con los
  datos de DigiKey; las **huellas** no se tocaron. No están hechas con el IPC Compliant Footprint Wizard.

## Tareas, en orden

1. **UART de depuración en el esquemático.**
   - USART1: TX en PB6 (pin 43) y RX en PB7 (pin 44).
   - El LED de heartbeat pasa de PB6 a PB9 (pin 46, mismo lado del LQFP).
   - Header nuevo J7 1x4 BOOMELE de 2,54 mm: 1 V3V3_MCU (referencia), 2 TX del MCU, 3 RX del MCU, 4 GND.
   - Verificar las funciones alternativas en CubeMX (PB6 = USART1_TX AF7, PB7 = USART1_RX AF7).
   - Crear el símbolo `CONN - BOOMELE 2.54-1x04` y su huella.
   - La programación sigue por SWD.
   - Alternativa si J7 no cabe: USART3 con TX en PB9 y RX en PB11, moviendo FOC_CS4 a PB12 (pin 26, al lado del 25).
2. **Esquemático jerárquico con hoja superior de módulos.**
   - Bloques: módulo de poder (01), MCU (02), sensores (03), comunicaciones (SPI de entrada por J1, SWD y UART de
     depuración), y 4 salidas SPI a los FOC (`Repeat` o 4 bloques).
   - Pasos:
     - Puertos en cada hoja hija y entradas de hoja cableadas en la superior.
     - Alcance de red jerárquico.
     - Comparar la netlist aplanada con la actual: debe quedar idéntica, salvo lo de la tarea 1.
   - Al cambiar la jerarquía cambian los Unique ID de todos los componentes. Hay que re-enlazarlos con la placa
     (*Project » Component Links* o un script que ajuste `SourceUniqueId`) antes del Update PCB, para no perder la
     colocación ni el ruteo.
3. **Placa.**
   - Update PCB y reponer las clases de red con `Placa.pas` (`ClasesDeRed`).
   - Colocar y rutear J7.
   - Rutear el LED desde PB9.
4. **Serigrafía por encima de los mínimos de JLCPCB.**
   - Revisar en la página de capacidades de JLCPCB los valores exactos (≈ 0,15 mm de línea y 1,0 mm de alto de texto).
   - Hoy hay 317 trazos de 0,10–0,12 mm (líneas de las huellas) y 55 de 56 designadores de 0,8 mm.
   - Ensanchar las líneas, agrandar los designadores y reubicar u ocultar los que choquen.
   - DRC completo en 0 (incluye silk a máscara y silk a silk).
5. **Regenerar `fabricacion/`.**
   - Gerber, taladro y Pick & Place con `Fabricacion.OutJob`.
   - Zip para JLCPCB con `jlcpcb.py`. Reemplaza el zip de la raíz y el de `fabricacion/`.
   - **BOM con DigiKey:** MPN y código DigiKey de `generadores/digikey/metadatos_digikey.tsv`, LCSC como segundo
     proveedor, más J7. El de hoy es LCSC y tiene 3 MPN obsoletos.
   - Volver a revisar los Gerber: taladro contra pads, plano GND y serigrafía.
6. **Regenerar `esquematicos/`.**
   - PDF del esquemático completo, hoja superior incluida.
   - PNG por hoja y de la placa: los actuales son del 30/10.
7. **ActiveBOM** (`.BomDoc`) con DigiKey como proveedor favorito, como en el proyecto del profesor.
8. **Huellas con el IPC Compliant Footprint Wizard** (método del ramo).
   - Rehacerlas desde las hojas de datos de DigiKey; J1, J2 y J7 con la huella de pin header del profesor.
   - Si cambian los pads, re-verificar el ruteo y el DRC.
   - Decidir en grupo si entra en esta entrega, porque toca la placa.
9. **Documento de diseño v6, solo a nivel de sistema.** Se parte de `Documento_de_Diseno_ELO301_Grupo1_v5.docx`
   (Descargas) y se exporta a PDF en `docs/`. Cambios:
   - BOM y costos con DigiKey (Tablas 3, 7 y 8).
   - Capacitores reemplazados.
   - Cristal ABM8-25.000MHZ-10-D1G-T con 2 × 12 pF.
   - L2 LQW18AN47NJ00D.
   - Tira BOOMELE.
   - 4 M3.
   - UART de depuración (Tabla 9: PB6/PB7, LED en PB9).
   - Diagrama de módulos de la hoja superior.
   - Fila de revisión v6.
10. **README.**
    - Quitar el pendiente de coordinar H3/H4 con la motherboard (no hay equipo de motherboard).
    - Actualizar estado, hojas, salidas y pendientes.
    - Retirar o actualizar `ELO301_G1_Altium_por_etapas.zip`.
11. **Git:** rama nueva, commit, push y PR, como en el PR #1.
