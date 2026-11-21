#!/bin/bash
# Genera los 8 artículos de prueba con el modelo SIN entrenar (el "antes").
# Uso: bash 2_linea_base.sh        (4B)   |   bash 2_linea_base.sh 8b
TAMANO="${1:-4b}"
source "$(dirname "$0")/herramientas/comun.sh"; activar
caffeinate -i -s python herramientas/generar.py --modelo "$MODELO" --salida "resultados/$TAMANO-base"
echo; echo "✅ Listo. Resultados en resultados/$TAMANO-base/. Siguiente: bash 3_entrenar.sh uniforme $TAMANO"
