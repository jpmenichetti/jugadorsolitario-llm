#!/bin/bash
# Genera los 8 artículos de prueba con el modelo SIN entrenar (el "antes").
# Uso: bash 2_linea_base.sh                    (4B, fase 1: sin fichas)
#      bash 2_linea_base.sh 4b fichas          (fase 2: el pedido incluye la ficha del juego)
#      bash 2_linea_base.sh 4b fichas-largo    (fase 2b: ficha + largo aproximado)
TAMANO="${1:-4b}"; FASE="${2:-}"
source "$(dirname "$0")/herramientas/comun.sh"; activar
if [ -n "$FASE" ]; then PROMPTS="datos/prueba/prompts_${FASE}.jsonl"; SALIDA="resultados/$TAMANO-$FASE-base"
else PROMPTS="datos/prueba/prompts.jsonl"; SALIDA="resultados/$TAMANO-base"; fi
if [ ! -f "$PROMPTS" ]; then echo "No existe $PROMPTS"; exit 1; fi
caffeinate -i -s python herramientas/generar.py --modelo "$MODELO" --prompts "$PROMPTS" --salida "$SALIDA"
echo; echo "✅ Listo. Resultados en $SALIDA/"
