# LLM Personal

Durante un fin de semana hice un experimento donde entrené un pequeño modelo de lenguaje en mi computadora sin conexión a internet para que escribiera usando mi estilo. Para esto usé 121 artículos de mi newsletter, *El Jugador Solitario*, donde comparto información suficiente para hacer reviews de video juegos.

El principal resultado de este experimento fue que el proceso de entrenamiento logró transferir el estilo (aunque no el conocimiento). Muy temprano en el entrenamiento del modelo, el estilo se hizo evidente, pero al no tener acceso al contenido, inventaba mucha información con alta seguridad.

La combinación que funcionó fue dividir las tareas: un modelo “grande” escribe un borrador utilizando los datos disponibles y mi modelo personal lo reescribe utilizando mi voz particular. De esta forma, los datos fueron preservados y el estilo se acercó al mío.

También hubo una inesperada observación: un detector comercial de IA identificó estos textos como escritos por humanos. El mismo texto, antes de la reescritura, estaba etiquetado como 89% IA; después de la transformación, solo 3%. Sin embargo cuando el modelo grande intentó imitar mi estilo por sí solo, este detector continuó identificándolo. Esto nos lleva a pensar que estas herramientas son frágiles.

Un informe completo de todo esto, incluyendo lo que funcionó, lo que no y los aprendizajes obtenidos, está disponible en el repositorio del proyecto.
