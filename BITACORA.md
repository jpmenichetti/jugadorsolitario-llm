# Bitácora: LLM Personal

Registro cronológico de lo ejecutado, lo observado y lo aprendido. Sirve de base para el documento final.

---

## 2026-11-21: Preparación

- **Datos:** export de Substack con 148 posts (~86.700 palabras). Se usan 139 artículos, tras quitar 9 que no son reseñas y 228 párrafos repetidos. División 121 / 10 / 8 (entrenamiento / validación / prueba).
- **Ponderación:** el export solo trae aperturas de email, no lecturas web ni comentarios. Se usa la tasa de apertura relativa a los posts vecinos; los 15 mejores se duplican en la variante "ponderado".
- **Modelos:** se decide usar la familia Qwen3 en dos tamaños (4B y 8B), para que al compararlos solo cambie el tamaño.
- **Herramientas:** MLX + mlx-lm (LoRA), uv para el entorno de Python, modelos de mlx-community en Hugging Face.
- **Repositorio:** `jpmenichetti/jugadorsolitario-llm` (privado).

## 2026-11-21: Línea base Qwen3-4B (sin entrenar)

Script: `2_linea_base.sh` → `resultados/4b-base/`

**Observaciones:**
- Largo similar a los originales (480–615 palabras).
- Estilo de blog genérico: subtítulos tipo "¿Qué es X?", exceso de negritas, tono grandilocuente y vago. No usa la apertura "Bienvenidos a El Jugador Solitario…".
- Inventa datos: atribuye TOEM a Giant Sparrow (es de Something We Made) y Sable a Ninja Theory (es de Shedworks).

**Aprendizaje:** el fine-tuning enseña **estilo, no conocimiento**. Hay que evaluar por separado "¿suena a mí?" y "¿es correcto?".

## 2026-11-21: Entrenamiento 1, 4B uniforme

Configuración: LoRA rank 16, 16 capas, lr 5e-5, batch 2 × acumulación 2, 180 iteraciones planificadas (~3 épocas).
Registro: `registros/entrenamiento_4b-uniforme-20261121-1323.log`

- Parámetros entrenables: 14,7 M de 4.022 M (0,365%).
- Velocidad: ~90–100 tokens/s (~4 min cada 10 iteraciones).

| Iteración | Val loss | Train loss |
|---|---|---|
| 1 | 2,694 | – |
| 30 | 2,159 | 2,161 |
| **60** | **2,085** | 2,078 |
| 90 | 2,187 | 1,518 |
| 120 | 2,181 | 1,513 |
| 150 | 2,596 | 0,885 (iter 140) |

**Qué pasó:**
- La gran mejora ocurrió en las primeras 30 iteraciones. El mejor Val loss se alcanzó al terminar la primera época (iteración ~60).
- Al comenzar la segunda época, el Train loss cayó de golpe (2,08 → 1,53) porque el modelo releía artículos ya vistos. En la tercera época se desplomó (0,885) mientras el Val loss subía a 2,596: **sobreajuste o memorización**.
- La pantalla del Mac se bloqueó y el sistema se suspendió. Las iteraciones 140→150 tardaron ~1,5 horas, cuando normalmente toman ~4 minutos. El entrenamiento se detuvo manualmente en la iteración 150.

**Decisiones:**
- Se elige el adaptador de la **iteración 60** como el oficial (`adapters.safetensors`). El resto de los puntos de guardado se conservan.
- Nueva configuración: **70 iteraciones (~1 época)**, con medición y guardado cada 15.
- Los scripts 2, 3 y 4 ahora usan `caffeinate` para que el Mac no se duerma. La tapa debe quedar abierta.
- Los registros llevan fecha y hora, y los adaptadores anteriores se respaldan en vez de sobrescribirse.

**Aprendizajes:**
1. **Con pocos datos, una época basta.** Con ~120 artículos, más pasadas llevan a memorizar en vez de generalizar.
2. **El Train loss engaña; el Val loss es la verdad.** Un Train loss bajísimo puede significar que el modelo se sabe los textos de memoria.
3. **Guardar puntos intermedios salva el experimento.** Permitió recuperar el mejor modelo aunque el final había empeorado.
4. **La logística también importa.** Un Mac que se duerme detiene el entrenamiento sin avisar.

## 2026-11-21: Generación 4B uniforme (adaptador de la iteración 60)

Script: `4_generar.sh uniforme` → `resultados/4b-uniforme/`. Comparación: `resultados/comparacion.html`.

| Métrica (promedio de 8) | Original | 4B sin entrenar | 4B uniforme |
|---|---|---|---|
| Palabras | 606 | 545 | **373** |
| Palabras por oración | 22,4 | 18,5 | 20,9 |
| Párrafos | 10,4 | 19,4 | 8,6 |
| Cursivas/negritas | 9,4 | 32,9 | 7,9 |
| Vocabulario típico (por 1000 palabras) | 118 | 95 | **172** |

**Lo que mejoró (estilo):**
- Desaparecieron los subtítulos genéricos y el exceso de negritas. Ahora usa prosa continua, cursivas para el nombre del juego y cierre con recomendación y plataformas ("Disponible para PC (Steam)…").
- Aparecen giros propios, como "En mi caso particular…" y "Lo recomiendo sin duda a quienes…".
- La estructura (número de párrafos, largo de oraciones) se acerca a los originales.

**Lo que empeoró o falta:**
- **Artículos más cortos:** 373 palabras en promedio, contra 606 de los originales.
- **Caricatura:** usa tu vocabulario típico más que tú mismo (172 contra 118 por cada 1000 palabras). Imita los rasgos más visibles con exageración.
- **Bucle de repetición en 1 de 8 (Sable):** repite el párrafo de bienvenida 5 veces y otro párrafo 4 veces. La penalización de repetición solo mira los últimos 64 tokens, así que no detecta repeticiones a nivel de párrafo.
- **Inventa más y con más seguridad:** Blue Prince descrito como mezcla de Minecraft, GTA V y Bob's Burgers; Sable atribuido a Playdead; un "Toby Fox, director de Square Enix".

**Aprendizajes:**
1. **El estilo se aprende rápido:** con una sola época ya se nota el cambio de forma.
2. **El fine-tuning de estilo empeora las alucinaciones.** Tus artículos afirman datos concretos (estudio, año, mecánicas), así que el modelo aprende a *sonar* concreto y seguro, pero sin saber los datos. El resultado son invenciones más específicas y convincentes que las del modelo base.
3. **Un modelo pequeño tiende a la caricatura y a los bucles:** exagera los rasgos frecuentes y puede quedar atrapado repitiendo.

**Ideas para corregir:**
- Repeticiones: ampliar la ventana de la penalización de repetición (de 64 a ~256 tokens). Es un ajuste de generación; no requiere reentrenar.
- Datos inventados: entregarle al modelo una **ficha con datos del juego** en el pedido (estudio, año, género, notas propias) y entrenarlo con fichas extraídas de cada artículo. Así el modelo aporta el estilo y tú aportas los hechos, que es además el uso realista de una herramienta así.
- Largo: indicar el largo deseado en el pedido, o revisar si más iteraciones o un learning rate mayor ayudan (búsqueda de hiperparámetros).
