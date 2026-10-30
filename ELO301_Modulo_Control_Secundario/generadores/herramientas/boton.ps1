# Presiona un botón (o selecciona un ítem) por su nombre con UI Automation.
# Uso: boton.ps1 "<nombre>" ["<título de la ventana>"] [invocar|seleccionar|clic|menu]
# Con «menu», <nombre> es una ruta de menú «Route>Auto Route>All...» que se recorre con clics reales en un solo proceso
# (un PowerShell nuevo por paso le quita la activación a Altium y el menú desplegado se cierra).
param([string]$Nombre, [string]$Ventana = '', [string]$Accion = 'invocar')
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$AE = [System.Windows.Automation.AutomationElement]
$Arbol = [System.Windows.Automation.TreeScope]
$log = 'C:\Users\Public\boton.log'
Add-Type 'using System; using System.Runtime.InteropServices; public class Raton { [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y); [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, uint d, IntPtr e); }'
function Clic($e) {
    $r = $e.Current.BoundingRectangle
    [Raton]::SetCursorPos([int]($r.X + $r.Width / 2), [int]($r.Y + $r.Height / 2)); Start-Sleep -Milliseconds 200
    [Raton]::mouse_event(2, 0, 0, 0, [IntPtr]::Zero); [Raton]::mouse_event(4, 0, 0, 0, [IntPtr]::Zero)
}
function Buscar($nombre, $ventana) {
    $c = New-Object System.Windows.Automation.PropertyCondition($AE::NameProperty, $nombre)
    if ($ventana) {
        $w = $AE::RootElement.FindFirst($Arbol::Children, (New-Object System.Windows.Automation.PropertyCondition($AE::NameProperty, $ventana)))
        if ($w) { return $w.FindFirst($Arbol::Descendants, $c) }
        return $null
    }
    $todas = @($AE::RootElement.FindAll($Arbol::Children, [System.Windows.Automation.Condition]::TrueCondition))
    $orden = @($todas | Where-Object { $_.Current.Name -notlike '*Altium Designer*' }) + @($todas | Where-Object { $_.Current.Name -like '*Altium Designer*' })
    foreach ($w in $orden) { $e = $w.FindFirst($Arbol::Descendants, $c); if ($e) { return $e } }
    return $null
}
if ($Accion -eq 'menu') {
    $pasos = $Nombre -split '>'
    $hechos = @()
    for ($k = 0; $k -lt $pasos.Count; $k++) {
        $e = $null
        for ($t = 0; $t -lt 10 -and -not $e; $t++) { $e = Buscar $pasos[$k] $(if ($k -eq 0) { $Ventana } else { '' }); if (-not $e) { Start-Sleep -Milliseconds 300 } }
        if (-not $e) { "menú: no apareció «$($pasos[$k])» tras $($hechos -join ' > ')" | Out-File $log; exit 1 }
        Clic $e; $hechos += $pasos[$k]; Start-Sleep -Milliseconds 700
    }
    "menú recorrido: $($hechos -join ' > ')" | Out-File $log; exit 0
}
$cond = New-Object System.Windows.Automation.PropertyCondition($AE::NameProperty, $Nombre)
$b = $null
if ($Ventana) {
    $raiz = $AE::RootElement.FindFirst($Arbol::Children, (New-Object System.Windows.Automation.PropertyCondition($AE::NameProperty, $Ventana)))
    if (-not $raiz) { "sin ventana: $Ventana" | Out-File $log; exit 1 }
    $b = $raiz.FindFirst($Arbol::Descendants, $cond)
} else {
    # sin ventana: primero las ventanas chicas (menús desplegados, diálogos) y al final la principal de Altium
    $todas = @($AE::RootElement.FindAll($Arbol::Children, [System.Windows.Automation.Condition]::TrueCondition))
    $orden = @($todas | Where-Object { $_.Current.Name -notlike '*Altium Designer*' }) + @($todas | Where-Object { $_.Current.Name -like '*Altium Designer*' })
    foreach ($w in $orden) { $b = $w.FindFirst($Arbol::Descendants, $cond); if ($b) { break } }
}
if (-not $b) { "sin botón: $Nombre" | Out-File $log; exit 1 }
try {
    if ($Accion -eq 'clic') { throw 'clic real pedido' }
    if ($Accion -eq 'seleccionar') {
        $b.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select()
        "seleccionado: $Nombre ($($b.Current.ClassName))" | Out-File $log
    } else {
        $b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
        "presionado: $Nombre ($($b.Current.ClassName))" | Out-File $log
    }
} catch {
    # sin el patrón: clic real en el centro del elemento (coordenadas de pantalla de UIA, sin la cizalla del screendump)
    Add-Type 'using System; using System.Runtime.InteropServices; public class Raton { [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y); [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, uint d, IntPtr e); }'
    $r = $b.Current.BoundingRectangle
    [Raton]::SetCursorPos([int]($r.X + $r.Width / 2), [int]($r.Y + $r.Height / 2)); Start-Sleep -Milliseconds 200
    [Raton]::mouse_event(2, 0, 0, 0, [IntPtr]::Zero); [Raton]::mouse_event(4, 0, 0, 0, [IntPtr]::Zero)
    "clic en $Nombre ($([int]$r.X),$([int]$r.Y)) tras: $_" | Out-File $log
}
