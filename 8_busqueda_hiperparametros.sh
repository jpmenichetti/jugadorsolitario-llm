#!/bin/bash
# Entrena 6 variantes del 4B (cambiando un parámetro a la vez) y arma una tabla comparativa.
# Toma ~3,5 a 4 horas: ideal para dejarlo corriendo de noche, con el Mac enchufado y la tapa abierta.
# Si se interrumpe, vuelve a correrlo: se salta las corridas ya terminadas.
# Uso: bash 8_busqueda_hiperparametros.sh
TAMANO=4b
source "$(dirname "$0")/herramientas/comun.sh"; activar
mkdir -p resultados
echo "Inicio: $(date +%H:%M). El Mac no se dormirá durante el proceso (no cierres la tapa)."
caffeinate -i -s python herramientas/busqueda.py 2>&1 | tee registros/busqueda_hiperparametros.log
