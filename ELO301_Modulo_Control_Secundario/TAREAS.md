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
- **Salidas de `fabricacion/` regeneradas (04/11):**
  - Gerber, taladro, Pick & Place, zip para JLCPCB y CPL con las 67 piezas.
  - BOM con DigiKey (`generadores/digikey/bom_digikey.py`), con los LCSC verificados contra JLCPCB.
  - La regla Silk To Solder Mask quedó en 0,15 mm.
  - Se taparon las 3 vías del PR #2.
  - En el esquemático volvieron los «Description» de la hoja 02 y se corrigió la descripción del J9.
- **Decidir C16** (4,7 µF, GRM188R61C475ME11J): no tiene stock en LCSC/JLCPCB. El equivalente con stock es Samsung
  CL10A475KO8NNNC (C19666, «Basic»). Si se arma en JLCPCB, hay que cambiarlo en `metadatos_digikey.tsv` y en el
  esquemático.

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
2. **Regenerar `esquematicos/`.**
   - PDF del esquemático completo, hoja superior incluida.
   - PNG por hoja y de la placa.
3. **Detalle del PR #2:** el símbolo `BOOMELE_HDR_1X04_J7` no sigue el formato de nombre `BOOMELE 2.54-1x04`.
4. **ActiveBOM** (`.BomDoc`) con DigiKey como proveedor favorito, como en el proyecto del profesor.
5. **Huellas con el IPC Compliant Footprint Wizard** (método del ramo).
   - Hoy son las convertidas desde KiCad.
   - J1, J2 y J9 deberían usar la huella de pin header del profesor.
   - Si cambian los pads, hay que re-verificar el ruteo y el DRC.
6. **Documento de diseño v6, solo a nivel de sistema.** Se parte de `Documento_de_Diseno_ELO301_Grupo1_v5.docx`
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
7. **README.**
   - Actualizar estado, hojas, salidas y pendientes cuando se regeneren las salidas.
   - Retirar o actualizar `ELO301_G1_Altium_por_etapas.zip`.
