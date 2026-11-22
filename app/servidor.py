"""App local del LLM Personal: una interfaz en el navegador para usar los modelos entrenados.

Uso: doble clic en 9_app.command   (o, desde la carpeta del proyecto: python app/servidor.py)
Todo corre en tu Mac: el servidor escucha solo en 127.0.0.1 y no necesita internet
(salvo la primera vez que se use un modelo base que aún no esté descargado).

Para probar la interfaz sin cargar modelos: LLM_FALSO=1 python app/servidor.py
"""
import datetime, difflib, gc, json, os, queue, re, socket, sys, threading, time, unicodedata, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
PUERTO = int(os.environ.get("LLM_PUERTO", "8765"))
FALSO = os.environ.get("LLM_FALSO") == "1"
CARPETA_GUARDADOS = os.path.join("resultados", "app")
HTML = os.path.join(RAIZ, "app", "index.html")

BASES = {"4b": "mlx-community/Qwen3-4B-4bit", "8b": "mlx-community/Qwen3-8B-4bit"}

INTRO = ("Eres el autor de El Jugador Solitario, un newsletter en español donde cada semana "
         "recomiendas un videojuego que se puede disfrutar en solitario.")
# Las mismas instrucciones de sistema que se usaron al entrenar cada adaptador (datos/prueba/prompts_*.jsonl).
MODOS = {
    "reescribir": {
        "nombre": "Reescribir un borrador",
        "descripcion": "Pegas un borrador neutro con todos los datos y el modelo lo reescribe con tu voz. "
                       "Es el modelo de la fase 3 (8B, transferencia de estilo): el que mejor resultado dio.",
        "tamano": "8b", "adaptador": "adaptadores/8b-transferencia-uniforme",
        "system": INTRO + " Te entregan un borrador escrito en estilo neutro y lo reescribes con tu voz y tu "
                          "estilo, conservando todos los datos: no agregues ni quites información sobre el juego.",
    },
    "ficha": {
        "nombre": "Escribir desde una ficha",
        "descripcion": "Escribes una ficha con los datos del juego y el modelo redacta el artículo completo. "
                       "Es el modelo de la fase 2b (8B con fichas). Puede inventar detalles: revisa los datos.",
        "tamano": "8b", "adaptador": "adaptadores/8b-fichas-largo-uniforme",
        "system": INTRO + " Escribes a partir de la ficha que te entregan: usa solo los datos de la ficha y no "
                          "inventes información sobre el juego.",
    },
    "libre": {
        "nombre": "Solo con el título",
        "descripcion": "Le das solo el nombre del juego y, si quieres, un subtítulo. Es el modelo de la fase 1 (4B). "
                       "Sirve para ver el estilo puro, pero inventa casi todo el contenido.",
        "tamano": "4b", "adaptador": "adaptadores/4b-uniforme",
        "system": INTRO,
    },
}


def armar_prompt(modo, d):
    titulo = (d.get("titulo") or "").strip() or "un juego"
    sub = (d.get("subtitulo") or "").strip()
    if modo == "reescribir":
        return f"Reescribe con tu estilo este borrador sobre «{titulo}»:\n\n{(d.get('borrador') or '').strip()}"
    p = f"Escribe el artículo de esta semana sobre «{titulo}»."
    if sub:
        p += f"\nSubtítulo: {sub}"
    if modo == "ficha":
        largo = str(d.get("largo") or "").strip()
        if largo:
            p += f"\nLargo aproximado: {largo} palabras"
        p += f"\n\nFicha:\n{(d.get('ficha') or '').strip()}"
    return p


def palabras(t):
    return re.findall(r"[a-záéíóúñü0-9]+", t.lower())


def parecido(a, b):
    """Secuencia de palabras en común (0 a 1), la misma medida de la bitácora."""
    pa, pb = palabras(a), palabras(b)
    if not pa or not pb:
        return None
    return round(difflib.SequenceMatcher(None, pa, pb, autojunk=False).ratio(), 2)


def limpiar(texto):
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.S).strip()
    # El modelo a veces agrega un título "# Nombre" que no va en el artículo (ver bitácora, fase 3).
    quitado = None
    m = re.match(r"#\s+([^\n]*)\n+", texto)
    if m:
        quitado, texto = m.group(1).strip(), texto[m.end():]
    return texto.strip(), quitado


# ---------------------------------------------------------------------------
# Motor: un único hilo hace todo el trabajo con MLX (cargar y generar).
# Así la GPU nunca recibe dos pedidos a la vez y el navegador solo lee eventos.
# ---------------------------------------------------------------------------
class Trabajo:
    def __init__(self, tipo, datos=None):
        self.tipo, self.datos = tipo, datos or {}
        self.salida = queue.Queue()
        self.parar = threading.Event()


class Motor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.pendientes = queue.Queue()
        self.clave = None          # (tamaño, adaptador o None) del modelo en memoria
        self.model = self.tok = None
        self.estado = "Sin modelo cargado"
        self.actual = None

    # -- carga -------------------------------------------------------------
    def ruta_base(self, tamano):
        """Usa la copia ya descargada si existe (funciona sin internet)."""
        from huggingface_hub import snapshot_download
        try:
            return snapshot_download(BASES[tamano], local_files_only=True)
        except Exception:
            self.estado = f"Descargando el modelo base {tamano.upper()} (solo la primera vez)…"
            return snapshot_download(BASES[tamano])

    def cargar(self, tamano, adaptador, avisar):
        clave = (tamano, adaptador)
        if clave == self.clave:
            return
        nombre = f"{tamano.upper()} " + ("entrenado" if adaptador else "sin entrenar")
        self.estado = f"Cargando {nombre}…"
        avisar({"t": "estado", "v": self.estado + " (unos segundos; la primera vez puede tardar más)"})
        self.model = self.tok = None
        self.clave = None
        gc.collect()
        if FALSO:
            time.sleep(1.0)
        else:
            import mlx.core as mx
            from mlx_lm import load
            try:
                mx.clear_cache()
            except Exception:
                pass
            self.model, self.tok = load(self.ruta_base(tamano), adapter_path=adaptador)
        self.clave = clave
        self.estado = f"Listo: {nombre}"
        avisar({"t": "estado", "v": self.estado})

    # -- generación ----------------------------------------------------------
    def generar(self, job):
        d = job.datos
        modo = d.get("modo") if d.get("modo") in MODOS else "reescribir"
        cfg = MODOS[modo]
        adaptador = None if d.get("sin_entrenar") else cfg["adaptador"]
        if adaptador and not os.path.isdir(adaptador):
            raise RuntimeError(f"No encuentro {adaptador}. ¿Entrenaste ese modelo?")
        self.cargar(cfg["tamano"], adaptador, job.salida.put)

        temp = min(max(float(d.get("temperatura", 0.6)), 0.0), 1.5)
        max_tokens = int(d.get("max_tokens") or 3000)
        msgs = [{"role": "system", "content": cfg["system"]}, {"role": "user", "content": armar_prompt(modo, d)}]
        job.salida.put({"t": "estado", "v": "Escribiendo…"})
        t0, texto, n, tps = time.time(), "", 0, 0.0

        if FALSO:
            base = (d.get("borrador") or "Este es un texto de prueba.").replace(" es un ", " es un *gran* ", 1)
            base = "# Título\n\nBienvenidos a El Jugador Solitario.\n\n" + base + "\n\nCompletamente recomendado."
            for w in re.split(r"(\s+)", base):
                if job.parar.is_set():
                    break
                time.sleep(0.01)
                texto += w
                n += 1
                job.salida.put({"t": "texto", "v": w})
            tps, n_prompt = 25.0, 500
        else:
            from mlx_lm import stream_generate
            from mlx_lm.sample_utils import make_logits_processors, make_sampler
            # enable_thinking=False: Qwen3 escribe directo, sin "modo razonamiento" (igual que en generar.py)
            prompt = self.tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False)
            n_prompt = len(prompt)
            if n_prompt > 5000:
                job.salida.put({"t": "aviso", "v": f"La entrada es larga ({n_prompt} tokens). El modelo se entrenó con "
                                                    "textos de hasta ~5.000 tokens; puede perder calidad."})
            sampler = make_sampler(temp=temp, top_p=0.9, min_p=0.05)
            procs = make_logits_processors(repetition_penalty=1.1, repetition_context_size=256)
            for r in stream_generate(self.model, self.tok, prompt, max_tokens=max_tokens,
                                     sampler=sampler, logits_processors=procs):
                if job.parar.is_set():
                    break
                texto += r.text
                n, tps = r.generation_tokens, r.generation_tps
                job.salida.put({"t": "texto", "v": r.text})
                if n % 20 == 0:
                    job.salida.put({"t": "progreso", "tokens": n, "tps": round(tps, 1)})

        final, titulo_quitado = limpiar(texto)
        job.salida.put({
            "t": "fin", "texto": final, "titulo_quitado": titulo_quitado, "detenido": job.parar.is_set(),
            "tokens": n, "tokens_entrada": n_prompt, "tps": round(tps, 1), "segundos": round(time.time() - t0, 1),
            "palabras": len(final.split()),
            "parecido": parecido(d.get("borrador", ""), final) if modo == "reescribir" else None,
            "modelo": f"{cfg['tamano'].upper()} " + ("entrenado" if adaptador else "sin entrenar"),
        })

    def run(self):
        while True:
            job = self.pendientes.get()
            self.actual = job
            try:
                if job.tipo == "precargar":
                    cfg = MODOS["reescribir"]
                    if os.path.isdir(cfg["adaptador"]):
                        self.cargar(cfg["tamano"], cfg["adaptador"], lambda e: None)
                else:
                    self.generar(job)
            except Exception as e:  # noqa: BLE001 — cualquier error se muestra en la app
                if self.clave is None:
                    self.estado = "Sin modelo cargado"
                elif not self.estado.startswith("Listo"):
                    t, a = self.clave
                    self.estado = f"Listo: {t.upper()} " + ("entrenado" if a else "sin entrenar")
                print("ERROR:", repr(e), file=sys.stderr)
                job.salida.put({"t": "error", "v": str(e) or repr(e)})
            finally:
                self.actual = None


MOTOR = Motor()


# ---------------------------------------------------------------------------
# Guardado e historial (resultados/app/)
# ---------------------------------------------------------------------------
def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:50] or "sin-titulo"


def guardar(d):
    os.makedirs(CARPETA_GUARDADOS, exist_ok=True)
    nombre = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + slug(d.get("titulo", ""))
    with open(os.path.join(CARPETA_GUARDADOS, nombre + ".md"), "w") as f:
        f.write(d.get("texto", "").strip() + "\n")
    d["guardado"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(os.path.join(CARPETA_GUARDADOS, nombre + ".json"), "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return nombre


def historial():
    if not os.path.isdir(CARPETA_GUARDADOS):
        return []
    items = []
    for a in sorted(os.listdir(CARPETA_GUARDADOS), reverse=True):
        if a.endswith(".json"):
            try:
                with open(os.path.join(CARPETA_GUARDADOS, a)) as f:
                    d = json.load(f)
                items.append({"id": a[:-5], "titulo": d.get("titulo", ""), "modo": d.get("modo", ""),
                              "modelo": (d.get("stats") or {}).get("modelo", ""), "fecha": d.get("guardado", ""),
                              "palabras": len(d.get("texto", "").split())})
            except Exception:
                pass
    return items


# ---------------------------------------------------------------------------
# Servidor HTTP
# ---------------------------------------------------------------------------
class Manejador(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silencio en la Terminal

    def responder(self, cuerpo, tipo="application/json; charset=utf-8", codigo=200):
        if not isinstance(cuerpo, (bytes, bytearray)):
            cuerpo = json.dumps(cuerpo, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def leer_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta in ("/", "/index.html"):
            with open(HTML, "rb") as f:
                return self.responder(f.read(), "text/html; charset=utf-8")
        if ruta == "/api/info":
            return self.responder({
                "estado": MOTOR.estado, "ocupado": MOTOR.actual is not None and MOTOR.actual.tipo == "generar",
                "falso": FALSO,
                "modos": {k: {"nombre": v["nombre"], "descripcion": v["descripcion"],
                              "disponible": os.path.isdir(v["adaptador"])} for k, v in MODOS.items()},
            })
        if ruta == "/api/historial":
            return self.responder(historial())
        if ruta.startswith("/api/historial/"):
            ident = os.path.basename(ruta)
            p = os.path.join(CARPETA_GUARDADOS, ident + ".json")
            if os.path.isfile(p):
                with open(p, "rb") as f:
                    return self.responder(f.read())
        self.responder({"error": "no encontrado"}, codigo=404)

    def do_POST(self):
        ruta = self.path.split("?")[0]
        if ruta == "/api/generar":
            job = Trabajo("generar", self.leer_json())
            if MOTOR.actual is not None and MOTOR.actual.tipo == "generar":
                return self.responder({"error": "Ya hay un texto generándose."}, codigo=409)
            MOTOR.pendientes.put(job)
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                while True:
                    try:
                        ev = job.salida.get(timeout=15)
                    except queue.Empty:
                        ev = {"t": "latido"}  # mantiene viva la conexión mientras carga el modelo
                    self.wfile.write((json.dumps(ev, ensure_ascii=False) + "\n").encode())
                    self.wfile.flush()
                    if ev["t"] in ("fin", "error"):
                        break
            except (BrokenPipeError, ConnectionResetError):
                job.parar.set()  # el navegador se cerró: no seguir generando
            return
        if ruta == "/api/detener":
            if MOTOR.actual is not None:
                MOTOR.actual.parar.set()
            return self.responder({"ok": True})
        if ruta == "/api/guardar":
            return self.responder({"ok": True, "id": guardar(self.leer_json())})
        if ruta == "/api/salir":
            self.responder({"ok": True})
            if MOTOR.actual is not None:
                MOTOR.actual.parar.set()
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        self.responder({"error": "no encontrado"}, codigo=404)


def puerto_ocupado(p):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", p)) == 0


def main():
    url = f"http://127.0.0.1:{PUERTO}/"
    if puerto_ocupado(PUERTO):
        print(f"La app ya está abierta. Abriendo {url}")
        webbrowser.open(url)
        return
    servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador)
    MOTOR.start()
    MOTOR.pendientes.put(Trabajo("precargar"))  # deja listo el modelo principal mientras abres la página
    print(f"\n  App del LLM Personal en {url}")
    print("  Para cerrarla: botón «Salir» en la app, o Ctrl+C aquí.\n")
    if os.environ.get("LLM_SIN_NAVEGADOR") != "1":
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    print("  App cerrada.")


if __name__ == "__main__":
    main()
