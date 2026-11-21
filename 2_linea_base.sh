#!/bin/bash
# Genera los 8 artículos de prueba con el modelo SIN entrenar (el "antes").
# Uso: bash 2_linea_base.sh              (4B, fase 1: sin fichas)
#      bash 2_linea_base.sh 4b fichas    (4B, fase 2: el pedido incluye la ficha del juego)
#      bash 2_linea_base.sh 8b fichas
TAMANO="${1:-4b}"; FASE="${2:-}"
source "$(dirname "$0")/herramientas/comun.sh"; activar
if [ "$FASE" = "fichas" ]; then PROMPTS="datos/prueba/prompts_fichas.jsonl"; SALIDA="resultados/$TAMANO-fichas-base"
else PROMPTS="datos/prueba/prompts.jsonl"; SALIDA="resultados/$TAMANO-base"; fi
caffeinate -i -s python herramientas/generar.py --modelo "$MODELO" --prompts "$PROMPTS" --salida "$SALIDA"
echo; echo "✅ Listo. Resultados en $SALIDA/"
