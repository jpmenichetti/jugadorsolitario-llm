#!/bin/bash
# Genera los 8 artículos de prueba con el modelo entrenado.
# Uso: bash 4_generar.sh uniforme                |  bash 4_generar.sh ponderado 8b
#      bash 4_generar.sh fichas-uniforme         |  bash 4_generar.sh fichas-largo-uniforme
VARIANTE="${1:-uniforme}"; TAMANO="${2:-4b}"
source "$(dirname "$0")/herramientas/comun.sh"; activar; revisar_variante
# la fase es lo que va antes de -uniforme / -ponderado (ej. "fichas-largo"); sin fase = fase 1
FASE="${VARIANTE%-*}"
if [ "$FASE" = "$VARIANTE" ]; then PROMPTS="datos/prueba/prompts.jsonl"; else PROMPTS="datos/prueba/prompts_${FASE}.jsonl"; fi
caffeinate -i -s python herramientas/generar.py --modelo "$MODELO" --adaptador "adaptadores/$TAMANO-$VARIANTE" --prompts "$PROMPTS" --salida "resultados/$TAMANO-$VARIANTE"
echo; echo "✅ Listo. Resultados en resultados/$TAMANO-$VARIANTE/. Para comparar: bash 5_comparar.sh  (fase 2: bash 5_comparar.sh fichas)"
