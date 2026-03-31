Nombre sugerido del chat: Apertura_estrictamente_controlada_de_E7_Prophet

Quiero que abras y ejecutes la familia E7 del proyecto Radar bajo el mismo estándar metodológico, operativo y de trazabilidad que se ha venido consolidando en E1–E6. La familia E7 corresponde a Prophet con regresores exógenos.

CONTEXTO DEL PROYECTO

A estas alturas del proyecto ya quedaron exploradas o abiertas las siguientes familias:

- E1 = Ridge
- E2 = Huber
- E3 = Random Forest
- E4 = XGBoost
- E5 = CatBoost
- E6 = ARIMAX

Estado comparativo relevante al momento de abrir E7:

- E1_v5_clean = mejor baseline lineal limpio global
- E1_v4_clean = referencia parsimoniosa fuerte y equilibrada
- E5_v4_clean = una de las referencias no lineales más competitivas
- E3_v2_clean = referencia no lineal útil
- E4_v1_clean = boosting útil pero no líder
- E6 = familia debilitada; no seguir de momento

Lectura metodológica heredada de E6:

- ARIMAX no fue competitivo.
- La parsimonia sí ayudó frente a amplitud exógena.
- No conviene seguir insistiendo en E6.
- El siguiente paso razonable del plan es abrir E7 = Prophet.

OBJETIVO DE ESTA ETAPA

Quiero evaluar si Prophet, usando tendencia estructural y regresores exógenos, puede capturar mejor la dinámica del Radar que ARIMAX y si puede ofrecer una alternativa competitiva frente a los modelos tabulares ya corridos.

No quiero una exploración caótica. Quiero una apertura limpia, comparable y defendible.

MARCO METODOLÓGICO OBLIGATORIO

Debes mantener exactamente el mismo marco de evaluación que en las familias previas para asegurar comparabilidad real:

- mismos horizontes: 1, 2, 3, 4
- misma validación externa: walk-forward expanding
- mismo dataset base
- mismo esquema de métricas Radar por horizonte
- mismo cálculo de L_total_Radar por corrida
- misma lógica de artefactos por run
- mismo registro en grid / tracker / auditoría

VERSIONES A IMPLEMENTAR Y CORRER

1. `E7_v1_clean`
   - `target_mode=nivel`
   - `feature_mode=corr`
   - `lags=1,2,3,4,5,6`
   - `changepoint_prior_scale=0.05`
   - `seasonality_mode=additive`
   - `weekly_seasonality=false`
   - `yearly_seasonality=false`
   - `daily_seasonality=false`

2. `E7_v2_clean`
   - igual a `E7_v1_clean`
   - único cambio: `feature_mode=all`

3. `E7_v3_clean`
   - igual a `E7_v1_clean`
   - único cambio: `changepoint_prior_scale=0.20`

ORDEN DE EJECUCIÓN

1. `E7_v1_clean`
2. `E7_v2_clean`
3. `E7_v3_clean`

REFERENCIAS OBLIGATORIAS

- `E1_v5_clean`
- `E1_v4_clean`
- `E5_v4_clean`
- `E3_v2_clean`
- `E4_v1_clean`
- `E6_v1_clean`
- `E6_v2_clean`

SALIDAS OBLIGATORIAS POR RUN

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `predicciones_h1.csv`
- `predicciones_h2.csv`
- `predicciones_h3.csv`
- `predicciones_h4.csv`
- comparaciones contra referencias
- trazabilidad de features efectivamente utilizadas por horizonte cuando aplique
- registro correcto en `grid_experimentos_radar.xlsx`
- actualización consistente de tabla maestra / auditoría
