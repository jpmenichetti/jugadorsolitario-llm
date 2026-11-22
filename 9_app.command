#!/bin/bash
# Abre la app del LLM Personal en tu navegador. Se usa con doble clic desde Finder.
# Para cerrarla: botón «Salir» en la app (libera la memoria del modelo) o cierra esta ventana.
cd "$(dirname "$0")"
TAMANO=8b
source herramientas/comun.sh
activar
echo "Iniciando la app… se abrirá sola en tu navegador."
echo "La primera vez que generas, el modelo tarda unos segundos en cargarse."
# caffeinate evita que el Mac se suspenda mientras la app está abierta
caffeinate -i python app/servidor.py
