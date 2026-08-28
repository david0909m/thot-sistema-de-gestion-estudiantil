@echo off
echo === DETENIENDO SERVIDOR THOT EN EL PUERTO 8000 ===
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%a
echo [OK] Servidor detenido correctamente.
pause
