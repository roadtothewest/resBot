"""Página real de cada entrada del índice en el PDF exportado -> paginas.json"""
import json, re, subprocess, sys
pdf = sys.argv[1]
n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
pag = [subprocess.run(['pdftotext', '-f', str(i), '-l', str(i), '-layout', pdf, '-'], capture_output=True, text=True).stdout for i in range(1, n + 1)]
ini = next(i for i, s in enumerate(pag) if 'Índice general' in s)
toc = ''.join(pag[ini:ini + 2])
out = {}
for t, p in re.findall(r'^\s*(.+?)\s*\.{2,}\s*(\d+)\s*$', toc, re.M) or re.findall(r'^\s*(.+?)\s{2,}(\d+)\s*$', toc, re.M):
    titulo = re.sub(r'^\d+(\.\d+)*\s+', '', t).strip()[:40]
    real = next((i + 1 for i in range(ini + 2, n) if re.search(r'^\s*(\d+(\.\d+)*\s+)?' + re.escape(titulo), pag[i], re.M)), None)
    if real: out[titulo] = real
json.dump(out, open('paginas.json', 'w'), ensure_ascii=False, indent=0)
print(n, 'páginas; índice en la', ini + 1, ';', len(out), 'entradas')
