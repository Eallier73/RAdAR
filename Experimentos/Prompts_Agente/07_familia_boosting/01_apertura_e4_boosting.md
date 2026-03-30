# Apertura de E4 Boosting

## Objetivo

Abrir la familia `E4 = Boosting` dentro del pipeline experimental de Radar, manteniendo comparabilidad estricta con `E1`, `E2` y `E3`.

## Estado confirmado

- `E1_v5_clean` = mejor Ridge limpio global
- `E1_v4_clean` = Ridge parsimonioso de referencia
- `E3_v2_clean` = mejor run interno de bagging
- `E3_v3_clean` no aporto mejora relevante
- La familia `E3` mostro senal no lineal real, pero no desplazo a Ridge

Referencias vigentes:

- `E1_v5_clean`: `0.243442`
- `E1_v4_clean`: `0.253277`
- `E3_v2_clean`: `0.266387`

## Justificacion metodologica

`Boosting` entra ahora porque la no linealidad ya mostro utilidad en Radar, pero la rama de `bagging` no alcanzo a Ridge. La hipotesis es que una no linealidad secuencial y mas dirigida pueda convertir esa senal en una mejora real.

Diferencia conceptual:

- `Random Forest / bagging`: muchos arboles independientes, agregacion por promedio, buena reduccion de varianza.
- `Boosting`: arboles secuenciales donde cada nuevo arbol corrige residuales del ensamble previo.

Riesgo central:

- mayor capacidad de ajuste y mayor riesgo de sobreajuste
- por eso la linea base inicial debe ser conservadora, limpia y temporalmente defendible

## Reglas no negociables

- mismos horizontes: `1,2,3,4`
- mismo dataset maestro
- misma construccion de `model frame`
- misma validacion externa `walk-forward expanding`
- mismo calculo de metricas Radar y `L_total_Radar`
- misma trazabilidad de artefactos
- comparabilidad directa con `E1_v5_clean`, `E1_v4_clean` y `E3_v2_clean`
- no validacion aleatoria
- no tuning con fuga temporal
- no decisiones de hiperparametros usando el test externo

## Runner de familia

Usar `run_e4_xgboost.py` con estructura homogenea al resto:

- `parse_args()`
- `build_estimator()`
- carga dataset
- construccion del frame por horizonte
- entrenamiento temporal limpio
- prediccion walk-forward
- evaluacion Radar
- guardado de predicciones y metricas
- registro final en tracker/grid

## Apertura deseada

### `E4_v1_clean`

Configuracion base:

- modelo: `xgboost_regressor`
- `target_mode = nivel`
- `feature_mode = all`
- `lags = 1,2,3,4,5,6`
- `initial_train_size = 40`
- `horizons = 1,2,3,4`
- sin escalado
- baseline fijo sin tuning interno en esta etapa

Hiperparametros base:

- `n_estimators = 300`
- `learning_rate = 0.05`
- `max_depth = 3`
- `subsample = 0.8`
- `colsample_bytree = 0.8`
- `min_child_weight = 3`
- `reg_alpha = 0.0`
- `reg_lambda = 1.0`
- `random_state = 42`

## Segunda corrida opcional

Solo si `E4_v1_clean` queda estable.

Elegir solo una ruta:

- Ruta A: `E4_v2_clean` con `feature_mode = corr`
- Ruta B: `E4_v2_clean` con `target_mode = delta`

No abrir ambas a la vez.

## Respuestas que debe entregar E4

- si `Boosting` supera a `E3_v2_clean`
- si alcanza o supera a `E1_v4_clean`
- si alcanza o supera a `E1_v5_clean`
- en que horizontes aporta mas
- si mejora solo error numerico o tambien metricas operativas
- si mejora `direction_accuracy`
- si mejora `deteccion_caidas`
- si la no linealidad secuencial aporta mas que el bagging
- si `E4` merece expansion posterior

## Artefactos obligatorios

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `predicciones_h1.csv`
- `predicciones_h2.csv`
- `predicciones_h3.csv`
- `predicciones_h4.csv`
- snapshot del runner
- comparaciones contra referencias
- registro completo en tracker/grid

## Comparacion minima

Tabla consolidada entre:

- `E1_v5_clean`
- `E1_v4_clean`
- `E3_v2_clean`
- `E4_v1_clean`

Columnas minimas:

- `run_id`
- `family`
- `model`
- `target_mode`
- `feature_mode`
- `lags`
- `feature_count_prom`
- `mae_promedio`
- `rmse_promedio`
- `direction_accuracy_promedio`
- `deteccion_caidas_promedio`
- `L_total_Radar`
- `observacion_breve`

## Criterios de decision

- si `E4_v1_clean` supera a `E3_v2_clean` pero no a Ridge: `mejor no lineal parcial`
- si supera a `E1_v4_clean`: `nuevo contendiente serio`
- si supera a `E1_v5_clean`: `nuevo lider provisional`
- si mejora MAE pero no metricas operativas: `mejora numerica limitada`
- si mejora direccion y caidas aunque MAE cambie poco: `mejora operativamente valiosa`
- si no supera ni a Ridge ni a `E3_v2_clean`: cerrar `E4` base y no expandir todavia
