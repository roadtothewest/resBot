"""Agrega al diagrama de bloques la UART de depuración (J9) y actualiza a 31 E/S. Uso: bloques_v6.py entrada.png salida.png"""
import sys
from PIL import Image, ImageDraw, ImageFont
im = Image.open(sys.argv[1]).convert('RGB'); d = ImageDraw.Draw(im)
F = im.width / 1400
def p(*v): return [round(x * F) for x in v]
FONT = '/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf'
reg = ImageFont.truetype(FONT % 'Regular', round(11.6 * F)); neg = ImageFont.truetype(FONT % 'Bold', round(13.2 * F))
neg2 = ImageFont.truetype(FONT % 'Bold', round(14 * F))
col = lambda x, y: im.getpixel((round(x * F), round(y * F)))
MCU, CONN_F, CONN_B, EXT_F, EXT_B = col(620, 600), col(930, 560), col(916, 547), col(1120, 560), col(1108.5, 547)
UART = col(762.5 + 8, 455)
BLANCO = col(830, 610)
def caja(x0, y0, x1, y1, f, b, l1, l2):
    d.rounded_rectangle(p(x0, y0, x1, y1), radius=round(5 * F), fill=f, outline=b, width=round(2.2 * F))
    cx, cy = (x0 + x1) / 2 * F, (y0 + y1) / 2 * F
    d.text((cx, cy - 8.5 * F), l1, font=reg, fill='black', anchor='mm'); d.text((cx, cy + 8.5 * F), l2, font=reg, fill='black', anchor='mm')
def flecha(x0, x1, y, etiqueta=None):
    d.line(p(x0, y, x1, y), fill=UART, width=round(3 * F))
    for x, s in ((x0, 1), (x1, -1)):
        d.polygon([(x * F, y * F), ((x + s * 8) * F, (y - 4) * F), ((x + s * 8) * F, (y + 4) * F)], fill=UART)
    if etiqueta:
        w = neg.getlength(etiqueta) / F + 8; c = (x0 + x1) / 2
        d.rectangle(p(c - w / 2, y - 9, c + w / 2, y + 9), fill=BLANCO)
        d.text((c * F, y * F), etiqueta, font=neg, fill=UART, anchor='mm')
Y0, Y1 = 586, 631; YM = (Y0 + Y1) / 2
flecha(761, 915, YM, 'USART1 (2)')
caja(916, Y0, 1058, Y1, CONN_F, CONN_B, 'Conector UART (banco)', 'Header 2,54 mm 1×4 (J9)')
flecha(1059, 1107, YM)
caja(1108, Y0, 1273, Y1, EXT_F, EXT_B, 'Adaptador USB-UART', '(banco de pruebas)')
d.rectangle(p(610, 476, 740, 494), fill=MCU)
d.text((675 * F, 485 * F), '31 E/S utilizadas', font=neg2, fill='black', anchor='mm')
im.save(sys.argv[2])
