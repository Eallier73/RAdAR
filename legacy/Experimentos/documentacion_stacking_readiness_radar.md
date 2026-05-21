# Readiness para Stacking y Master Table Enriquecida

## Alcance de este documento

Este documento audita elegibilidad para stacking de runs base reutilizables. No fija por si solo el estado canónico completo de cada familia.

En particular:

- `E10_v1_clean` ya existe como corrida canonica de la familia `E10`, pero no aparece como elegible para stacking porque es un meta-selector final y sus predicciones no son mergeables como base simple de `E9`.
- `C1_v1_clean`, `C1_v2_clean` y `C1_v3_clean` si existen como corridas canonicas de clasificacion, pero quedan fuera de stacking por cambio de tarea (`task_type=clasificacion`).

## Que significa un run elegible para stacking en Radar

Un run se considera elegible para stacking solo si cumple simultaneamente estas reglas:

1. Tiene identidad canonica clara (`run_id`, directorio canonico y metadata recuperable).
2. No es un intento abortado, inconsistente o parcial.
3. Tiene predicciones fuera de muestra por horizonte en archivos reales `predicciones_h*.csv`.
4. Esas predicciones incluyen fecha, `y_true` y `y_pred`, sin duplicados de fecha y con merge estructuralmente valido.
5. Tiene metricas trazables por horizonte (`loss_h` y resto del bloque Radar).
6. Su configuracion puede reconstruirse con certeza suficiente desde artefactos reales (`completo` o `parcial`, nunca inventada).
7. No presenta una inconsistencia critica que invalide su reutilizacion.

La elegibilidad se distingue en dos niveles:

- Global: el run es elegible en `H1`, `H2`, `H3` y `H4`.
- Por horizonte: el run puede ser elegible solo en algunos horizontes.

## Campos nuevos incorporados a la tabla maestra

Se amplian cuatro capas:

- Identidad y linaje: `script_nombre`, `script_ruta`, `timestamp_run`, `version_canonica`, `status_canonico`, `motivo_exclusion_si_aplica`.
- Configuracion y reconstruccion: `validation_scheme`, `tuning_metric`, `hyperparams_json`, `hyperparams_hash`, `hyperparams_firma`, `hyperparams_resumen`, `reconstruccion_hiperparams_status`.
- Features y datos: `feature_count_h1..h4`, `features_artifact_available`, `source_dataset_period`, `exogenas_o_no`, `usa_target_delta`, `usa_target_nivel`.
- Stacking y explicabilidad: `mergeable_h1..h4`, `stacking_eligible_h1..h4`, `stacking_eligible_global`, `motivo_no_elegibilidad`, `tiene_coeficientes`, `tiene_importancias`, `tiene_shap_o_equivalente`.

## Como se reconstruyo retrospectivamente

Fuentes utilizadas:

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `predicciones_h1..h4.csv`
- `features_seleccionadas_h1..h4.csv`
- workbook maestro actual
- nombres de script y directorios

Supuestos permitidos:

- Se normalizan hiperparametros a partir de los parametros realmente guardados por cada familia.
- Cuando un run historico no trae exactamente la misma estructura que los recientes, se marca como reconstruccion `parcial`, no se rellena de manera ficticia.

Supuestos no permitidos:

- No se inventan hiperparametros ausentes.
- No se marcan runs elegibles solo por score.
- No se tratan directorios abortados como canonicos.

## Estado de reconstruccion retrospectiva

- Hiperparametros completos: 42
- Hiperparametros parciales: 5
- Hiperparametros no recuperables: 0
- Runs elegibles globalmente para stacking: 38
- Elegibles por horizonte: {"H1": 38, "H2": 38, "H3": 38, "H4": 38}

## Bases stacking por horizonte

```
horizonte                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            run_ids_incluidos  n_runs_incluidos                                                                                       run_ids_excluidos                                                                                                                                                                                                                                                                                                                                                                     exclusiones_detalle  filas_base  filas_completas_todos_modelos  filas_incompletas  cobertura_promedio_modelos_fila
       H1 E11_v1_clean,E11_v2_clean,E11_v3_clean,E12_v1_clean,E12_v2_clean,E12_v3_clean,E1_1_v1_bayesian_base,E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E1_v5_operativo_rebuild_v2,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean,E8_v1_clean,E8_v2_clean,E8_v3_clean,E9_v1_clean,E9_v2_clean,E9_v2_operativo_rebuild                38 C1_v1_clean,C1_v2_clean,C1_v3_clean,C2_v1_clean,C2_v2_clean,C2_v3_clean,E10_v1_clean,E1_v1,E9_smoke_tmp                             C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | C2_v1_clean:task_type=clasificacion | C2_v2_clean:task_type=clasificacion | C2_v3_clean:task_type=clasificacion | E10_v1_clean:columnas_minimas_invalidas;predicciones_no_mergeables | E1_v1:sin_loss_h | E9_smoke_tmp:status_run=parcial          28                             14                 14                         0.870301
       H2 E11_v1_clean,E11_v2_clean,E11_v3_clean,E12_v1_clean,E12_v2_clean,E12_v3_clean,E1_1_v1_bayesian_base,E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E1_v5_operativo_rebuild_v2,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean,E8_v1_clean,E8_v2_clean,E8_v3_clean,E9_v1_clean,E9_v2_clean,E9_v2_operativo_rebuild                38 C1_v1_clean,C1_v2_clean,C1_v3_clean,C2_v1_clean,C2_v2_clean,C2_v3_clean,E10_v1_clean,E1_v1,E9_smoke_tmp C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | C2_v1_clean:task_type=clasificacion | C2_v2_clean:task_type=clasificacion | C2_v3_clean:task_type=clasificacion | E10_v1_clean:columnas_minimas_invalidas;predicciones_no_mergeables | E1_v1:sin_loss_h | E9_smoke_tmp:status_run=parcial;sin_loss_h;sin_predicciones          27                             13                 14                         0.865497
       H3 E11_v1_clean,E11_v2_clean,E11_v3_clean,E12_v1_clean,E12_v2_clean,E12_v3_clean,E1_1_v1_bayesian_base,E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E1_v5_operativo_rebuild_v2,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean,E8_v1_clean,E8_v2_clean,E8_v3_clean,E9_v1_clean,E9_v2_clean,E9_v2_operativo_rebuild                38 C1_v1_clean,C1_v2_clean,C1_v3_clean,C2_v1_clean,C2_v2_clean,C2_v3_clean,E10_v1_clean,E1_v1,E9_smoke_tmp C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | C2_v1_clean:task_type=clasificacion | C2_v2_clean:task_type=clasificacion | C2_v3_clean:task_type=clasificacion | E10_v1_clean:columnas_minimas_invalidas;predicciones_no_mergeables | E1_v1:sin_loss_h | E9_smoke_tmp:status_run=parcial;sin_loss_h;sin_predicciones          26                             12                 14                         0.860324
       H4 E11_v1_clean,E11_v2_clean,E11_v3_clean,E12_v1_clean,E12_v2_clean,E12_v3_clean,E1_1_v1_bayesian_base,E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E1_v5_operativo_rebuild_v2,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean,E8_v1_clean,E8_v2_clean,E8_v3_clean,E9_v1_clean,E9_v2_clean,E9_v2_operativo_rebuild                38 C1_v1_clean,C1_v2_clean,C1_v3_clean,C2_v1_clean,C2_v2_clean,C2_v3_clean,E10_v1_clean,E1_v1,E9_smoke_tmp C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | C2_v1_clean:task_type=clasificacion | C2_v2_clean:task_type=clasificacion | C2_v3_clean:task_type=clasificacion | E10_v1_clean:columnas_minimas_invalidas;predicciones_no_mergeables | E1_v1:sin_loss_h | E9_smoke_tmp:status_run=parcial;sin_loss_h;sin_predicciones          25                             11                 14                         0.854737
```

## Limitaciones vigentes

- La explicabilidad transversal entre familias sigue sin estar homogenea.
- Algunos runs historicos mantienen estructura antigua y su reconstruccion es solo parcial.
- La elegibilidad global y la elegibilidad por horizonte no coinciden siempre.
- Las bases stacking siguen siendo preparatorias: no contienen todavia meta-features ni entrenamiento del meta-modelo.
- La no elegibilidad de `E10_v1_clean` en este documento no equivale a que `E10` siga en premodelado; solo significa que `E10` no es un modelo base reutilizable dentro de stacking clasico.

## Uso hacia adelante

La automatizacion hacia adelante no requiere infraestructura paralela:

- `experiment_logger.py` ya refresca la auditoria maestra al cerrar runs completos.
- `backfill_runs.py` ya rehidrata el workbook y dispara el refresh unico al final.
- Esta ampliacion hace que cada corrida nueva quede retroproyectada automaticamente al catalogo enriquecido y a las bases stacking por horizonte.
