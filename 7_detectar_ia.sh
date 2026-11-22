#!/bin/bash
# Evalúa con Pangram si los textos parecen escritos por IA (originales y todo lo generado).
# Solo evalúa textos nuevos; antes de gastar muestra cuántas palabras son y el costo estimado.
# Uso: bash 7_detectar_ia.sh                       (todo lo nuevo)
#      bash 7_detectar_ia.sh 8b-fichas-largo-uniforme   (solo esa carpeta de resultados/)
# Luego: bash 5_comparar.sh  (o bash 5_comparar.sh fichas)
source "$(dirname "$0")/herramientas/comun.sh"; activar
python herramientas/detectar.py "$@"
