# Búsqueda de hiperparámetros (Qwen3-4B, fichas + largo, 60 iteraciones)

| Corrida | Qué cambia | Val inicial | Mejor Val loss | En iteración | Val final | Minutos |
|---|---|---|---|---|---|---|
| base | configuración base (lr 5e-5, rank 16, 16 capas) | 2.403 | **1.725** | 60 | 1.725 | ~35 |
| lr-2e-5 | learning rate 2e-5 (más lento) | 2.403 | **1.730** | 60 | 1.730 | 27 |
| lr-1e-4 | learning rate 1e-4 (más rápido) | 2.403 | **1.773** | 60 | 1.773 | 29 |
| rank-8 | rank 8 (adaptador más chico) | 2.403 | **1.729** | 60 | 1.729 | 30 |
| rank-32 | rank 32 (adaptador más grande) | 2.403 | **1.739** | 60 | 1.739 | 29 |
| capas-8 | 8 capas adaptadas | 2.403 | **1.779** | 60 | 1.779 | 24 |
| capas-todas | las 36 capas adaptadas | 2.403 | **1.702** | 60 | 1.702 | 44 |

Val loss por iteración:

- base: 1→2.403, 15→1.823, 30→1.771, 45→1.738, 60→1.725
- lr-2e-5: 1→2.403, 15→1.863, 30→1.796, 45→1.751, 60→1.730
- lr-1e-4: 1→2.403, 15→1.851, 30→1.817, 45→1.806, 60→1.773
- rank-8: 1→2.403, 15→1.858, 30→1.787, 45→1.743, 60→1.729
- rank-32: 1→2.403, 15→1.830, 30→1.785, 45→1.767, 60→1.739
- capas-8: 1→2.403, 15→1.890, 30→1.829, 45→1.798, 60→1.779
- capas-todas: 1→2.403, 15→1.796, 30→1.747, 45→1.728, 60→1.702
