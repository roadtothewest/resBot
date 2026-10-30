#!/usr/bin/env python3
"""Reemplaza un símbolo de ELO301_G1.SchLib: lo borra (verificando que el documento sea una SchLib), lo crea de nuevo
desde un spec de create_symbols_batch en la carpeta compartida y guarda la biblioteca.
Uso: reemplazar_simbolo.py <nombre del símbolo> <spec.txt en altium/specs/>"""
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
LIB = 'C:\\Users\\altium\\Documents\\Altium\\ELO301_G1\\ELO301_G1.SchLib'


def mcp(tool, args):
    return subprocess.run([str(AQUI / 'mcpc.py'), 'call', tool, json.dumps(args)],
                          capture_output=True, text=True, timeout=900).stdout


nombre, spec = sys.argv[1], sys.argv[2]
borrar = f"""var
    SchLib, Comp : IDispatch;
Obj1 := Client.OpenDocument('SCHLIB', '{LIB}');
Client.ShowDocument(Obj1);
SchLib := SchServer.GetCurrentSchDocument;
if SchLib.ObjectID = 33 then
begin
    Comp := SchLib.GetState_SchComponentByLibRef('{nombre}');
    if Comp <> nil then SchLib.RemoveSchComponent(Comp);
    SaveDoc('{LIB}');
    ResultText := 'borrado';
end
else
    ResultText := 'NO es SchLib';"""
print(json.loads(mcp('run_altium_script', {'script': borrar})).get('result'))
print(mcp('create_symbols_batch', {'spec_file': f'\\\\10.0.2.4\\qemu\\specs\\{spec}'}).replace('\n', ' '))
print(json.loads(mcp('run_altium_script', {'script': f"SaveDoc('{LIB}');\nResultText := 'guardada';"})).get('result'))
