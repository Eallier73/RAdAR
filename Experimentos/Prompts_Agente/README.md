# Prompts Agente

Esta carpeta concentra prompts operativos del proyecto Radar organizados por tema.

Estructura:

- `01_pipeline_arquitectura/`
  Prompts para refactor del pipeline, estructura experimental y organizacion por familias.
- `02_analisis/`
  Prompts para pedir explicaciones tecnicas o auditoria de scripts.
- `03_familia_ridge/`
  Prompts especificos de la familia E1 Ridge: plan experimental, limpieza metodologica y continuacion.
- `04_familia_huber/`
  Prompts especificos de la familia E2 Huber: transicion desde Ridge limpio y experimentos robustos.
- `05_familia_random_forest/`
  Prompts de cierre de E2 y arranque de la familia E3 Random Forest dentro de la arquitectura por familias.
- `06_auditoria_experimental/`
  Prompts de auditoria retrospectiva, inventario de runs y consolidacion de resultados experimentales.
  Tambien incluye prompts para automatizar esa auditoria dentro del tracker.
- `07_familia_boosting/`
  Prompts de apertura de la familia E4 Boosting, comparacion contra Ridge y arboles bagging, y continuidad futura.
- `08_familia_catboost/`
  Prompts de cierre formal de E4 y apertura de la familia E5 CatBoost, dejando mapeada la continuidad hacia E6, E7 y E8.
- `09_clasificacion_radar/`
  Prompt rector de apertura de la rama paralela de clasificacion C1-C4.
- `10_clasificacion_random_forest/`
  Prompt operativo de la familia C1 RandomForestClassifier.
- `11_clasificacion_xgboost/`
  Prompt operativo de la familia C2 XGBoostClassifier.
- `12_clasificacion_catboost/`
  Prompt operativo de la familia C3 CatBoostClassifier.
- `13_clasificacion_lightgbm/`
  Prompt operativo de la familia C4 LightGBMClassifier.
- `14_familia_arimax/`
  Prompt operativo de apertura de la familia E6 ARIMAX/SARIMAX con exogenas.
- `15_familia_prophet/`
  Prompt operativo de apertura de la familia E7 Prophet con regresores exogenos.

Convencion de nombres:

- Prefijo numerico para mantener orden de lectura.
- Nombres descriptivos en minusculas y ASCII.
- Extension `.md` para que el contenido sea legible y editable facilmente.

Mapa actual:

- `01_pipeline_arquitectura/01_refactor_pipeline_experimentos_por_familias.md`
- `02_analisis/01_analisis_tecnico_de_script_experimental.md`
- `03_familia_ridge/01_plan_experimentos_ridge_e1_v2_a_e1_v10.md`
- `03_familia_ridge/02_reconstruccion_ridge_e1_v2_clean_sin_leakage.md`
- `03_familia_ridge/03_continuacion_ridge_e1_v3_clean_e1_v4_clean.md`
- `03_familia_ridge/04_continuacion_ridge_e1_v5_clean_memoria_larga.md`
- `03_familia_ridge/05_cierre_ridge_y_transicion_a_familia_no_lineal.md`
- `04_familia_huber/01_transicion_ridge_a_huber_clean.md`
- `04_familia_huber/02_micro_rama_diagnostica_huber_e2_v2_a_e2_v4.md`
- `05_familia_random_forest/01_cierre_e2_y_arranque_e3_random_forest.md`
- `05_familia_random_forest/02_extratrees_e3_v3_clean.md`
- `06_auditoria_experimental/01_auditoria_retro_experimentos_master_table.md`
- `06_auditoria_experimental/02_integracion_automatica_auditoria_tracker.md`
- `06_auditoria_experimental/03_ampliacion_tabla_maestra_ranking_metricas_horizonte.md`
- `06_auditoria_experimental/04_ampliacion_tabla_maestra_para_stacking.md`
- `06_auditoria_experimental/05_retrofitting_stacking_y_hiperparametros_master_table.md`
- `07_familia_boosting/01_apertura_e4_boosting.md`
- `07_familia_boosting/02_continuacion_controlada_e4_v2_e4_v3.md`
- `08_familia_catboost/01_cierre_e4_y_apertura_e5_catboost.md`
- `09_clasificacion_radar/01_apertura_rama_clasificacion_c1_c4.md`
- `10_clasificacion_random_forest/01_c1_random_forest_classifier.md`
- `11_clasificacion_xgboost/01_c2_xgboost_classifier.md`
- `12_clasificacion_catboost/01_c3_catboost_classifier.md`
- `13_clasificacion_lightgbm/01_c4_lightgbm_classifier.md`
- `14_familia_arimax/01_apertura_e6_arimax.md`
- `15_familia_prophet/01_apertura_e7_prophet.md`
