@echo off
echo Iniciando Signalink API...

REM Verificar que existe .env
if not exist .env (
    echo Copiando .env.example a .env...
    copy .env.example .env
)

REM Ejecutar la aplicación
python src/app.py