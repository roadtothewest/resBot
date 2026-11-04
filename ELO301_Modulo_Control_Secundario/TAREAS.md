# Tareas pendientes para la entrega (04/11/2026)

Rama: `elo301-entrega`. Altium queda abierto (X2.EXE). No cerrarlo a la fuerza: bloquea la licencia.

## Hecho

- **UART de depuración (PR #2, b0ingkid):**
  - TX en PB6 y RX en PB7 (USART1). El LED de heartbeat pasa a PB9.
  - Header J9 1x4 BOOMELE: 1 V3V3_MCU, 2 TX, 3 RX, 4 GND.
  - La programación sigue por SWD: J2 1x5 y también J1.
- **J9 fuera de la zona del tornillo de H1:** su courtyard se metía 1,33 mm en el radio de 3,45 mm de la M3.
  - Se corrió 1,45 mm a la derecha y se ajustaron sus pistas en Bottom.
  - VIN_12V en Top ahora pasa por fuera del J9.
- **Serigrafía sobre los mínimos de JLCPCB** (línea 0,15 mm, texto 1,0 mm, pad a serigrafía 0,15 mm):

  | | Valor actual |
  |---|---|
  | Líneas | 0,18 mm |
  | Distancia al cobre de los pads | 0,2 mm o más |
  | Designadores y texto de la cara inferior | 1,2 mm con trazo de 0,2 mm (1:6) |

  - 61 designadores visibles. Ocultos: C6, C12, C19, C25, J4 y R13, que no caben sin pisar algo o sin quedar más
    cerca de otra pieza del mismo tipo, más H1–H4, a propósito.
  - Las huellas de las tres bibliotecas quedaron igual que en la placa.
- **DRC: 0 violaciones.** Sin choques de courtyard.

## Pendiente, en orden

1. **Esquemático jerárquico con hoja superior de módulos.**
   - Bloques:
     - Módulo de poder (01).
     - MCU (02).
     - Sensores (03).
     - Comunicaciones: SPI de entrada por J1, SWD y UART de depuración.
     - 4 salidas SPI a los FOC, con `Repeat` o 4 bloques.
   - Pasos:
     - Puertos en cada hoja hija y entradas de hoja cableadas en la superior.
     - Alcance de red jerárquico.
     - Comparar la netlist aplanada con la actual: debe quedar idéntica.
   - Al cambiar la jerarquía cambian los Unique ID de todos los componentes. Antes del Update PCB hay que re-enlazarlos
     con la placa, con *Project » Component Links* o con un script que ajuste `SourceUniqueId`.
2. **Regenerar `fabricacion/`.** Hoy sigue siendo la del 01/11, sin UART ni la serigrafía nueva.
   - Gerber, taladro y Pick & Place con `Fabricacion.OutJob`.
   - Zip para JLCPCB con `jlcpcb.py`. Reemplaza el zip de la raíz y el de `fabricacion/`.
   - **BOM con DigiKey:** MPN y código DigiKey de `generadores/digikey/metadatos_digikey.tsv`, LCSC como segundo
     proveedor, y J9. El BOM de hoy es de LCSC y tiene 3 MPN obsoletos.
   - Volver a revisar los Gerber: taladro contra pads, plano GND y serigrafía.
3. **Regenerar `esquematicos/`.**
   - PDF del esquemático completo, hoja superior incluida.
   - PNG por hoja y de la placa.
4. **Detalles del PR #2:**
   - La descripción del J9 dice «cortada a 1x5».
   - El nombre del símbolo `BOOMELE_HDR_1X04_J7` no sigue el formato `BOOMELE 2.54-1x04`.
   - En la hoja 02_MCU, 19 componentes perdieron el parámetro «Description». Volver a correr
     `correr.ps1 -Proc ActualizarEsquematico`.
5. **Regla Silk To Solder Mask:** subirla a mano de 0,1 a 0,15 mm en *Design » Rules*.
   - Así el DRC exige los 0,2 mm al cobre que ya cumple la placa.
   - La API de scripts no expone el valor de esta regla.
6. **ActiveBOM** (`.BomDoc`) con DigiKey como proveedor favorito, como en el proyecto del profesor.
7. **Huellas con el IPC Compliant Footprint Wizard** (método del ramo).
   - Hoy son las convertidas desde KiCad.
   - J1, J2 y J9 deberían usar la huella de pin header del profesor.
   - Si cambian los pads, hay que re-verificar el ruteo y el DRC.
8. **Documento de diseño v6, solo a nivel de sistema.** Se parte de `Documento_de_Diseno_ELO301_Grupo1_v5.docx`
   (Descargas) y se exporta a PDF en `docs/`. Cambios:
   - BOM y costos con DigiKey (Tablas 3, 7 y 8).
   - Capacitores reemplazados.
   - Cristal ABM8-25.000MHZ-10-D1G-T con 2 × 12 pF.
   - L2 LQW18AN47NJ00D.
   - Tira BOOMELE.
   - 4 M3.
   - UART de depuración (Tabla 9: PB6/PB7, LED en PB9).
   - Diagrama de módulos.
   - Fila de revisión v6.
9. **README.**
   - Actualizar estado, hojas, salidas y pendientes cuando se regeneren las salidas.
   - Retirar o actualizar `ELO301_G1_Altium_por_etapas.zip`.
