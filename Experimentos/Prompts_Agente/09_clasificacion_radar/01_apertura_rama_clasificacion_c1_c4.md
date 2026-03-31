Prompt para el agente
Nombre sugerido del chat o documento:
Apertura rama clasificacion Radar C1-C4

## Objetivo general

Abrir una rama experimental de clasificacion dentro del pipeline de modelado del proyecto Radar, en continuidad estricta con la arquitectura actual por familias y sin romper la rama de regresion ya existente.

Esta tarea no busca optimizar umbrales ni inventar una taxonomia despues de ver resultados. Busca abrir una rama limpia, comparable y trazable para clasificar el movimiento politico del Radar.

## Variable objetivo de clasificacion

La variable objetivo no es el valor continuo del Radar.

Debe construirse, para cada horizonte `h`, como:

- `delta_objetivo_h = y_{t+h} - y_t`

Y asignarse obligatoriamente a estas cinco clases:

- `baja_fuerte`: `cambio <= -3.0`
- `baja_moderada`: `-3.0 < cambio <= -1.5`
- `se_mantiene`: `-1.5 < cambio < 1.5`
- `sube_moderada`: `1.5 <= cambio < 3.0`
- `sube_fuerte`: `cambio >= 3.0`

Los umbrales son fijos ex ante y no se redefinen ni se optimizan con los datos.

## Familias a abrir

La rama de clasificacion debe quedar preparada y documentada para estas cuatro familias:

- `C1` RandomForestClassifier
- `C2` XGBoostClassifier
- `C3` CatBoostClassifier
- `C4` LightGBMClassifier

Cada familia se trabaja con:

- un script por familia
- variantes por CLI
- trazabilidad completa
- comparacion homogenea entre familias

Organizacion documental esperada:

- este prompt rector en `09_clasificacion_radar/`
- un prompt operativo por familia en su propia carpeta:
  - `10_clasificacion_random_forest/`
  - `11_clasificacion_xgboost/`
  - `12_clasificacion_catboost/`
  - `13_clasificacion_lightgbm/`

Runners esperados:

- `run_c1_random_forest_classifier.py`
- `run_c2_xgboost_classifier.py`
- `run_c3_catboost_classifier.py`
- `run_c4_lightgbm_classifier.py`

## Restriccion metodologica central

Esta rama debe respetar la logica central del proyecto Radar:

- validacion temporal estricta
- horizontes `1, 2, 3 y 4`
- trazabilidad completa por corrida
- comparacion homogenea entre familias
- cero leakage
- cero validacion aleatoria
- cero tuning usando informacion del futuro
- cero snooping basado en resultados observados

## Regla critica sobre leakage y snooping

### Prohibido

No debes:

- mezclar observaciones futuras en el entrenamiento de folds pasados
- seleccionar features usando toda la serie antes de validar
- balancear clases usando informacion de todo el dataset antes del split temporal
- calibrar hiperparametros usando el conjunto de evaluacion final
- cambiar umbrales de clase despues de ver resultados
- escoger variantes ganadoras usando promedios que incluyan informacion no disponible en tiempo real
- hacer oversampling global antes del `walk-forward`
- estandarizar o transformar con `fit` global previo al loop temporal

### Obligatorio

Si debes:

- construir cada fold de forma temporal
- hacer cualquier seleccion, escalado o rebalanceo solo dentro del fold de entrenamiento
- aplicar a validacion solo lo aprendido en train
- mantener flujo completamente separado por horizonte
- documentar cualquier decision sensible a leakage

## Compatibilidad obligatoria con el tracker actual

No rompas compatibilidad con el tracker actual.

Toda corrida de clasificacion debe registrarse con `RadarExperimentTracker` exactamente igual que las corridas existentes de regresion.

Cada run debe:

- crear `metadata_run.json`
- crear `parametros_run.json`
- crear `metricas_horizonte.json`
- crear `resumen_modeling_horizontes.json`
- crear `predicciones_h1.csv` a `predicciones_h4.csv`
- crear los artefactos nuevos de clasificacion
- registrar todo en `RUN_ARTEFACTOS`
- dejar su fila en `RUN_SUMMARY`
- dejar sus resultados por horizonte en `RESULTADOS_GRID` o equivalente actual
- disparar la actualizacion automatica de auditoria si esa integracion ya existe

Los artefactos nuevos de clasificacion deben incluir, como minimo:

- `matriz_confusion_h1.json`
- `matriz_confusion_h2.json`
- `matriz_confusion_h3.json`
- `matriz_confusion_h4.json`
- `soporte_clases_h1.json`
- `soporte_clases_h2.json`
- `soporte_clases_h3.json`
- `soporte_clases_h4.json`

## Construccion del target de clasificacion

Debe existir una logica reusable que:

- calcule `delta_objetivo_h = y_{t+h} - y_t`
- asigne la clase con la taxonomia fija
- mantenga la alineacion temporal correcta
- descarte filas inutilizables por borde temporal
- deje trazabilidad de como fue construido el target

Esto debe quedar documentado en metadata.

## Que se mantiene igual respecto a regresion

Se debe conservar:

- dataset maestro existente
- variables base ya usadas en el pipeline
- horizontes `1, 2, 3, 4`
- lags comparables
- validacion `walk-forward expanding`
- `initial_train_size` configurable
- tracker y artefactos estandarizados

## Metricas obligatorias por horizonte

### Clasificacion 5 clases

- `accuracy_5clases`
- `balanced_accuracy_5clases`
- `macro_f1_5clases`
- `weighted_f1_5clases`
- `recall_baja_fuerte`
- `recall_baja_total`
- `precision_baja_fuerte`
- `recall_sube_fuerte`
- `recall_sube_total`
- `matriz_confusion_5clases`
- `soporte_por_clase`

### Version colapsada a 3 clases

- `accuracy_3clases`
- `macro_f1_3clases`
- `balanced_accuracy_3clases`

### Metrica compuesta prioritaria

Debes proponer y calcular una `L_total_clasificacion`, documentada y justificable, que priorice:

- detectar bien `baja_fuerte`
- no confundir `sube_fuerte` con `se_mantiene`
- mantener balance general entre clases

## Desbalance de clases

Debes auditar el desbalance por horizonte.

Se permite usar:

- `class_weight`
- `sample_weight` dentro del fold
- equivalentes nativos del modelo

No se permite:

- `SMOTE` global
- oversampling global
- remuestreo sintetico fuera del fold de entrenamiento

En esta apertura, por defecto, no usar remuestreo sintetico.

## Variantes a correr por familia

Cada familia debe abrir tres variantes:

- `v1` baseline prudente
- `v2` mas regularizada o mas parsimoniosa
- `v3` un poco mas flexible pero aun controlada

No abrir grids masivos.
No hacer busqueda oportunista.

## Regla sobre features y preprocessing

Baseline principal:

- `feature_mode = all`
- `lags = 1,2,3,4,5,6`

No escalar arboles salvo obligacion tecnica real del wrapper.

No abrir todavia una rama de seleccion de variables ni `LASSO`.

## Validacion temporal

Esquema minimo:

- `initial_train_size = 40`
- validacion `walk-forward expanding`
- evaluacion `out-of-sample` por cada paso temporal posible

No usar:

- `KFold`
- `StratifiedKFold` aleatorio
- `shuffle`
- `train_test_split` aleatorio

## Entregables finales esperados de la rama

Al terminar las 12 corridas, el agente debe entregar:

- lista de archivos creados o modificados
- explicacion breve de la funcion de cada archivo
- scripts completos de las cuatro familias de clasificacion
- helpers nuevos necesarios
- comandos exactos para correr las 12 corridas
- resultados resumidos de las 12 corridas
- comparacion consolidada entre familias
- nota metodologica explicita sobre leakage, snooping y limitaciones
- recomendacion de que familias ameritan segunda ola experimental

## Nomenclatura sugerida

- `C1_v1_clean`
- `C1_v2_clean`
- `C1_v3_clean`
- `C2_v1_clean`
- `C2_v2_clean`
- `C2_v3_clean`
- `C3_v1_clean`
- `C3_v2_clean`
- `C3_v3_clean`
- `C4_v1_clean`
- `C4_v2_clean`
- `C4_v3_clean`

## Criterio de exito

La tarea se considera exitosa solo si queda:

- una rama nueva de clasificacion operable
- 12 corridas comparables y trazables
- cero leakage
- cero validacion aleatoria
- una comparacion honesta entre familias
- una base solida para decidir si ampliar o no la experimentacion
