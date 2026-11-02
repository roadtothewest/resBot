param([string]$Proc, [int]$Espera = 120, [string]$Script = 'Simbolos')
# Ejecuta un procedimiento DelphiScript en el Altium abierto y espera el archivo fin.flag que deja el script.
# - Copia el script con un nombre unico: si el .pas ya esta abierto en Altium, se ejecutaria la version en memoria.
# - No abre log.txt hasta que el script termina: si Altium no puede escribirlo, el depurador detiene el script.
$d = Split-Path -Parent $MyInvocation.MyCommand.Path
$tmp = Join-Path $env:TEMP 'altium_simbolos'; New-Item -ItemType Directory -Force $tmp | Out-Null
$log = Join-Path $tmp 'log.txt'
$flag = Join-Path $tmp 'fin.flag'
Remove-Item $log, $flag -ErrorAction SilentlyContinue
$nombre = $Script + '_' + (Get-Date -Format 'HHmmss')
Copy-Item (Join-Path $d "$Script.pas") (Join-Path $tmp "$nombre.pas")
Set-Content -Path (Join-Path $tmp "$nombre.PrjScr") -Value "[Design]`r`nVersion=1.0`r`n`r`n[Document1]`r`nDocumentPath=$nombre.pas" -Encoding ASCII
Start-Process -FilePath "C:\Program Files\Altium\AD26\X2.EXE" -ArgumentList "-RScriptingSystem:RunScript(ProjectName=`"$tmp\$nombre.PrjScr`"|ProcName=`"$nombre.pas>$Proc`")"
$t0 = Get-Date
while (-not (Test-Path $flag) -and ((Get-Date) - $t0).TotalSeconds -lt $Espera) { Start-Sleep -Milliseconds 500 }
if (Test-Path $flag) {
  Start-Sleep -Milliseconds 300
  Get-Content $log -Encoding UTF8
  "(terminado en $([int]((Get-Date) - $t0).TotalSeconds) s)"
} else {
  "SIN fin.flag tras $Espera s: el script sigue corriendo o quedo detenido en el depurador de Altium"
}
