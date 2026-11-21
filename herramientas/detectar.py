"""Evalúa con Pangram (detector de texto generado por IA) tus originales de prueba y todos los textos
generados en resultados/. Guarda los resultados en resultados/deteccion_pangram.json para no pagar
dos veces por el mismo texto. Necesita una clave de API en el archivo .pangram_key (no se sube a GitHub)
o en la variable de entorno PANGRAM_API_KEY.
API: https://docs.pangram.com/api-reference/ai-detection (envío asíncrono: POST /task y luego GET /task/{id})."""
import glob, hashlib, json, os, re, sys, time, urllib.request, urllib.error

BASE = "https://text.external-api.pangram.com/task"
CACHE = "resultados/deteccion_pangram.json"
COSTO_100_PALABRAS = 0.05  # USD, según la página de precios de Pangram

def clave():
    k = os.environ.get("PANGRAM_API_KEY", "").strip()
    if not k and os.path.exists(".pangram_key"): k = open(".pangram_key").read().strip()
    if not k: sys.exit("Falta la clave: guárdala en el archivo .pangram_key (ver LEEME).")
    return k

def cuerpo(path):  # mismo texto que usa el informe: sin la línea de título
    return re.sub(r"^# .*\n+", "", open(path).read(), count=1).strip()

def pedir(url, key, datos=None):
    req = urllib.request.Request(url, data=json.dumps(datos).encode() if datos else None,
                                 headers={"Content-Type": "application/json", "x-api-key": key},
                                 method="POST" if datos else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        msg = {401: "clave inválida o sin créditos", 400: "solicitud mal formada"}.get(e.code, e.read().decode()[:200])
        sys.exit(f"Error de Pangram ({e.code}): {msg}")

def evaluar(texto, key):
    tarea = pedir(BASE, key, {"text": texto, "model": "default", "public_dashboard_link": False})
    for _ in range(90):  # hasta ~3 minutos
        time.sleep(2)
        r = pedir(f"{BASE}/{tarea['task_id']}", key)
        if r.get("stage") == "STAGE_SUCCESS":
            return {k: r.get(k) for k in ("prediction_short", "headline", "fraction_ai", "fraction_ai_assisted", "fraction_human", "version")}
        if r.get("stage") == "STAGE_FAILED": return {"error": r.get("headline", "falló")}
    return {"error": "tiempo de espera agotado"}

cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
archivos = [("original", f) for f in sorted(glob.glob("datos/prueba/originales/*.md"))]
archivos += [(os.path.basename(os.path.dirname(f)), f) for f in sorted(glob.glob("resultados/*/*.md"))]
pendientes = []
for grupo, f in archivos:
    t = cuerpo(f); h = hashlib.sha256(t.encode()).hexdigest()[:16]
    if h not in cache or "error" in cache[h]: pendientes.append((grupo, f, t, h))
palabras = sum(len(t.split()) for *_, t, _ in pendientes)
print(f"Textos ya evaluados: {len(archivos) - len(pendientes)} | por evaluar: {len(pendientes)} (~{palabras:,} palabras, ~US${palabras/100*COSTO_100_PALABRAS:.2f})".replace(",", "."))
if not pendientes: sys.exit("Nada nuevo que evaluar.")
if input("¿Continuar? (s/n): ").strip().lower() != "s": sys.exit("Cancelado.")
key = clave()
for i, (grupo, f, t, h) in enumerate(pendientes, 1):
    r = evaluar(t, key); r.update(grupo=grupo, archivo=f)
    cache[h] = r
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False, indent=1)  # guardar tras cada texto
    print(f"[{i}/{len(pendientes)}] {grupo:22s} {os.path.basename(f)[:40]:40s} -> " +
          (r.get("error") or f"{r['prediction_short']}  (IA {r['fraction_ai']:.0%}, asistido {r['fraction_ai_assisted']:.0%})"))
print("\n✅ Listo. Ahora corre: bash 5_comparar.sh   (o bash 5_comparar.sh fichas)")
