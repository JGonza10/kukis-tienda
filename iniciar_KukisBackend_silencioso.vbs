' Generado por instalar-servicio-generico.ps1. Lanza run_forever_KukisBackend.ps1
' sin ventana visible.
Set objShell = CreateObject("WScript.Shell")
rutaScript = "C:\Claude_2026\Proyectos\07 Tienda en Linea Kukis\run_forever_KukisBackend.ps1"
objShell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & rutaScript & """", 0, False
