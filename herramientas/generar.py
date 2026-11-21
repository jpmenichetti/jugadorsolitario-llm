"""Genera un artículo por cada pedido de datos/prueba/prompts.jsonl."""
import argparse, json, os, re, time
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler, make_logits_processors

ap = argparse.ArgumentParser()
ap.add_argument("--modelo", required=True)
ap.add_argument("--adaptador", default=None)
ap.add_argument("--salida", required=True)
ap.add_argument("--max-tokens", type=int, default=2500)
ap.add_argument("--temp", type=float, default=0.6)
ap.add_argument("--prompts", default="datos/prueba/prompts.jsonl")
a = ap.parse_args()

model, tok = load(a.modelo, adapter_path=a.adaptador)
# min_p descarta palabras muy improbables (ej. variantes en otros idiomas); la ventana de 256 tokens
# ayuda a evitar bucles de repetición a nivel de párrafo (ajustes de la fase 2)
sampler = make_sampler(temp=a.temp, top_p=0.9, min_p=0.05)
procs = make_logits_processors(repetition_penalty=1.1, repetition_context_size=256)
os.makedirs(a.salida, exist_ok=True)
pedidos = [json.loads(l) for l in open(a.prompts)]
for i, p in enumerate(pedidos, 1):
    print(f"[{i}/{len(pedidos)}] {p['titulo']} ...", flush=True)
    msgs = [{"role": "system", "content": p["system"]}, {"role": "user", "content": p["prompt"]}]
    # enable_thinking=False: Qwen3 escribe directo, sin su "modo razonamiento"
    prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False)
    t = time.time()
    texto = generate(model, tok, prompt=prompt, max_tokens=a.max_tokens, sampler=sampler, logits_processors=procs)
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.S).strip()
    with open(os.path.join(a.salida, f"{p['id']}.md"), "w") as f:
        f.write(f"# {p['titulo']}\n\n{texto.strip()}\n")
    print(f"     {len(texto.split())} palabras en {time.time()-t:.0f}s")
