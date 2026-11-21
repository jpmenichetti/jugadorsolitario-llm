"""Compara los artículos originales de prueba con los generados por cada variante.
Métricas simples de estilo + lectura lado a lado. Escribe resultados/comparacion.html"""
import json, os, re, sys, html, glob, statistics as st
FICHAS = len(sys.argv) > 1 and sys.argv[1] == "fichas"   # fase 2: solo resultados con fichas
from collections import Counter

def cuerpo(path):
    t = open(path).read()
    return re.sub(r"^# .*\n+", "", t, count=1).strip()

def oraciones(t): return [o for o in re.split(r"(?<=[.!?…])\s+", re.sub(r"[*#>_-]", "", t)) if len(o.split()) > 2]
def palabras(t): return re.findall(r"[a-záéíóúñü]+", t.lower())

# vocabulario característico: palabras que usas mucho más que un texto genérico (se calcula desde tus artículos de entrenamiento)
tuyos = Counter()
for l in open("datos/uniforme/train.jsonl"):
    tuyos.update(palabras(json.loads(l)["messages"][-1]["content"]))
FUNC = set("de la que el en y a los se del las un por con no una su para es al lo como más pero sus le ya o este si porque esta entre cuando muy sin sobre también me hasta hay donde quien desde todo nos durante todos uno les ni contra otros ese eso ante ellos e esto mí antes algunos qué unos yo otro otras otra él tanto esa estos mucho quienes nada muchos cual poco ella estar estas algunas algo nosotros mi mis tú te ti tu tus ellas nosotras vosotros vosotras os mío mía míos mías tuyo tuya tuyos tuyas suyo suya suyos suyas nuestro nuestra nuestros nuestras vuestro vuestra vuestros vuestras esos esas estoy estás está estamos estáis están ser es son fue era han ha he juego juegos".split())
marcas = [w for w, n in tuyos.most_common(400) if w not in FUNC and len(w) > 3][:120]

def metricas(t):
    o, p = oraciones(t), palabras(t)
    return {
        "Palabras": len(p),
        "Palabras por oración": round(st.mean([len(x.split()) for x in o]), 1) if o else 0,
        "Párrafos": len([x for x in t.split("\n\n") if x.strip()]),
        "Riqueza de vocabulario (%)": round(100 * len(set(p)) / max(len(p), 1), 1),
        "Uso de tu vocabulario típico (por 1000 palabras)": round(1000 * sum(1 for w in p if w in marcas) / max(len(p), 1), 1),
        "Cursivas/negritas": t.count("*") // 2,
    }

orig = {os.path.basename(f)[:-3]: f for f in glob.glob("datos/prueba/originales/*.md")}
pedidos = [json.loads(l) for l in open("datos/prueba/prompts_fichas.jsonl" if FICHAS else "datos/prueba/prompts.jsonl")]
ORDEN = {"base": 0, "uniforme": 1, "ponderado": 2, "fichas-base": 0, "fichas-uniforme": 1, "fichas-ponderado": 2}
encontradas = [d for d in os.listdir("resultados") if glob.glob(f"resultados/{d}/*.md") and (("fichas" in d) == FICHAS)] if os.path.isdir("resultados") else []
variantes = ["original"] + sorted(encontradas, key=lambda d: (d.split("-")[0], ORDEN.get(d.split("-", 1)[-1], 9)))
textos = {v: {} for v in variantes}
for p in pedidos:
    textos["original"][p["id"]] = cuerpo(orig[p["id"]])
    for v in variantes[1:]:
        f = f"resultados/{v}/{p['id']}.md"
        if os.path.exists(f): textos[v][p["id"]] = cuerpo(f)

# Detección de IA (Pangram), si se ejecutó 7_detectar_ia.sh
import hashlib
DET = json.load(open("resultados/deteccion_pangram.json")) if os.path.exists("resultados/deteccion_pangram.json") else {}
def det(t): return DET.get(hashlib.sha256(t.encode()).hexdigest()[:16])
prom = {}
for v in variantes:
    ms = [metricas(t) for t in textos[v].values()]
    prom[v] = {k: round(st.mean(m[k] for m in ms), 1) for k in ms[0]} if ms else {}
    ds = [det(t) for t in textos[v].values()]; ds = [d for d in ds if d and "error" not in d]
    if DET and prom[v]:
        prom[v]["Pangram: % del texto escrito por IA"] = round(100 * st.mean(d["fraction_ai"] for d in ds), 1) if ds else "–"
        prom[v]["Pangram: % asistido por IA"] = round(100 * st.mean(d["fraction_ai_assisted"] for d in ds), 1) if ds else "–"
        prom[v]["Pangram: textos clasificados como IA"] = f"{sum(d['prediction_short'] == 'AI' for d in ds)} de {len(ds)}" if ds else "–"

E = html.escape
filas = "".join(f"<tr><td>{E(k)}</td>" + "".join(f"<td>{prom[v].get(k,'–')}</td>" for v in variantes) + "</tr>" for k in prom["original"])
ETIQ = {"base": "sin entrenar", "uniforme": "uniforme", "ponderado": "ponderado", "fichas-base": "sin entrenar + ficha", "fichas-uniforme": "uniforme + ficha", "fichas-ponderado": "ponderado + ficha"}
nombres = {"original": "Tu original"}
for v in variantes[1:]:
    t, _, var = v.partition("-")
    nombres[v] = f"Qwen3 {t.upper()} · {ETIQ.get(var, var)}"
def md2html(t): return "".join(f"<p>{E(x).replace(chr(10), '<br>')}</p>" for x in t.split("\n\n"))
secciones = ""
for p in pedidos:
    def etiqueta(v):
        d = det(textos[v].get(p["id"], ""))
        return f"<p class='det'>Pangram: <b>{E(d['prediction_short'])}</b> (IA {d['fraction_ai']:.0%})</p>" if d and "error" not in d else ""
    cols = "".join(f"<div class='col'><h4>{nombres[v]}</h4>{etiqueta(v)}{md2html(textos[v].get(p['id'], '(sin generar)'))}</div>" for v in variantes)
    secciones += f"<details><summary>{E(p['titulo'])}</summary><div class='grid'>{cols}</div></details>"

page = f"""<!doctype html><html lang=es><meta charset=utf-8><title>Comparación — LLM Personal</title>
<style>body{{font:15px/1.5 -apple-system,system-ui;max-width:1400px;margin:2em auto;padding:0 1em;color:#222}}
table{{border-collapse:collapse;margin:1em 0}}td,th{{border:1px solid #ddd;padding:.4em .8em;text-align:right}}td:first-child{{text-align:left}}
th{{background:#f3f3f3}}details{{margin:.6em 0;border:1px solid #ddd;border-radius:6px;padding:.5em 1em}}summary{{cursor:pointer;font-weight:600}}
.grid{{display:grid;grid-template-columns:repeat({len(variantes)},1fr);gap:1em}}.col{{font-size:13px;border-top:3px solid #999;padding-top:.3em}}
.col p{{margin:.5em 0}}.det{{font-size:12px;background:#f3f3f3;padding:.2em .5em;border-radius:4px}}</style>
<h1>El Jugador Solitario: original vs. modelo{" (fase 2: con fichas)" if FICHAS else " (fase 1: sin fichas)"}</h1>
<p>Promedios sobre los {len(pedidos)} artículos de prueba (que el modelo nunca vio). Cuanto más se parezca una columna a <b>Tu original</b>, mejor imitó tu estilo.</p>
<table><tr><th>Métrica</th>{''.join(f'<th>{nombres[v]}</th>' for v in variantes)}</tr>{filas}</table>
<h2>Lectura lado a lado</h2><p>Consejo: lee primero las versiones generadas sin mirar la original y anota cuál "suena" más a ti.</p>{secciones}</html>"""
os.makedirs("resultados", exist_ok=True)
SALIDA = "resultados/comparacion_fichas.html" if FICHAS else "resultados/comparacion.html"
open(SALIDA, "w").write(page)
print("Informe escrito en", SALIDA)
for v in variantes: print(f"{nombres[v]:26s}", prom[v])
if DET: print("(Incluye resultados de Pangram. Los detectores pueden equivocarse, sobre todo fuera del inglés.)")
