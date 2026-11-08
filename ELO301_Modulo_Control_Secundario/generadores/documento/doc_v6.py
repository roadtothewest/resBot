"""Documento de diseño v6 (revisión 1.4) a partir del v5 descomprimido. Uso: doc_v6.py <dir v5> <dir salida> <BOM.csv> <precios_lcsc.json> <image2_v6.png>"""
import copy, csv, json, os, shutil, sys
from lxml import etree

v5, out, fbom, fprecios, fimg = sys.argv[1:6]
if os.path.exists(out): shutil.rmtree(out)
shutil.copytree(v5, out)
shutil.copy(fimg, os.path.join(out, 'word', 'media', 'image2.png'))
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
XS = '{http://www.w3.org/XML/1998/namespace}space'
arbol = etree.parse(os.path.join(out, 'word', 'document.xml'))
cuerpo = list(arbol.getroot().find(W + 'body'))


def texto(p):
    return ''.join(t.text or '' for t in p.iter(W + 't'))


def poner(p, nuevo, antes=None):
    """Deja el texto en el primer run (conserva su formato) y borra el texto de los demás."""
    if antes is not None: assert antes in texto(p), (antes, texto(p)[:120])
    ts = list(p.iter(W + 't'))
    assert ts, 'párrafo sin texto'
    ts[0].text = nuevo; ts[0].set(XS, 'preserve')
    for t in ts[1:]:
        r = t.getparent(); r.getparent().remove(r)


def cambiar(i, viejo, nuevo):
    p = cuerpo[i]; s = texto(p)
    assert s.count(viejo) == 1, (i, viejo, s[:150])
    poner(p, s.replace(viejo, nuevo))


filas = lambda i: cuerpo[i].findall(W + 'tr')
celdas = lambda fila: fila.findall(W + 'tc')


def celda(c, nuevo):
    ps = c.findall(W + 'p')
    for p in ps[1:]: c.remove(p)
    if list(ps[0].iter(W + 't')): poner(ps[0], nuevo)
    else:  # celda vacía: se copia un run de otra celda de la fila
        r = copy.deepcopy(next(x for x in c.getparent().iter(W + 'r') if x.find(W + 't') is not None))
        r.find(W + 't').text = nuevo; ps[0].append(r)


def fila_nueva(i, despues, valores, molde=None):
    fs = filas(i)
    f = copy.deepcopy(fs[molde if molde is not None else despues])
    for c, v in zip(celdas(f), valores): celda(c, v)
    fs[despues].addnext(f)
    return f


def fila_buscar(i, primera):
    return next(k for k, f in enumerate(filas(i)) if texto(celdas(f)[0]).strip() == primera)


num = lambda v, d=2: f'{v:,.{d}f}'.replace(',', ' ').replace('.', ',').replace(' ', '.')

# ---------- portada: fila de revisión ----------
assert texto(cuerpo[5]).strip() == '' and cuerpo[5].tag == W + 'p'
cuerpo[5].getparent().remove(cuerpo[5])  # párrafo vacío de separación: deja lugar en la portada para la fila 1.4
fila_nueva(6, len(filas(6)) - 1, ['08/11/26', '1.4', 'Grupo 1', 'UART de depuración, 4 M3 y costos DigiKey/LCSC'])

# ---------- texto ----------
fila_nueva(32, fila_buscar(32, 'Interfaz SWD'), ['Interfaz UART de depuración', 'Consola serie para el banco de pruebas (USART1, header J9).'])
cambiar(36, '(29 en total)', '(31 en total)')
t2 = 40
k = fila_buscar(t2, 'Oscilador → MCU')
celda(celdas(filas(t2)[k])[3], 'Cristal ABM8-25.000MHZ-10-D1G-T de 25 MHz (HSE, CL = 10 pF) con 2 × 12 pF C0G; ruteo corto con anillo de GND; 2 pines')
k = fila_buscar(t2, 'GPIO_LED')
celda(celdas(filas(t2)[k])[3], 'LED de encendido (en el riel) y LED heartbeat en PB9; 1 pin')
fila_nueva(t2, fila_buscar(t2, 'SWD'), ['UART_DBG (banco de pruebas)', 'UART', 'MCU ↔ PC por adaptador USB-UART',
                                         'USART1 (PB6 TX, PB7 RX) en un header 1×4 de 2,54 mm (J9: 3,3 V, TX, RX, GND); 2 pines'])
cambiar(48, '29 pines de E/S (Tabla 4)', '31 pines de E/S (Tabla 4)')
cambiar(48, 'Se usa un cristal de 25 MHz (ABM8)', 'Se usa un cristal de 25 MHz (ABM8-25.000MHZ-10-D1G-T, CL = 10 pF, con dos capacitores de 12 pF C0G)')
cambiar(50, 'a través de un inductor de 47 nH hacia RF_IN', 'a través de un inductor bobinado de 47 nH (Murata LQW18AN47NJ00D, de mayor Q que uno multicapa) hacia RF_IN')
cambiar(55, 'Dos perforaciones M3 con separadores evitan que el conector soporte las vibraciones.',
        'Cuatro perforaciones M3 con separadores, una en cada esquina, fijan la placa para que el conector no soporte las vibraciones.')
cambiar(57, 'No hay UART de servicio: el diagnóstico se realiza por el enlace SPI.',
        'Para el banco de pruebas se agrega una UART de depuración (USART1, PB6/PB7) en un header de 1×4 pines (J9: 3,3 V, TX, RX y GND); en vuelo, el diagnóstico se realiza por el enlace SPI.')
cambiar(57, '(encendido y heartbeat)', '(encendido y heartbeat, este último en PB9)')
t3 = 60
k = fila_buscar(t3, 'Procesamiento')
celda(celdas(filas(t3)[k])[3], 'LQFP-48: encapsulado mínimo para 31 E/S; tres SPI, FPU y aceleradores para el EKF')
k = next(k for k, f in enumerate(filas(t3)) if 'Cristal' in texto(f))
celda(celdas(filas(t3)[k])[2], 'Abracon ABM8-25.000MHZ-10-D1G-T')
celda(celdas(filas(t3)[k])[3], 'Mayor exactitud que el HSI16 interno; CL de 10 pF, con cargas de 12 pF estándar')
k = next(k for k, f in enumerate(filas(t3)) if 'Conector de antena' in texto(f))
fila_nueva(t3, k, ['Sensores', 'Inductor de antena', 'Murata LQW18AN47NJ00D', '47 nH del circuito de aplicación; bobinado, de alto Q a 1,575 GHz'])
k = next(k for k, f in enumerate(filas(t3)) if 'Expansión y SWD' in texto(f))
celda(celdas(filas(t3)[k])[1], 'Expansión, SWD y UART')
celda(celdas(filas(t3)[k])[2], 'BOOMELE 2,54-1×40P (cortada a 1×14, 1×5 y 1×4)')
cambiar(62, 'Agrupar los cuatro FOC en un bus con selección independiente y prescindir de la UART de servicio deja 29 E/S, de las 38 disponibles en LQFP-48; las 8 restantes quedan como reserva.',
        'Agrupar los cuatro FOC en un bus con selección independiente deja 31 E/S en uso, incluida la UART de depuración; quedan libres seis pines (PA11, PA12, PB12 y PC13–PC15), con PA11 y PA12 reservados para FDCAN1.')
t4 = 63
fila_nueva(t4, fila_buscar(t4, 'Arranque'), ['UART_DBG', 'USART1', 'TX, RX', '2'], molde=fila_buscar(t4, 'Arranque'))
k = fila_buscar(t4, 'Total de E/S')
celda(celdas(filas(t4)[k])[3], '31')
cambiar(76, 'del ATGM336H (USART2).', 'del ATGM336H (USART2); consola de depuración por USART1 (J9).')
cambiar(97, 'por el enlace SPI.', 'por el enlace SPI; en el banco de pruebas, también por la consola de USART1.')
cambiar(104, 'y responda una trama de prueba por el enlace SPI.', 'responda una trama de prueba por el enlace SPI y envíe un mensaje por la UART de depuración (J9).')
cambiar(137, 'La Ilustración 3 muestra los 29 pines utilizados, la Ilustración 4 los periféricos habilitados y la Tabla 9 la conexión de cada uno.',
        'La Ilustración 3 muestra la asignación de pines, la Ilustración 4 los periféricos habilitados y la Tabla 9 la conexión de cada uno. Las ilustraciones corresponden a la revisión 1.3 (29 pines); la Tabla 9 ya incluye la USART1 de depuración (PB6/PB7) y el LED heartbeat en PB9, agregados en la revisión 1.4.')
t9 = 142
fila_nueva(t9, fila_buscar(t9, 'USART2'), ['USART1', 'Asíncrono', 'PB6, PB7', 'UART de depuración (J9)'])
k = fila_buscar(t9, 'GPIO')
celda(celdas(filas(t9)[k])[2], 'PA4, PB1, PB2, PB10, PB11, PA10, PB9; PB0')

# ---------- costos (BOM de fabricación + precios LCSC por tramo) ----------
precios = json.load(open(fprecios))
def precio(lcsc, q):
    pr = (precios.get(lcsc) or {}).get('precios') or []
    for b in pr:
        if b['startNumber'] <= q and (b['endNumber'] == -1 or q <= b['endNumber']): return b['productPrice']
    return None

MODULO = {**{d: 'Módulo 1' for d in 'U4 Y1 C13 C14 C15 C16 C17 C18 C19 C20 C21 C22 C23 FB2 R4'.split()},
          **{d: 'Módulo 2' for d in 'U5 U6 J8 L2 C24 C25 C26 C27 R7 R8 R9'.split()},
          **{d: 'Módulo 3' for d in 'D1 D2 U1 L1 U2 U3 C1 C2 C3 C4 C5 C6 C7 C8 C9 C10 C11 C12 FB1 R1 R2'.split()},
          **{d: 'Otros' for d in 'J1 J2 J9 J3 J4 J5 J6 J7 SW1 SW2 LED1 LED2 R10 R11 R12 R13 R14 R15 R3 R5'.split()}}
DESC = {'STM32G431CBT6': 'Microcontrolador Cortex-M4F 170 MHz, LQFP-48', 'ABM8-25.000MHZ-10-D1G-T': 'Cristal 25 MHz, CL 10 pF, 3,2 × 2,5 mm',
        'GCM188R71H104KA57D': 'Capacitor 100 nF 50 V X7R 0603', 'GRM188R61C475ME11J': 'Capacitor 4,7 µF 16 V 0603 (bulk; sin stock en LCSC: equivalente CL10A475KO8NNNC)',
        'GCM188R71E105KA64D': 'Capacitor 1 µF 25 V X7R 0603', 'CL10C120JB8NNNC': 'Capacitor 12 pF C0G 0603 (cristal)', 'BLM18PG221SN1D': 'Ferrita 220 Ω @ 100 MHz 0603',
        'RC0603FR-0710KL': 'Resistencia 10 kΩ 0603', 'BMI270': 'IMU 6 ejes (SPI)', 'ATGM336H-5N31': 'Receptor GNSS en placa (UART + PPS)', 'U.FL-R-SMT-1(10)': 'Conector RF U.FL',
        'LQW18AN47NJ00D': 'Inductor bobinado 47 nH 0603 (VCC_RF → RF_IN)', 'GRM188R61E106MA73D': 'Capacitor 10 µF 25 V X5R 0603', 'RC0603FR-074K7L': 'Resistencia 4,7 kΩ 0603 (pull-up I2C)',
        'AP63205WU-7': 'Convertidor buck 12 V → 5 V, 2 A, 1,1 MHz', 'SRN4018-4R7M': 'Inductor 4,7 µH, 1,9 A', 'TLV75533PDBVR': 'Regulador LDO 3,3 V, 500 mA',
        'SMAJ15A-13-F': 'TVS 15 V, 400 W (entrada)', 'B240A-13-F': 'Diodo Schottky 40 V, 2 A (polaridad inversa)', 'GRM188R61A226ME15D': 'Capacitor 22 µF 10 V X5R 0603 (salida buck)',
        'RC0603FR-07100KL': 'Resistencia 100 kΩ 1 % 0603 (divisor)', 'RC0603FR-0712KL': 'Resistencia 12 kΩ 1 % 0603 (divisor)',
        'B5B-XH-A(LF)(SN)': 'Conector JST XH 5 pines, THT (FOC 1–4)', 'B4B-XH-A(LF)(SN)': 'Conector JST XH 4 pines, THT (ToF)',
        '2.54-1*40P': 'Tira de pines 2,54 mm 1×40 (expansión 1×14, SWD 1×5, UART 1×4)', 'PTS810 SJM 250 SMTR LFS': 'Pulsador SMD (NRST y BOOT0)',
        'LTST-C191KGKT': 'LED 0603 verde (encendido)', 'LTST-C191KRKT': 'LED 0603 rojo (heartbeat)', 'RC0603FR-0733RL': 'Resistencia 33 Ω 0603 (serie SPI FOC)', 'RC0603FR-071KL': 'Resistencia 1 kΩ 0603 (LED)'}
USO = {('GCM188R71H104KA57D', 'Módulo 1'): ' (desacople)', ('GCM188R71H104KA57D', 'Módulo 2'): ' (IMU y GNSS)', ('GCM188R71H104KA57D', 'Módulo 3'): ' (bootstrap y filtro ADC)',
       ('GCM188R71E105KA64D', 'Módulo 1'): ' (VDDA)', ('GCM188R71E105KA64D', 'Módulo 3'): ' (LDO)', ('BLM18PG221SN1D', 'Módulo 1'): ' (VDDA)', ('BLM18PG221SN1D', 'Módulo 3'): ' (entrada LDO de sensores)',
       ('RC0603FR-0710KL', 'Módulo 1'): ' (pull-down BOOT0)', ('RC0603FR-0710KL', 'Módulo 2'): ' (GNSS)', ('GRM188R61E106MA73D', 'Módulo 2'): ' (GNSS)', ('GRM188R61E106MA73D', 'Módulo 3'): ' (entrada buck)'}
FAB = {'Murata Electronics': 'Murata', 'Samsung Electro-Mechanics': 'Samsung', 'Diodes Incorporated': 'Diodes', 'BOOMELE(Boom Precision Elec)': 'BOOMELE', 'JST Sales America Inc.': 'JST',
       'Hirose Electric Co Ltd': 'Hirose', 'Bourns Inc.': 'Bourns', 'Lite-On Inc.': 'Lite-On', 'YAGEO': 'Yageo', 'Texas Instruments': 'Texas Instruments', 'STMicroelectronics': 'STMicroelectronics',
       'Bosch Sensortec': 'Bosch Sensortec', 'ZHONGKEWEI': 'ZKW', 'Abracon LLC': 'Abracon', 'C&K': 'C&K'}
lineas = {}
for f in csv.DictReader(open(fbom, encoding='utf-8-sig')):
    for d in f['Designator'].split(','):
        m, mpn = MODULO[d], f['Manufacturer Part Number']
        clave = (m, mpn)
        l = lineas.setdefault(clave, dict(mod=m, mpn=mpn, fab=FAB.get(f['Manufacturer'], f['Manufacturer']), dk=f['DigiKey Part Number'] or 'No disponible (LCSC)',
                                          lcsc=f['LCSC Part #'], des=[]))
        l['des'].append(d)
assert sum(len(l['des']) for l in lineas.values()) == 67 == len(MODULO), 'BOM y módulos no calzan'
orden = ['Módulo 1', 'Módulo 2', 'Módulo 3', 'Otros']
filas8, suma1, suma100 = [], dict.fromkeys(orden, 0.0), dict.fromkeys(orden, 0.0)
for m in orden:
    PRIO = ['U', 'Y', 'D', 'L', 'J', 'SW', 'LED', 'C', 'FB', 'R']  # integrados y cristal primero, pasivos al final
    pref = lambda d: d.rstrip('0123456789')
    for l in sorted([l for l in lineas.values() if l['mod'] == m], key=lambda l: (PRIO.index(pref(l['des'][0])), int(l['des'][0][len(pref(l['des'][0])):]))):
        q = 1 if l['mpn'] == '2.54-1*40P' else len(l['des'])  # una tira de 40 alcanza para J1, J2 y J9
        p1, p100 = precio(l['lcsc'], q), precio(l['lcsc'], 100 * q)
        est = p1 is None
        if est: p1, p100 = 0.05, 0.02  # C16 sin stock: estimación
        suma1[m] += q * p1; suma100[m] += 100 * q * p100
        ap = '≈ ' if est else ''
        filas8.append([m, DESC[l['mpn']] + USO.get((l['mpn'], m), ''), f"{l['fab']} {l['mpn']}", l['dk'], str(q), ap + num(p1, 3 if p1 < 0.1 else 2), ap + num(p100, 3)])
t8 = 134
fs = filas(t8)
celda(celdas(fs[0])[3], 'N.º DigiKey')
externos = [[texto(c) for c in celdas(f)] for f in fs if texto(celdas(f)[0]).strip() in ('Externo', 'Arnés')]
for f in externos: f[3] = 'Mouser ' + f[3] if f[3] not in ('—', '') else f[3]
molde = copy.deepcopy(fs[1])
for f in fs[1:]: cuerpo[t8].remove(f)
for vals in filas8 + externos:
    f = copy.deepcopy(molde)
    for c, v in zip(celdas(f), vals): celda(c, v)
    cuerpo[t8].append(f)
t7 = 130
FIJO = {'PCB': (8.00, 130.00), 'Ensamblado': (20.00, 400.00), 'Pruebas': (6.00, 80.00), 'Componentes externos': (18.89, 1331.00), 'Arnés': (5.07, 277.00), 'Transporte': (10.00, 125.00)}
DESC7 = {'Módulo 1': 'Procesamiento: STM32G431CBT6, cristal 25 MHz, desacoples y pasivos', 'Módulo 2': 'Sensores: BMI270, ATGM336H, conector U.FL, inductor de antena y pasivos',
         'Módulo 3': 'Alimentación y monitoreo: AP63205, 2 × TLV75533, TVS, diodo y pasivos (incluye divisor RC)',
         'Otros': 'Conectores JST XH, tira de pines (expansión, SWD y UART), pulsadores, LED y resistencias de interfaz'}
tot1 = sum(suma1.values()) + sum(v[0] for v in FIJO.values()); tot100 = sum(suma100.values()) + sum(v[1] for v in FIJO.values())
sin = (tot100 - FIJO['Componentes externos'][1] - FIJO['Arnés'][1]) / 100
for f in filas(t7)[1:]:
    c = celdas(f); k = texto(c[0]).strip()
    if k in suma1: celda(c[1], DESC7[k]); celda(c[2], num(suma1[k])); celda(c[3], num(suma100[k]))
    elif k in FIJO: celda(c[2], num(FIJO[k][0])); celda(c[3], num(FIJO[k][1]))
    elif k == 'Total': celda(c[2], num(tot1)); celda(c[3], num(tot100))
    elif k == 'Costo por unidad': celda(c[3], num(tot100 / 100) if 'incluida' in texto(c[1]) else num(sin))
cambiar(129, 'con precios de Mouser (octubre de 2026); el ATGM336H y la tira BOOMELE se cotizaron en LCSC.',
        'con los códigos DigiKey del proyecto (ActiveBOM) y precios de LCSC por tramo de cantidad, consultados el 03/11/2026; la antena y el arnés mantienen los precios de Mouser de octubre de 2026.')
poner(cuerpo[132], f'El costo total es de USD {num(tot100 / 100)} por unidad en un lote de 100, dentro de la meta; la PCB ensamblada, sin antena ni arnés, cuesta USD {num(sin)}. '
      'La antena activa Taoglas (USD 13,31 en volumen) es el ítem más caro; una antena genérica lo reduciría a pocos dólares.', antes='El costo total es de USD')
# índice: número de página real por título (segunda pasada, desde el PDF exportado)
import re
if len(sys.argv) > 6:
    paginas = json.load(open(sys.argv[6]))
    for i in (8, 10):
        for p in cuerpo[i].iter(W + 'p'):
            s = texto(p); m = re.match(r'^(?:\d+(?:\.\d+)*)?\s*(.+?)\s*(\d+)$', s)
            if not m: continue
            real = next((v for k, v in paginas.items() if m.group(1).startswith(k)), None)
            num_t = [t for t in p.iter(W + 't') if (t.text or '').strip().isdigit()]
            if real and num_t: num_t[-1].text = str(real)
arbol.write(os.path.join(out, 'word', 'document.xml'), xml_declaration=True, encoding='UTF-8', standalone=True)
print('módulos (1):', {k: round(v, 2) for k, v in suma1.items()}, '(100):', {k: round(v, 2) for k, v in suma100.items()})
print(f'total 1: {tot1:.2f}  total 100: {tot100:.2f}  por unidad: {tot100 / 100:.2f}  sin antena ni arnés: {sin:.2f}  filas tabla 8: {len(filas8)} + {len(externos)}')
