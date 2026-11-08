#!/usr/bin/env python3
"""Dibuja la placa desde los archivos que se mandan a fabricar, no desde Altium.

Uso: python3 render_gerber.py <zip JLCPCB> <carpeta destino>
Escribe arriba.png y abajo.png (vista real: máscara, cobre expuesto, serigrafía), capas.png (cobre de las 4 capas) y
plantilla_1a1.pdf (contorno, agujeros M3 y headers a escala 1:1, para comprobar en papel contra la motherboard).
"""
import os, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, PathPatch, Rectangle
from matplotlib.path import Path
import numpy as np
from jlcpcb import taladro
from lvs_gerber import capa, piezas
from shapely.geometry import box

W, H = 70, 50
MASCARA, COBRE_BAJO, ORO, SERI = '#0e5a3c', '#177a53', '#d9ae3c', '#f4f4f0'


def trazo(ax, g, **kw):
    for p in piezas(g):
        v, c = [], []
        for anillo in [p.exterior] + list(p.interiors):
            a = np.asarray(anillo.coords)
            v += a.tolist(); c += [Path.MOVETO] + [Path.LINETO] * (len(a) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(v, c), lw=0, **kw))


def agujeros(ax, hs, color='white'):
    for h in hs: ax.add_patch(Circle(h[:2], h[2] / 2, color=color, lw=0))


def lado(a, cu, sm, so, hs, salida, espejo):
    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    ax.add_patch(Rectangle((0, 0), W, H, color=MASCARA, lw=0))
    c = capa(a[cu]); m = capa(a[sm]); s = capa(a[so])
    trazo(ax, c, color=COBRE_BAJO)
    trazo(ax, c.intersection(m), color=ORO)
    trazo(ax, s.difference(m).intersection(box(0, 0, W, H)), color=SERI)
    agujeros(ax, hs, '#1b1b1b')
    ax.set_xlim(W, 0) if espejo else ax.set_xlim(0, W)
    ax.set_ylim(0, H); ax.set_aspect('equal'); ax.axis('off')
    fig.subplots_adjust(0, 0, 1, 1); fig.savefig(salida); plt.close(fig)


def capas(a, hs, salida):
    fig, ejes = plt.subplots(2, 2, figsize=(10, 7.4), dpi=220)
    titulos = [('GTL', 'Capa 1: Top'), ('G2L', 'Capa 2: plano GND'), ('G3L', 'Capa 3: Señal-Potencia + GND'), ('GBL', 'Capa 4: Bottom')]
    for ax, (e, t) in zip(ejes.flat, titulos):
        ax.add_patch(Rectangle((0, 0), W, H, color='#f1f1ee', lw=0))
        trazo(ax, capa(a[e]), color='#b4532a')
        agujeros(ax, hs)
        ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect('equal'); ax.set_title(t, fontsize=10); ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout(); fig.savefig(salida); plt.close(fig)


def plantilla(hs, salida):
    """Vista desde arriba, a escala 1:1: figura en pulgadas exactas, sin márgenes."""
    M = 12  # mm de margen para cotas
    fig = plt.figure(figsize=((W + 2 * M) / 25.4, (H + 2 * M + 14) / 25.4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(-M, W + M); ax.set_ylim(-M - 14, H + M); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Rectangle((0, 0), W, H, fill=False, lw=.8))
    for h in hs:
        if not h[3]:  # M3
            ax.add_patch(Circle(h[:2], h[2] / 2, fill=False, lw=.7))
            ax.plot([h[0] - 3, h[0] + 3], [h[1], h[1]], 'k', lw=.3); ax.plot([h[0], h[0]], [h[1] - 3, h[1] + 3], 'k', lw=.3)
            izq = h[0] < W / 2
            ax.text(h[0] + (3.4 if izq else -3.4), h[1] + 0.3, f'({h[0]:.1f} ; {h[1]:.1f})'.replace('.', ','), ha='left' if izq else 'right', va='bottom', fontsize=5)
        elif h[2] >= 0.9:
            ax.add_patch(Circle(h[:2], h[2] / 2, fill=False, lw=.3))
    ax.text(35, 5.0, 'J1 (cara inferior)', ha='center', fontsize=5.5)
    ax.text(62.6, 19, 'J2 SWD', ha='right', va='center', fontsize=5.5)
    ax.text(0, -2.2, 'Origen (0 ; 0): esquina inferior izquierda, vista desde arriba. Cotas en mm.', fontsize=5.5, va='top')
    ax.plot([0, 50], [-9, -9], 'k', lw=.8); ax.plot([0, 0], [-10, -8], 'k', lw=.8); ax.plot([50, 50], [-10, -8], 'k', lw=.8)
    ax.text(25, -8.4, 'Esta barra debe medir 50 mm al imprimir', ha='center', fontsize=5.5, va='bottom')
    fig.savefig(salida); plt.close(fig)


def main(zp, destino):
    z = zipfile.ZipFile(zp)
    a = {os.path.splitext(n)[1][1:].upper(): z.read(n).decode('latin-1') for n in z.namelist()}
    hs = taladro(a['TXT'])
    os.makedirs(destino, exist_ok=True)
    lado(a, 'GTL', 'GTS', 'GTO', hs, os.path.join(destino, 'arriba.png'), False)
    lado(a, 'GBL', 'GBS', 'GBO', hs, os.path.join(destino, 'abajo.png'), True)
    capas(a, hs, os.path.join(destino, 'capas.png'))
    plantilla(hs, os.path.join(destino, 'plantilla_1a1.pdf'))
    print(sorted(os.listdir(destino)))


if __name__ == '__main__':
    main(*sys.argv[1:3])
