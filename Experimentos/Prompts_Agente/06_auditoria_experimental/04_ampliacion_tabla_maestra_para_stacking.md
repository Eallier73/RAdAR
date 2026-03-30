# Ampliacion de tabla maestra experimental para readiness de stacking

## Objetivo

Ampliar la tabla maestra experimental de Radar para que no solo sirva como auditoria y ranking de corridas, sino tambien como base preparatoria para una futura familia de hipermodelos, ensembles o stacking.

## Requerimiento central

Mantener la capa actual de auditoria y comparacion experimental, pero agregar una segunda capa orientada a readiness para meta-modelado.

La estructura debe permitir:

1. seguirse llenando automaticamente con nuevos runs;
2. reconstruir retrospectivamente runs historicos;
3. identificar que runs son utilizables como modelos base;
4. dejar preparada la base que luego permita construir datasets de stacking por horizonte.

## Hojas requeridas

### `runs_catalogo`

Una fila por run con metadata general, configuracion, rutas y elegibilidad para meta-modelo.

Columnas minimas:

- `run_id`
- `family`
- `model`
- `script_family`
- `target_mode`
- `feature_mode`
- `transform_mode`
- `lags`
- `horizons`
- `initial_train_size`
- `tuning_interno`
- `fecha_run`
- `status_run`
- `L_total_Radar`
- `path_run`
- `metadata_run_path`
- `parametros_run_path`
- `metricas_horizonte_path`
- `resumen_horizontes_path`
- `predicciones_h1_path`
- `predicciones_h2_path`
- `predicciones_h3_path`
- `predicciones_h4_path`
- `predicciones_h1_existe`
- `predicciones_h2_existe`
- `predicciones_h3_existe`
- `predicciones_h4_existe`
- `es_candidato_meta_modelo`
- `motivo_exclusion_meta_modelo`
- `notas_config`

### `metricas_por_horizonte_long`

Una fila por `run_id + horizonte`.

Columnas minimas:

- `run_id`
- `horizonte`
- `family`
- `model`
- `target_mode`
- `feature_mode`
- `lags`
- `mae`
- `rmse`
- `direction_accuracy`
- `deteccion_caidas`
- `l_num`
- `l_trend`
- `l_risk`
- `l_tol`
- `loss_h`
- `status_run`
- `rank_mae_por_horizonte`
- `rank_rmse_por_horizonte`
- `rank_direction_accuracy_por_horizonte`
- `rank_deteccion_caidas_por_horizonte`
- `rank_loss_h_por_horizonte`

### `ganadores_por_metrica_horizonte`

Mantener y fortalecer la hoja compacta con top 1, top 2 y top 3 por horizonte y metrica.

### `stacking_readiness`

Una fila por run con auditoria estructural para meta-modelado.

Columnas minimas:

- `run_id`
- `family`
- `model`
- `horizontes_disponibles`
- `predicciones_completas_1a4`
- `columnas_minimas_ok`
- `tiene_fecha`
- `tiene_y_true`
- `tiene_y_pred`
- `orden_temporal_ok`
- `sin_duplicados_fecha`
- `cantidad_obs_h1`
- `cantidad_obs_h2`
- `cantidad_obs_h3`
- `cantidad_obs_h4`
- `cobertura_total_predicciones`
- `compatible_para_stacking`
- `prioridad_para_meta_modelo`
- `motivo_no_compatible`

### `cobertura_predicciones`

Una fila por `run_id + horizonte`.

Columnas minimas:

- `run_id`
- `horizonte`
- `pred_path`
- `existe_archivo`
- `fecha_min_pred`
- `fecha_max_pred`
- `n_predicciones`
- `n_fechas_unicas`
- `sin_duplicados_fecha`
- `columnas_detectadas`
- `compatible_para_merge`

### Bases parciales por horizonte

Si es viable retrospectivamente:

- `stacking_base_h1`
- `stacking_base_h2`
- `stacking_base_h3`
- `stacking_base_h4`

Cada una con estructura:

- `fecha`
- `y_true`
- una columna por run elegible con su `y_pred`
- `n_modelos_disponibles_fila`

## Regla de oro

No inventar datos.
Si algo no existe en los artefactos, marcarlo como faltante o no detectable.

## Criterios conservadores para stacking

Un run solo debe marcarse como candidato a meta-modelo si:

- es un run completo;
- tiene metricas por horizonte;
- tiene predicciones por horizonte;
- se identifica columna temporal;
- se identifica `y_true`;
- se identifica `y_pred`;
- no hay duplicados graves de fecha;
- y las predicciones son mergeables por horizonte.

## Resultado esperado

Dejar una tabla maestra ampliada que siga sirviendo para auditoria, pero que ademas deje preparado el terreno para una futura arquitectura de stacking por horizonte sin rehacer el trabajo historico.
