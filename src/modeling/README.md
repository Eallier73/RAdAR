# modeling

Estatus: `canonica_vigente`

Proposito:

- concentrar la arquitectura reusable de modelado del Radar
- servir como referencia de estandar para el resto del repo

Capas principales:

- `config.py`: rutas y constantes del pipeline
- `data_master.py`: carga y validacion del dataset maestro
- `feature_engineering.py`: lags y frames por horizonte
- `preprocessing.py`: transformaciones reutilizables
- `evaluation.py`: validacion temporal y metricas Radar
- `pipeline_common.py`: orquestacion comun de runs
- `experiment_logger.py`: tracker canonico del grid y de artefactos
- `build_experiments_master_table.py`: consolidacion y auditoria experimental
- `build_e10_meta_selector_table.py`: construccion de tabla operativa para E10
- `run_e*.py` y `run_c*.py`: runners canonicos por familia

Relacion con otras carpetas:

- lee dataset maestro desde `data/processed/modeling/`
- usa workbook y tablas en `experiments/audit/`
- guarda corridas en `experiments/runs/`
- escribe logs tecnicos en `artifacts/` cuando aplica

Compatibilidad:

- `src/nlp/experiment_logger.py` es solo wrapper hacia `src/modeling/experiment_logger.py`
- las rutas historicas `Scripts/Modeling/*` ya fueron retiradas; usar `src/modeling/*`

Reglas:

- una familia, un runner canonico
- la configuracion entra por CLI o por constantes comunes, no por forks de script
- los cambios metodologicos se documentan en `experiments/research/`

Documentacion asociada:

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
