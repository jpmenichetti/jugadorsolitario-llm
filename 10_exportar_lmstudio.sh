#!/bin/bash
# Fusiona un adaptador con su modelo base y lo deja listo para usar en LM Studio.
# Uso: bash 10_exportar_lmstudio.sh                              (8B de transferencia, el recomendado)
#      bash 10_exportar_lmstudio.sh fichas-largo-uniforme 8b     (otro adaptador)
#      bash 10_exportar_lmstudio.sh transferencia-uniforme 8b "/otra/carpeta/de/modelos"
VARIANTE="${1:-transferencia-uniforme}"; TAMANO="${2:-8b}"
DESTINO_LMS="${3:-$HOME/.lmstudio/models}"
source "$(dirname "$0")/herramientas/comun.sh"; activar

ADAPTADOR="adaptadores/$TAMANO-$VARIANTE"
if [ ! -f "$ADAPTADOR/adapters.safetensors" ]; then echo "No encuentro $ADAPTADOR. ¿Entrenaste ese modelo?"; exit 1; fi
if [ ! -d "$DESTINO_LMS" ]; then
  echo "No encuentro la carpeta de modelos de LM Studio ($DESTINO_LMS)."
  echo "Abre LM Studio una vez y vuelve a intentarlo. Si cambiaste la carpeta de modelos en LM Studio,"
  echo "pásala como tercer argumento: bash 10_exportar_lmstudio.sh $VARIANTE $TAMANO \"/ruta/a/tus/modelos\""
  exit 1
fi

NOMBRE="qwen3-$TAMANO-$VARIANTE-mlx"
SALIDA="$DESTINO_LMS/jugador-solitario/$NOMBRE"
if [ -d "$SALIDA" ]; then
  echo "Ya existe $SALIDA."; read -r -p "¿Reemplazarlo? (s/n) " R
  [ "$R" = "s" ] || exit 0
  mv "$SALIDA" "$SALIDA.anterior-$(date +%H%M%S)"   # no se borra nada: queda como copia
fi
LIBRE_GB=$(df -g "$DESTINO_LMS" | awk 'NR==2 {print $4}')
if [ "${LIBRE_GB:-99}" -lt 8 ]; then echo "⚠️  Quedan solo ${LIBRE_GB} GB libres; el modelo fusionado ocupa ~5 GB."; fi

echo "1/3  Fusionando $ADAPTADOR con $MODELO (unos minutos)…"
mlx_lm.fuse --model "$MODELO" --adapter-path "$ADAPTADOR" --save-path "$SALIDA"

echo "2/3  Ajustando la plantilla para que Qwen3 no use su «modo razonamiento»…"
# En el entrenamiento y en la app se generó con enable_thinking=False. LM Studio no siempre ofrece
# esa opción para modelos propios, así que se deja como comportamiento por defecto del modelo.
python - "$SALIDA" <<'PY'
import json, os, sys
d = sys.argv[1]
viejo = "enable_thinking is defined and enable_thinking is false"
cambios = 0
jinja = os.path.join(d, "chat_template.jinja")
if os.path.exists(jinja):
    t = open(jinja).read()
    if viejo in t:
        open(jinja, "w").write(t.replace(viejo, "true")); cambios += 1
tc = os.path.join(d, "tokenizer_config.json")
if os.path.exists(tc):
    c = json.load(open(tc))
    if isinstance(c.get("chat_template"), str) and viejo in c["chat_template"]:
        c["chat_template"] = c["chat_template"].replace(viejo, "true")
        json.dump(c, open(tc, "w"), ensure_ascii=False, indent=2); cambios += 1
print("     listo" if cambios else "     ⚠️  No encontré la plantilla esperada: agrega /no_think al final de cada mensaje en LM Studio.")
PY

echo "3/3  Probando que el modelo fusionado carga y escribe…"
python - "$SALIDA" <<'PY'
import sys
from mlx_lm import load, generate
m, t = load(sys.argv[1])
p = t.apply_chat_template([{"role": "user", "content": "Escribe una frase de bienvenida para el newsletter."}], add_generation_prompt=True)
print("     →", generate(m, t, prompt=p, max_tokens=40).strip().replace("\n", " ")[:200])
PY

# Las instrucciones de sistema con las que se entrenó este adaptador
FASE="${VARIANTE%-*}"
PROMPTS="datos/prueba/prompts_${FASE}.jsonl"; [ -f "$PROMPTS" ] || PROMPTS="datos/prueba/prompts.jsonl"
SISTEMA="$(python -c "import json,sys;print(json.loads(open(sys.argv[1]).readline())['system'])" "$PROMPTS")"
printf "%s" "$SISTEMA" | pbcopy

echo
echo "✅ Modelo listo en: $SALIDA"
echo "   En LM Studio aparece como «$NOMBRE» (pestaña My Models)."
echo
echo "📋 Copié al portapapeles las instrucciones de sistema (System Prompt) de este modelo:"
echo "   $SISTEMA"
echo
echo "Siguiente paso: abre LM Studio y sigue la guía en LEEME.md, sección «Usar el modelo en LM Studio»."
