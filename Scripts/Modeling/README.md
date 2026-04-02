# Modeling

Este directorio concentra el pipeline experimental del Radar organizado por familias de modelos.

Capas comunes:

1. `config.py`
   Rutas base, columnas del dataset, modos de target y modos de seleccion de features.
2. `data_master.py`
   Carga y validacion del dataset maestro.
3. `feature_engineering.py`
   Construccion de lags y model frame por horizonte / target mode.
4. `evaluation.py`
   Walk-forward temporal, seleccion de features por fold y metricas Radar.
5. `custom_estimators.py`
   Wrappers para SARIMAX, Prophet, hibridos residuales y stacking temporal.
6. `preprocessing.py`
   Transformaciones reutilizables para familias que las necesiten, incluyendo winsorizacion.
7. `pipeline_common.py`
   Orquestacion reusable del experimento, guardado de artefactos y finalize en tracker.
8. `experiment_logger.py`
   Tracker del grid y de artefactos.
9. `backfill_runs.py`
   Repara o retrocarga resultados numericos al grid desde runs ya guardados.
10. `classification_targets.py`
   Construccion reusable del target de clasificacion por bandas politicas.
11. `classification_evaluation.py`
   Walk-forward de clasificacion, metricas multiclase y perdida compuesta de clasificacion.
12. `classification_pipeline_common.py`
   Orquestacion reusable de clasificacion con el mismo tracker del pipeline principal.

Runners por familia:

- `run_e1_ridge.py`
- `run_e1_ridge_clean.py`
- `run_e2_huber.py`
- `run_e2_huber_clean.py`
- `run_e3_random_forest.py`
- `run_e4_xgboost.py`
- `run_e5_catboost.py`
- `run_e6_arimax.py`
- `run_e7_prophet.py`
- `run_e8_hibrido_residuales.py`
- `run_e9_stacking.py`
- `run_c1_random_forest_classifier.py`
- `run_c2_xgboost_classifier.py`
- `run_c3_catboost_classifier.py`
- `run_c4_lightgbm_classifier.py`

Reglas de organizacion:

- Un script por familia de modelo, no por mini corrida.
- Las variantes experimentales entran por CLI.
- La validacion se mantiene temporal y expansiva.
- El grid se actualiza via `experiment_logger.py`.
- Si un run historico quedo incompleto en el Excel, usar `backfill_runs.py`.

Estado metodologico:

- `E1` Ridge queda cerrado como baseline lineal principal: `E1_v5_clean` mejor global y `E1_v4_clean` referencia parsimoniosa.
- `E2` Huber queda cerrado como familia no competitiva: `E2_v3_clean` gana internamente, pero no supera a Ridge y `E2_v4_clean` se cancela por decision metodologica.
- `E3` queda cerrado en su rama base con `E3_v2_clean` como mejor bagging interno.
- `E4` queda cerrado en su rama base con `E4_v1_clean` como mejor run interno, pero sin superar a `E3_v2_clean` ni a Ridge.
- `E5` ya queda abierto con `run_e5_catboost.py` y `E5_v1_clean` como primera referencia CatBoost.
- `E3`, `E4` y `E5` usan la misma base reusable para comparaciones contra runs de referencia y guardado de features seleccionadas cuando aplica.
- `E9` ya no usa el stacking tabular generico anterior; consume directamente la tabla curada `tabla_maestra_experimentos_radar_e9_curada.xlsx`, restringe por default a `fila_completa == True` y reconstruye `y_current` desde el dataset maestro solo para evaluar metricas Radar sin leakage.
- `E9_v2_clean` queda como mejor run interno de la familia de stacking clasico controlado y como referente operativo actual de riesgo-direccion-caidas.
- `E10` ya tiene infraestructura de datos especifica en `build_e10_meta_selector_table.py`, que construye la tabla operativa de meta-seleccion/gating a partir de predicciones OOF, contexto observable, desacuerdo entre modelos y etiquetas retrospectivas del selector.
- `E10` ya tiene runner canonico en `run_e10_meta_selector.py` y una primera corrida diagnostica `E10_v1_clean`; la familia ya paso de premodelado a modelado inicial, aunque todavia sin consolidarse frente a los benchmarks centrales.
- `E11` queda solo como familia conceptual futura de arquitectura dual numerica + categorica.
- La rama `C1-C4` de clasificacion queda preparada con scripts por familia, pero todavia sin corridas ejecutadas.
- La clasificacion reutiliza el mismo `RadarExperimentTracker`; no abre un tracker paralelo.
