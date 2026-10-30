#!/usr/bin/env python3
"""Comandos dentro de la VM vía QEMU Guest Agent (corren como SYSTEM, sin ventana).
Uso: ./qga.py ping   |   ./qga.py 'Get-ChildItem C:\\Users'   (PowerShell; imprime la salida y devuelve su código)"""
import base64
import json
import os
import socket
import sys
import time

SOCK = f'/tmp/altium-qga-{os.getuid()}.sock'


def send(f, cmd, **args):
    f.write(json.dumps({'execute': cmd, 'arguments': args}).encode() + b'\n')
    f.flush()


def recv(f):
    while True:
        r = json.loads(f.readline())
        if 'return' in r or 'error' in r:
            return r


def main():
    s = socket.socket(socket.AF_UNIX)
    s.settimeout(5)                      # sin agente (Windows instalándose) -> timeout = "no está listo"
    s.connect(SOCK)
    f = s.makefile('rwb')
    sid = int(time.time())
    send(f, 'guest-sync', id=sid)        # descarta respuestas viejas que quedaron en el canal
    while recv(f).get('return') != sid:
        pass
    if sys.argv[1] == 'ping':
        send(f, 'guest-ping')
        return 'error' in recv(f)
    s.settimeout(None)
    send(f, 'guest-exec', path='powershell.exe', arg=['-NoProfile', '-Command', sys.argv[1]], **{'capture-output': True})
    pid = recv(f)['return']['pid']
    while True:
        send(f, 'guest-exec-status', pid=pid)
        st = recv(f)['return']
        if st['exited']:
            break
        time.sleep(1)
    for k in ('out-data', 'err-data'):
        if k in st:
            sys.stdout.write(base64.b64decode(st[k]).decode(errors='replace'))
    return st.get('exitcode', 0)


sys.exit(main())
