#!/usr/bin/env bash
# build.sh - Script de construcción para Render

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt