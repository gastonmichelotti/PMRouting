@echo off

REM Activa el entorno virtual usando la ruta absoluta
call .\PMRouting\PMRoutingEnv\Scripts\activate

REM Instala las dependencias
pip install -r .\PMRouting\requirements.txt

wfastcgi-enable

REM Ejecuta tu API
python .\PMRouting\run.py

pause
