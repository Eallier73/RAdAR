Prompt para el agente
Nombre: Apertura C2 XGBoostClassifier

Trabaja sobre la rama de clasificacion Radar siguiendo el prompt maestro de `C1-C4`, sin romper compatibilidad con el tracker actual.

## Objetivo

Abrir la familia `C2` con `XGBoostClassifier` multiclase nativo bajo validacion temporal estricta.

## Corridas obligatorias

### C2_v1_clean

Objetivo:

- baseline prudente de boosting regularizado

Parametros:

- `n_estimators = 200`
- `max_depth = 3`
- `learning_rate = 0.05`
- `subsample = 0.8`
- `colsample_bytree = 0.8`
- `min_child_weight = 4`
- `reg_alpha = 0.5`
- `reg_lambda = 2.0`
- `objective = multi:softprob`
- `eval_metric = mlogloss`
- `random_state = 42`

### C2_v2_clean

Objetivo:

- variante mas regularizada y conservadora

Parametros:

- `n_estimators = 250`
- `max_depth = 2`
- `learning_rate = 0.04`
- `subsample = 0.8`
- `colsample_bytree = 0.7`
- `min_child_weight = 5`
- `reg_alpha = 1.0`
- `reg_lambda = 3.0`
- `objective = multi:softprob`
- `eval_metric = mlogloss`
- `random_state = 42`

### C2_v3_clean

Objetivo:

- variante algo mas flexible pero controlada

Parametros:

- `n_estimators = 300`
- `max_depth = 4`
- `learning_rate = 0.05`
- `subsample = 0.85`
- `colsample_bytree = 0.85`
- `min_child_weight = 3`
- `reg_alpha = 0.25`
- `reg_lambda = 2.0`
- `objective = multi:softprob`
- `eval_metric = mlogloss`
- `random_state = 42`

## Configuracion comun

- `feature_mode = all`
- `target_mode_clf = bandas_5clases`
- `lags = 1,2,3,4,5,6`
- `initial_train_size = 40`
- `horizons = 1,2,3,4`

## Hipotesis a probar

- `C2_v1_clean`: baseline serio de boosting regularizado
- `C2_v2_clean`: menos riesgo de memorizar ruido
- `C2_v3_clean`: mas capacidad para patrones complejos, pero mayor riesgo de inestabilidad

## Restricciones

- sin tuning con futuro
- sin calibracion sobre test externo
- sin rebalanceo global
- sin leakage en cualquier seleccion o transformacion
- todos los artefactos deben quedar dados de alta en tracker

## Analisis obligatorio al cierre de C2

Responde explicitamente:

- cual variante fue mas estable por horizonte
- cual detecto mejor `baja_fuerte` y `baja_total`
- si la familia justifica segunda ola experimental
