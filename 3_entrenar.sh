#!/bin/bash
# Entrena el modelo con tus artículos.
# Uso: bash 3_entrenar.sh uniforme      |  bash 3_entrenar.sh ponderado
#      bash 3_entrenar.sh uniforme 8b   |  bash 3_entrenar.sh ponderado 8b
VARIANTE="${1:-uniforme}"; TAMANO="${2:-4b}"
source "$(dirname "$0")/herramientas/comun.sh"; activar; revisar_variante
mkdir -p adaptadores registros
SALIDA="adaptadores/$TAMANO-$VARIANTE"
echo "Entrenando '$VARIANTE' sobre $MODELO ..."
echo "(Verás 'Train loss' y 'Val loss'. Es normal que bajen; si 'Val loss' empieza a subir, el modelo está memorizando.)"
mlx_lm.lora --config config/base.yaml --model "$MODELO" --data "datos/$VARIANTE" --adapter-path "$SALIDA" 2>&1 | tee "registros/entrenamiento_$TAMANO-$VARIANTE.log"
echo; echo "✅ Entrenamiento listo en $SALIDA. Siguiente: bash 4_generar.sh $VARIANTE $TAMANO"
