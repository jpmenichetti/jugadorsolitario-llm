# LLM Personal: informe final

Este proyecto buscó entender, de forma práctica, qué se puede lograr al entrenar un modelo de lenguaje pequeño, en un computador personal, para que escriba con el estilo de un autor. La conclusión central es que el entrenamiento transfiere el estilo, pero no el conocimiento: el modelo aprende rápido a sonar como el autor, pero no sabe de qué hablar, y si no recibe el contenido, lo inventa. La combinación que mejor funcionó fue dividir el trabajo: un modelo grande escribe un borrador con los datos y el modelo personal lo reescribe con la voz del autor. Así se conservaron los datos y, de paso, el detector de IA usado clasificó los textos como humanos, lo que muestra lo frágiles que son estos detectores.

**Aprendizajes más relevantes** (detalle en la sección 7):

- Con pocos datos, una época basta.
- El ajuste de estilo puede empeorar las alucinaciones.
- Un modelo pequeño tiende a la caricatura.
- El tamaño del modelo domina (8B frente a 4B).
- Parecer humano a un lector y a un detector son cosas distintas.
- Imitar con instrucciones no basta.

*Fuente de entrenamiento: artículos del newsletter [El Jugador Solitario](https://eljugadorsolitario.substack.com/) (reseñas de videojuegos). Período: 21 y 22 de noviembre de 2026. Repositorio: `jpmenichetti/jugadorsolitario-llm`; el detalle cronológico está en `BITACORA.md`.*

---

## 1. Fases en breve

| Fase | Qué recibe el modelo | Resultado principal |
|---|---|---|
| 1 | Solo el tema del artículo | Aprende el tono, pero **inventa todo el contenido** |
| 2 y 2b | Datos de contexto sobre el tema (y el largo deseado) | Datos correctos, pero **copia o recicla esos datos** y rellena inventando |
| 3 | Un borrador completo en estilo neutro escrito por Claude, para reescribir | **Conserva los datos** y cambia la voz; el detector Pangram lo clasifica como **humano** en 10 de 10 textos |

---

## 2. Objetivo y contexto

- **Idea original:** un LLM que funcione offline, entrenado con textos de un autor, que se evalúa pidiéndole artículos en su estilo y comparándolos con los reales.
- **Aclaración de objetivo:** el proyecto es de aprendizaje. El modelo no se usará para escribir en nombre del autor. Por eso cada experimento se eligió por lo que enseñaba, no para pulir el resultado.
- **Diseño práctico:** todo se empaquetó en scripts numerados (`1_instalar.sh` a `8_busqueda_hiperparametros.sh`) que se ejecutan con un solo comando.

---

## 3. Datos

- **Origen:** export de Substack con 148 publicaciones (~86.700 palabras).
- **Limpieza:** se excluyeron 9 publicaciones fuera del formato habitual (resúmenes anuales, aniversario, etc.) y se quitaron 245 párrafos repetidos (cierres estándar, créditos de imágenes, enlaces a otras publicaciones). Quedaron **139 artículos**.
- **División:** 121 para entrenar, 10 para validar (medir la pérdida durante el entrenamiento) y **8 de prueba** que el modelo nunca vio, uno por cada tramo de la historia del newsletter.
- **Ponderación:** se intentó dar más peso a los artículos "mejores" según las estadísticas. El export solo trae aperturas de correo, así que se usó la tasa de apertura relativa a las publicaciones vecinas, y los 15 mejores se duplicaron en una variante "ponderada".

---

## 4. Herramientas

| Pieza | Elección | Por qué |
|---|---|---|
| Entrenamiento | **MLX + mlx-lm** (LoRA) | Diseñado para chips Apple; entrena en el Mac sin GPU dedicada |
| Modelos | **Qwen3-4B y Qwen3-8B** (4 bits, mlx-community) | Misma familia en dos tamaños: al compararlos solo cambia el tamaño. Buen español |
| Técnica | **LoRA**: se entrena un "adaptador" de 15 a 20 millones de parámetros (0,2% a 0,4% del modelo) | Cabe en 24 GB y entrena en 35 a 80 minutos |
| Entorno | uv + Python 3.12 | Instalación reproducible con un comando |
| Detector de IA | **Pangram** (API de pago) | Soporta español; se descartó Binoculars por estar evaluado sobre todo en inglés |
| Evaluación | Script propio con métricas de estilo e informe HTML lado a lado | Comparar original y versiones generadas |

**Configuración base de entrenamiento:** rank 16, 16 capas adaptadas, learning rate 5e-5, lotes de 2 con acumulación de 2, 60 iteraciones (~1 época) y `mask_prompt` (el modelo solo aprende del artículo, no del pedido).

**Ajustes de generación (desde la fase 2):** temperatura 0,6, filtro `min_p` 0,05, penalización de repetición 1,1 con una ventana de 256 tokens y modo "razonamiento" de Qwen3 desactivado.

---

## 5. Recorrido

### Fase 1: solo el tema (4B)

- **Sin entrenar:** estilo de blog genérico (subtítulos, negritas, tono grandilocuente). Inventa datos concretos, como autorías equivocadas.
- **Entrenamiento 1:** planificado para 3 épocas. La pérdida de validación mejoró hasta el final de la primera época (iteración 60: 2,085) y después subió a 2,596 mientras la de entrenamiento se desplomaba a 0,885. Fue **memorización**. Se rescató el punto guardado en la iteración 60.
- **Resultado:** el tono mejora (prosa continua, cursivas, cierres típicos del autor), pero el modelo exagera sus rasgos (usa su vocabulario típico un 46% más que él), escribe textos más cortos (373 palabras contra 606), cae en un bucle de repetición e **inventa todo el contenido**, con más seguridad que antes. Apareció una palabra en portugués ("pessoal").
- **Pangram:** originales 0 de 8 como IA; modelo sin entrenar y entrenado, **8 de 8 como IA**.

### Fase 2: con datos de contexto (4B)

Se extrajo de cada artículo un bloque de **información concreta** (autoría, año, premisa, características principales, opinión del autor) y se entrenó con el par "datos de contexto → artículo".

- **Sin entrenar + datos:** los datos son correctos, pero el estilo sigue siendo genérico y copia frases de los datos.
- **Entrenado + datos:** el estilo mejora, pero los artículos se reducen a **246 palabras**. El modelo aprendió que "el artículo son los datos en prosa".

### Fase 2b: datos de contexto y largo deseado

Se agregó "Largo aproximado: N palabras" a cada pedido.

- **4B:** respeta el largo (540 palabras de promedio) y la estructura de párrafos coincide con los originales. Pero para llegar al largo **recicla los datos** (repite tres veces el mismo detalle en un artículo) y, cuando se le acaban, **vuelve a inventar**.
- **8B:** entiende mejor los datos, rellena menos y usa por primera vez el saludo de apertura habitual del autor. La exageración del vocabulario se mantiene.
- **Pangram 8B entrenado:** 2 Human, 2 Mixed, 4 AI (**56%** promedio). **8B sin entrenar:** 95%. Primer indicio de que el entrenamiento cambia lo que ve el detector.

### Búsqueda de hiperparámetros (4B, datos de contexto + largo)

Seis corridas cambiando un parámetro a la vez:

| Cambio | Mejor pérdida de validación | Diferencia |
|---|---|---|
| Base (lr 5e-5, rank 16, 16 capas) | 1,725 | – |
| lr 2e-5 | 1,730 | empate |
| lr 1e-4 | 1,773 | peor |
| rank 8 | 1,729 | empate |
| rank 32 | 1,739 | algo peor |
| 8 capas | 1,779 | peor |
| **36 capas (todas)** | **1,702** | **mejor** |
| *8B con la configuración base* | *1,599* | *seis veces más mejora que el mejor ajuste* |

### Variante ponderada

Duplicar los 15 artículos con mejor tasa de apertura dio una pérdida levemente peor (1,740 contra 1,725) y ninguna diferencia visible en los textos. La señal era demasiado ruidosa: audiencias de 2 a 60 personas, y una tasa de apertura que mide el interés por el asunto del correo, no la calidad del texto.

### Fase 3: transferencia de estilo (8B)

**Idea:** dividir el trabajo entre dos modelos. Un modelo de lenguaje grande y de propósito general, **Claude** (de Anthropic, que se usa a través de internet y que asistió todo el proyecto), investiga y escribe el contenido. El modelo personal (Qwen3-8B ajustado, que corre en el Mac) lo reescribe con la voz del autor. Al final, Claude verifica que no se hayan perdido ni deformado datos. Claude tiene el conocimiento y la capacidad de investigar que le faltan al modelo pequeño; el modelo pequeño aporta el estilo que Claude no logra imitar.

1. **Borradores neutros:** Claude reescribió los 139 artículos en estilo neutro, conservando todos los datos (~62.700 palabras, 82% del largo original). Al revisarlos, Claude encontró un dato agregado y cifras redondeadas en dos de sus propios borradores, y los corrigió.
2. **Entrenamiento:** pares "borrador neutro → artículo original", con 120 iteraciones, ejemplos de a uno y largo máximo de 5.120 tokens. La pérdida de validación bajó de 1,327 a **0,834** en ~80 minutos, sin señales de memorización.
3. **Prueba con los 8 artículos:** sin datos inventados y con 3 deformaciones menores (por ejemplo, "casi todas las mecánicas son opcionales" pasó a "todas"). El modelo **edita poco**: conserva el 81% del borrador y cambia la voz (primera persona plural, cierres propios, cursivas, comillas en términos en inglés). El 8B sin entrenar, en cambio, reescribe todo y solo conserva el 33%.
4. **Uso real:** Claude investigó y escribió borradores sobre dos temas nuevos que el autor nunca había tratado. El modelo los reescribió, y Claude verificó con cambios mínimos: 5 y 12 correcciones, la mayoría de ortografía, un dato que el modelo había resumido con un "etc." y el género del protagonista, que el modelo cambió.
5. **Control:** Claude reescribió los mismos borradores imitando el estilo con artículos de ejemplo, sin entrenamiento.

**Pangram, fase 3:**

| Texto | % IA | Clasificación |
|---|---|---|
| Originales | 0% | 8 Human |
| 8B sin entrenar reescribiendo | 96% | 7 AI, 1 Mixed |
| **8B entrenado reescribiendo (prueba)** | **0%** | **8 Human** |
| Borrador de Claude (temas nuevos) | 89% | 2 AI |
| **8B entrenado sobre ese borrador** | **3%** | **2 Human** |
| Lo mismo, después de la verificación | 4% | 2 Human |
| Claude imitando el estilo (control) | 80% | 1 AI, 1 Mixed |

---

## 6. Comparación global

| Versión | Datos correctos | Suena al autor | Pangram (% IA) |
|---|---|---|---|
| 4B sin entrenar, solo el tema | No | No | 100% |
| 4B entrenado, solo el tema | No (inventa todo) | Caricatura | 100% |
| 4B entrenado + datos de contexto + largo | En parte (recicla e inventa) | Caricatura | – |
| 8B entrenado + datos de contexto + largo | En parte | Mejor | 56% |
| **8B entrenado, reescribiendo un borrador** | **Sí (deformaciones menores)** | **Sí, con errores de ortografía** | **0% a 4%** |

---

## 7. Aprendizajes

### Sobre el entrenamiento

1. **Con pocos datos, una época basta.** Con ~120 artículos, la segunda pasada empieza a memorizar. Pasó en todos los entrenamientos del 4B.
2. **La pérdida de entrenamiento engaña; la de validación es la referencia.** Una pérdida de entrenamiento muy baja puede significar que el modelo se sabe los textos de memoria.
3. **Guardar puntos intermedios salva el experimento.** Permitió recuperar el mejor modelo aunque el final había empeorado.

### Sobre lo que aprende el modelo

1. **El estilo se aprende rápido; el conocimiento, no.** En todas las fases, la mayor parte de la mejora ocurrió en las primeras 30 iteraciones.
2. **El ajuste de estilo puede empeorar las alucinaciones.** El modelo aprende a *sonar* concreto y seguro sin saber los datos, y produce invenciones más específicas y convincentes.
3. **Un modelo pequeño tiende a la caricatura:** exagera los rasgos más frecuentes del autor y puede caer en bucles.
4. **El contenido tiene que venir de alguna parte.** Si el pedido no trae suficiente material, el modelo solo puede repetir o inventar. La forma de entregar el contenido (tema, datos de contexto o borrador) define el resultado más que cualquier parámetro.
5. **El modelo aprende la tarea que se le muestra.** Con datos de contexto aprendió a "pasar los datos a prosa"; con borradores aprendió a "editar poco y cambiar la voz". El diseño de los pares de entrenamiento decide el comportamiento.

### Sobre los parámetros

1. **El tamaño del modelo domina.** 8B contra 4B mejoró la pérdida 0,13; el mejor hiperparámetro, 0,02.
2. **Importa dónde se ponen los parámetros, no cuántos son.** Adaptar las 36 capas mejoró; duplicar el rank no.
3. **El learning rate tiene un rango seguro** (2e-5 a 5e-5). Por encima, empeora.
4. **Ponderar datos solo sirve con una buena señal.** Con una métrica ruidosa no aportó nada.

### Sobre la evaluación y los detectores

1. **Parecer humano a un lector y a un detector son cosas distintas.** En la fase 1 el estilo mejoró y el detector siguió marcando 100%.
2. **Al detector le importa la forma, no el fondo.** Cambiar ~18% de las palabras de un texto de Claude, con las marcas idiosincráticas del autor (incluidas sus faltas), lo lleva de 89% a 3% de IA.
3. **Imitar con instrucciones no basta.** Claude imitando el estilo siguió siendo detectado (80%): escribe "demasiado limpio" y no reproduce las irregularidades del autor.
4. **Hay que medir, no suponer.** Varias predicciones razonables fallaron (por ejemplo, que el 8B seguiría en 100%), y algunos resultados solo se entendieron midiendo una versión de control.

---

## 8. Limitaciones

- **Muestras pequeñas:** 8 artículos de prueba, 2 temas nuevos, 10 de validación y una sola generación por texto. Los resultados son señales claras, no mediciones definitivas.
- **Un solo detector** (Pangram, versión de noviembre de 2026). Otros detectores, o versiones futuras, podrían comportarse distinto.
- **Fase 3 con ventaja en la prueba:** los borradores de prueba se escribieron a partir de los originales y conservan su estructura y parte de sus palabras. Los dos temas nuevos no tienen esa ventaja y dieron el mismo resultado, lo que refuerza la conclusión, aunque con solo dos casos.
- **El control de Claude no es "pocos ejemplos" puro:** Claude ya había leído los 139 artículos al escribir los borradores.
- **Los borradores de los temas nuevos se basan solo en fuentes de prensa:** el texto no puede tener experiencias reales del autor.
- **Errores de lenguaje persistentes:** el modelo sigue cometiendo faltas de ortografía y de concordancia. Para un uso real, la verificación final es imprescindible.

---

## 9. Costos y tiempos

| Concepto | Costo / tiempo |
|---|---|
| Entrenamientos 4B | ~35 min cada uno (60 iteraciones) |
| Entrenamientos 8B | ~80 min cada uno |
| Búsqueda de hiperparámetros | ~3 h (seis corridas, de noche) |
| Generación de 8 artículos | ~5 a 10 min |
| Pangram, fase 1 | US$ 6,7 |
| Pangram, 8B entrenado y sin entrenar (fase 2b) | US$ 4,5 |
| Pangram, fase 3 | ~US$ 6,4 |
| **Pangram, total del proyecto** | **~US$ 17,6** |
| Espacio en disco (adaptadores) | 2,8 GB |

Todo el entrenamiento y la generación corrieron en el Mac, sin costo de nube.

---

## 10. Si se quisiera seguir

- **Mejorar la ortografía:** un paso automático de corrección ortográfica después de reescribir, o agregar más ejemplos de entrenamiento.
- **Combinar lo aprendido:** entrenar el 8B de transferencia con las 36 capas adaptadas, el mejor ajuste de la búsqueda.
- **Robustez:** generar varias veces cada texto y probar con otros detectores, para saber si el resultado de Pangram se sostiene.
- **Uso realista:** que el propio autor escriba notas rápidas o un borrador (en lugar de Claude), para medir cuánto del resultado depende de quién escribe el contenido.

---

## 11. Mapa del repositorio

| Ruta | Contenido |
|---|---|
| `1_instalar.sh` … `8_busqueda_hiperparametros.sh` | Scripts del flujo completo |
| `herramientas/` | Generación, comparación, detección y búsqueda (Python) |
| `config/base.yaml`, `config/transferencia.yaml` | Configuraciones de entrenamiento |
| `datos/` | Conjuntos de cada fase, datos de contexto, borradores neutros, prueba y uso real |
| `resultados/` | Textos generados por versión, informes HTML, `deteccion_pangram.json`, `hiperparametros.md` |
| `registros/` | Logs de cada entrenamiento |
| `BITACORA.md` | Registro cronológico detallado |
| `INFORME_FINAL.md` | Este documento |
| `RESUMEN.md` | Versión breve centrada en los resultados (con su versión reescrita por el modelo) |
