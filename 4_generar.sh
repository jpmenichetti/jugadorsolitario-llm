#!/bin/bash
# Genera los 8 artículos de prueba con el modelo entrenado.
# Uso: bash 4_generar.sh uniforme   |   bash 4_generar.sh ponderado 8b
VARIANTE="${1:-uniforme}"; TAMANO="${2:-4b}"
source "$(dirname "$0")/herramientas/comun.sh"; activar; revisar_variante
caffeinate -i -s python herramientas/generar.py --modelo "$MODELO" --adaptador "adaptadores/$TAMANO-$VARIANTE" --salida "resultados/$TAMANO-$VARIANTE"
echo; echo "✅ Listo. Resultados en resultados/$TAMANO-$VARIANTE/. Para comparar: bash 5_comparar.sh"
