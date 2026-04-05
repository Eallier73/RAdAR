# Resumen Metodologico E11 Dual

Fecha de actualizacion: `2026-04-03`

## Estado de la familia

`E11` ya no queda solo como especificacion futura. La familia fue abierta con tres variantes duales controladas y queda:

- `evaluada sin promocion`
- `abierta como evidencia dual no promotable todavia`
- `util como antecedente metodologico para una futura reformulacion dual`

La apertura formal se hizo con:

- [E11_v1_clean_20260403_051406](/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v1_clean_20260403_051406)
- [E11_v2_clean_20260403_051823](/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v2_clean_20260403_051823)
- [E11_v3_clean_20260403_051823](/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v3_clean_20260403_051823)

Runner canónico:

- [run_e11_dual.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e11_dual.py)

## Hipotesis de apertura

La hipotesis central de `E11` fue que una arquitectura dual podia capturar mejor la tension real del problema Radar si separaba explicitamente:

- forecast numerico del porcentaje
- lectura categorica del movimiento o de la caida

La apertura no busco un meta-ganador opaco ni una continuidad informal de `E10`.

## Definicion de targets categoricos

Los targets categoricos se fijaron ex ante y quedaron persistidos por run en `thresholds_clases.json`.

Regla usada:

- `E11_v1_clean`:
  - variable base: `delta = y_true_level - y_current`
  - `baja` si `delta < -0.5`
  - `se_mantiene` si `-0.5 <= delta <= 0.5`
  - `sube` si `delta > 0.5`
- `E11_v2_clean` y `E11_v3_clean`:
  - variable base: `delta = y_true_level - y_current`
  - `cae` si `delta <= 0.0`
  - `no_cae` si `delta > 0.0`

Lectura metodologica:

- la formulacion ternaria fue limpia, pero demasiado gruesa para la escala efectiva observada y por eso casi colapso a `se_mantiene`;
- la formulacion binaria `cae / no_cae` fue mucho mas defendible y dejo señal real.
- la autopsia posterior sobre la distribucion del delta real mostro que `+-0.5` era un threshold excesivo para la escala empirica del problema;
- para una futura reapertura ternaria, `+-0.15` queda como threshold preferente y `+-0.10` / `+-0.20` como rango plausible de prueba.

## Variantes corridas

### E11_v1_clean

- modo: `parallel`
- salida numerica: Ridge temporal identica a `E1_v5_clean`
- salida dual: clasificador ternario `baja / se_mantiene / sube`

Lectura:

- preserva exactamente el benchmark numerico `E1_v5_clean`
- la tarea ternaria sigue casi colapsada a `se_mantiene`
- accuracy alta solo por desbalance extremo, no por señal direccional real

### E11_v2_clean

- modo: `fall_detector`
- salida numerica: Ridge temporal identica a `E1_v5_clean`
- salida dual: detector binario `cae / no_cae`

Lectura:

- preserva exactamente el benchmark numerico `E1_v5_clean`
- la capa binaria si deja senal real
- recall promedio de `cae`: `0.598485`
- accuracy binaria promedio: `0.512907`
- balanced accuracy binaria promedio: `0.522411`

Esta es la mejor apertura interna de la familia porque agrega una salida operativa interpretable sin degradar el forecast numerico.

### E11_v3_clean

- modo: `residual_dual`
- salida numerica: Ridge base + correccion residual OOF temporal
- salida dual: detector binario `cae / no_cae`

Lectura:

- es la unica variante que intenta mejorar el forecast numerico final
- mejora levemente `H1` y `H3`
- empeora `H2` y `H4`
- no mejora el global frente a `E1_v5_clean`

## Comparacion consolidada

| run_id | family | dual_mode | target_mode_reg | target_mode_cls | feature_mode | lags | mae_promedio | rmse_promedio | direction_accuracy_promedio | deteccion_caidas_promedio | L_total_Radar | observacion_breve |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| E1_v5_clean | E1 | n/a | nivel | n/a | corr | 1,2,3,4,5,6 | 0.102512 | 0.136512 | 0.743753 | 0.782323 | 0.243442 | benchmark numerico puro vigente |
| E9_v2_clean | E9 | n/a | nivel | n/a | tabla curada | n/a | 0.123691 | 0.159756 | 0.735847 | 0.916667 | 0.227510 | benchmark operativo vigente de riesgo-direccion-caidas |
| E11_v1_clean | E11 | parallel | nivel | direction_3clases | corr | 1,2,3,4,5,6 | 0.102512 | 0.136512 | 0.743753 | 0.782323 | 0.243442 | preserva exactamente E1; la capa ternaria casi colapsa a estabilidad |
| E11_v2_clean | E11 | fall_detector | nivel | fall_binary | corr | 1,2,3,4,5,6 | 0.102512 | 0.136512 | 0.743753 | 0.782323 | 0.243442 | preserva exactamente E1 y agrega detector binario de caidas con senal moderada |
| E11_v3_clean | E11 | residual_dual | nivel | fall_binary | corr | 1,2,3,4,5,6 | 0.102558 | 0.137657 | 0.732883 | 0.777273 | 0.243845 | intento residual dual limpio; agrega complejidad y no mejora el global |

## Veredicto metodologico

### Valor dual

Si hay evidencia de valor dual parcial:

- la separacion `forecast numerico + detector binario de caidas` es viable y trazable
- la formulacion binaria `cae / no_cae` tiene mucha mas senal que la version ternaria simple

### Limite de la apertura

No hay evidencia suficiente para promocion:

- `E11_v1_clean` no agrega señal operativa real
- `E11_v2_clean` agrega una capa binaria util, pero no desplaza a `E9_v2_clean`
- `E11_v3_clean` no mejora `L_total_Radar` ni justifica el costo residual adicional
- la lectura ternaria de `E11_v1_clean` no debe interpretarse como invalidez estructural total de la tarea, sino como evidencia de que el threshold inicial fue demasiado ancho

### Decision vigente

`E11` queda:

- abierta como familia dual ya ejecutada
- no promocionable todavia
- congelada despues de su primera apertura controlada

No procede tratar a `E11` como modelo final unico ni como reemplazo automatico de la salida dual vigente `E1_v5_clean + E9_v2_clean`.
