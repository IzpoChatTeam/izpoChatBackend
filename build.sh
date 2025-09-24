#!/usr/bin/env bash
# build.sh - Script de construcción para Render

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt

# Añade esta línea para crear las tablas durante el build
echo "Creando tablas de la base de datos..."
python -c "from app import app, db; app.app_context().push(); db.create_all()"
echo "Tablas creadas."