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
4. **Revisión manual de Juan Pablo (TOEM):** el tono se parece más al suyo, pero no solo los datos duros son falsos: **todo el contenido del juego es inventado** (premisa, mecánicas, protagonista). El modelo no conoce juegos de nicho. Además apareció una **palabra en portugués** ("pessoal" en vez de "personal"). Qwen es multilingüe, y las palabras parecidas entre idiomas pueden colarse, sobre todo con temperatura alta.

**Ideas para corregir:**
- Repeticiones: ampliar la ventana de la penalización de repetición (de 64 a ~256 tokens). Es un ajuste de generación; no requiere reentrenar.
- Datos inventados: entregarle al modelo una **ficha con datos del juego** en el pedido (estudio, año, género, notas propias) y entrenarlo con fichas extraídas de cada artículo. Así el modelo aporta el estilo y tú aportas los hechos, que es además el uso realista de una herramienta así.
- Largo: indicar el largo deseado en el pedido, o revisar si más iteraciones o un learning rate mayor ayudan (búsqueda de hiperparámetros).

## 2026-11-21: Preparación de la fase 2 (con fichas)

**Motivo:** en la fase 1 el modelo aprendió el tono, pero inventó *todo* el contenido de los juegos. Un modelo de 4B no conoce juegos de nicho, y el entrenamiento le enseñó a sonar seguro y concreto.

**Cambio de enfoque:** el pedido ahora incluye una **ficha del juego** (estudio, año, género, premisa, mecánicas destacadas, opinión y veredicto). El modelo aporta el estilo y la ficha aporta los hechos. Es también el uso realista: Juan Pablo escribe notas rápidas y el modelo redacta el borrador.

- Se extrajeron 139 fichas, una por artículo (mediana ~130 palabras), solo con información presente en cada texto. Están en `datos/fichas.json` para revisarlas o corregirlas.
- La instrucción de sistema ahora pide usar solo los datos de la ficha y no inventar.
- Se quitaron 17 párrafos repetidos más que no detectó la limpieza anterior ("Thanks for reading…", créditos de imágenes, enlaces a otros posts, una nota al pie suelta).
- Se mantienen la misma división (121 / 10 / 8) y los mismos 15 artículos duplicados en la variante ponderada.
- Datos nuevos: `datos/fichas-uniforme/`, `datos/fichas-ponderado/`, `datos/prueba/prompts_fichas.jsonl`.

**Ajustes de generación** (aplican a todo lo que se genere desde ahora):
- Temperatura 0,7 → 0,6, más un filtro `min_p` 0,05 que descarta palabras muy improbables. Busca evitar intrusiones de otros idiomas como "pessoal".
- La ventana de la penalización de repetición pasa de 64 a 256 tokens, contra bucles a nivel de párrafo.

**Nota de método:** los resultados de la fase 1 no se regeneran. Al comparar las fases cambian a la vez el formato (con ficha) y los ajustes de generación. Dentro de la fase 2, la línea base y el modelo entrenado usan las mismas condiciones, así que esa comparación es limpia.

## 2026-11-21: Se agrega la detección de IA (Pangram)

**Idea de Juan Pablo:** agregar a la comparación un factor externo: qué probabilidad asigna un detector comercial a que cada texto haya sido escrito por IA.

- **Herramienta elegida:** Pangram. Soporta español y, según el propio fabricante, tiene más de 99% de precisión y una tasa de falsos positivos en español de 0,0026% (cifras no independientes). Cuesta US$ 0,05 por cada 100 palabras.
- **Alternativa descartada:** Binoculars, un método local y gratuito con dos modelos de lenguaje como jueces. Se descartó por tres razones: se evaluó sobre todo en inglés, al usar modelos Qwen como jueces se evaluaría a su propia familia, y es menos confiable que un servicio entrenado en español.
- **Implementación:** `7_detectar_ia.sh` y `herramientas/detectar.py`. Usa la API asíncrona (`POST /task` y luego `GET /task/{id}`) y guarda en caché por texto para no pagar dos veces. En el informe se agregan el % del texto escrito por IA, el % asistido por IA y cuántos textos se clasificaron como IA, más una etiqueta en cada texto de la lectura lado a lado.
- **Advertencia de método:** los detectores se equivocan, sobre todo fuera del inglés. Si un original se marca como IA, es un falso positivo y debe registrarse como tal.

## 2026-11-21: Primera evaluación con Pangram (fase 1)

Costo: **US$ 6,7** (24 textos: 8 originales, 8 del 4B sin entrenar, 8 del 4B uniforme).

| Versión | Clasificados como IA | % del texto escrito por IA |
|---|---|---|
| Originales | 0 de 8 | 0% (todos "Human" con certeza total) |
| 4B sin entrenar | 8 de 8 | 100% |
| 4B uniforme | 8 de 8 | 100% |

**Lectura:**
- Ningún falso positivo: Pangram reconoce los 8 originales como humanos.
- El entrenamiento de estilo **no engaña al detector en absoluto**. El modelo entrenado sigue con 100% IA en los 8 textos, aunque las métricas de estilo se acercaron a las del original.
- Aprendizaje: parecer humano ante un lector y ante un detector son cosas distintas. El detector capta patrones estadísticos (por ejemplo, la elección de palabras) que el fine-tuning de una época no cambia, aunque cambie la forma visible del texto.

**Política de uso decidida por Juan Pablo:** por el costo, Pangram se ejecuta solo en momentos importantes, no después de cada generación. Los originales ya están guardados en caché y no se vuelven a cobrar. Cada nueva versión de 8 textos cuesta ~US$ 2,2.

## 2026-11-21: Línea base fase 2: Qwen3-4B sin entrenar + ficha

Script: `2_linea_base.sh 4b fichas` → `resultados/4b-fichas-base/`

| Métrica (promedio) | Original | 4B sin entrenar + ficha |
|---|---|---|
| Palabras | 606 | 471 |
| Palabras por oración | 22,4 | 20,7 |
| Párrafos | 10,4 | 11,6 |
| Cursivas/negritas | 9,4 | 19 |
| Vocabulario típico (por 1000) | 118 | 100 |

**Observaciones:**
- **Los hechos ahora son correctos:** TOEM aparece como juego de 2021 del estudio sueco Something We Made. La ficha cumple su función.
- **Copia frases de la ficha casi textuales** ("cuatro puercoespines en un parque, niños escondidos", la lista de herramientas de la cámara). Se lee como una ficha en prosa.
- **Malinterpreta algunos datos:** dice que el jugador *es* el funcionario de turismo, y que en Sable uno se une "a otros jugadores".
- Convierte notas en primera persona en anécdotas ajenas ("un pescador loco convenció al jugador…").
- **El estilo genérico persiste:** subtítulos "###" en 3 de 8 textos, el doble de negritas y cursivas, y un "Verdicto" final en negrita. Tampoco usa la apertura "Bienvenidos…".
- Sin bucles de repetición ni palabras en otros idiomas en estos 8 textos.

**Lectura:** la ficha resuelve los datos, pero no el estilo. El entrenamiento debería aportar el estilo y enseñar a reescribir la ficha con voz propia en lugar de copiarla.

## 2026-11-21: Entrenamiento 2, 4B fichas-uniforme (70 iteraciones)

| Iteración | Val loss | Train loss |
|---|---|---|
| 1 | 2,403 | – |
| 15 | 1,825 | 1,998 (iter 10) |
| 30 | 1,774 | 1,795 |
| 45 | 1,740 | 1,690 (iter 40) |
| **60** | **1,729** | 1,674 |
| 70 | 1,856 | 1,258 |

- La velocidad bajó a ~70–77 tokens/s, porque los ejemplos son más largos con la ficha. Duró ~35 minutos, sin suspensión gracias a `caffeinate`.
- El Val loss parte más bajo que en la fase 1 (2,40 contra 2,69) porque la ficha ya entrega el contenido. No es comparable entre fases.
- **El patrón se repitió:** el mejor punto fue el **fin de la primera época (iteración 60)**. Al entrar en la segunda época (iteración 70), el Train loss cayó a 1,26 y el Val loss subió a 1,86: memorización inmediata.
- **Adaptador elegido:** iteración 60. El final (iteración 70) quedó guardado como `final_iter70_adapters.safetensors`.
- **Incidente:** la primera generación se lanzó con el adaptador de la iteración 70. Se detuvo y se volvió a generar con el de la 60.
- **Aprendizaje:** con este dataset, el óptimo está casi exactamente en una época. Para los próximos entrenamientos conviene fijar 60 iteraciones, o mantener 70 y elegir siempre el mejor punto guardado.

## 2026-11-21: Generación 4B fichas-uniforme (adaptador de la iteración 60)

| Métrica (promedio) | Original | Sin entrenar + ficha | Uniforme + ficha |
|---|---|---|---|
| Palabras | 606 | 471 | **246** |
| Palabras por oración | 22,4 | 20,7 | 17,7 |
| Párrafos | 10,4 | 11,6 | 5,8 |
| Cursivas/negritas | 9,4 | 19 | 1,5 |
| Vocabulario típico (por 1000) | 118 | 100 | 136 |

(La "riqueza de vocabulario" sube a 64,9%, pero es un efecto de que los textos son más cortos, no una mejora real.)

**Lo que mejoró:**
- Desaparecieron los subtítulos, las negritas y el "Verdicto". Usa prosa continua y un cierre al estilo de Juan Pablo ("Una pequeña joya, completamente recomendado…").
- Los hechos básicos son correctos (año, estudio, premisa).
- Sin bucles ni palabras en otros idiomas.

**Lo que empeoró o falta:**
- **Artículos de menos de la mitad del largo** (246 contra 606 palabras). El modelo aprendió a "pasar la ficha a prosa": recorre los puntos de la ficha y termina.
- **Sigue copiando la ficha**, incluso con enumeraciones ("Aparecen los siguientes: zoom, efectos, marcos…") y frases textuales.
- **Errores de comprensión:** confunde las medallas y la máscara de Sable con "un simulacro del vehículo", y cambia el género del protagonista de TOEM.
- No usa la apertura "Bienvenidos…".

**Lectura:** las fichas son demasiado completas y estructuradas. Como contienen casi todo el contenido, el modelo aprendió que el artículo es la ficha reescrita, y la riqueza de los originales (anécdotas, reflexiones, comparaciones, desarrollo de cada idea) no está en la ficha.

## 2026-11-21: Preparación de la fase 2b (ficha + largo)

- **Cambio único:** cada pedido incluye "Largo aproximado: N palabras" con el largo real del artículo, redondeado a 50. En la prueba se usa el largo del original (350 a 850 palabras). Las fichas no cambian.
- **Objetivo:** que el modelo deje de terminar cuando se le acaba la ficha y desarrolle las ideas como en los originales.
- Datos: `datos/fichas-largo-uniforme/`, `datos/fichas-largo-ponderado/`, `datos/prueba/prompts_fichas-largo.jsonl`.
- **Configuración:** `iters` pasa de 70 a **60** (una época exacta), porque en los dos entrenamientos anteriores el mejor Val loss fue en la iteración 60. Así el adaptador final ya es el óptimo y no hay que reemplazarlo.
- Los scripts 2 y 4 ahora aceptan cualquier fase (por ejemplo `bash 2_linea_base.sh 4b fichas-largo`).
