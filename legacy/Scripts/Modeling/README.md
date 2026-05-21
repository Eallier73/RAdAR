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
   Es la implementacion canonica compartida; la version de `Scripts/NLP_Data_Procesing/experiment_logger.py`
   ya no mantiene una copia divergente y funciona como wrapper de compatibilidad.
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
- `run_e1_bayesian_ridge.py`
- `run_e2_huber.py`
- `run_e2_huber_clean.py`
- `run_e3_random_forest.py`
- `run_e4_xgboost.py`
- `run_e5_catboost.py`
- `run_e6_arimax.py`
- `run_e7_prophet.py`
- `run_e8_hibrido_residuales.py`
- `run_e9_stacking.py`
- `run_e11_dual.py`
- `run_e12_representacion.py`
- `run_c1_random_forest_classifier.py`
- `run_c2_xgboost_classifier.py`
- `run_c3_catboost_classifier.py`
- `run_c4_lightgbm_classifier.py`

Reglas de organizacion:

- Un script por familia de modelo, no por mini corrida.
- Las variantes experimentales entran por CLI.
- La validacion se mantiene temporal y expansiva.
- El grid se actualiza via `experiment_logger.py`.
- La trazabilidad runtime comun usa `Scripts/common_runtime_logging.py` para mensajes con timestamp,
  severidad y contexto minimo en los modulos centrales del pipeline.
- Si un run historico quedo incompleto en el Excel, usar `backfill_runs.py`.

Estado metodologico:

- `E1` Ridge queda cerrado como baseline lineal principal: `E1_v5_clean` mejor global y `E1_v4_clean` referencia parsimoniosa.
- `E1.1` BayesianRidge funciona como micro-rama diagnostica corta dentro de la via lineal; no abre una familia principal nueva y solo sirve para verificar si queda margen lineal real frente a `E1_v5_clean`.
- `E2` Huber queda cerrado como familia no competitiva: `E2_v3_clean` gana internamente, pero no supera a Ridge y `E2_v4_clean` se cancela por decision metodologica.
- `E3` queda cerrado en su rama base con `E3_v2_clean` como mejor bagging interno.
- `E4` queda cerrado en su rama base con `E4_v1_clean` como mejor run interno, pero sin superar a `E3_v2_clean` ni a Ridge.
- `E5` queda abierta y madura con `E5_v4_clean` como campeon interno y mejor referencia no lineal tabular vigente.
- `E3`, `E4` y `E5` usan la misma base reusable para comparaciones contra runs de referencia y guardado de features seleccionadas cuando aplica.
- `E9` ya no usa el stacking tabular generico anterior; consume directamente la tabla curada `tabla_maestra_experimentos_radar_e9_curada.xlsx`, restringe por default a `fila_completa == True` y reconstruye `y_current` desde el dataset maestro solo para evaluar metricas Radar sin leakage.
- `E9_v2_clean` queda como mejor run interno de la familia de stacking clasico controlado y como referente operativo actual de riesgo-direccion-caidas.
- `E10` ya tiene infraestructura de datos especifica en `build_e10_meta_selector_table.py`, que construye la tabla operativa de meta-seleccion/gating a partir de predicciones OOF, contexto observable, desacuerdo entre modelos y etiquetas retrospectivas del selector.
- `E10` ya tiene runner canonico en `run_e10_meta_selector.py` y una primera corrida canonica `E10_v1_clean`; la familia ya fue probada y queda cerrada para promocion bajo su formulacion actual porque no supero al selector fijo ni a los benchmarks centrales.
- `E11` ya fue abierta con tres variantes controladas (`E11_v1_clean`, `E11_v2_clean`, `E11_v3_clean`) y queda evaluada sin promocion; `E11_v2_clean` es la mejor apertura interna, pero no desplaza a `E1_v5_clean` ni a `E9_v2_clean`.
- La autopsia posterior a `E11` deja dos lecturas utiles: la ventaja operativa de `E9_v2_clean` se concentra sobre todo en `H1` y es mas consistente con representacion enriquecida que con una ventaja puramente arquitectonica; ademas, el `movement_threshold=0.5` de la formulacion ternaria de `E11_v1_clean` resulto excesivo y `+-0.15` queda como valor preferente para una futura reapertura prudente.
- `E12` ya fue abierta como familia de representacion enriquecida con tres variantes (`E12_v1_clean`, `E12_v2_clean`, `E12_v3_clean`) sobre un `Ridge` simple. Ninguna variante mejora de forma defendible a `E1_v5_clean` ni a `E9_v2_clean`; `E12_v3_clean` deja el mejor hallazgo interno porque el desacuerdo entre bases aporta mas que el bloque de regimen, pero la familia queda evaluada sin promocion.
- `C1` ya tiene tres corridas canonicas (`C1_v1_clean`, `C1_v2_clean`, `C1_v3_clean`) y queda pausada tempranamente por colapso del target a clase unica.
- `C2` ya tiene tres corridas canonicas (`C2_v1_clean`, `C2_v2_clean`, `C2_v3_clean`) y replica el mismo colapso de clase unica observado en `C1`, por lo que tambien queda pausada tempranamente.
- `C3` y `C4` quedan con infraestructura preparada y sin corridas ejecutadas todavia.
- La clasificacion reutiliza el mismo `RadarExperimentTracker`; no abre un tracker paralelo.
- La capa explicativa transversal del proyecto sigue siendo parcial intra-familia: hay `features_seleccionadas_h*.csv` en algunos runs, pero no coeficientes, importancias o SHAP exportados de forma homogénea y comparable entre familias.

Documentacion canonica asociada:

- `/home/emilio/Documentos/RAdAR/Experimentos/plan_de_experimentacion_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/bitacora_experimental_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_dual_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_operacion_controlada.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/politica_operativa_sistema_dual_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/preparacion_automatizacion_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/politica_promocion_sistemas_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/consolidacion_operativa_post_produccion_controlada.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/cierre_formal_e10_no_promocionable.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/especificacion_futura_e11_dual.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/diccionario_constructos_canonicos_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e1_1_bayesian.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e5_catboost.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e6_arimax.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e7_prophet.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e8_hibrido_residual.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e9_stacking.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e10_gating_contextual.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e11_dual.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e12_representacion.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/constructos_representacion_e12.md`
- `/home/emilio/Documentos/RAdAR/Scripts/Modeling/analyze_post_e11_decision_phase.py`
- `/home/emilio/Documentos/RAdAR/Experimentos/autopsia_e1_v5_vs_e9_v2.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/analisis_recombinacion_ex_post_horizontes_e1_e9.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/recomendacion_thresholds_e11_o_futura_clasificacion.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_resultados_e2_verificacion_tactica.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/decision_formal_siguiente_paso_post_e11.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_resultados_e12_apertura_controlada.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_clasificacion_c1_c4.md`

Separacion de capas vigente:

- `Scripts/Modeling/` sigue siendo la capa experimental canonica.
- `Scripts/Operational_Controlada/` concentra la capa operativa controlada y no redefine la logica de evaluacion.
- Los benchmarks operativos vigentes se congelan contra los artefactos reales de `E1_v5_clean` y `E9_v2_clean`.
- La fase vigente del proyecto ya no es abrir nuevas familias, sino operar el sistema dual compuesto y preparar la futura automatizacion sin reinterpretar la politica funcional congelada.
