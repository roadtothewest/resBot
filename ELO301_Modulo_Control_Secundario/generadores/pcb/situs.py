"""Corre Situs (Route All) con la estrategia indicada y espera su mensaje de término. Uso: situs.py [Cleanup]"""
import json, os, re, socket, subprocess, sys, time
sys.path.insert(0, '/mnt/sda3/vms/altium')
from construir_hoja import mcp, L

def ocr():
    m = socket.socket(socket.AF_UNIX); m.connect(f'/tmp/altium-mon-{os.getuid()}.sock')
    m.sendall(b'screendump /tmp/sd.ppm\n'); time.sleep(2); m.close()
    return subprocess.run(['tesseract', '/tmp/sd.ppm', '-', '--psm', '11'], capture_output=True, text=True).stdout

def situs(estrategia=None, bloquear=False):
    d = json.loads(mcp('run_altium_script', {'script': f"""Obj1 := Client.OpenDocument('PCB', '{L}ELO301_G1.PcbDoc'); Client.ShowDocument(Obj1);
try GetWorkspace.DM_MessagesManager.ClearMessages; except end;
ResultText := 'ok';""", 'timeout_seconds': 120}))
    if not d.get('success'):
        sys.exit(f'no se pudo preparar: {d}')
    subprocess.run(['./teclas.py', 'esc', '1'])
    # menú Route > Auto Route > All... con clics reales en un solo proceso (el teclado depende del foco, que roba el panel Messages flotante)
    print(subprocess.run(['./boton.sh', 'Route>Auto Route>All...', 'ELO301_G1.PrjPcb - Altium Designer Professional (26.11.1)', 'menu'], capture_output=True, text=True).stdout.strip())
    time.sleep(4)
    t = ocr()
    if 'Route All' not in t and 'Strateg' not in t:
        sys.exit('no se abrió «Situs Routing Strategies»: ' + ' '.join(t.split())[:300])
    if bloquear:    # «Lock All Pre-routes» (sin marcar por omisión): Situs no toca lo ya ruteado
        print(subprocess.run(['./boton.sh', 'Lock All Pre-routes', 'Situs Routing Strategies'], capture_output=True, text=True).stdout.strip())
    if estrategia:
        print(subprocess.run(['./boton.sh', estrategia, 'Situs Routing Strategies', 'seleccionar'], capture_output=True, text=True).stdout.strip())
    print(subprocess.run(['./boton.sh', 'Route All', 'Situs Routing Strategies'], capture_output=True, text=True).stdout.strip())
    inicio = time.time()
    while time.time() - inicio < 420:
        time.sleep(15)
        m = re.search(r'Routing finished[^\n]*', ocr())
        if m:
            print(f'{estrategia or "Default Multi Layer Board"}: {(time.time() - inicio) / 60:.1f} min:', m.group(0))
            return
    print('sin "Routing finished" tras 7 min')

if __name__ == '__main__':
    os.chdir('/mnt/sda3/vms/altium')
    situs(next((a for a in sys.argv[1:] if a != '--bloquear'), None), '--bloquear' in sys.argv)
