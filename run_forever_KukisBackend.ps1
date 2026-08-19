# Generado por instalar-servicio-generico.ps1 el 2026-08-11.
# Supervisor: mantiene "venv\Scripts\python.exe app.py" corriendo indefinidamente, reiniciandolo
# si se cae. Arranca solo via el acceso directo en la carpeta de Inicio de
# Windows -- no se corre a mano.
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$rutaProyecto = "C:\Claude_2026\Proyectos\07 Tienda en Linea Kukis"
$rutaTrabajo = "C:\Claude_2026\Proyectos\07 Tienda en Linea Kukis\backend"
Set-Location $rutaTrabajo

$carpetaLogs = Join-Path $rutaProyecto "logs"
New-Item -ItemType Directory -Force -Path $carpetaLogs | Out-Null
$logSupervisor = Join-Path $carpetaLogs "supervisor_KukisBackend.log"
$logCrashes = Join-Path $carpetaLogs "crashes_KukisBackend.log"

function Escribir-Log($mensaje) {
    $linea = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $mensaje"
    Add-Content -Path $logSupervisor -Value $linea -Encoding UTF8
}

Escribir-Log "Supervisor iniciado (KukisBackend)."

while ($true) {
    Escribir-Log "Iniciando: venv\Scripts\python.exe app.py (puerto 5013)..."
    # La redireccion la hace cmd.exe (parte de la linea que le pasamos), no
    # el "2>>" de PowerShell: sobre un comando nativo, PowerShell envuelve
    # cada linea de stderr en un objeto ErrorRecord y el archivo queda
    # ilegible (texto separado letra por letra). Encontrado el 2026-08-07.
    $lineaComando = "venv\Scripts\python.exe app.py 2>> `"$logCrashes`""
    cmd /c $lineaComando
    $codigo = $LASTEXITCODE
    Escribir-Log "Se detuvo (codigo de salida: $codigo). Reiniciando en 30s..."
    Start-Sleep -Seconds 30
}
