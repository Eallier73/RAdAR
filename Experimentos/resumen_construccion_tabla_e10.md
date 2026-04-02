# Resumen de construccion de la tabla E10

## 1. Archivo base

- Workbook maestro canonico: `/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar.xlsx`
- Workbook curado de E9 usado como referencia: `/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar_e9_curada.xlsx`

## 2. Modelos incluidos finalmente

| run_id | family | model | constructo_e10 | justificacion_e10 |
| --- | --- | --- | --- | --- |
| E1_v5_clean | lineal_regularizado | ridge_tscv | referente numerico puro | Benchmark numerico puro principal del proyecto y ancla lineal regularizada. |
| E2_v3_clean | robusto | huber_tscv | referencia robusta / especialista H2-H4 | Aporta sesgo robusto y senal util en horizontes intermedios y largos. |
| E3_v2_clean | arboles_boosting | random_forest_regressor | bagging de diversidad | Referencia bagging util para diversidad funcional frente a lineales y boosting. |
| E5_v4_clean | arboles_boosting | catboost_regressor | mejor no lineal tabular | Campeon no lineal tabular vigente y candidato fuerte a familia base competitiva. |
| E7_v3_clean | series_tiempo_exogenas | prophet_exogenous_regressor | referencia temporal con changepoints | Aporta una familia temporal estructurada distinta a ARIMAX y distinta de los tabulares. |
| E9_v2_clean | stacking_controlado | stacking_huber_curado_por_horizonte | referente operativo de riesgo-direccion-caidas | Mejor run orientado a riesgo, direccion y deteccion de caidas; inclusion minima obligatoria para E10. |

## 3. Modelos excluidos explicitamente del pool principal

| run_id | family | model | justificacion_e10 |
| --- | --- | --- | --- |
| E1_v4_clean | lineal_regularizado | ridge_tscv | Queda fuera por alta redundancia con E1_v5_clean; se evita duplicar Ridge en la primera base E10. |
| E4_v1_clean | arboles_boosting | xgboost_regressor | XGBoost queda dominado como fuente de diversidad frente a E5_v4_clean y E3_v2_clean. |
| E6_v1_clean | series_tiempo_exogenas | sarimax_regressor | ARIMAX quedo debilitado y no aporta diversidad competitiva suficiente frente a E7_v3_clean. |
| E8_v2_clean | hibrido_residual | hybrid_residual_catboost_regressor_ridge_tscv | Hibrido residual util, pero derivativo respecto a E5 y aun no suficientemente estable para entrar al pool principal de E10. |

## 4. Cobertura por horizonte

| horizonte | filas_total | filas_completas_pool | cobertura_media_pool | filas_con_E9_v2 | filas_sin_E9_v2 |
| --- | --- | --- | --- | --- | --- |
| H1 | 28 | 14 | 0.8690476190476192 | 14 | 14 |
| H2 | 27 | 13 | 0.8641975308641976 | 13 | 14 |
| H3 | 26 | 12 | 0.858974358974359 | 12 | 14 |
| H4 | 25 | 11 | 0.8533333333333334 | 11 | 14 |

## 5. Que horizontes quedaron bien cubiertos

- Todos los horizontes `H1-H4` quedaron cubiertos por al menos un subconjunto amplio del pool.
- La union de candidatos deja `28/27/26/25` filas evaluables por horizonte.
- La interseccion completa de todo el pool principal queda limitada por `E9_v2_clean`.

## 6. La tabla quedo lista para meta-selector duro

- Estado: `utilizable con reservas`
- Motivo: ya existen features observables, labels retrospectivos y trazabilidad fila-horizonte, pero el overlap completo del pool principal sigue siendo corto.

## 7. La tabla quedo lista para gating blando

- Estado: `utilizable con reservas`
- Motivo: la tabla ya contiene predicciones base, desacuerdo entre modelos, contexto observable e historicos shifted de rendimiento.

## 8. Que columnas si pueden ser features

- Predicciones base `pred_*`
- Disponibilidad de prediccion `pred_disponible_*`
- Direccion y caida predichas `direccion_pred_*`, `caida_pred_*`
- Variables de desacuerdo entre modelos
- Contexto `ctx_*`
- Historicos shifted `hist_*`

## 9. Que columnas estan prohibidas para entrenamiento

- `y_real`
- `actual_delta`, `actual_direction`, `actual_caida`
- `abs_error_*`, `sq_error_*`
- `acierto_direccion_*`, `acierto_caida_*`
- `loss_local_*`
- `mejor_modelo_*`
- `empate_*`

## 10. Artefactos que faltan o sobran

- No faltan predicciones OOF para los modelos incluidos.
- Sobra cobertura asimetrica: `E9_v2_clean` entra por decision metodologica minima, pero reduce el numero de filas completas del pool.
- No se agregaron columnas oportunistas basadas en informacion futura.

## 11. Limitaciones persistentes

- Falta decidir politica formal para filas incompletas en `E10`.
- Falta decidir si el primer `E10` usara el pool completo o una variante por horizonte con subset estable.
- Falta definir el primer objetivo exacto del selector: numerico, direccion, caida o operativo.
- No existe todavia `run_e10_*` operativo; esta tarea deja la infraestructura de datos, no el modelado final.

## 12. Cierre metodologico

La tabla ya permite investigar E10, pero la cobertura completa del pool principal queda limitada por `E9_v2_clean` (14/13/12/11 filas completas por horizonte). Antes de correr el primer selector real hace falta fijar explicitamente la politica de filas incompletas y el criterio de entrenamiento por horizonte.

E10 requiere una tabla especifica distinta de la tabla usada por `E9`. La tabla construida aqui no busca todavia decidir el mejor selector, sino habilitar de forma limpia esa investigacion futura. La separacion entre predicciones base, contexto observable, desacuerdo entre modelos y etiquetas retrospectivas es condicion indispensable para evitar leakage y sostener trazabilidad fuerte.
