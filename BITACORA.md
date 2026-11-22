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

## 2026-11-21: Entrenamiento 3 + generación, 4B fichas-largo-uniforme

Entrenamiento: 60 iteraciones, Val loss 2,403 → 1,823 → 1,771 → 1,738 → **1,725** (iteración 60, la final). Casi idéntico al entrenamiento 2: la línea de largo pesa poco en la pérdida.

**Largo pedido vs. generado:**

| Artículo | Pedido | Generado | Original |
|---|---|---|---|
| Old Man's Journey | 350 | 310 | 342 |
| The Callisto Protocol | 400 | 340 | 408 |
| Alan Wake II | 750 | 544 | 745 |
| Sable | 450 | 353 | 454 |
| Dave the Diver | 650 | 747 | 671 |
| Blue Prince | 750 | 802 | 758 |
| Spirit of the North | 850 | 649 | 828 |
| TOEM | 650 | 590 | 655 |

| Métrica (promedio) | Original | Uniforme + ficha | Uniforme + ficha + largo |
|---|---|---|---|
| Palabras | 606 | 246 | **540** |
| Párrafos | 10,4 | 5,8 | **10,2** |
| Palabras por oración | 22,4 | 17,7 | 19,0 |
| Cursivas/negritas | 9,4 | 1,5 | 2,8 |
| Vocabulario típico (por 1000) | 118 | 136 | 151 |

**Lo que funcionó:** el modelo **respeta el largo pedido** (sigue la tendencia: textos cortos cuando se piden cortos, largos cuando se piden largos) y la estructura de párrafos ya coincide con los originales. Sin subtítulos, sin bucles exactos, sin palabras en otros idiomas.

**El nuevo problema: relleno.** Para alcanzar el largo, el modelo **recicla la ficha**: en TOEM menciona tres veces los puercoespines y "algo que me inspire una melodía", y en Blue Prince repite la grilla de 5x9 y los 50 pasos. Cuando se le acaba la ficha, **vuelve a inventar** (un niño que "debe ser invisible al menos 10 segundos") y comete errores de comprensión ("la jugabilidad es bastante baja" en vez de "la dificultad es baja"; "estudio sueño"). La exageración del vocabulario típico aumentó (151 vs. 118).

**Aprendizaje central del experimento:** el contenido de un artículo tiene que venir de alguna parte. Hay dos fuentes posibles: la ficha (lo que aporta el autor) o el conocimiento del modelo. Un modelo de 4B no conoce estos juegos, así que si la ficha no trae suficiente material, solo puede repetir o inventar. El fine-tuning resolvió la **forma** (estructura, largo, cierre, ausencia de negritas), pero no puede crear el **fondo**.

## 2026-11-21: Aclaración de objetivo (Juan Pablo)

El objetivo del proyecto es **aprender la mecánica, los parámetros y los resultados posibles** de los LLM personalizados, no obtener un modelo que escriba artículos publicables. No se usará para escribir en su nombre. Desde aquí, cada experimento se elige por lo que enseña, no para pulir el resultado.

## 2026-11-21: Experimento futuro acordado: transferencia de estilo

Se retoma después de terminar el recorrido actual (8B, hiperparámetros, ponderado).

- **Idea de Juan Pablo:** un modelo grande (Claude) investiga y escribe el contenido con referencias de internet, el modelo personalizado lo reescribe con su estilo, y Claude verifica al final que no se hayan deformado los datos.
- **Esquema elegido: el "correcto", con reentrenamiento.** Un modelo grande reescribe cada uno de los 139 artículos en un estilo neutro, conservando el contenido. Con eso se arman pares "versión genérica → original" y se entrena un modelo específico de reescritura.
- **La verificación:** Claude solo marca errores y hace cambios mínimos (o devuelve una lista para que el modelo personalizado corrija), para no borrar el estilo ganado. Conviene conservar las fuentes del paso 1.
- **Preguntas a responder:** ¿se pierden o deforman datos al reescribir? ¿Cuántos errores detecta el verificador? ¿La verificación borra el estilo? ¿Pangram sigue detectando IA? Comparación adicional: Claude con ejemplos en el pedido, sin fine-tuning.

## 2026-11-21: Entrenamiento 4, 8B fichas-largo-uniforme (misma configuración que el 4B)

| Iteración | Val loss 4B | Val loss 8B |
|---|---|---|
| 1 | 2,403 | **2,110** |
| 15 | 1,823 | 1,694 |
| 30 | 1,771 | 1,638 |
| 45 | 1,738 | 1,615 |
| 60 | 1,725 | **1,599** |
| Mejora total | 0,678 | 0,511 |

- Parámetros entrenables: 19,4 M de 8.191 M (0,237%), contra 14,7 M (0,365%) en el 4B.
- Velocidad ~40 tokens/s (aprox. la mitad del 4B); validaciones de ~110 s. Duración: ~80 minutos.
- **Hipótesis 1 (parte más bajo): confirmada.** Antes de entrenar ya predice mejor el español del autor.
- **Hipótesis 2 (mejora menos): confirmada.** Termina más abajo, pero el entrenamiento le aporta menos (0,51 contra 0,68), porque ya sabía más.
- **Hipótesis 3 (sobreajusta antes): no se cumplió.** El Val loss siguió bajando hasta la iteración 60. Con el mismo learning rate y una época, el 8B no alcanzó a memorizar.
- El adaptador final (iteración 60) es el mejor; no hay que reemplazarlo.

## 2026-11-21: Generación 8B fichas-largo-uniforme

| Métrica (promedio) | Original | 4B ficha + largo | 8B ficha + largo |
|---|---|---|---|
| Palabras | 606 | 540 | 510 |
| Párrafos | 10,4 | 10,2 | 10,2 |
| Palabras por oración | 22,4 | 19,0 | 19,5 |
| Cursivas/negritas | 9,4 | 2,8 | 4,2 |
| Riqueza de vocabulario (%) | 53,1 | 50,9 | 55,2 |
| Vocabulario típico (por 1000) | 118 | 151 | 149 |

Generación: ~5 minutos para los 8 textos.

**Diferencias con el 4B:**
- **Menos relleno:** en TOEM ya no repite tres veces los puercoespines ni la melodía; reformula la ficha en vez de enumerarla.
- **Mejor comprensión:** en Sable entiende bien la máscara y las medallas (el 4B hablaba de "un simulacro del vehículo").
- **Más cerca del estilo:** más cursivas en los nombres de juegos, primera persona ocasional ("por lo menos no en mi caso") y, por primera vez, la apertura "Bienvenidos…" (2 de 8).
- **Sigue respetando el largo**, aunque tiende a quedarse algo corto (296–867 palabras para pedidos de 350–850).
- **Persisten algunos errores:** mezcla ideas (la bocina "almacena imágenes en el catálogo de fauna"), una lógica rara ("mi única crítica es que existe una secuela") y el género del protagonista de Sable es inconsistente. La exageración del vocabulario típico se mantiene (149 contra 118).

**Lectura:** duplicar el tamaño mejoró la **comprensión y la fluidez**, que es lo que el fine-tuning no podía dar, pero no eliminó los errores ni la caricatura del estilo. El salto de calidad del 8B se nota más en la lectura que en las métricas.

## 2026-11-21: Búsqueda de hiperparámetros (preparación)

Script: `8_busqueda_hiperparametros.sh` (`herramientas/busqueda.py`). Corre de noche, unas 3,5 a 4 horas.

- **Modelo y datos:** Qwen3-4B con fichas + largo, 60 iteraciones (lo mismo que el entrenamiento 3, que sirve de referencia: Val loss 1,725).
- **Diseño:** se cambia **un parámetro a la vez** respecto de la base, para atribuir cada efecto:

| Corrida | Cambio |
|---|---|
| lr-2e-5 / lr-1e-4 | learning rate más bajo / más alto (base 5e-5) |
| rank-8 / rank-32 | adaptador más chico / más grande (base 16) |
| capas-8 / capas-todas | adaptar 8 o las 36 capas (base 16) |

- **Medida:** el mejor Val loss y en qué iteración ocurre. Solo se guarda el adaptador final, para ahorrar disco.
- Resultados en `resultados/hiperparametros.md`, que se actualiza tras cada corrida. Si se interrumpe, se retoma sin repetir lo hecho.

## 2026-11-21/22: Resultados de la búsqueda de hiperparámetros (4B, fichas + largo, 60 iteraciones)

| Corrida | Parámetros entrenables | Mejor Val loss | Diferencia con la base | Minutos |
|---|---|---|---|---|
| base (lr 5e-5, rank 16, 16 capas) | 14,7 M | 1,725 | – | ~35 |
| lr 2e-5 | 14,7 M | 1,730 | +0,005 | 27 |
| lr 1e-4 | 14,7 M | 1,773 | +0,048 | 29 |
| rank 8 | ~7 M | 1,729 | +0,004 | 30 |
| rank 32 | 29,4 M | 1,739 | +0,014 | 29 |
| 8 capas | ~7 M | 1,779 | +0,054 | 24 |
| **36 capas (todas)** | 33,0 M | **1,702** | **−0,023** | 44 |
| *Referencia: 8B base* | *19,4 M* | *1,599* | *−0,126* | *~80* |

En ninguna corrida hubo sobreajuste dentro de la época: todas mejoraron hasta la iteración 60.

**Aprendizajes:**
1. **Learning rate:** hay un rango "seguro". 2e-5 y 5e-5 terminan igual (el más bajo solo arranca más lento). 1e-4 es claramente peor: con pasos demasiado grandes el modelo no se acerca con precisión al óptimo.
2. **Rank casi no importa:** el rank 8, con la mitad de parámetros, empata con el 16. El rank 32, con el doble, es levemente peor. La capacidad del adaptador **no** era el cuello de botella.
3. **Qué capas se adaptan importa más que cuán grande es el adaptador.** Con 8 capas empeora y con las 36 mejora. El rank 32 (29 M parámetros) y las 36 capas (33 M) tienen un tamaño parecido, pero solo las 36 capas mejoran: importa *dónde* se ponen los parámetros, no *cuántos* hay. A cambio, entrenar las 36 capas toma un 50% más de tiempo.
4. **El tamaño del modelo pesa más que todo lo demás.** El mejor ajuste de hiperparámetros movió el Val loss 0,02. Pasar de 4B a 8B lo movió 0,13, seis veces más.
5. **Precaución estadística:** con solo 10 artículos de validación y una sola corrida por configuración, las diferencias menores a ~0,01 (lr 2e-5, rank 8) deben considerarse empates.
