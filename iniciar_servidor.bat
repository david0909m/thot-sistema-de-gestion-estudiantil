@echo off
echo === INICIANDO SERVIDOR THOT (127.0.0.1:8000) ===
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python manage.py runserver 127.0.0.1:8000
pause
