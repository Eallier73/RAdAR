Prompt para el agente
Nombre: Apertura C1 RandomForestClassifier

Trabaja sobre la rama de clasificacion Radar siguiendo el prompt maestro de `C1-C4`, sin romper compatibilidad con el tracker actual.

## Objetivo

Abrir la familia `C1` con `RandomForestClassifier` como baseline robusto y conservador para clasificacion temporal del movimiento del Radar.

## Corridas obligatorias

### C1_v1_clean

Objetivo:

- baseline prudente

Parametros:

- `n_estimators = 300`
- `max_depth = 4`
- `min_samples_leaf = 4`
- `min_samples_split = 8`
- `max_features = sqrt`
- `class_weight = balanced_subsample`
- `random_state = 42`

Configuracion experimental:

- `feature_mode = all`
- `target_mode_clf = bandas_5clases`
- `lags = 1,2,3,4,5,6`
- `initial_train_size = 40`
- `horizons = 1,2,3,4`

### C1_v2_clean

Objetivo:

- version mas parsimoniosa / mas conservadora

Parametros:

- `n_estimators = 400`
- `max_depth = 3`
- `min_samples_leaf = 5`
- `min_samples_split = 10`
- `max_features = sqrt`
- `class_weight = balanced_subsample`
- `random_state = 42`

Configuracion experimental:

- igual que `C1_v1_clean`

### C1_v3_clean

Objetivo:

- version un poco mas flexible pero todavia prudente

Parametros:

- `n_estimators = 500`
- `max_depth = 6`
- `min_samples_leaf = 3`
- `min_samples_split = 6`
- `max_features = sqrt`
- `class_weight = balanced_subsample`
- `random_state = 42`

Configuracion experimental:

- igual que `C1_v1_clean`

## Hipotesis a probar

- `C1_v1_clean`: baseline estable con bajo riesgo de overfitting
- `C1_v2_clean`: mejor generalizacion si la muestra efectiva por horizonte es pequena
- `C1_v3_clean`: mejor captura de no linealidades, pero con mayor riesgo de sobreajuste

## Restricciones

- no usar validacion aleatoria
- no usar oversampling global
- no hacer seleccion de variables mirando toda la serie
- no cambiar taxonomia de clases
- registrar todo con `RadarExperimentTracker`

## Artefactos obligatorios por run

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `predicciones_h1.csv` a `predicciones_h4.csv`
- `matriz_confusion_h1.json` a `matriz_confusion_h4.json`
- `soporte_clases_h1.json` a `soporte_clases_h4.json`

## Analisis obligatorio al cierre de C1

Responde explicitamente:

- cual de `C1_v1`, `C1_v2`, `C1_v3` fue mas estable
- si `RandomForestClassifier` colapsa hacia la clase dominante
- si detecta bien `baja_fuerte`
- si justifica una segunda ola experimental o no
