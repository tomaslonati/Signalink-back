#!/bin/bash
echo "Iniciando Signalink API..."

# Verificar que existe .env
if [ ! -f .env ]; then
    echo "Copiando .env.example a .env..."
    cp .env.example .env
fi

# Ejecutar la aplicación
python src/app.py