#!/usr/bin/env python3
"""Construye una hoja de ELO301_G1 desde su generador (specs/hoja_*.py): cierra la versión anterior, llama a
build_schematic, compara cada pin con el mapa real de Altium (si alguno no calza, no guarda), guarda la hoja con su
nombre dentro del proyecto, compila y lista el ERC, y deja una captura de la hoja.
Uso: construir_hoja.py <generador.py> <Hoja.SchDoc> <captura.png> [SheetN.SchDoc ya construida]"""
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
L = 'C:\\Users\\altium\\Documents\\Altium\\ELO301_G1\\'


def mcp(tool, args=None):
    r = subprocess.run([str(AQUI / 'mcpc.py'), 'call', tool, json.dumps(args or {})],
                       capture_output=True, text=True, timeout=1200)
    return r.stdout


def script(cuerpo):
    d = json.loads(mcp('run_altium_script', {'script': cuerpo, 'timeout_seconds': 240}))
    if not d.get('success'):
        sys.exit(f'script falló: {d}')
    return d.get('result', '')


def main(generador, hoja, captura, ya_construida=None):
    sys.path.insert(0, str(Path(generador).resolve().parent))   # para que el generador encuentre hojas_comun
    spec = importlib.util.spec_from_file_location('gen', generador)
    gen = importlib.util.module_from_spec(spec)
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        spec.loader.exec_module(gen)
    args = json.loads(salida.getvalue())
    ruta = L + hoja
    script(f"if Client.IsDocumentOpen('{ruta}') then\n    Client.CloseDocument(Client.GetDocumentByPath('{ruta}'));\n"
           "ResultText := 'ok';")
    if ya_construida:                                             # hoja ya construida y verificada antes
        r = {'sheet': ya_construida}
    else:
        r = json.loads(mcp('build_schematic', args))
        print({k: v for k, v in r.items() if k not in ('pin_map', 'pin_map_note')})
        if not r.get('success') or r.get('missing_parts'):
            sys.exit('build_schematic no terminó bien; no se guarda nada')
        malos = []
        for des, (sim, *_) in gen.pos.items():
            reales = {tuple(v) for v in r['pin_map'].get(des, {}).values()}
            omitir = gen.REPETIDOS.get(sim, set())   # nombres repetidos o vacíos: el pin_map guarda uno solo
            malos += [(des, pin, gen.P(des, pin)) for pin in gen.PINES[sim]
                      if pin not in omitir and gen.P(des, pin) not in reales]
        if malos:
            sys.exit(f'pines que no calzan (la hoja {r["sheet"]} queda abierta sin guardar): {malos}')
        print('pines: todos calzan con el mapa real')
    # Guardar la hoja nueva con un nombre temporal y copiarla sobre la del proyecto (cerrada): si se guarda
    # directo con la ruta de un documento del proyecto, Altium la adopta como una entrada repetida más.
    tmp = 'C:\\Users\\Public\\_tmp_hoja.SchDoc'      # fuera de la carpeta del proyecto
    print(script(f"""var
    Modulo, SD, Cand : IDispatch;
    k : Integer;
SD := nil;
Modulo := Client.ServerModuleByName('SCH');
for k := 0 to Modulo.DocumentCount - 1 do
begin
    Cand := Modulo.Documents[k];
    if Cand.FileName = '{r['sheet']}' then SD := Cand;
end;
if SD <> nil then
begin
    SD.SetFileName('{tmp}');
    SD.DoFileSave('');
    Client.CloseDocument(SD);
    GetWorkspace.DM_FocusedProject.DM_RemoveSourceDocument('{tmp}');   // por si Altium lo adoptó
    ResultText := 'temporal guardada';
end
else
    ResultText := 'NO encontré {r['sheet']}';"""))
    subprocess.run([str(AQUI / 'qga.py'), f"Copy-Item '{tmp}' '{ruta}' -Force; Remove-Item '{tmp}'"],
                   check=True, capture_output=True, timeout=120)
    print(script(f"OpenSchDoc('{ruta}');\nResultText := 'guardada como {hoja}';"))
    erc = json.loads(mcp('get_erc_violations'))
    print('ERC:', {k: erc.get(k) for k in ('errors', 'warnings')})
    for v in erc.get('violations', []):
        print('  -', v.get('level'), v.get('type'), '|', v.get('detail'))
    subprocess.run(['python3', '-c', "import os,socket,time; m=socket.socket(socket.AF_UNIX); "
                    "m.connect(f'/tmp/altium-mon-{os.getuid()}.sock'); m.sendall(b'sendkey ctrl-pgdn\\n'); time.sleep(2)"])
    for f in Path('/tmp').glob('mcpc_*.png'):
        f.unlink()
    mcp('get_screenshot', {'view_type': 'sch'})
    img = next(Path('/tmp').glob('mcpc_*.png'), None)
    if img:
        subprocess.run(['convert', str(img), '-crop', '1560x880+300+40', '-resize', '80%', captura], check=True)
        print('captura:', captura)


if __name__ == '__main__':
    main(*sys.argv[1:5])
