# LLM Personal: plan y decisiones

## Enfoque
- Fine-tuning con LoRA de un modelo abierto pequeño (no entrenar desde cero) usando MLX en un Mac M4 de 24 GB.
- Modelos: familia **Qwen3** en dos tamaños, para que al comparar solo cambie el tamaño (decidido el 21-nov-2026):
  - 4B: `mlx-community/Qwen3-4B-4bit` (~2,3 GB), por defecto.
  - 8B: `mlx-community/Qwen3-8B-4bit` (~4,6 GB), se elige agregando `8b` a los comandos.
- Qwen3 tiene un "modo razonamiento"; al generar se desactiva (`enable_thinking=False`).
- Carpeta en el Mac: `/Users/jmenichetti/Projects/JugadorSolitarioLLM/LLM_Personal`.

## Datos (export de Substack, 21-nov-2026)
- 148 posts, ~86.700 palabras. Se usan 139: se excluyen 9 que no son reseñas (resúmenes anuales y de mitad de año, aniversario, presentación, fondos de pantalla, Geek Orchestra, Secret Level).
- Se eliminaron 228 párrafos repetidos (cierres "Gracias por leer…", aviso de capturas de pantalla, encabezados "Otras publicaciones…"). Se conservó el párrafo de bienvenida.
- División: 121 entrenamiento / 10 validación / 8 prueba (uno por tramo de tiempo).
- Prueba: Old Man's Journey, The Callisto Protocol, Alan Wake II, Sable, Dave the Diver, Blue Prince, Spirit of the North (1&2), TOEM.

## Ponderación por estadísticas
- El export no trae lecturas web ni comentarios, solo envíos y aperturas de email. La métrica es la tasa de apertura comparada con la de los ~12 posts vecinos (corrige el crecimiento de la audiencia).
- Señal débil: la mayoría de los posts se envió a 2–60 personas.
- Variante "ponderado": los 15 mejores del set de entrenamiento aparecen 2 veces (Cuphead, Dredge, Ancestors, Mystic Pillars, After Us, Storyteller, Nothing Door, Nine Sols, Another World, Endling, Gylt, Mosaic, Hoa, The Cub, Harold Halibut).

## Experimento
Matriz de 2 × 3 sobre los mismos 8 artículos de prueba: tamaño (4B, 8B) × versión (sin entrenar, uniforme, ponderado).

## Entrenamiento (config/base.yaml, igual para ambos tamaños)
LoRA rank 16, 16 capas, lr 5e-5, batch 2 × acumulación 2, max_seq_length 4096, mask_prompt.
- **70 iteraciones (~1 época)**, con medición y guardado cada 15. Antes eran 180 (~3 épocas); se cambió porque el entrenamiento 1 sobreajustó después de la primera época (ver BITACORA.md).
- Los scripts usan `caffeinate` para que el Mac no se suspenda.

## Evaluación
`5_comparar.sh` genera un HTML con métricas de estilo (palabras por oración, riqueza de vocabulario, uso de vocabulario típico, párrafos, cursivas) y lectura lado a lado de todas las versiones generadas junto al original.
