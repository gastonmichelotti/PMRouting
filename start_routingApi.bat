@echo off

REM Activa el entorno virtual usando la ruta absoluta
call C:\Users\alejo\OneDrive\Escritorio\PMRouting\PMRoutingEnv\Scripts\activate

REM Instala las dependencias
pip install -r C:\Users\alejo\OneDrive\Escritorio\PMRouting\requirements.txt

wfastcgi-enable

REM Ejecuta tu API
python C:\Users\alejo\OneDrive\Escritorio\PMRouting\run.py

pause
