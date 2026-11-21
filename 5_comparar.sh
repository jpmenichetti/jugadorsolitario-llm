#!/bin/bash
# Compara originales vs. generados y abre un informe en el navegador.
source "$(dirname "$0")/herramientas/comun.sh"; activar
python herramientas/comparar.py && open resultados/comparacion.html
