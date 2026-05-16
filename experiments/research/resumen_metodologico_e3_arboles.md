# Cierre Metodologico E3 Arboles Bagging

Fecha de cierre: 2026-03-25

## Alcance

La familia `E3` se evaluo bajo el mismo marco limpio y comparable usado en `E1` y `E2`:

- mismo dataset maestro
- horizontes `1, 2, 3 y 4` semanas
- validacion externa `walk-forward expanding`
- sin validacion aleatoria
- `feature_mode` calculado dentro del fold correspondiente cuando aplica
- sin escalado por naturaleza basada en arboles
- mismas metricas Radar, mismo tracker y misma integracion al grid

En esta etapa `E3` se trato como baseline no lineal de bagging, no como familia tuneada con grid temporal interno.

## Corridas auditadas

- `E3_v1_clean`
  Baseline `Random Forest` con `feature_mode=corr`, `target_mode=nivel` y `lags 1..6`.
- `E3_v2_clean`
  Variante de base amplia. Mantiene el setup de `E3_v1_clean` y cambia solo `feature_mode=all`.
- `E3_v3_clean`
  Variante `ExtraTrees`. Mantiene `target_mode=nivel`, `feature_mode=corr` y `lags 1..6`, cambiando solo el algoritmo.

## Tabla consolidada

| run_id | family | model | target_mode | feature_mode | lags | feature_count_prom | mae_promedio | rmse_promedio | direction_accuracy_promedio | deteccion_caidas_promedio | L_total_Radar | lectura |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| E1_v4_clean | E1 | ridge_tscv | nivel | corr | 1,2,3,4 | 21.0 | 0.1029 | 0.1329 | 0.7444 | 0.7657 | 0.2533 | referencia parsimoniosa |
| E1_v5_clean | E1 | ridge_tscv | nivel | corr | 1,2,3,4,5,6 | 30.0 | 0.1025 | 0.1365 | 0.7438 | 0.7823 | 0.2434 | mejor Ridge global |
| E2_v3_clean | E2 | huber_tscv | nivel | corr | 1,2,3,4 | 21.0 | 0.1297 | 0.1571 | 0.7076 | 0.7699 | 0.2865 | mejor Huber interno |
| E3_v1_clean | E3 | random_forest_regressor | nivel | corr | 1,2,3,4,5,6 | 30.0 | 0.1059 | 0.1366 | 0.7041 | 0.6809 | 0.2809 | baseline no lineal util |
| E3_v2_clean | E3 | random_forest_regressor | nivel | all | 1,2,3,4,5,6 | 83.0 | 0.1042 | 0.1347 | 0.7338 | 0.7087 | 0.2664 | mejor run interno de E3 |
| E3_v3_clean | E3 | extra_trees_regressor | nivel | corr | 1,2,3,4,5,6 | 30.0 | 0.1107 | 0.1414 | 0.7233 | 0.6559 | 0.2873 | ExtraTrees no mejora |

## Que probo cada corrida

### E3_v1_clean

`E3_v1_clean` probo si una familia no lineal de bagging, aun sin tuning interno, podia captar senal util para Radar bajo el mismo marco temporal limpio.

Resultado:

- mejora claramente a `E2_v3_clean` en `L_total_Radar`
- no alcanza a `E1_v4_clean` ni a `E1_v5_clean`
- deja una senal particularmente util en `H3`

Conclusion:

La no linealidad si sirve para Radar, pero el baseline de bagging aun no desplaza a Ridge.

### E3_v2_clean

`E3_v2_clean` probo si `Random Forest` aprovecha mejor una base amplia de predictores que una version parsimoniosa por correlacion.

Resultado:

- mejora material frente a `E3_v1_clean` en `L_total_Radar`: `0.2809 -> 0.2664`
- mejora `H1`, `H2` y `H4`
- empeora levemente `H3`
- supera a `E2_v3_clean`
- sigue por debajo de `E1_v4_clean` y `E1_v5_clean`

Conclusion:

En `E3`, `feature_mode=all` ayuda mas que `feature_mode=corr`. La familia de bagging gana estabilidad general usando la base amplia completa.

### E3_v3_clean

`E3_v3_clean` probo si `ExtraTrees` aporta una flexibilidad util adicional dentro de la misma familia de arboles.

Resultado:

- empeora frente a `E3_v1_clean` en `L_total_Radar`
- no mejora `H3/H4` como linea principal
- no mejora deteccion de caidas

Conclusion:

`ExtraTrees` no aporto mejora sustantiva y no justifico una subrama adicional dentro de `E3`.

## Lectura por horizonte

- `H1`
  `E3_v2_clean` mejora de forma clara frente a `E3_v1_clean` y se vuelve mas competitivo, aunque no domina el horizonte frente a Ridge.
- `H2`
  `E3_v2_clean` mejora frente a `E3_v1_clean`, pero `E2_v3_clean` sigue siendo mas fuerte por `loss_h` y por senal operativa.
- `H3`
  `E3_v1_clean` y `E3_v2_clean` muestran la mejor senal interna de `E3`, pero ambos quedan por debajo de `E1_v2_clean`, `E1_v4_clean` y `E1_v5_clean`.
- `H4`
  `E3_v2_clean` mejora frente a `E3_v1_clean`, pero no supera a los mejores especialistas del horizonte.

## Respuestas formales

- ¿Que probo `E3_v1_clean` realmente?
  Que una familia no lineal tipo bagging si capta senal util y mejora a Huber.
- ¿Que probo `E3_v2_clean` realmente?
  Que `Random Forest` funciona mejor con `feature_mode=all` que con `feature_mode=corr`.
- ¿Que probo `E3_v3_clean` realmente?
  Que `ExtraTrees` no agrega una mejora real sobre el mejor `Random Forest` interno.
- ¿La mejora de `E3` fue global o parcial?
  Global dentro de la familia, pero no suficiente para desplazar a Ridge.
- ¿Hubo mejora operativa o solo numerica?
  Hubo mejora operativa parcial, sobre todo respecto a Huber, pero no una superioridad sostenida frente a Ridge.
- ¿Hay razon real para mantener viva la familia `E3`?
  Si, como mejor baseline no lineal de bagging y como referencia fuerte para comparaciones futuras.

## Veredicto final formal

- Ganador interno de `E3`: `E3_v2_clean`
- Diagnostico sobre universo de variables: `feature_mode=all` ayuda mas que `corr` dentro de `Random Forest`
- Diagnostico sobre variante `ExtraTrees`: no aporta mejora y no justifica expansion
- Competitividad final: `E3` no supera a `E1_v4_clean` ni a `E1_v5_clean`, pero si supera a `E2_v3_clean`
- Decision: cerrar la rama base de bagging con `E3_v2_clean` como mejor run interno y referencia no lineal vigente

## Siguiente paso

La siguiente familia a abrir es `E4` Boosting, manteniendo el mismo marco de comparabilidad:

- referencia principal: `E1_v5_clean`
- referencia parsimoniosa: `E1_v4_clean`
- referencia no lineal de bagging: `E3_v2_clean`
