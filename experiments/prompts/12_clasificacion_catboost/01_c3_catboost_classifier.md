Prompt para el agente
Nombre: Apertura C3 CatBoostClassifier

Trabaja sobre la rama de clasificacion Radar siguiendo el prompt maestro de `C1-C4`, sin romper compatibilidad con el tracker actual.

## Objetivo

Abrir la familia `C3` con `CatBoostClassifier` multiclase nativo bajo validacion temporal estricta.

## Corridas obligatorias

### C3_v1_clean

Objetivo:

- baseline prudente

Parametros:

- `iterations = 300`
- `depth = 4`
- `learning_rate = 0.05`
- `l2_leaf_reg = 5.0`
- `subsample = 0.8`
- `loss_function = MultiClass`
- `eval_metric = MultiClass`
- `random_seed = 42`
- `verbose = False`

### C3_v2_clean

Objetivo:

- version mas conservadora / mas regularizada

Parametros:

- `iterations = 250`
- `depth = 3`
- `learning_rate = 0.04`
- `l2_leaf_reg = 6.0`
- `subsample = 0.8`
- `loss_function = MultiClass`
- `eval_metric = MultiClass`
- `random_seed = 42`
- `verbose = False`

### C3_v3_clean

Objetivo:

- variante un poco mas flexible

Parametros:

- `iterations = 400`
- `depth = 5`
- `learning_rate = 0.05`
- `l2_leaf_reg = 4.0`
- `subsample = 0.85`
- `loss_function = MultiClass`
- `eval_metric = MultiClass`
- `random_seed = 42`
- `verbose = False`

## Configuracion comun

- `feature_mode = all`
- `target_mode_clf = bandas_5clases`
- `lags = 1,2,3,4,5,6`
- `initial_train_size = 40`
- `horizons = 1,2,3,4`

## Hipotesis a probar

- `C3_v1_clean`: baseline fuerte con buen equilibrio entre flexibilidad y control
- `C3_v2_clean`: menor riesgo de sobreajuste con muestra pequena
- `C3_v3_clean`: mejor captura de clases extremas si existe senal suficiente

## Aclaracion metodologica obligatoria

Si el dataset actual no aporta columnas categoricas explicitas tratables como tales, debes documentar que CatBoost esta funcionando como clasificador tabular sobre variables numericas y no inflar el argumento de uso de categoricas.

## Restricciones

- cero leakage
- cero tuning con futuro
- cero remuestreo sintetico global
- preservacion completa del tracker actual

## Analisis obligatorio al cierre de C3

Responde explicitamente:

- si CatBoost fue realmente una de las familias mas prometedoras
- cual variante equilibra mejor sensibilidad a bajas y estabilidad general
- si amerita segunda ola experimental
