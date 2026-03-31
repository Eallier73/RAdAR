# Readiness para Stacking y Master Table Enriquecida

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

- Hiperparametros completos: 28
- Hiperparametros parciales: 0
- Hiperparametros no recuperables: 0
- Runs elegibles globalmente para stacking: 24
- Elegibles por horizonte: {"H1": 24, "H2": 24, "H3": 24, "H4": 24}

## Bases stacking por horizonte

```
horizonte                                                                                                                                                                                                                                                                         run_ids_incluidos  n_runs_incluidos                         run_ids_excluidos                                                                                                                exclusiones_detalle  filas_base  filas_completas_todos_modelos  filas_incompletas  cobertura_promedio_modelos_fila
       H1 E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean                24 C1_v1_clean,C1_v2_clean,C1_v3_clean,E1_v1 C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | E1_v1:sin_loss_h          28                             26                  2                         0.943452
       H2 E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean                24 C1_v1_clean,C1_v2_clean,C1_v3_clean,E1_v1 C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | E1_v1:sin_loss_h          27                             25                  2                         0.941358
       H3 E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean                24 C1_v1_clean,C1_v2_clean,C1_v3_clean,E1_v1 C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | E1_v1:sin_loss_h          26                             24                  2                         0.939103
       H4 E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean                24 C1_v1_clean,C1_v2_clean,C1_v3_clean,E1_v1 C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | E1_v1:sin_loss_h          25                             23                  2                         0.936667
```

## Limitaciones vigentes

- La explicabilidad transversal entre familias sigue sin estar homogenea.
- Algunos runs historicos mantienen estructura antigua y su reconstruccion es solo parcial.
- La elegibilidad global y la elegibilidad por horizonte no coinciden siempre.
- Las bases stacking siguen siendo preparatorias: no contienen todavia meta-features ni entrenamiento del meta-modelo.

## Uso hacia adelante

La automatizacion hacia adelante no requiere infraestructura paralela:

- `experiment_logger.py` ya refresca la auditoria maestra al cerrar runs completos.
- `backfill_runs.py` ya rehidrata el workbook y dispara el refresh unico al final.
- Esta ampliacion hace que cada corrida nueva quede retroproyectada automaticamente al catalogo enriquecido y a las bases stacking por horizonte.
