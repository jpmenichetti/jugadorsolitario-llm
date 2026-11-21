#!/bin/bash
# Chat en la Terminal con tu modelo entrenado. Escribe 'q' para salir.
# Uso: bash 6_conversar.sh uniforme   |   bash 6_conversar.sh ponderado 8b
VARIANTE="${1:-uniforme}"; TAMANO="${2:-4b}"
source "$(dirname "$0")/herramientas/comun.sh"; activar; revisar_variante
SISTEMA="$(python -c "import json;print(json.loads(open('datos/prueba/prompts.jsonl').readline())['system'])")"
echo "Prueba pedirle: Escribe el artículo de esta semana sobre «Hades»."
mlx_lm.chat --model "$MODELO" --adapter-path "adaptadores/$TAMANO-$VARIANTE" --system-prompt "$SISTEMA" --max-tokens 2500 --temp 0.7 --top-p 0.9
