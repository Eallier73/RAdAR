# Plan Inicial Clasificacion Radar C1-C4

Fecha: `2026-03-30`

## Objetivo

Dejar documentada una rama paralela de clasificacion del movimiento del Radar, sin ejecutar corridas todavia y sin romper la rama de regresion vigente.

## Taxonomia fija de clases

- `baja_fuerte`: `cambio <= -3.0`
- `baja_moderada`: `-3.0 < cambio <= -1.5`
- `se_mantiene`: `-1.5 < cambio < 1.5`
- `sube_moderada`: `1.5 <= cambio < 3.0`
- `sube_fuerte`: `cambio >= 3.0`

Con:

- `delta_objetivo_h = y_{t+h} - y_t`

## Familias previstas

- `C1` RandomForestClassifier
- `C2` XGBoostClassifier
- `C3` CatBoostClassifier
- `C4` LightGBMClassifier

## Orden de lectura analitica recomendado

1. `C3` CatBoost
2. `C4` LightGBM
3. `C2` XGBoost
4. `C1` Random Forest

Este orden no implica preferencia metodologica definitiva. Solo prioriza las familias con mejor techo potencial esperado para clasificacion tabular.

## Estado actual

- Rama documentada: si
- Carpetas de prompts por familia: si
- Prompts por familia: si
- Scripts por familia preparados: si
- Corridas ejecutadas: no
- Integracion real al tracker: preparada, pero aun no probada con corridas reales

## Estructura documental

- [01_apertura_rama_clasificacion_c1_c4.md](/home/emilio/Documentos/RAdAR/Experimentos/Prompts_Agente/09_clasificacion_radar/01_apertura_rama_clasificacion_c1_c4.md)
- [01_c1_random_forest_classifier.md](/home/emilio/Documentos/RAdAR/Experimentos/Prompts_Agente/10_clasificacion_random_forest/01_c1_random_forest_classifier.md)
- [01_c2_xgboost_classifier.md](/home/emilio/Documentos/RAdAR/Experimentos/Prompts_Agente/11_clasificacion_xgboost/01_c2_xgboost_classifier.md)
- [01_c3_catboost_classifier.md](/home/emilio/Documentos/RAdAR/Experimentos/Prompts_Agente/12_clasificacion_catboost/01_c3_catboost_classifier.md)
- [01_c4_lightgbm_classifier.md](/home/emilio/Documentos/RAdAR/Experimentos/Prompts_Agente/13_clasificacion_lightgbm/01_c4_lightgbm_classifier.md)

## Trazabilidad exigida cuando se ejecute

Cada run de clasificacion debe crear y registrar:

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `predicciones_h1.csv` a `predicciones_h4.csv`
- `matriz_confusion_h1.json` a `matriz_confusion_h4.json`
- `soporte_clases_h1.json` a `soporte_clases_h4.json`

Y todo debe quedar registrado en:

- `RUN_ARTEFACTOS`
- `RUN_SUMMARY`
- `RESULTADOS_GRID`

## Siguiente paso natural

Implementar los runners de clasificacion y abrir primero `C3` o `C1` segun la estrategia elegida, pero manteniendo comparabilidad total y cero leakage.
