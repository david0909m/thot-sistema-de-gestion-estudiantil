Write-Host "=== INICIANDO SERVIDOR THOT (127.0.0.1:8000) ===" -ForegroundColor Green
$ScriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $ScriptDir
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
