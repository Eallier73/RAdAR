# Resumen Auditoria Experimentos Radar

## Hallazgos principales

- Runs maestros consolidados: 15
- Runs en catalogo integral: 15
- Directorios auditados en inventario: 17
- Directorios con artefactos parciales o inconsistentes: 2
- Familias con runs maestros: {"lineal_regularizado": 6, "arboles_boosting": 6, "robusto": 3}

## Mejor desempeño encontrado

- Mejor global por `L_total_Radar`: `E1_v5_clean` con `0.243442`
- Mejor `H1`: `E1_v4_clean` con `loss_h=0.064009`
- Mejor `H2`: `E2_v3_clean` con `loss_h=0.069277`
- Mejor `H3`: `E1_v2_clean` con `loss_h=0.064304`
- Mejor `H4`: `E2_v3_clean` con `loss_h=0.036988`
- Mejor `direction_accuracy` promedio: `E1_v1` con `0.745044`
- Mejor `deteccion_caidas` promedio: `E1_v5_clean` con `0.782323`

## Fortalezas operativas por horizonte

- Mejor `direction_accuracy` en `H1`: `E1_v4_clean` con `0.857143`
- Mejor `direction_accuracy` en `H2`: `E1_v5_clean` con `0.680000`
- Mejor `direction_accuracy` en `H3`: `E1_v1` con `0.846154`
- Mejor `direction_accuracy` en `H4`: `E2_v3_clean` con `0.760000`
- Mejor `deteccion_caidas` en `H1`: `E1_v4_clean` con `0.846154`
- Mejor `deteccion_caidas` en `H2`: `E2_v3_clean` con `0.750000`
- Mejor `deteccion_caidas` en `H3`: `E1_v1` con `0.833333`
- Mejor `deteccion_caidas` en `H4`: `E2_v3_clean` con `0.900000`

## Ganadores por metrica y horizonte

### H1
- mejor en mae: `E1_v5_clean` con `0.100599`
- mejor en rmse: `E3_v2_clean` con `0.128575`
- mejor en direction_accuracy: `E1_v4_clean` con `0.857143`
- mejor en deteccion_caidas: `E1_v4_clean` con `0.846154` | empate exacto con `E2_v3_clean`
- mejor en loss_h: `E1_v4_clean` con `0.064009`
- dominio_multiple: `E1_v4_clean` gana 3 de 5 metricas en H1.
### H2
- mejor en mae: `E1_v4_clean` con `0.100670`
- mejor en rmse: `E1_v2_clean` con `0.129020`
- mejor en direction_accuracy: `E1_v5_clean` con `0.680000`
- mejor en deteccion_caidas: `E2_v3_clean` con `0.750000`
- mejor en loss_h: `E2_v3_clean` con `0.069277`
- dominio_multiple: `E2_v3_clean` gana 2 de 5 metricas en H2.
### H3
- mejor en mae: `E1_v2_clean` con `0.100720`
- mejor en rmse: `E1_v2_clean` con `0.130351`
- mejor en direction_accuracy: `E1_v1` con `0.846154` | empate exacto con `E1_v2`
- mejor en deteccion_caidas: `E1_v4_clean` con `0.833333` | empate exacto con `E1_v1`
- mejor en loss_h: `E1_v2_clean` con `0.064304`
- dominio_multiple: `E1_v2_clean` gana 3 de 5 metricas en H3.
### H4
- mejor en mae: `E3_v2_clean` con `0.100297`
- mejor en rmse: `E1_v2_clean` con `0.135512`
- mejor en direction_accuracy: `E2_v3_clean` con `0.760000`
- mejor en deteccion_caidas: `E2_v3_clean` con `0.900000`
- mejor en loss_h: `E2_v3_clean` con `0.036988`
- dominio_multiple: `E2_v3_clean` gana 3 de 5 metricas en H4.

## Inventario real por familia

- `E1`: 6 runs maestros
- `E2`: 3 runs maestros
- `E3`: 3 runs maestros
- `E4`: 3 runs maestros

## Runs parciales / inconsistentes

- `E2_v1_clean` | `parcial` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E2_v1_clean_20260323_045221_aborted` | duplicado_detectado=3; intento_descartado_por_menor_completitud; directorio_abortado; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E2_v1_clean` | `inconsistente` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E2_v1_clean_20260323_045930_aborted` | duplicado_detectado=3; intento_descartado_por_menor_completitud; directorio_abortado; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas

## Runs planeados detectados sin artefactos consolidados

E1_v10, E1_v3, E1_v4, E1_v5, E1_v6, E1_v6_clean, E1_v7, E1_v8, E1_v9, E2_v2, E2_v3, E2_v4_clean, E3_v2, E3_v4, E4_v4_clean

Nota: esta lista sale de menciones en prompts/documentos `.md`; no distingue automaticamente entre runs cancelados, diferidos o nunca ejecutados.

## Inconsistencias detectadas

- `E2_v1_clean` tiene tres directorios: dos intentos abortados y un directorio canónico completo. Se consolidó el directorio `E2_v1_clean_20260323_050029`.
- Los runs históricos `E1_v1` y `E1_v2` usan una estructura de artefactos más antigua, pero contienen métricas y predicciones suficientes para tratarlos como completos.
- No se encontraron artefactos experimentales fuera de `Experimentos/runs/` para `metadata_run.json`, `parametros_run.json`, `metricas_horizonte.json` o `resumen_modeling_horizontes.json`.

## Artefactos útiles para explicación por horizonte

- Directorios con `features_seleccionadas_h*.csv`: 9
- Directorios con `resumen_modeling_horizontes.json`: 15
- No se encontraron artefactos homogéneos y reutilizables de importancias de variables o coeficientes comparables entre familias. Esa capa explicativa sigue pendiente.

## Readiness para stacking / hipermodelo

- Runs compatibles para stacking 1..4: 15
- Runs con utilidad parcial para merge por horizonte: 0
- Cobertura mergeable por horizonte: {"H1": 15, "H2": 15, "H3": 15, "H4": 15}

### Bases parciales reconstruidas

- `stacking_base_h1`: filas=28, modelos_integrados=15
- `stacking_base_h2`: filas=27, modelos_integrados=15
- `stacking_base_h3`: filas=26, modelos_integrados=15
- `stacking_base_h4`: filas=25, modelos_integrados=15

### Lectura retrospectiva

- Se pudo reconstruir retrospectivamente catalogo, metricas por horizonte, cobertura de predicciones y compatibilidad estructural para stacking a partir de artefactos reales en disco.
- Se pudieron construir hojas `stacking_base_h1` a `stacking_base_h4` con los runs que tienen predicciones mergeables por horizonte.
- Lo que todavia no se pudo homogeneizar retrospectivamente es la capa explicativa transversal entre familias: coeficientes, importancias e interpretabilidad comparable.

## Lectura preliminar

- La evidencia sí sugiere especialización por horizonte: `E1_v4_clean` domina `H1`, `E2_v3_clean` domina `H2`, `E1_v2_clean` domina `H3` y `E2_v3_clean` domina `H4`.
- También hay especialización operativa: dirección y detección de caídas no siempre coinciden con el mejor `loss_h`.
- En `E3`, la señal más útil quedó en `E3_v2_clean`; `E3_v3_clean` no mejora esa línea y `E4` no desplazó a bagging.
- Ya existe base suficiente para pensar en un ensamblado por horizonte como hipótesis metodológica futura, con cobertura real de `E1-E4` y auditoría explícita de compatibilidad de predicciones.
- Conviene automatizar a partir de ahora la reconstrucción de esta tabla maestra en cada corrida nueva para evitar que el análisis dependa del workbook manual.
