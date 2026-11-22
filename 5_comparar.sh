#!/bin/bash
# Compara originales vs. generados y abre un informe en el navegador.
# Uso: bash 5_comparar.sh          (fase 1, sin fichas)
#      bash 5_comparar.sh fichas   (fase 2, con fichas)
#      bash 5_comparar.sh transferencia   (fase 3, reescritura de borradores)
source "$(dirname "$0")/herramientas/comun.sh"; activar
python herramientas/comparar.py $1
if [ -n "$1" ]; then open "resultados/comparacion_$1.html"; else open resultados/comparacion.html; fi
