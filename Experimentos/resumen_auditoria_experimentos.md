# Resumen Auditoria Experimentos Radar

## Hallazgos principales

- Runs maestros consolidados: 47
- Runs en catalogo integral: 47
- Directorios auditados en inventario: 64
- Directorios con artefactos parciales o inconsistentes: 15
- Familias con runs maestros de regresion: {"arboles_boosting": 11, "lineal_regularizado": 8, "series_tiempo_exogenas": 5, "arquitectura_dual_controlada": 3, "representacion_enriquecida": 3, "robusto": 3, "hibrido_residual": 3, "stacking_controlado": 3, "gating_contextual": 1}
- Corridas canonicas de clasificacion detectadas: `C1=3, C2=3, C3=0, C4=0`

## Mejor desempeño encontrado

- Mejor global crudo por `L_total_Radar`: `E9_v2_clean` con `0.227510`
- Mejor `H1`: `E9_v2_clean` con `loss_h=0.051557`
- Mejor `H2`: `E12_v3_clean` con `loss_h=0.059278`
- Mejor `H3`: `E9_v1_clean` con `loss_h=0.054110`
- Mejor `H4`: `E5_v4_clean` con `loss_h=0.035979`
- Mejor `direction_accuracy` promedio: `E12_v1_clean` con `0.756161`
- Mejor `deteccion_caidas` promedio: `E9_v2_clean` con `0.916667`

## Nota metodologica vigente

- El ranking crudo por `L_total_Radar` no agota la adjudicacion metodologica del proyecto.
- `E1_v5_clean` sigue siendo el referente numerico puro principal del Radar.
- `E9_v2_clean` queda como el mejor referente actual orientado a riesgo, direccion y deteccion de caidas.
- Esa diferencia no se interpreta como contradiccion, sino como dualidad funcional entre pronostico numerico del porcentaje y utilidad operativa del movimiento.
- En consecuencia, `E9` queda util pero pausada, `E10` ya fue probado formalmente con `E10_v1_clean` y queda cerrada para promocion bajo su formulacion actual, y `E11` ya fue abierta con tres variantes controladas y queda evaluada sin promocion tras su primera apertura dual.

## Fortalezas operativas por horizonte

- Mejor `direction_accuracy` en `H1`: `E1_v4_clean` con `0.857143`
- Mejor `direction_accuracy` en `H2`: `E12_v1_clean` con `0.769231`
- Mejor `direction_accuracy` en `H3`: `E1_1_v1_bayesian_base` con `0.875000`
- Mejor `direction_accuracy` en `H4`: `E10_v1_clean` con `0.769231`
- Mejor `deteccion_caidas` en `H1`: `E9_v2_clean` con `1.000000`
- Mejor `deteccion_caidas` en `H2`: `E6_v1_clean` con `0.900000`
- Mejor `deteccion_caidas` en `H3`: `E10_v1_clean` con `1.000000`
- Mejor `deteccion_caidas` en `H4`: `E2_v3_clean` con `0.900000`

## Ganadores por metrica y horizonte

### H1
- mejor en mae: `E5_v4_clean` con `0.095556`
- mejor en rmse: `E5_v4_clean` con `0.125179`
- mejor en direction_accuracy: `E9_v2_clean` con `0.857143` | empate exacto con `E9_v2_operativo_rebuild`
- mejor en deteccion_caidas: `E9_v2_clean` con `1.000000` | empate exacto con `E9_v2_operativo_rebuild`
- mejor en loss_h: `E9_v2_clean` con `0.051557` | empate exacto con `E9_v2_operativo_rebuild`
- dominio_multiple: `E9_v2_clean` gana 3 de 5 metricas en H1.
### H2
- mejor en mae: `E1_v4_clean` con `0.100670`
- mejor en rmse: `E1_v2_clean` con `0.129020`
- mejor en direction_accuracy: `E12_v3_clean` con `0.769231` | empate exacto con `E12_v2_clean`
- mejor en deteccion_caidas: `E6_v1_clean` con `0.900000`
- mejor en loss_h: `E12_v3_clean` con `0.059278`
- dominio_multiple: `E12_v3_clean` gana 2 de 5 metricas en H2.
### H3
- mejor en mae: `E1_v2_clean` con `0.100720`
- mejor en rmse: `E1_v2_clean` con `0.130351`
- mejor en direction_accuracy: `E1_1_v1_bayesian_base` con `0.875000`
- mejor en deteccion_caidas: `E9_v2_clean` con `1.000000` | empate exacto con `E9_v2_operativo_rebuild`
- mejor en loss_h: `E9_v1_clean` con `0.054110`
- dominio_multiple: `E1_v2_clean` gana 2 de 5 metricas en H3.
### H4
- mejor en mae: `E3_v2_clean` con `0.100297`
- mejor en rmse: `E1_v2_clean` con `0.135512`
- mejor en direction_accuracy: `E10_v1_clean` con `0.769231`
- mejor en deteccion_caidas: `E2_v3_clean` con `0.900000`
- mejor en loss_h: `E5_v4_clean` con `0.035979`
- lectura: no hay un dominador unico en H4; el horizonte reparte ventajas.

## Inventario real por familia

- `E1`: 8 runs maestros
- `E2`: 3 runs maestros
- `E3`: 3 runs maestros
- `E4`: 3 runs maestros

## Estado vigente de familias

```
family                   estado_vigente    mejor_run                                    rol_funcional                                                                                                                                                                                                                                                                                                                                                               decision_metodologica                                                               siguiente_movimiento
    E1                          cerrada  E1_v5_clean                          referente numerico puro                                                                                                                                                                                                                                                                                        Mejor baseline lineal y mejor referente actual para pronostico numerico puro del porcentaje.                                                             sin expansion prevista
    E2                          cerrada  E2_v3_clean                               referencia robusta                                                                                                                                                                                                                                                                                              Familia robusta util como contraste historico, pero sin competitividad frente a Ridge.                                                             sin expansion prevista
    E3             cerrada en rama base  E3_v2_clean                        referencia no lineal base                                                                                                                                                                                                                                                                                                           Sigue siendo la referencia bagging util, pero ya desplazada por CatBoost.                                              mantener como candidato de diversidad
    E4                          cerrada  E4_v1_clean                               boosting historico                                                                                                                                                                                                                                                                                                                      No desplazo a E3 ni a Ridge; queda como referencia secundaria.                                                             sin expansion prevista
    E5                   abierta madura  E5_v4_clean                          mejor no lineal tabular                                                                                                                                                                                                                                                                                                     Campeon no lineal tabular vigente; sigue siendo referencia competitiva central.                       mantener como candidato fuerte para arquitecturas compuestas
    E6                       debilitada  E6_v1_clean           referencia temporal estructurada debil                                                                                                                                                                                                                                                                                                                     ARIMAX no fue competitivo y no justifica continuidad inmediata.                                              solo reserva conceptual para hibridos
    E7                       intermedia  E7_v3_clean             referencia temporal con changepoints                                                                                                                                                                                                                                                                                                                 Prophet supero a E6 pero no entro al bloque contendiente principal.                                       mantener como referencia temporal secundaria
    E8                       intermedia  E8_v2_clean                       hibrido residual auditable                                                                                                                                                                                                                                                                                                     Mostro validez metodologica, pero no agrego mejora suficiente frente a su base.             sin expansion amplia; solo hipotesis residual muy acotada si reaparece
    E9                     pausada util  E9_v2_clean                referente riesgo-direccion-caidas                                                                                                                                                                                                                                                       No reemplaza a E1_v5_clean; aporta valor operativo en riesgo, direccion y deteccion de caidas. Queda util pero no definitiva.                                    pausa metodologica; posible reactivacion futura
   E10           cerrada para promocion E10_v1_clean antecedente metodologico de seleccion contextual                                                                                                              E10 ya fue probado con E10_v1_clean. La corrida fue metodologicamente limpia y trazable, pero no supero al selector fijo, a E1_v5_clean ni a E9_v2_clean; la hipotesis de promocion no quedo confirmada y la rama se cierra para promocion bajo su formulacion actual.                    conservar como antecedente; no reabrir sin reformulacion fuerte
   E11           evaluada sin promocion E11_v2_clean              apertura dual numerica + categorica E11 ya fue abierta con tres variantes controladas. E11_v1_clean y E11_v2_clean preservan exactamente el bloque numerico de E1_v5_clean; E11_v2_clean agrega una capa binaria de caidas con senal moderada; E11_v3_clean no mejora el global. Ninguna variante desplaza a E1_v5_clean ni a E9_v2_clean y la familia queda abierta solo como evidencia dual no promocionable todavia. sin promocion; congelar apertura y solo reabrir con hipotesis dual realmente nueva
   E12           evaluada sin promocion E12_v3_clean         representacion enriquecida por horizonte E12 abrio la pregunta de si parte de la ventaja operativa de E9 podia absorberse mediante representacion enriquecida dentro de un Ridge simple y trazable. Ninguna de sus tres variantes mejora de forma defendible a E1_v5_clean ni a E9_v2_clean; la mejor lectura es un hallazgo parcial de que el bloque de desacuerdo aporta mas que el bloque de regimen, pero sin promocion. sin expansion inmediata; reabrir solo con hipotesis de H1 mas precisa y defendible
    C1 evaluada y pausada tempranamente                                    clasificacion bagging base                                                                                                                                                                                C1 si se ejecuto con tres corridas canonicas, pero las tres colapsaron a clase unica y no dejaron senal discriminativa util. La rama queda abierta solo como antecedente, no como linea prioritaria.           sin expansion inmediata; revisar target clasificacion antes de reactivar
    C2 evaluada y pausada tempranamente  C2_v1_clean                           clasificacion boosting                                                                                                                                                                                                        C2 si se ejecuto con tres corridas canonicas de XGBoost, pero las tres reprodujeron el mismo colapso a clase unica observado en C1 y no agregaron senal discriminativa util.           sin expansion inmediata; revisar target clasificacion antes de reactivar
    C3        infraestructura preparada                                        clasificacion boosting                                                                                                                                                                                                                                                                                                    La familia tiene runner y prompt canonicos, pero no corridas ejecutadas todavia.            no prioritaria; ejecutar solo si se redefine la agenda de clasificacion
    C4        infraestructura preparada                                        clasificacion boosting                                                                                                                                                                                                                                                                                                    La familia tiene runner y prompt canonicos, pero no corridas ejecutadas todavia.            no prioritaria; ejecutar solo si se redefine la agenda de clasificacion
```

## Constructos canonicos

```
family                             constructo_familia    mejor_run                   estado_vigente
    E1             baseline lineal numerico principal  E1_v5_clean                          cerrada
    E2         familia robusta de contraste historico  E2_v3_clean                          cerrada
    E3               referencia bagging de diversidad  E3_v2_clean             cerrada en rama base
    E4                     boosting historico cerrado  E4_v1_clean                          cerrada
    E5              campeon no lineal tabular vigente  E5_v4_clean                   abierta madura
    E6                 referencia temporal debilitada  E6_v1_clean                       debilitada
    E7                 referencia temporal secundaria  E7_v3_clean                       intermedia
    E8                     hibrido residual auditable  E8_v2_clean                       intermedia
    E9      rama operativa de riesgo-direccion-caidas  E9_v2_clean                     pausada util
   E10     selector contextual probado y no promovido E10_v1_clean           cerrada para promocion
   E11      apertura dual controlada no promocionable E11_v2_clean           evaluada sin promocion
   E12 familia de representacion enriquecida evaluada E12_v3_clean           evaluada sin promocion
    C1                    clasificacion base evaluada              evaluada y pausada tempranamente
    C2                clasificacion boosting evaluada  C2_v1_clean evaluada y pausada tempranamente
    C3               clasificacion boosting preparada                     infraestructura preparada
    C4               clasificacion boosting preparada                     infraestructura preparada
```

Registro ampliado:

- El detalle completo de constructos por run se exporta en `registro_constructos_runs_radar.csv` y `diccionario_constructos_canonicos_radar.md`.

## Estado de la capa explicativa transversal

```
                              dimension                                                  valor                                                                                                                                                                                          justificacion
                clasificacion_principal                                  parcial intra-familia Existen artefactos parciales de seleccion de variables por horizonte en una fraccion de runs, pero no hay coeficientes, importancias o SHAP exportados de forma homogénea y comparable entre familias.
        runs_con_features_seleccionadas                                                     20                                   20 de 47 runs maestros tienen archivos `features_seleccionadas_h*.csv`; esto sirve para lectura intra-run o intra-familia, no para comparacion transversal canonica.
       runs_con_coeficientes_exportados                                                      0                                                                                                                          No se localizaron artefactos de coeficientes exportados de forma sistematica.
       runs_con_importancias_exportadas                                                      0                                                                                                                          No se localizaron artefactos de importancias exportadas de forma sistematica.
                runs_con_shap_exportado                                                      0                                                                                                                   No se localizaron artefactos SHAP o equivalentes reutilizables de forma sistematica.
          runs_marcados_como_homogeneos                                                      0                                                                                         Ningun run puede considerarse parte de una capa explicativa transversal canonica solo con la evidencia actual.
           lectura_metodologica_vigente performance_y_riesgo_siguen_siendo_la_base_de_decision      La eleccion de modelos sigue descansando principalmente en performance, direccion y deteccion de caidas; la interpretabilidad actual es fragmentaria y no resuelve comparabilidad inter-familias.
faltante_para_capa_transversal_canonica exportar_artefactos_homogeneos_por_familia_y_horizonte                       Haria falta exportar de forma sistematica, por horizonte y con taxonomia comun, coeficientes o importancias comparables entre lineales, arboles, boosting y familias temporales.
```

## Runs parciales / inconsistentes

- `C2_v1_clean` | `inconsistente` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/C2_v1_clean_20260403_040331` | duplicado_detectado=2; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E10_v1_clean` | `inconsistente` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E10_v1_clean_20260401_090258` | duplicado_detectado=3; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E10_v1_clean` | `parcial` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E10_v1_clean_20260401_090352` | duplicado_detectado=3; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas
- `E11_v1_clean` | `inconsistente` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v1_clean_20260403_051326` | duplicado_detectado=2; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E11_v2_clean` | `inconsistente` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v2_clean_20260403_051326` | duplicado_detectado=2; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E11_v3_clean` | `inconsistente` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v3_clean_20260403_051326` | duplicado_detectado=2; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E12_v1_clean` | `inconsistente` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v1_clean_20260403_075016` | duplicado_detectado=3; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E12_v1_clean` | `parcial` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v1_clean_20260403_075100` | duplicado_detectado=3; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E12_v2_clean` | `parcial` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v2_clean_20260403_075736` | duplicado_detectado=4; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E1_1_v1_bayesian_base` | `parcial` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E1_1_v1_bayesian_base_20260402_063647` | duplicado_detectado=2; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas
- `E2_v1_clean` | `parcial` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E2_v1_clean_20260323_045221_aborted` | duplicado_detectado=3; intento_descartado_por_menor_completitud; directorio_abortado; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E2_v1_clean` | `inconsistente` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E2_v1_clean_20260323_045930_aborted` | duplicado_detectado=3; intento_descartado_por_menor_completitud; directorio_abortado; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E5_v4_clean` | `inconsistente` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E5_v4_clean_20260330_091517` | duplicado_detectado=2; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas,faltante_resumen,predicciones_incompletas
- `E6_v1_clean` | `parcial` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E6_v1_clean_20260330_095252` | duplicado_detectado=2; intento_descartado_por_menor_completitud; faltante_metadata,faltante_metricas
- `E9_smoke_tmp` | `parcial` | `/home/emilio/Documentos/RAdAR/Experimentos/runs/E9_smoke_tmp_20260401_065645` | predicciones_incompletas

## Runs planeados detectados sin artefactos consolidados

C1_v1, C1_v2, C1_v3, C3_v1_clean, C3_v2_clean, C3_v3_clean, C4_v1_clean, C4_v2_clean, C4_v3_clean, E11_v1, E1_v10, E1_v3, E1_v4, E1_v5, E1_v6, E1_v6_clean, E1_v7, E1_v8, E1_v9, E2_v2, E2_v3, E2_v4_clean, E3_v2, E3_v4, E4_v4_clean

Nota: esta lista sale de menciones en prompts/documentos `.md`; no distingue automaticamente entre runs cancelados, diferidos o nunca ejecutados.

## Inconsistencias detectadas

- `E2_v1_clean` tiene tres directorios: dos intentos abortados y un directorio canónico completo. Se consolidó el directorio `E2_v1_clean_20260323_050029`.
- Los runs históricos `E1_v1` y `E1_v2` usan una estructura de artefactos más antigua, pero contienen métricas y predicciones suficientes para tratarlos como completos.
- No se encontraron artefactos experimentales fuera de `Experimentos/runs/` para `metadata_run.json`, `parametros_run.json`, `metricas_horizonte.json` o `resumen_modeling_horizontes.json`.

## Artefactos útiles para explicación por horizonte

- Directorios con `features_seleccionadas_h*.csv`: 28
- Directorios con `resumen_modeling_horizontes.json`: 53
- No se encontraron artefactos homogéneos y reutilizables de importancias de variables o coeficientes comparables entre familias. Esa capa explicativa sigue pendiente.
- La clasificacion principal de esa capa sigue siendo `parcial intra-familia`: hay seleccion de variables por horizonte en algunos runs, pero no una taxonomia homogenea y comparable entre familias.

## Readiness para stacking / hipermodelo

- Runs compatibles para stacking 1..4: 38
- Runs con utilidad parcial para merge por horizonte: 0
- Reconstrucciones completas de hiperparametros: 42
- Reconstrucciones parciales de hiperparametros: 5
- Runs con hiperparametros no recuperables: 0
- Cobertura mergeable por horizonte: {"H1": 46, "H2": 45, "H3": 45, "H4": 45}
- Elegibilidad real para stacking por horizonte: {"H1": 38, "H2": 38, "H3": 38, "H4": 38}

### Bases parciales reconstruidas

- `stacking_base_h1`: filas=28, modelos_integrados=38
- `stacking_base_h2`: filas=27, modelos_integrados=38
- `stacking_base_h3`: filas=26, modelos_integrados=38
- `stacking_base_h4`: filas=25, modelos_integrados=38

### Resumen de bases stacking por horizonte

```
horizonte                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            run_ids_incluidos  n_runs_incluidos                                                                                       run_ids_excluidos                                                                                                                                                                                                                                                                                                                                                                     exclusiones_detalle  filas_base  filas_completas_todos_modelos  filas_incompletas  cobertura_promedio_modelos_fila
       H1 E11_v1_clean,E11_v2_clean,E11_v3_clean,E12_v1_clean,E12_v2_clean,E12_v3_clean,E1_1_v1_bayesian_base,E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E1_v5_operativo_rebuild_v2,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean,E8_v1_clean,E8_v2_clean,E8_v3_clean,E9_v1_clean,E9_v2_clean,E9_v2_operativo_rebuild                38 C1_v1_clean,C1_v2_clean,C1_v3_clean,C2_v1_clean,C2_v2_clean,C2_v3_clean,E10_v1_clean,E1_v1,E9_smoke_tmp                             C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | C2_v1_clean:task_type=clasificacion | C2_v2_clean:task_type=clasificacion | C2_v3_clean:task_type=clasificacion | E10_v1_clean:columnas_minimas_invalidas;predicciones_no_mergeables | E1_v1:sin_loss_h | E9_smoke_tmp:status_run=parcial          28                             14                 14                         0.870301
       H2 E11_v1_clean,E11_v2_clean,E11_v3_clean,E12_v1_clean,E12_v2_clean,E12_v3_clean,E1_1_v1_bayesian_base,E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E1_v5_operativo_rebuild_v2,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean,E8_v1_clean,E8_v2_clean,E8_v3_clean,E9_v1_clean,E9_v2_clean,E9_v2_operativo_rebuild                38 C1_v1_clean,C1_v2_clean,C1_v3_clean,C2_v1_clean,C2_v2_clean,C2_v3_clean,E10_v1_clean,E1_v1,E9_smoke_tmp C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | C2_v1_clean:task_type=clasificacion | C2_v2_clean:task_type=clasificacion | C2_v3_clean:task_type=clasificacion | E10_v1_clean:columnas_minimas_invalidas;predicciones_no_mergeables | E1_v1:sin_loss_h | E9_smoke_tmp:status_run=parcial;sin_loss_h;sin_predicciones          27                             13                 14                         0.865497
       H3 E11_v1_clean,E11_v2_clean,E11_v3_clean,E12_v1_clean,E12_v2_clean,E12_v3_clean,E1_1_v1_bayesian_base,E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E1_v5_operativo_rebuild_v2,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean,E8_v1_clean,E8_v2_clean,E8_v3_clean,E9_v1_clean,E9_v2_clean,E9_v2_operativo_rebuild                38 C1_v1_clean,C1_v2_clean,C1_v3_clean,C2_v1_clean,C2_v2_clean,C2_v3_clean,E10_v1_clean,E1_v1,E9_smoke_tmp C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | C2_v1_clean:task_type=clasificacion | C2_v2_clean:task_type=clasificacion | C2_v3_clean:task_type=clasificacion | E10_v1_clean:columnas_minimas_invalidas;predicciones_no_mergeables | E1_v1:sin_loss_h | E9_smoke_tmp:status_run=parcial;sin_loss_h;sin_predicciones          26                             12                 14                         0.860324
       H4 E11_v1_clean,E11_v2_clean,E11_v3_clean,E12_v1_clean,E12_v2_clean,E12_v3_clean,E1_1_v1_bayesian_base,E1_v2,E1_v2_clean,E1_v3_clean,E1_v4_clean,E1_v5_clean,E1_v5_operativo_rebuild_v2,E2_v1_clean,E2_v2_clean,E2_v3_clean,E3_v1_clean,E3_v2_clean,E3_v3_clean,E4_v1_clean,E4_v2_clean,E4_v3_clean,E5_v1_clean,E5_v2_clean,E5_v3_clean,E5_v4_clean,E5_v5_clean,E6_v1_clean,E6_v2_clean,E7_v1_clean,E7_v2_clean,E7_v3_clean,E8_v1_clean,E8_v2_clean,E8_v3_clean,E9_v1_clean,E9_v2_clean,E9_v2_operativo_rebuild                38 C1_v1_clean,C1_v2_clean,C1_v3_clean,C2_v1_clean,C2_v2_clean,C2_v3_clean,E10_v1_clean,E1_v1,E9_smoke_tmp C1_v1_clean:task_type=clasificacion | C1_v2_clean:task_type=clasificacion | C1_v3_clean:task_type=clasificacion | C2_v1_clean:task_type=clasificacion | C2_v2_clean:task_type=clasificacion | C2_v3_clean:task_type=clasificacion | E10_v1_clean:columnas_minimas_invalidas;predicciones_no_mergeables | E1_v1:sin_loss_h | E9_smoke_tmp:status_run=parcial;sin_loss_h;sin_predicciones          25                             11                 14                         0.854737
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
- `C2_v1_clean` H1: task_type=clasificacion
- `C2_v2_clean` H1: task_type=clasificacion
- `C2_v3_clean` H1: task_type=clasificacion
- `E10_v1_clean` H1: columnas_minimas_invalidas;predicciones_no_mergeables
- `E1_v1` H1: sin_loss_h
- `E9_smoke_tmp` H1: status_run=parcial
- `C1_v1_clean` H2: task_type=clasificacion

## Lectura preliminar

- La evidencia sí sugiere especialización por horizonte: `E9_v2_clean` domina `H1`, `E12_v3_clean` domina `H2`, `E9_v1_clean` domina `H3` y `E5_v4_clean` domina `H4`.
- También hay especialización operativa: dirección y detección de caídas no siempre coinciden con el mejor `loss_h`.
- En `E3`, la señal más útil quedó en `E3_v2_clean`; `E3_v3_clean` no mejora esa línea y `E4` no desplazó a bagging.
- Ya existe base suficiente para pensar en un ensamblado por horizonte como hipótesis metodológica futura, con cobertura real de `E1-E4` y auditoría explícita de compatibilidad de predicciones.
- Conviene automatizar a partir de ahora la reconstrucción de esta tabla maestra en cada corrida nueva para evitar que el análisis dependa del workbook manual.
