Prompt para el agente
Nombre: Apertura C4 LightGBMClassifier

Trabaja sobre la rama de clasificacion Radar siguiendo el prompt maestro de `C1-C4`, sin romper compatibilidad con el tracker actual.

## Objetivo

Abrir la familia `C4` con `LightGBMClassifier` multiclase nativo bajo validacion temporal estricta.

## Corridas obligatorias

### C4_v1_clean

Objetivo:

- baseline prudente

Parametros:

- `n_estimators = 200`
- `num_leaves = 15`
- `max_depth = 4`
- `learning_rate = 0.05`
- `min_child_samples = 10`
- `subsample = 0.8`
- `colsample_bytree = 0.8`
- `reg_alpha = 0.5`
- `reg_lambda = 2.0`
- `objective = multiclass`
- `random_state = 42`

### C4_v2_clean

Objetivo:

- version mas conservadora

Parametros:

- `n_estimators = 250`
- `num_leaves = 11`
- `max_depth = 3`
- `learning_rate = 0.04`
- `min_child_samples = 12`
- `subsample = 0.8`
- `colsample_bytree = 0.75`
- `reg_alpha = 1.0`
- `reg_lambda = 3.0`
- `objective = multiclass`
- `random_state = 42`

### C4_v3_clean

Objetivo:

- version un poco mas flexible

Parametros:

- `n_estimators = 300`
- `num_leaves = 21`
- `max_depth = 5`
- `learning_rate = 0.05`
- `min_child_samples = 8`
- `subsample = 0.85`
- `colsample_bytree = 0.85`
- `reg_alpha = 0.25`
- `reg_lambda = 2.0`
- `objective = multiclass`
- `random_state = 42`

## Configuracion comun

- `feature_mode = all`
- `target_mode_clf = bandas_5clases`
- `lags = 1,2,3,4,5,6`
- `initial_train_size = 40`
- `horizons = 1,2,3,4`

## Hipotesis a probar

- `C4_v1_clean`: baseline fuerte para tabular
- `C4_v2_clean`: control conservador frente a muestra corta
- `C4_v3_clean`: mayor capacidad para capturar estructura compleja, con riesgo mayor de overfitting

## Restricciones

- no usar validacion aleatoria
- no abrir tuning oportunista
- no usar transformaciones ajustadas globalmente
- todo debe quedar registrado como en regresion

## Analisis obligatorio al cierre de C4

Responde explicitamente:

- si LightGBM compite con CatBoost y XGBoost en clases extremas
- si alguna variante colapsa hacia la clase dominante
- si la familia merece segunda ola experimental
