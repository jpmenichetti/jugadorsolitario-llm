#!/bin/bash
# Compara originales vs. generados y abre un informe en el navegador.
# Uso: bash 5_comparar.sh          (fase 1, sin fichas)
#      bash 5_comparar.sh fichas   (fase 2, con fichas)
source "$(dirname "$0")/herramientas/comun.sh"; activar
python herramientas/comparar.py $1
if [ "$1" = "fichas" ]; then open resultados/comparacion_fichas.html; else open resultados/comparacion.html; fi
