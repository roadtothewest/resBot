# Tareas pendientes (08/11/2026)

## Para retomar en otra sesión u otro PC

- **Rama:** `git checkout elo301-entrega`.
- **Instrucción para Claude:** «lee ELO301_Modulo_Control_Secundario/TAREAS.md y el README, y sigue con el pendiente 1».
- **Scripts de Altium:**
  - Los de `generadores/digikey/` se corren con `correr.ps1 -Script Placa -Proc <proc>`. `RUTA_BASE` está fija en
    `Placa.pas` y `Simbolos.pas`: hay que ajustarla a la carpeta del repo en el PC nuevo.
  - Los de `generadores/pcb/`, `jerarquia/`, `serigrafia/completar.py` y `digikey/activebom.py` usan altium-mcp desde
    la VM (`generadores/pcb/drc_comun.py`).
- **Scripts de Python:** necesitan `pip install olefile shapely matplotlib lxml`.
- **Altium:** no cerrarlo a la fuerza, porque bloquea la licencia. Si un script queda detenido en el depurador, hay que
  usar Run › Stop.

## Hecho

- **04/11:**
  - UART de depuración J9 (PR #2), corrido fuera de la zona del tornillo de H1.
  - Serigrafía sobre los mínimos de JLCPCB y 3 vías tapadas.
  - BOM con DigiKey y salidas regeneradas.
- **08/11:** detalle en el README, sección «Cambios del 08/11/2026».
  - **Esquemático jerárquico:**
    - Hoja superior `00_Modulos` con PODER, MCU, SENSORES y CONECTORES.
    - Puertos en las hojas hijas y alcance de red jerárquico.
    - Netlist idéntica a la plana y ERC con 0 errores.
    - Placa re-enlazada a los Unique ID nuevos.
  - **Símbolo del 1x04:** pasa a llamarse `BOOMELE 2.54-1x04`.
  - **Serigrafía completa:**
    - Todos los designadores visibles, con línea guía donde no caben junto a su pieza.
    - Nombre de cada módulo y separadores.
    - Pad a serigrafía de 0,15 mm o más, línea de 0,18 mm, texto de 1,0 mm o más. DRC 0.
  - **ActiveBOM:** `altium/ELO301_G1.BomDoc`, con DigiKey como primera opción de compra.
  - **Salidas regeneradas:**
    - `esquematicos/`: PDF de 5 hojas y PNG.
    - `fabricacion/`: Gerber, zip, CPL y BOM.
    - `fabricacion/verificacion/`: Gerber contra netlist, sin abiertos ni cortos, y revisión de serigrafía.
  - **Documento de diseño v6** en `docs/` (`.docx` y PDF).
- **Huellas (antes «rehacer con el IPC Compliant Footprint Wizard»): no se rehacen.**
  - C0603 y R0603 son las del profesor.
  - Las demás coinciden con el fabricante o son compatibles (se contrastó el cobre).
  - Rehacerlas después de la serigrafía y los Gerber desharía ese trabajo.
  - **Si el grupo igual quiere la huella de pin header del profesor para J1, J2 y J9:** cambiarlas, revisar ruteo y DRC,
    y recién después volver a correr `serigrafia/completar.py` (placa y guardar) y las salidas.

## Pendiente, en orden

1. **Decidir C16** (4,7 µF, GRM188R61C475ME11J): no tiene stock en LCSC/JLCPCB. El equivalente con stock es Samsung
   CL10A475KO8NNNC (C19666, «Basic»). Si se arma en JLCPCB, hay que cambiarlo en `metadatos_digikey.tsv` y en el
   esquemático, y regenerar BOM, ActiveBOM y documento.
2. **Serigrafía heredada a 0,17 mm del borde superior:** las carcasas de J3–J6 (huella `B5B-XH-A - JST`). Pasa el DRC y
   JLCPCB no fija un mínimo, pero el resto de la placa respeta 0,2 mm. Se arregla recortando esa línea en la huella y en
   la placa.
3. **Antes de pedir:**
   - Revisar el zip en el Gerber Viewer de JLCPCB (pide cuenta).
   - Revisar las rotaciones del CPL en su vista previa de armado.
4. **ActiveBOM con conexión:** abrir `ELO301_G1.BomDoc` en Altium con internet para que complete precios y stock de
   DigiKey (sin conexión solo guarda los códigos).
5. **CubeMX:** regenerar las Ilustraciones 3 y 4 del documento con USART1 en PB6/PB7 y el LED en PB9. Hoy son las de la
   revisión 1.3, y el documento lo aclara.
6. **Clases de red:** el ECO propone quitar `Potencia` y `Alimentacion` porque solo existen en la placa. Desmarcarlo en
   cada *Update PCB* o reponerlas con `generadores/pcb/clases_red.py`.
7. **`metadatos_digikey.tsv`:** la fila de los M3 lista H1 y H2; faltan H3 y H4. No afecta la BOM, que los excluye.
8. **`ELO301_G1_Altium_por_etapas.zip`:** actualizarlo o retirarlo, porque ya no es la versión vigente.
