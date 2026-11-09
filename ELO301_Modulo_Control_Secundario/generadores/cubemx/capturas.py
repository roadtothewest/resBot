"""Ilustraciones 3 y 4 del documento desde STM32CubeMX: vista de pines y System view de ELO301_G1.ioc.

Abre CubeMX en un Xvfb de 2400x2000 (sin gestor de ventanas) con la interfaz a 2x, agranda la ventana a toda la
pantalla, captura la vista de pines, pasa a «System view» y la captura (System Core, Analog, Timers y Connectivity,
como en la revisión 1.3). Recorta lo que no es fondo blanco y lo deja en las proporciones de las figuras del documento
(952x942 y 1188x520). Probado con CubeMX 6.18.1; la primera vez que se abre CubeMX hay que dejar
que arme la base de paquetes (abrirlo sin proyecto), o no carga el .ioc.
Uso: python3 capturas.py <carpeta de CubeMX (la que tiene STM32CubeMX)> <carpeta destino>
"""
import os, subprocess, sys, time
from PIL import Image, ImageOps

AQUI = os.path.dirname(os.path.abspath(__file__))
PINES = (540, 380, 2340, 1820)  # dentro del marco de la vista de pines (ventana de 2400x2000, interfaz a 2x)
COLUMNAS = (548, 700, 1725, 1290)  # System view: las 4 primeras categorías
SISTEMA = (1580, 324)  # pestaña «System view»


def xdo(*a):
    return subprocess.run(['xdotool', *a], capture_output=True, text=True, env=ENV).stdout.strip()


def foto(nombre, tam, zona):
    p = os.path.join(DEST, nombre)
    subprocess.run(['import', '-window', 'root', p], check=True, env=ENV)
    im = ImageOps.expand(Image.open(p).convert('RGB').crop(zona), 20, fill='white')  # margen sin salirse (PIL rellena con negro)
    caja = ImageOps.invert(im.convert('L').point(lambda v: 255 if v > 245 else 0)).getbbox()  # lo que no es blanco
    im = im.crop((caja[0] - 20, caja[1] - 20, caja[2] + 20, caja[3] + 20))
    w, h = im.size; r = tam[0] / tam[1]  # se completa con blanco hasta la proporción de la figura y se escala
    W, H = (max(w, round(h * r)), max(h, round(w / r)))
    lienzo = Image.new('RGB', (W, H), 'white'); lienzo.paste(im, ((W - w) // 2, (H - h) // 2))
    lienzo.resize(tam, Image.LANCZOS).save(p, optimize=True)
    print(nombre, 'recorte', (w, h), '->', tam)


if __name__ == '__main__':
    MX, DEST = sys.argv[1], sys.argv[2]
    os.makedirs(DEST, exist_ok=True)
    ENV = dict(os.environ, DISPLAY=':59')
    x = subprocess.Popen(['Xvfb', ':59', '-screen', '0', '2400x2000x24'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    mx = subprocess.Popen(['java', '-Dsun.java2d.uiScale=2', '-jar', 'STM32CubeMX', os.path.join(AQUI, 'ELO301_G1.ioc')], cwd=MX, env=ENV,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(30):
            time.sleep(5); w = xdo('search', '--name', 'STM32CubeMX ELO301_G1.ioc')
            if w: break
        else: sys.exit('CubeMX no abrió el .ioc')
        w = w.split()[0]; xdo('windowmove', w, '0', '0'); xdo('windowsize', w, '2400', '2000')
        for u in xdo('search', '--name', 'User Preferences').split(): xdo('windowunmap', u)  # queda en blanco en Xvfb
        time.sleep(6); foto('cubemx_pinout.png', (952, 942), PINES)
        xdo('mousemove', *map(str, SISTEMA), 'click', '1'); time.sleep(5); foto('cubemx_system.png', (1188, 520), COLUMNAS)
    finally:
        mx.terminate(); x.terminate()
