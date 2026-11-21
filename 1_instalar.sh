#!/bin/bash
# Instala lo necesario (una sola vez). Usa "uv" para tener un Python aislado que no toca tu sistema.
# Uso: bash 1_instalar.sh        (descarga el modelo de 4B; el de 8B se descarga solo la primera vez que lo uses)
TAMANO=4b
source "$(dirname "$0")/herramientas/comun.sh"
if [ "$(uname -m)" != "arm64" ]; then echo "Este proyecto necesita un Mac con chip Apple (M1/M2/M3/M4)."; exit 1; fi
if ! command -v uv >/dev/null 2>&1; then
  echo "Instalando uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install "mlx-lm>=0.32" pyyaml
echo
echo "Descargando el modelo base ($MODELO)..."
python -c "from mlx_lm import load; load('$MODELO')"
echo; echo "✅ Instalación lista. Siguiente paso: bash 2_linea_base.sh"
