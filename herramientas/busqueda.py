"""Búsqueda de hiperparámetros: entrena el 4B varias veces cambiando UN parámetro a la vez respecto
de la configuración base (config/base.yaml) y arma una tabla con el mejor Val loss de cada corrida.
Si se interrumpe, al volver a correrlo se salta las corridas que ya terminaron."""
import copy, csv, os, re, subprocess, sys, time, yaml

MODELO = "mlx-community/Qwen3-4B-4bit"
DATOS = "datos/fichas-largo-uniforme"
# (nombre, qué se cambia, cambios respecto de la base)
CORRIDAS = [
    ("lr-2e-5",    "learning rate 2e-5 (más lento)",  {"learning_rate": 2.0e-5}),
    ("lr-1e-4",    "learning rate 1e-4 (más rápido)", {"learning_rate": 1.0e-4}),
    ("rank-8",     "rank 8 (adaptador más chico)",    {"lora_parameters": {"rank": 8}}),
    ("rank-32",    "rank 32 (adaptador más grande)",  {"lora_parameters": {"rank": 32}}),
    ("capas-8",    "8 capas adaptadas",               {"num_layers": 8}),
    ("capas-todas","las 36 capas adaptadas",          {"num_layers": -1}),
]
REFERENCIA = ("base", "configuración base (lr 5e-5, rank 16, 16 capas)",
              "registros/entrenamiento_4b-fichas-largo-uniforme-20261121-1818.log")
os.makedirs("registros/hiper", exist_ok=True); os.makedirs("config/hiper", exist_ok=True)
base = yaml.safe_load(open("config/base.yaml"))

def leer_val(log):
    if not os.path.exists(log): return []
    t = re.sub(r"\x1b\[[0-9;]*m", "", open(log, errors="ignore").read()).replace("\r", "\n")
    return [(int(i), float(v)) for i, v in re.findall(r"^\s*(\d+)\s+val\s+([\d.]+)", t, re.M)]

def terminada(log):
    vals = leer_val(log); return bool(vals) and vals[-1][0] >= base["iters"]

filas = []
v = leer_val(REFERENCIA[2])
if v: filas.append(dict(nombre=REFERENCIA[0], cambio=REFERENCIA[1], vals=v, minutos="~35"))
for i, (nombre, cambio, ajustes) in enumerate(CORRIDAS, 1):
    log = f"registros/hiper/{nombre}.log"
    if terminada(log):
        print(f"[{i}/{len(CORRIDAS)}] {nombre}: ya estaba hecha, la salto.")
    else:
        cfg = copy.deepcopy(base); cfg["save_every"] = base["iters"]  # solo guarda el adaptador final
        for k, val in ajustes.items():
            if isinstance(val, dict): cfg[k].update(val)
            else: cfg[k] = val
        ruta = f"config/hiper/{nombre}.yaml"; yaml.safe_dump(cfg, open(ruta, "w"), allow_unicode=True)
        print(f"\n[{i}/{len(CORRIDAS)}] {nombre}: {cambio}  ({time.strftime('%H:%M')})", flush=True)
        t0 = time.time()
        with open(log, "w") as f:
            r = subprocess.run(["mlx_lm.lora", "--config", ruta, "--model", MODELO, "--data", DATOS,
                                "--adapter-path", f"adaptadores/hiper/{nombre}"], stdout=f, stderr=subprocess.STDOUT)
        open(log, "a").write(f"\nDURACION_MIN {(time.time()-t0)/60:.0f}\n")
        if r.returncode != 0: print(f"   ⚠️ terminó con error, revisa {log}")
    d = re.findall(r"DURACION_MIN (\d+)", open(log, errors="ignore").read()) if os.path.exists(log) else []
    filas.append(dict(nombre=nombre, cambio=cambio, vals=leer_val(log), minutos=d[-1] if d else "?"))
    # tabla parcial tras cada corrida, por si se interrumpe
    with open("resultados/hiperparametros.md", "w") as f:
        f.write("# Búsqueda de hiperparámetros (Qwen3-4B, fichas + largo, 60 iteraciones)\n\n")
        f.write("| Corrida | Qué cambia | Val inicial | Mejor Val loss | En iteración | Val final | Minutos |\n|---|---|---|---|---|---|---|\n")
        for x in filas:
            if not x["vals"]: f.write(f"| {x['nombre']} | {x['cambio']} | – | – | – | – | {x['minutos']} |\n"); continue
            mejor = min(x["vals"], key=lambda p: p[1])
            f.write(f"| {x['nombre']} | {x['cambio']} | {x['vals'][0][1]:.3f} | **{mejor[1]:.3f}** | {mejor[0]} | {x['vals'][-1][1]:.3f} | {x['minutos']} |\n")
        f.write("\nVal loss por iteración:\n\n")
        for x in filas: f.write(f"- {x['nombre']}: " + ", ".join(f"{i}→{v:.3f}" for i, v in x["vals"]) + "\n")
print("\n✅ Búsqueda terminada. Tabla en resultados/hiperparametros.md")
