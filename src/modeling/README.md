# modeling

Estatus: `canonica_vigente`

Proposito:

- concentrar la arquitectura reusable de modelado del Radar
- servir como referencia de estandar para el resto del repo

## Subarquitectura de capas

Todos los modulos viven en `src/modeling/` como capa plana. Los imports usan nombres de modulo directos (sin paquete), lo que requiere que el directorio se incluya en `sys.path` al ejecutar. La clasificacion por capa es documental, no estructural en disco.

### core/ — modulos reutilizables

| Archivo | Responsabilidad |
| --- | --- |
| `config.py` | rutas, constantes y modos del pipeline |
| `data_master.py` | carga y validacion del dataset maestro |
| `feature_engineering.py` | lags, frames por horizonte, construccion de features |
| `preprocessing.py` | transformaciones reutilizables (escalado, encoding) |
| `evaluation.py` | validacion temporal y metricas Radar |
| `custom_estimators.py` | estimadores custom (Prophet, SARIMAX wrappers) |
| `classification_targets.py` | targets y frames para familia de clasificacion |
| `classification_evaluation.py` | metricas especificas de clasificacion |
| `experiment_logger.py` | tracker canonico del grid y de artefactos |

### runners/ — scripts de ejecucion experimental

| Archivo | Responsabilidad |
| --- | --- |
| `pipeline_common.py` | orquestacion comun de runs de regresion/forecast |
| `classification_pipeline_common.py` | orquestacion comun de runs de clasificacion |
| `run_e1_ridge.py` | E1: Ridge (implementacion compacta via run_tabular_experiment) |
| `run_e1_ridge_clean.py` | E1: Ridge (implementacion extendida clean) |
| `run_e1_bayesian_ridge.py` | E1: BayesianRidge |
| `run_e2_huber.py` | E2: HuberRegressor (compacto) |
| `run_e2_huber_clean.py` | E2: HuberRegressor (extendido clean) |
| `run_e3_random_forest.py` | E3: RandomForestRegressor |
| `run_e4_xgboost.py` | E4: XGBoost regressor |
| `run_e5_catboost.py` | E5: CatBoost regressor |
| `run_e6_arimax.py` | E6: ARIMAX/SARIMAX |
| `run_e7_prophet.py` | E7: Prophet con exogenas |
| `run_e8_hibrido_residuales.py` | E8: Hibrido residuales (Prophet + ML) |
| `run_e9_stacking.py` | E9: Stacking de modelos base |
| `run_e10_meta_selector.py` | E10: Meta-selector contextual |
| `run_c1_random_forest_classifier.py` | C1: RandomForest clasificador |
| `run_c2_xgboost_classifier.py` | C2: XGBoost clasificador |
| `run_c3_catboost_classifier.py` | C3: CatBoost clasificador |
| `run_c4_lightgbm_classifier.py` | C4: LightGBM clasificador |

### reporting/ — builders de tablas maestras y reportes

| Archivo | Responsabilidad |
| --- | --- |
| `build_experiments_master_table.py` | consolida y audita tabla maestra de experimentos |
| `build_e10_meta_selector_table.py` | construye tabla operativa para E10 |
| `backfill_runs.py` | rellena entradas faltantes en el grid desde artefactos existentes |

## Nota sobre estructura de imports

Los modulos de `core/` y `runners/` usan imports directos por nombre (ej: `from config import ...`).
Para ejecutar, el directorio `src/modeling/` debe estar en `sys.path`. Ejemplo:

```bash
PYTHONPATH=src/modeling python src/modeling/run_e5_catboost.py
```

O ejecutar directamente desde dentro del directorio.

## Relacion con otras carpetas

- lee dataset maestro desde `data/processed/modeling/`
- usa workbook y tablas en `experiments/audit/`
- guarda corridas en `experiments/runs/`
- escribe logs tecnicos en `artifacts/` cuando aplica

## Compatibilidad

- `src/nlp/experiment_logger.py` es solo wrapper hacia `src/modeling/experiment_logger.py`
- las rutas historicas `Scripts/Modeling/*` ya fueron retiradas; usar `src/modeling/*`

## Reglas

- una familia, un runner canonico
- la configuracion entra por CLI o por constantes comunes, no por forks de script
- los cambios metodologicos se documentan en `experiments/research/`

## Documentacion asociada

- `experiments/research/plan_de_experimentacion_radar.md`
- `experiments/research/bitacora_experimental_radar.md`
- `experiments/research/diccionario_constructos_canonicos_radar.md`
- `experiments/research/resumen_metodologico_e5_catboost.md`
- `experiments/research/resumen_metodologico_e6_arimax.md`
- `experiments/research/resumen_metodologico_e7_prophet.md`
- `experiments/research/resumen_metodologico_e8_hibrido_residual.md`
- `experiments/research/resumen_metodologico_e9_stacking.md`
- `experiments/research/resumen_metodologico_e10_gating_contextual.md`
- `experiments/research/resumen_metodologico_clasificacion_c1_c4.md`
