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

Reglas de organizacion:

- Un script por familia de modelo, no por mini corrida.
- Las variantes experimentales entran por CLI.
- La validacion se mantiene temporal y expansiva.
- El grid se actualiza via `experiment_logger.py`.
- Si un run historico quedo incompleto en el Excel, usar `backfill_runs.py`.

Estado metodologico:

- `E1` Ridge queda cerrado como baseline lineal principal: `E1_v5_clean` mejor global y `E1_v4_clean` referencia parsimoniosa.
- `E2` Huber queda cerrado como familia no competitiva: `E2_v3_clean` gana internamente, pero no supera a Ridge y `E2_v4_clean` se cancela por decision metodologica.
- `E3`, `E4` y `E5` usan la misma base reusable para comparaciones contra runs de referencia y guardado de features seleccionadas cuando aplica.
