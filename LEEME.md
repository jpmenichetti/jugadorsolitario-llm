# LLM Personal: El Jugador Solitario

Entrena un modelo de lenguaje en tu Mac para que escriba con tu estilo, y compara lo que genera con tus artículos reales.

## Qué hay en esta carpeta

- `datos/uniforme/`: 121 artículos de entrenamiento + 10 de validación, todos con el mismo peso.
- `datos/ponderado/`: los mismos artículos, pero los 15 con mejor tasa de apertura aparecen 2 veces.
- `datos/prueba/`: 8 artículos que el modelo **nunca ve**. Sirven para comparar.
- `datos/resumen_articulos.csv`: cada artículo con sus estadísticas, el conjunto al que pertenece y su peso.
- Scripts numerados del 1 al 6.

Modelos base: misma familia (**Qwen3**) en dos tamaños, para que la única diferencia al compararlos sea el tamaño:
- **4B** (`mlx-community/Qwen3-4B-4bit`, ~2,3 GB): el tamaño por defecto.
- **8B** (`mlx-community/Qwen3-8B-4bit`, ~4,6 GB): se elige agregando `8b` al final del comando. Se descarga solo la primera vez que lo uses.

## Cómo usarlo

1. Abre la app **Terminal**.
2. Escribe `cd ` (con un espacio al final), arrastra esta carpeta a la ventana de la Terminal y pulsa Enter.
3. Corre los pasos en orden, copiando cada línea y pulsando Enter:

```
bash 1_instalar.sh              # una sola vez, ~5 min (descarga ~2,3 GB)
bash 2_linea_base.sh            # el "antes": 8 artículos con el modelo sin entrenar
bash 3_entrenar.sh uniforme     # entrenamiento, ~15–40 min
bash 4_generar.sh uniforme      # el "después"
bash 3_entrenar.sh ponderado    # experimento: versión ponderada
bash 4_generar.sh ponderado
bash 5_comparar.sh              # abre el informe de comparación en el navegador
bash 6_conversar.sh uniforme    # chatea con tu modelo (escribe q para salir)
```

Para repetir el experimento con el modelo de 8B, agrega `8b` al final:

```
bash 2_linea_base.sh 8b
bash 3_entrenar.sh uniforme 8b
bash 4_generar.sh uniforme 8b
bash 3_entrenar.sh ponderado 8b
bash 4_generar.sh ponderado 8b
bash 5_comparar.sh              # el informe muestra todas las versiones juntas
```

El entrenamiento de 8B tarda aproximadamente el doble que el de 4B.

Durante el entrenamiento conviene que el Mac esté enchufado y sin otras apps pesadas abiertas.

## Cómo leer el entrenamiento

Cada 10 pasos verás `Train loss` y cada 30 pasos `Val loss`.

- **Train loss** mide qué tan bien predice tus artículos de entrenamiento.
- **Val loss** mide lo mismo con artículos que no está usando para aprender. Es el número importante.

Si **Val loss** baja y después empieza a subir, el modelo está memorizando en vez de aprender tu estilo. Los adaptadores se guardan cada 30 pasos en `adaptadores/<tamaño>-<variante>/`, así que se puede volver a uno anterior.

## Si algo falla

- **"Out of memory" o el Mac se pone muy lento:** en `config/base.yaml` cambia `batch_size: 2` por `batch_size: 1`.
- Los adaptadores de 4B no sirven para el modelo de 8B, ni al revés. Por eso cada tamaño tiene sus propias carpetas.

## Fase 2: con fichas

En la fase 2, cada pedido incluye una ficha con los datos del juego, para que el modelo no invente. Las fichas están en `datos/fichas.json`.

```
bash 2_linea_base.sh 4b fichas          # el "antes", con ficha
bash 3_entrenar.sh fichas-uniforme      # entrenamiento, ~25 min
bash 4_generar.sh fichas-uniforme
bash 5_comparar.sh fichas               # abre resultados/comparacion_fichas.html
```

Para la versión ponderada usa `fichas-ponderado`, y para el modelo grande agrega `8b` al final, como en la fase 1.

## Detección de IA con Pangram

`7_detectar_ia.sh` envía tus originales de prueba y todos los textos generados a Pangram, un servicio comercial que estima qué parte de un texto fue escrita por IA. Los resultados aparecen como filas nuevas en el informe de `5_comparar.sh`.

1. Crea una cuenta en pangram.com, entra al panel (dashboard) y haz clic en **API** para ver tu clave.
2. En esta carpeta, crea un archivo llamado `.pangram_key` que contenga solo la clave. Por ejemplo, en la Terminal: `echo "TU_CLAVE" > .pangram_key`. El archivo está en el `.gitignore` y no se sube a GitHub.
3. Corre `bash 7_detectar_ia.sh`. Antes de enviar nada te muestra cuántas palabras son y el costo estimado (US$ 0,05 cada 100 palabras), y pide confirmación.
4. Corre `bash 5_comparar.sh` (o `bash 5_comparar.sh fichas`).

Solo se evalúan los textos nuevos o modificados; lo ya evaluado queda guardado en `resultados/deteccion_pangram.json`.

## Fase 3: transferencia de estilo (reescribir un borrador con tu voz)
El modelo recibe un borrador escrito en estilo neutro y lo reescribe como si fuera tuyo, sin agregar ni quitar datos.
1. `bash 2_linea_base.sh 8b transferencia`: el "antes", con el 8B sin entrenar reescribiendo los 8 borradores (~30 min).
2. `bash 3_entrenar.sh transferencia-uniforme 8b`: entrena (2 a 3 horas; ideal de noche, con el cargador conectado).
3. `bash 4_generar.sh transferencia-uniforme 8b`: reescribe los 8 borradores de prueba.
4. `bash 5_comparar.sh transferencia`: informe en el navegador.
Los borradores neutros están en `datos/neutros.json` y la configuración en `config/transferencia.yaml`.
