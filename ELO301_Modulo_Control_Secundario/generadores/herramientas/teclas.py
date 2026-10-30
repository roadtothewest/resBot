#!/usr/bin/env python3
"""Envía teclas a la VM por el monitor de QEMU (sendkey), con pausas.
Uso: ./teclas.py alt-d u 5 tab tab spc   (un número = esperar esos segundos)"""
import os
import socket
import sys
import time

m = socket.socket(socket.AF_UNIX)
m.connect(f'/tmp/altium-mon-{os.getuid()}.sock')
for k in sys.argv[1:]:
    if k.replace('.', '').isdigit():
        time.sleep(float(k))
    else:
        m.sendall(f'sendkey {k}\n'.encode())
        time.sleep(0.7)
