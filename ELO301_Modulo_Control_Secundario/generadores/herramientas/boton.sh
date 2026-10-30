#!/usr/bin/env bash
# Presiona un botón (o selecciona un ítem) de la VM por su nombre (UI Automation, sesión del usuario):
# ./boton.sh "Route All" ["Situs Routing Strategies"] [invocar|seleccionar|clic|menu]
cd "$(dirname "$0")" && B64=$(base64 -w0 boton.ps1) && ./qga.py "[IO.File]::WriteAllBytes('C:\Users\Public\boton.ps1', [Convert]::FromBase64String('$B64'))
Remove-Item C:\Users\Public\boton.log -ErrorAction SilentlyContinue
\$a = New-ScheduledTaskAction -Execute powershell.exe -Argument '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File C:\Users\Public\boton.ps1 \"$1\" \"$2\" ${3:-invocar}'
\$p = New-ScheduledTaskPrincipal -UserId altium -LogonType Interactive -RunLevel Highest
Register-ScheduledTask -TaskName boton -Action \$a -Principal \$p -Force | Out-Null; Start-ScheduledTask -TaskName boton
\$t = 0; do { Start-Sleep 1; \$t++ } while ((Get-ScheduledTask -TaskName boton).State -eq 'Running' -and \$t -lt 60)
Unregister-ScheduledTask -TaskName boton -Confirm:\$false; Get-Content C:\Users\Public\boton.log"
