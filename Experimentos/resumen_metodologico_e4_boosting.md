# Cierre Metodologico E4 Boosting

Fecha de cierre: 2026-03-25

## Alcance

La familia `E4` se evaluo bajo el mismo marco limpio temporal de `E1`, `E2` y `E3`:

- mismo dataset maestro
- horizontes `1, 2, 3 y 4` semanas
- validacion externa `walk-forward expanding`
- sin validacion aleatoria
- sin tuning interno en esta etapa
- baseline fijo de `xgboost_regressor` con hiperparametros conservadores
- mismas metricas Radar, mismo tracker y misma integracion al grid

La intencion fue abrir `Boosting` con una linea base defendible, no exprimir hiperparametros.

## Corridas auditadas

- `E4_v1_clean`
  Baseline `xgboost_regressor` con `target_mode=nivel`, `feature_mode=all`, `lags 1..6`.
- `E4_v2_clean`
  Variante parsimoniosa. Mantiene el setup de `E4_v1_clean` y cambia solo `feature_mode=corr`.
- `E4_v3_clean`
  Variante `delta`. Mantiene el setup de `E4_v1_clean` y cambia solo `target_mode=delta`.

## Tabla consolidada

| run_id | family | model | target_mode | feature_mode | lags | feature_count_prom | mae_promedio | rmse_promedio | direction_accuracy_promedio | deteccion_caidas_promedio | L_total_Radar | lectura |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| E1_v5_clean | E1 | ridge_tscv | nivel | corr | 1,2,3,4,5,6 | 30.0 | 0.1025 | 0.1365 | 0.7438 | 0.7823 | 0.2434 | mejor Ridge global |
| E1_v4_clean | E1 | ridge_tscv | nivel | corr | 1,2,3,4 | 21.0 | 0.1029 | 0.1329 | 0.7444 | 0.7657 | 0.2533 | Ridge parsimonioso |
| E3_v2_clean | E3 | random_forest_regressor | nivel | all | 1,2,3,4,5,6 | 83.0 | 0.1042 | 0.1347 | 0.7338 | 0.7087 | 0.2664 | mejor bagging interno |
| E4_v1_clean | E4 | xgboost_regressor | nivel | all | 1,2,3,4,5,6 | 83.0 | 0.1133 | 0.1422 | 0.6938 | 0.7087 | 0.2839 | baseline de boosting |
| E4_v2_clean | E4 | xgboost_regressor | nivel | corr | 1,2,3,4,5,6 | 30.0 | 0.1111 | 0.1388 | 0.6933 | 0.6610 | 0.2973 | parsimonia empeora global |
| E4_v3_clean | E4 | xgboost_regressor | delta | all | 1,2,3,4,5,6 | 83.0 | 0.1465 | 0.1814 | 0.4925 | 0.5178 | 0.4248 | target delta deteriora fuerte |

## Que probo cada corrida

### E4_v1_clean

`E4_v1_clean` probo si una no linealidad secuencial tipo `Boosting` podia convertir la senal no lineal ya vista en `E3` en una mejora real sobre bagging y sobre Ridge.

Resultado:

- no supera a `E3_v2_clean`
- no alcanza a `E1_v4_clean` ni a `E1_v5_clean`
- muestra algunas ventajas locales, pero no una mejora global consistente

Conclusion:

El baseline de `Boosting` no fue un desastre, pero tampoco se volvio un contendiente serio.

### E4_v2_clean

`E4_v2_clean` probo si el problema de `E4_v1_clean` era el exceso de variables y si una version mas parsimoniosa con `feature_mode=corr` podia generalizar mejor.

Resultado:

- empeora frente a `E4_v1_clean` en `L_total_Radar`: `0.2839 -> 0.2973`
- mejora algunos valores puntuales, sobre todo en `H3`
- empeora `H2`, `H4` y la lectura global

Conclusion:

Reducir variables no rescata a `Boosting`; la parsimonia empeora la familia en terminos globales.

### E4_v3_clean

`E4_v3_clean` probo si `Boosting` funciona mejor capturando cambios (`delta`) que niveles absolutos.

Resultado:

- deterioro fuerte frente a `E4_v1_clean`: `0.2839 -> 0.4248`
- colapso de `H1` y `H3`
- mejora parcial en `H2` respecto a `E4_v1_clean`, pero insuficiente

Conclusion:

`target_mode=delta` no ayuda a `Boosting` en esta formulacion y debilita severamente la familia.

## Lectura por horizonte

- `H1`
  `E4_v3_clean` colapsa y `E4_v2_clean` no logra una mejora sustantiva. `E4_v1_clean` sigue siendo la mejor variante interna.
- `H2`
  `E4_v3_clean` mejora ligeramente el `loss_h` frente a `E4_v1_clean`, pero con peores errores numericos y sin compensar la degradacion en otros horizontes.
- `H3`
  `E4_v2_clean` mejora frente a `E4_v1_clean`, pero ambos quedan claramente por debajo de los mejores runs de `E1` y tambien por debajo de `E3_v1/E3_v2`.
- `H4`
  Ninguna variante de `E4` se vuelve dominante. `E4_v1_clean` mantiene la mejor lectura interna.

## Respuestas formales

- ¿Que probo `E4_v1_clean` realmente?
  Que `Boosting` baseline no supera ni a bagging ni a Ridge bajo este setup.
- ¿Que probo `E4_v2_clean` realmente?
  Que reducir variables a `corr` no mejora a `Boosting`; solo mueve metricas de forma local.
- ¿Que probo `E4_v3_clean` realmente?
  Que `target_mode=delta` perjudica fuertemente a `Boosting` en este problema.
- ¿Hubo mejora interna real?
  No. Hubo mejoras locales en algunos horizontes, pero no una mejora global defendible.
- ¿Alguna variante supero a `E3_v2_clean`?
  No.
- ¿Alguna variante alcanzo o supero a `E1_v4_clean` o `E1_v5_clean`?
  No.
- ¿Ayudo mas reducir variables o cambiar el target?
  Reducir variables fue menos malo; cambiar el target a `delta` fue claramente peor.

## Veredicto final formal

- Mejor run interno de `E4`: `E4_v1_clean`
- Diagnostico sobre parsimonia: `E4_v2_clean` no mejora y empeora el global
- Diagnostico sobre target `delta`: `E4_v3_clean` deteriora de forma fuerte la familia
- Competitividad final: `E4` queda por debajo de `E3_v2_clean`, `E1_v4_clean` y `E1_v5_clean`
- Decision: `E4` queda cerrada con evidencia suficiente en su rama base actual
- Alcance del cierre: no se sigue expandiendo `E4` con pequenas variantes base; esto no prohibe ideas futuras de boosting en abstracto, pero si cierra la linea ya explorada

## Siguiente paso

No se justifica seguir expandiendo `Boosting` base en este punto.

Los siguientes pasos razonables quedan en:

- abrir `E5` CatBoost como siguiente familia tabular pendiente
- mantener mapeada la continuidad metodologica hacia `E6` ARIMAX, `E7` Prophet y `E8` hibrido residual
- dejar `E9` stacking para una etapa posterior, no en este cierre
