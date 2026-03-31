# Resumen Auditoria Experimentos Radar

## Hallazgos principales

- Runs maestros consolidados: 28
- Runs en catalogo integral: 28
- Directorios auditados en inventario: 32
- Directorios con artefactos parciales o inconsistentes: 4
- Familias con runs maestros: {"arboles_boosting": 11, "lineal_regularizado": 6, "series_tiempo_exogenas": 5, "robusto": 3}

## Mejor desempeño encontrado

- Mejor global por `L_total_Radar`: `E1_v5_clean` con `0.243442`
- Mejor `H1`: `E5_v3_clean` con `loss_h=0.060367`
- Mejor `H2`: `E7_v3_clean` con `loss_h=0.068430`
- Mejor `H3`: `E1_v2_clean` con `loss_h=0.064304`
- Mejor `H4`: `E5_v4_clean` con `loss_h=0.035979`
- Mejor `direction_accuracy` promedio: `E1_v1` con `0.745044`
- Mejor `deteccion_caidas` promedio: `E1_v5_clean` con `0.782323`

## Fortalezas operativas por horizonte

- Mejor `direction_accuracy` en `H1`: `E1_v4_clean` con `0.857143`
- Mejor `direction_accuracy` en `H2`: `E1_v5_clean` con `0.680000`
- Mejor `direction_accuracy` en `H3`: `E1_v1` con `0.846154`
- Mejor `direction_accuracy` en `H4`: `E2_v3_clean` con `0.760000`
- Mejor `deteccion_caidas` en `H1`: `E1_v4_clean` con `0.846154`
- Mejor `deteccion_caidas` en `H2`: `E6_v1_clean` con `0.900000`
- Mejor `deteccion_caidas` en `H3`: `E7_v1_clean` con `0.909091`
- Mejor `deteccion_caidas` en `H4`: `E2_v3_clean` con `0.900000`

## Ganadores por metrica y horizonte

### H1
- mejor en mae: `E5_v4_clean` con `0.095556`
- mejor en rmse: `E5_v4_clean` con `0.125179`
- mejor en direction_accuracy: `E1_v4_clean` con `0.857143`
- mejor en deteccion_caidas: `E1_v4_clean` con `0.846154` | empate exacto con `E2_v3_clean`
- mejor en loss_h: `E5_v3_clean` con `0.060367`
- dominio_multiple: `E5_v4_clean` gana 2 de 5 metricas en H1.
### H2
- mejor en mae: `E1_v4_clean` con `0.100670`
- mejor en rmse: `E1_v2_clean` con `0.129020`
- mejor en direction_accuracy: `E1_v5_clean` con `0.680000`
- mejor en deteccion_caidas: `E6_v1_clean` con `0.900000`
- mejor en loss_h: `E7_v3_clean` con `0.068430`
- lectura: no hay un dominador unico en H2; el horizonte reparte ventajas.
### H3
- mejor en mae: `E1_v2_clean` con `0.100720`
- mejor en rmse: `E1_v2_clean` con `0.130351`
- mejor en direction_accuracy: `E1_v1` con `0.846154` | empate exacto con `E1_v2`
- mejor en deteccion_caidas: `E7_v3_clean` con `0.909091` | empate exacto con `E7_v1_clean`
- mejor en loss_h: `E1_v2_clean` con `0.064304`
- dominio_multiple: `E1_v2_clean` gana 3 de 5 metricas en H3.
### H4
- mejor en mae: `E3_v2_clean` con `0.100297`
- mejor en rmse: `E1_v2_clean` con `0.135512`
- mejor en direction_accuracy: `E2_v3_clean` con `0.760000`
- mejor en deteccion_caidas: `E2_v3_clean` con `0.900000`
- mejor en loss_h: `E5_v4_clean` con `0.035979`
- dominio_multiple: `E2_v3_clean` gana 2 de 5 metricas en H4.

## Inventario real por familia

- `E1`: 6 runs maestros
- `E2`: 3 runs maestros
- `E3`: 3 runs maestros
- `E4`: 3 runs maestros

## Runs parciales / inconsistentes

- `E2_v1_clean` | `parcial` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E2_v1_clean_20260323_045221_aborted` | duplicado_detectado=3; intento_descartado_por_menor_completitud; directorio_abortado; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E2_v1_clean` | `inconsistente` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E2_v1_clean_20260323_045930_aborted` | duplicado_detectado=3; intento_descartado_por_menor_completitud; directorio_abortado; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E5_v4_clean` | `inconsistente` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E5_v4_clean_20260330_091517` | duplicado_detectado=2; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E6_v1_clean` | `parcial` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E6_v1_clean_20260330_095252` | duplicado_detectado=2; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas

## Runs planeados detectados sin artefactos consolidados

C1_v1, C1_v2, C1_v3, C2_v1_clean, C2_v2_clean, C2_v3_clean, C3_v1_clean, C3_v2_clean, C3_v3_clean, C4_v1_clean, C4_v2_clean, C4_v3_clean, E1_v10, E1_v3, E1_v4, E1_v5, E1_v6, E1_v6_clean, E1_v7, E1_v8, E1_v9, E2_v2, E2_v3, E2_v4_clean, E3_v2, E3_v4, E4_v4_clean

Nota: esta lista sale de menciones en prompts/documentos `.md`; no distingue automaticamente entre runs cancelados, diferidos o nunca ejecutados.

## Inconsistencias detectadas

- `E2_v1_clean` tiene tres directorios: dos intentos abortados y un directorio canónico completo. Se consolidó el directorio `E2_v1_clean_20260323_050029`.
- Los runs históricos `E1_v1` y `E1_v2` usan una estructura de artefactos más antigua, pero contienen métricas y predicciones suficientes para tratarlos como completos.
- No se encontraron artefactos experimentales fuera de `Experimentos/runs/` para `metadata_run.json`, `parametros_run.json`, `metricas_horizonte.json` o `resumen_modeling_horizontes.json`.

## Artefactos útiles para explicación por horizonte

- Directorios con `features_seleccionadas_h*.csv`: 14
- Directorios con `resumen_modeling_horizontes.json`: 29
- No se encontraron artefactos homogéneos y reutilizables de importancias de variables o coeficientes comparables entre familias. Esa capa explicativa sigue pendiente.

## Readiness para stacking / hipermodelo

- Runs compatibles para stacking 1..4: 24
- Runs con utilidad parcial para merge por horizonte: 0
- Reconstrucciones completas de hiperparametros: 28
- Reconstrucciones parciales de hiperparametros: 0
- Runs con hiperparametros no recuperables: 0
- Cobertura mergeable por horizonte: {"H1": 28, "H2": 28, "H3": 28, "H4": 28}
- Elegibilidad real para stacking por horizonte: {"H1": 24, "H2": 24, "H3": 24, "H4": 24}

### Bases parciales reconstruidas

- `stacking_base_h1`: filas=28, modelos_integrados=24
- `stacking_base_h2`: filas=27, modelos_integrados=24
- `stacking_base_h3`: filas=26, modelos_integrados=24
- `stacking_base_h4`: filas=25, modelos_integrados=24

### Resumen de bases stacking por horizonte

```
horizonte                                                                                                                                                                                                                                                                         run_ids_incluidos  n_runs_incluidos                         run_ids_excluidos                                                                                                                exclusiones_detalle  filas_base  filas_completas_todos_modelos  filas_incompletas  cobertura_promedio_modelos_fila
       H1 E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean                24 C1_v1_clean,C1_v2_clean,C1_v3_clean,E1_v1 C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | E1_v1:sin_loss_h          28                             26                  2                         0.943452
       H2 E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean                24 C1_v1_clean,C1_v2_clean,C1_v3_clean,E1_v1 C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | E1_v1:sin_loss_h          27                             25                  2                         0.941358
       H3 E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean                24 C1_v1_clean,C1_v2_clean,C1_v3_clean,E1_v1 C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | E1_v1:sin_loss_h          26                             24                  2                         0.939103
       H4 E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean                24 C1_v1_clean,C1_v2_clean,C1_v3_clean,E1_v1 C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | E1_v1:sin_loss_h          25                             23                  2                         0.936667
```

### Lectura retrospectiva

- Se pudo reconstruir retrospectivamente catalogo, metricas por horizonte, cobertura de predicciones y compatibilidad estructural para stacking a partir de artefactos reales en disco.
- Se pudo normalizar retrospectivamente la configuracion e hiperparametros de las familias existentes sin inventar campos ausentes.
- Se pudieron construir hojas `stacking_base_h1` a `stacking_base_h4` con los runs que tienen predicciones mergeables por horizonte.
- Lo que todavia no se pudo homogeneizar retrospectivamente es la capa explicativa transversal entre familias: coeficientes, importancias e interpretabilidad comparable.

### Incompatibilidades tipicas detectadas

- `C1_v1_clean` H1: task_type=clasificacion
- `C1_v2_clean` H1: task_type=clasificacion
- `C1_v3_clean` H1: task_type=clasificacion
- `E1_v1` H1: sin_loss_h
- `C1_v1_clean` H2: task_type=clasificacion
- `C1_v2_clean` H2: task_type=clasificacion
- `C1_v3_clean` H2: task_type=clasificacion
- `E1_v1` H2: sin_loss_h
- `C1_v1_clean` H3: task_type=clasificacion
- `C1_v2_clean` H3: task_type=clasificacion

## Lectura preliminar

- La evidencia sí sugiere especialización por horizonte: `E5_v3_clean` domina `H1`, `E7_v3_clean` domina `H2`, `E1_v2_clean` domina `H3` y `E5_v4_clean` domina `H4`.
- También hay especialización operativa: dirección y detección de caídas no siempre coinciden con el mejor `loss_h`.
- En `E3`, la señal más útil quedó en `E3_v2_clean`; `E3_v3_clean` no mejora esa línea y `E4` no desplazó a bagging.
- Ya existe base suficiente para pensar en un ensamblado por horizonte como hipótesis metodológica futura, con cobertura real de `E1-E4` y auditoría explícita de compatibilidad de predicciones.
- Conviene automatizar a partir de ahora la reconstrucción de esta tabla maestra en cada corrida nueva para evitar que el análisis dependa del workbook manual.
