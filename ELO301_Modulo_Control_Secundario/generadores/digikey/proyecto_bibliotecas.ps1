# Reemplaza ELO301_G1.SchLib por las bibliotecas de un simbolo por pieza en ELO301_G1.PrjPcb.
# Correr con Altium sin el proyecto abierto.
$prj = Join-Path $PSScriptRoot '..\..\altium\ELO301_G1.PrjPcb' | Resolve-Path
$tsv = Get-Content (Join-Path $PSScriptRoot 'metadatos_digikey.tsv') -Encoding UTF8 | Select-Object -Skip 1
$genericasProfe = @('CAP - GENERIC.SchLib', 'RESISTOR - GENERIC.SchLib', 'INDUCTOR - GENERIC.SchLib', 'DIODE - GENERIC.SchLib')
$nuevas = $tsv | ForEach-Object { ($_ -split "`t")[4] } | Where-Object { $_ -and ($genericasProfe -notcontains $_) } | Sort-Object -Unique

$texto = [IO.File]::ReadAllText($prj)
$bloques = [regex]::Matches($texto, '(?ms)^\[Document(\d+)\]\r?\nDocumentPath=([^\r\n]*)\r?\n.*?(?=^\[|\z)')
$plantilla = ($bloques | Where-Object { $_.Groups[2].Value -eq 'ELO301_G1.SchLib' }).Value
if (-not $plantilla) { $plantilla = ($bloques | Where-Object { $_.Groups[2].Value -like '*.SchLib' } | Select-Object -First 1).Value }
$rutas = @($bloques | ForEach-Object { $_.Groups[2].Value } | Where-Object { $_ -ne 'ELO301_G1.SchLib' })
$rutas += $nuevas | Where-Object { $rutas -notcontains $_ }

# Reescribe la lista de documentos con numeracion continua, usando cada bloque original cuando existe
$nuevoBloque = { param($n, $ruta)
  $orig = $bloques | Where-Object { $_.Groups[2].Value -eq $ruta } | Select-Object -First 1
  $base = if ($orig) { $orig.Value } else { $plantilla -replace '(?m)^DocumentPath=.*$', "DocumentPath=$ruta" }
  $base -replace '(?m)^\[Document\d+\]', "[Document$n]" }
$lista = (1..$rutas.Count | ForEach-Object { & $nuevoBloque $_ $rutas[$_ - 1] }) -join ''
$inicio = $bloques[0].Index
$fin = $bloques[$bloques.Count - 1].Index + $bloques[$bloques.Count - 1].Length
$texto = $texto.Substring(0, $inicio) + $lista + $texto.Substring($fin)
[IO.File]::WriteAllText($prj, $texto)
"Documentos en el proyecto: $($rutas.Count)"; $rutas | ForEach-Object { "  $_" }
