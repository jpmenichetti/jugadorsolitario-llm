# Variables compartidas por todos los scripts.
# Antes de cargar este archivo, cada script define TAMANO (4b u 8b) y, si corresponde, VARIANTE.
set -e
cd "$(dirname "$0")"
TAMANO="${TAMANO:-4b}"
case "$TAMANO" in
  4b) MODELO="mlx-community/Qwen3-4B-4bit" ;;   # ~2,3 GB
  8b) MODELO="mlx-community/Qwen3-8B-4bit" ;;   # ~4,6 GB
  *) echo "Tamaño desconocido: $TAMANO (usa 4b u 8b)"; exit 1 ;;
esac
export PATH="$HOME/.local/bin:$PATH"
activar() {
  if [ ! -f .venv/bin/activate ]; then echo "Primero corre: bash 1_instalar.sh"; exit 1; fi
  source .venv/bin/activate
}
revisar_variante() {
  if [ ! -d "datos/$VARIANTE" ]; then echo "Variante desconocida: $VARIANTE (usa uniforme o ponderado)"; exit 1; fi
}
