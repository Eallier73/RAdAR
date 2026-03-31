Nombre sugerido del chat: Retrofitting_stacking_y_hiperparametros_master_table

Quiero que prepares el proyecto Radar para stacking futuro de manera seria, auditable y retrospectiva.

ESTE TRABAJO NO ES TODAVÍA ENTRENAR EL STACKING.
ES DEJAR LA INFRAESTRUCTURA Y LA TABLA MAESTRA LISTAS PARA QUE EL STACKING FUTURO SEA METODOLÓGICAMENTE DEFENDIBLE.

OBJETIVO CENTRAL

Debes ampliar la tabla maestra de experimentos, la auditoría y los artefactos asociados para que:

1. cada run histórico quede descrito con suficiente detalle para ser reutilizable como modelo base en stacking;
2. esa preparación sea retrospectiva, o sea, no solo para corridas nuevas, sino también para las corridas ya existentes en disco;
3. quede explícito qué runs son elegibles para stacking por horizonte, cuáles no, y por qué;
4. el sistema pueda seguir actualizándose automáticamente con cada run nuevo, sin depender de reconstrucciones manuales posteriores.

CONTEXTO REAL DEL PROYECTO

Ya existe evidencia de readiness parcial para stacking:

- se pudieron reconstruir retrospectivamente catálogo, métricas por horizonte, cobertura de predicciones y compatibilidad estructural para stacking;
- ya existen bases `stacking_base_h1` a `stacking_base_h4`;
- hay runs compatibles para stacking y cobertura mergeable por horizonte;
- lo que todavía no está homogéneo transversalmente es la capa explicativa entre familias (coeficientes, importancias, interpretabilidad comparable).

Debes partir de esa realidad. No quiero un diseño abstracto desconectado del repositorio real.

ARQUITECTURA EXISTENTE QUE DEBES RESPETAR Y APROVECHAR

El proyecto ya tiene:

- `experiment_logger.py`
- `backfill_runs.py`
- workbook maestro `grid_experimentos_radar.xlsx`
- auditoría consolidada
- runs con artefactos en `Experimentos/runs/`
- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- predicciones por horizonte

No quiero que inventes otra infraestructura paralela si puede resolverse extendiendo limpiamente la actual.

PRINCIPIO GENERAL

Cada run debe quedar tratado como un activo auditable y reutilizable.

Eso significa que la tabla maestra no debe limitarse a “qué score tuvo”, sino registrar:

- qué modelo fue exactamente;
- con qué configuración exacta;
- con qué features exactas o resumidas;
- con qué predicciones fuera de muestra cuenta;
- con qué cobertura temporal cuenta;
- si es apto o no para meta-modelado;
- si su estructura es comparable con la de otros runs.

REQUISITO CRÍTICO: RETROSPECTIVO

No basta con dejar listo el pipeline hacia adelante.
Debes reconstruir retrospectivamente esta información para los runs ya existentes.

Eso significa:

- leer artefactos históricos reales en disco;
- inferir o recuperar hiperparámetros desde `parametros_run.json`, metadata y/o nombre del script si aplica;
- detectar faltantes;
- dejar explícito cuándo algo pudo reconstruirse con certeza y cuándo solo parcialmente;
- no inventar datos ausentes;
- no sobrescribir ambiguamente la historia experimental.

META FINAL

Quiero una tabla maestra y una auditoría enriquecidas que permitan, en una fase posterior, construir stacking por horizonte con base en evidencia real y trazabilidad sólida.

QUÉ DEBES HACER

A. EXPANDIR EL CATÁLOGO MAESTRO DE RUNS

Amplía la estructura maestra actual para que cada run incluya, como mínimo, estos campos nuevos o equivalentes claramente mapeados:

IDENTIDAD Y LINAGE
- run_id
- family
- model
- script_nombre
- script_ruta
- timestamp_run
- run_dir
- version_canonica
- es_run_maestro
- status_canonico
- motivo_exclusion_si_aplica

CONFIGURACIÓN DEL MODELO
- target_mode
- feature_mode
- transform_mode
- lags
- horizons
- initial_train_size
- validation_scheme
- tuning_interno
- tuning_metric
- hyperparams_json
- hyperparams_hash o firma compacta reproducible
- notas_config_clave

DATOS Y FEATURES
- feature_count_promedio
- feature_count_h1
- feature_count_h2
- feature_count_h3
- feature_count_h4
- features_artifact_available
- seleccion_variables_tipo
- source_dataset_period
- exogenas_o_no
- usa_target_delta
- usa_target_nivel

MÉTRICAS DESEMPEÑO
- mae_promedio
- rmse_promedio
- direction_accuracy_promedio
- deteccion_caidas_promedio
- L_total_Radar
- loss_h1
- loss_h2
- loss_h3
- loss_h4
- mejor_horizonte_por_loss
- fortalezas_operativas
- observacion_breve

PREDICCIONES Y ELEGIBILIDAD PARA STACKING
- tiene_predicciones_h1
- tiene_predicciones_h2
- tiene_predicciones_h3
- tiene_predicciones_h4
- filas_pred_h1
- filas_pred_h2
- filas_pred_h3
- filas_pred_h4
- mergeable_h1
- mergeable_h2
- mergeable_h3
- mergeable_h4
- stacking_eligible_global
- stacking_eligible_h1
- stacking_eligible_h2
- stacking_eligible_h3
- stacking_eligible_h4
- motivo_no_elegibilidad

EXPLICABILIDAD / TRAZABILIDAD EXPLICATIVA
- tiene_coeficientes
- tiene_importancias
- tiene_shap_o_equivalente
- explicabilidad_transversal_homogenea
- artifact_explicabilidad_path
- observacion_explicabilidad

B. DEFINIR REGLAS FORMALES DE ELEGIBILIDAD PARA STACKING

Debes dejar reglas explícitas, documentadas y automatizables para decidir si un run entra o no como candidato a meta-modelado.

Como mínimo, un run solo debe marcarse elegible si:

1. tiene identidad canónica clara;
2. no es un intento abortado, parcial o descartado;
3. tiene predicciones fuera de muestra utilizables por horizonte;
4. esas predicciones son mergeables estructuralmente con otras;
5. tiene métricas mínimas trazables;
6. su configuración puede reconstruirse con suficiente certeza;
7. no presenta una inconsistencia crítica que invalide su uso.

Debes distinguir:

- elegibilidad global;
- elegibilidad por horizonte.

Porque un run puede servir para H2 y no para H4, o viceversa.

C. HACER LA RECONSTRUCCIÓN RETROSPECTIVA

Debes recorrer retrospectivamente los runs ya existentes y poblar la nueva estructura usando artefactos reales.

Fuentes permitidas para reconstrucción:
- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `predicciones_h*.csv`
- `features_seleccionadas_h*.csv`
- rutas de artefactos en grid
- nombres de scripts
- nombres de directorios
- auditoría previa ya generada

Si algún campo no puede reconstruirse con confianza:
- déjalo vacío o nulo;
- marca `reconstruccion_parcial`;
- documenta la razón.

No quiero inferencias fantasiosas.
No quiero “rellenos” inventados.

D. NORMALIZAR HIPERPARÁMETROS

Este punto es central.

Necesito que cada run quede con una representación homogénea de hiperparámetros, aunque provenga de familias distintas.

Debes construir, como mínimo:

1. `hyperparams_json`
2. `hyperparams_firma`
3. `hyperparams_resumen`

La meta no es uniformar el contenido técnico, sino uniformar la trazabilidad.

E. DEJAR BASES DE STACKING MÁS ROBUSTAS

Revisa y fortalece la construcción de:
- `stacking_base_h1`
- `stacking_base_h2`
- `stacking_base_h3`
- `stacking_base_h4`

Cada una debe dejar claro:

- índice temporal o clave de alineación
- target real del horizonte
- columnas de predicción por run_id
- qué runs entraron
- cuáles quedaron fuera
- por qué quedaron fuera
- cobertura efectiva
- filas completas vs incompletas
- posibilidad de entrenamiento futuro de meta-modelo sin leakage

No entrenes todavía el meta-modelo.
Solo deja las bases limpias y auditadas.

F. AUTOMATIZAR HACIA ADELANTE

Además del backfill retrospectivo, debes dejar la infraestructura lista para que cada corrida nueva:

- registre automáticamente hiperparámetros normalizados;
- actualice elegibilidad para stacking;
- deje trazabilidad de cobertura de predicciones por horizonte;
- pueda integrarse a las bases stacking sin reconstrucción manual completa.

G. DOCUMENTACIÓN OBLIGATORIA

Debes crear o actualizar documentación que explique:

1. qué significa “run elegible para stacking” en este proyecto;
2. qué campos nuevos se añadieron a la tabla maestra;
3. cómo se reconstruyeron retrospectivamente;
4. qué supuestos se usaron y cuáles no;
5. qué limitaciones siguen pendientes;
6. cómo usar esta infraestructura en futuras familias.

LO QUE NO DEBES HACER

- No entrenes todavía stacking final.
- No mezcles predicciones in-sample con predicciones out-of-sample.
- No marques como elegible un run solo porque “tuvo buen score”.
- No uses directorios abortados o inconsistentes como si fueran canónicos.
- No sobreescribas la historia experimental para que se vea más ordenada de lo que realmente fue.
- No inventes hiperparámetros ausentes.
- No rompas compatibilidad con el grid actual.
- No dependas de edición manual del Excel como mecanismo principal.

CRITERIOS DE CALIDAD

El trabajo estará bien hecho si:

1. puedo ver para cada run histórico qué configuración exacta tuvo y qué tan recuperable fue;
2. puedo distinguir con claridad qué runs sirven o no para stacking y por qué;
3. puedo identificar por horizonte qué modelos son candidatos reales;
4. las bases stacking quedan alineadas y auditables;
5. el sistema puede seguir creciendo automáticamente con corridas nuevas;
6. queda trazabilidad suficiente para construir después un meta-modelo serio.
