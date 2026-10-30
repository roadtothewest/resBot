#!/usr/bin/env python3
"""Cliente MCP mínimo (SSE, solo stdlib) para altium-mcp en la VM.
Uso: ./mcpc.py list               -> nombre y primera línea de cada herramienta
     ./mcpc.py list <tool>        -> descripción completa y parámetros de una herramienta
     ./mcpc.py call <tool> [json] -> resultado de la herramienta"""
import base64
import http.client
import json
import queue
import sys
import threading

HOST, PORT = '127.0.0.1', 8765
respuestas = queue.Queue()
endpoint = queue.Queue()


def escuchar():
    c = http.client.HTTPConnection(HOST, PORT)
    c.request('GET', '/sse', headers={'Accept': 'text/event-stream'})
    r = c.getresponse()
    evento, datos = None, []
    for linea in r:
        linea = linea.decode().rstrip('\r\n')
        if linea.startswith('event:'):
            evento = linea[6:].strip()
        elif linea.startswith('data:'):
            datos.append(linea[5:].strip())
        elif not linea and datos:
            (endpoint if evento == 'endpoint' else respuestas).put('\n'.join(datos))
            evento, datos = None, []


def enviar(ruta, msg):
    c = http.client.HTTPConnection(HOST, PORT)
    c.request('POST', ruta, json.dumps(msg), {'Content-Type': 'application/json'})
    c.getresponse().read()


def pedir(ruta, n, metodo, params, espera=600):
    enviar(ruta, {'jsonrpc': '2.0', 'id': n, 'method': metodo, 'params': params})
    while True:
        r = json.loads(respuestas.get(timeout=espera))
        if r.get('id') == n:
            return r


def main():
    threading.Thread(target=escuchar, daemon=True).start()
    ruta = endpoint.get(timeout=15)
    pedir(ruta, 1, 'initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                                  'clientInfo': {'name': 'mcpc', 'version': '0'}})
    enviar(ruta, {'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    if sys.argv[1] == 'list':
        for t in pedir(ruta, 2, 'tools/list', {})['result']['tools']:
            if len(sys.argv) > 2:
                if t['name'] == sys.argv[2]:
                    print(t.get('description'), json.dumps(t.get('inputSchema'), ensure_ascii=False, indent=1))
                continue
            print(f"{t['name']}: {(t.get('description') or '').strip().splitlines()[0][:150]}")
        return 0
    args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    r = pedir(ruta, 2, 'tools/call', {'name': sys.argv[2], 'arguments': args})
    if 'error' in r:
        print(r['error'])
        return 1
    for i, c in enumerate(r['result'].get('content', [])):
        if c.get('type') == 'image':  # capturas: se guardan junto al script
            ruta = f"/tmp/mcpc_{i}.{c.get('mimeType', 'image/png').split('/')[-1]}"
            open(ruta, 'wb').write(base64.b64decode(c['data']))
            print(f'[imagen guardada en {ruta}]')
        else:
            print(c.get('text', f"[{c.get('type')}]"))
    return 1 if r['result'].get('isError') else 0


sys.exit(main())
