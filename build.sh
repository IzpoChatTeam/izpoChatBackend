#!/usr/bin/env bash
# build.sh - Script de construcción para Render

set -o errexit  # Salir si un comando falla

echo "--- Instalando dependencias ---"
pip install -r requirements.txt

echo "--- Creando/Verificando tablas de la base de datos ---"
# Ejecuta el código Python para inicializar la BD dentro del contexto de la app
python -c "from app import app, db; app.app_context().push(); db.create_all()"

echo "--- Build finalizado exitosamente ---"