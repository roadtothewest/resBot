"""Compara la serigrafía guardada en los .PcbLib con huellas_plan.tsv (mismo marco: coordenadas del archivo).
huellas_antes.tsv es el volcado (VolcarHuellas) hecho antes de aplicar el plan.
Uso: verificar_huellas.py ELO301_G1.PcbLib "C0603 - MURATA.PcbLib" "R0603 - YAGEO.PcbLib" (las tres juntas)."""
import os, struct, sys
from collections import defaultdict, Counter
import olefile

U = 1e-4 * 0.0254
NSUB = {1: 1, 2: 6, 3: 1, 4: 1, 5: 2, 6: 1, 11: 2, 12: 3}
base = os.path.join(os.environ['TEMP'], 'altium_simbolos')
libs = sys.argv[1:4]


def seda_archivo(ruta):
    ole = olefile.OleFileIO(ruta)
    out = {}
    for e in ole.listdir():
        if len(e) != 2 or e[1] != 'Data' or e[0] in ('Library', 'FileVersionInfo'):
            continue
        d = ole.openstream(e).read()
        n = struct.unpack_from('<I', d, 0)[0]
        nombre = d[4:4 + n].split(b'\0')[0].decode('latin-1')
        nombre = nombre[1:] if nombre and ord(nombre[0]) == len(nombre) - 1 else nombre
        i, seda = 4 + n, []
        while i + 5 <= len(d):
            t = d[i]; i += 1
            subs = []
            try:
                for _ in range(NSUB.get(t, 1)):
                    m = struct.unpack_from('<I', d, i)[0]; i += 4; subs.append(d[i:i + m]); i += m
            except struct.error:
                break
            if t == 4 and subs[0][0] in (33, 34):
                x1, y1, x2, y2, w = struct.unpack_from('<iiiii', subs[0], 13)
                a, b = (round(x1 * U * 1e4), round(y1 * U * 1e4)), (round(x2 * U * 1e4), round(y2 * U * 1e4))
                seda.append((min(a, b), max(a, b), round(w * U * 1e4)))
        out[e[0]] = (nombre, seda)
    return out


orden = []
for l in open(os.path.join(base, 'huellas_antes.tsv'), encoding='latin-1'):
    c = l.rstrip('\r\n').split('\t')
    if c[0] == 'FP':
        orden.append((int(c[1]), c[2]))
esperado = defaultdict(list)
for l in open(os.path.join(base, 'huellas_plan.tsv')):
    c = [int(v) for v in l.split('\t')]
    clave = [k for k in orden if k[0] == c[0]][c[1]]
    for j in range(c[7]):
        x1, y1, x2, y2 = c[8 + 4 * j: 12 + 4 * j]
        a, b = (x1, y1), (x2, y2)
        esperado[clave].append((min(a, b), max(a, b), 1800))


def igual(s, t):
    return all(abs(s[0][k] - t[0][k]) <= 30 and abs(s[1][k] - t[1][k]) <= 30 for k in (0, 1)) and abs(s[2] - t[2]) <= 2


malas, total, anchos = 0, 0, Counter()
for li, ruta in enumerate(libs):
    arch = seda_archivo(ruta)
    por_nombre = {v[0]: v[1] for v in arch.values()}
    for (l, nombre) in [k for k in orden if k[0] == li]:
        h = por_nombre.get(nombre)
        if h is None:
            print('  no encontrada en el archivo:', nombre, sorted(por_nombre)[:5]); malas += 1; continue
        e = esperado[(l, nombre)]
        total += len(h); anchos.update(t[2] for t in h)
        faltan = [s for s in e if not any(igual(s, t) for t in h)]
        sobran = [t for t in h if not any(igual(s, t) for s in e)]
        if faltan or sobran or len(e) != len(h):
            malas += 1
            print(f'  {nombre}: esperadas {len(e)}, hay {len(h)}, faltan {len(faltan)}, sobran {len(sobran)}')
print(f'huellas distintas al plan: {malas}; líneas de serigrafía en los archivos: {total}; anchos (0,1 µm): {dict(anchos)}')
