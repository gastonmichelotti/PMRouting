@echo off

REM Cambia al directorio donde reside este script
cd /d %~dp0

REM Activa el entorno virtual usando la ruta relativa
call PMRoutingEnv\Scripts\activate

REM Instala las dependencias
pip install -r requirements.txt

wfastcgi-enable

REM Ejecuta tu API
python run.py

pause
