# Diccionario metodologico de la tabla E10

## Proposito

Este diccionario documenta la tabla `E10` como infraestructura especifica para meta-seleccion / gating contextual.

`E10` no reutiliza directamente la tabla de `E9` como si fuera suficiente por si sola. La tabla construida aqui separa:

- predicciones base,
- contexto observable en `t`,
- historicos shifted de rendimiento,
- variables de desacuerdo,
- targets retrospectivos del selector,
- y columnas prohibidas como features.

## Pool incluido de modelos base

| run_id | family | model | constructo_e10 | justificacion_e10 |
| --- | --- | --- | --- | --- |
| E1_v5_clean | lineal_regularizado | ridge_tscv | referente numerico puro | Benchmark numerico puro principal del proyecto y ancla lineal regularizada. |
| E2_v3_clean | robusto | huber_tscv | referencia robusta / especialista H2-H4 | Aporta sesgo robusto y senal util en horizontes intermedios y largos. |
| E3_v2_clean | arboles_boosting | random_forest_regressor | bagging de diversidad | Referencia bagging util para diversidad funcional frente a lineales y boosting. |
| E5_v4_clean | arboles_boosting | catboost_regressor | mejor no lineal tabular | Campeon no lineal tabular vigente y candidato fuerte a familia base competitiva. |
| E7_v3_clean | series_tiempo_exogenas | prophet_exogenous_regressor | referencia temporal con changepoints | Aporta una familia temporal estructurada distinta a ARIMAX y distinta de los tabulares. |
| E9_v2_clean | stacking_controlado | stacking_huber_curado_por_horizonte | referente operativo de riesgo-direccion-caidas | Mejor run orientado a riesgo, direccion y deteccion de caidas; inclusion minima obligatoria para E10. |

## Modelos explicitamente excluidos del pool principal

| run_id | family | model | justificacion_e10 |
| --- | --- | --- | --- |
| E1_v4_clean | lineal_regularizado | ridge_tscv | Queda fuera por alta redundancia con E1_v5_clean; se evita duplicar Ridge en la primera base E10. |
| E4_v1_clean | arboles_boosting | xgboost_regressor | XGBoost queda dominado como fuente de diversidad frente a E5_v4_clean y E3_v2_clean. |
| E6_v1_clean | series_tiempo_exogenas | sarimax_regressor | ARIMAX quedo debilitado y no aporta diversidad competitiva suficiente frente a E7_v3_clean. |
| E8_v2_clean | hibrido_residual | hybrid_residual_catboost_regressor_ridge_tscv | Hibrido residual util, pero derivativo respecto a E5 y aun no suficientemente estable para entrar al pool principal de E10. |

## Constructos metodologicos de la tabla

### 1. Predicciones base

Columnas `pred_*`, `direccion_pred_*`, `caida_pred_*` y `pred_disponible_*`.

- representan salidas OOF ya observadas por modelo base;
- son observables en tiempo real si ese modelo emite prediccion para la fila;
- pueden alimentar un meta-selector o gating futuro.

### 2. Variables de desacuerdo

Columnas como `rango_predicciones`, `desviacion_predicciones`, `consenso_direccion` y `numero_modelos_predicen_caida`.

- resumen cuanta dispersion o consenso existe entre modelos;
- son especialmente utiles para `E10`, porque el gating contextual depende de reconocer cuando los modelos discrepan;
- no usan `y_real`, por tanto son candidatas a feature.

### 3. Contexto observable en t

Columnas `ctx_*`.

- se derivan solo de informacion conocida al momento de predecir;
- incluyen nivel reciente, cambios recientes, volatilidad reciente y resumenes simples del bloque exogeno actual;
- no usan informacion futura.

### 4. Historicos shifted de rendimiento por modelo

Columnas `hist_*` con ventana `rolling=4`.

- usan errores o aciertos pasados ya observados;
- se calculan con `shift(1)` para evitar que la fila actual contamine su propia feature;
- son candidatas a feature solo bajo esa disciplina temporal estricta.

### 5. Error ex post y diagnostico retrospectivo

Columnas `abs_error_*`, `sq_error_*`, `acierto_direccion_*`, `acierto_caida_*`, `loss_local_*`, `actual_*`.

- existen para auditoria, comparacion y construccion de labels retrospectivos;
- usan `y_real` de la misma fila;
- estan prohibidas como features de entrenamiento online.

### 6. Targets retrospectivos del selector

Columnas `mejor_modelo_*` y `empate_*`.

- no son features;
- son labels para entrenar selectores duros, selectores operativos o modelos de gating supervisado;
- deben usarse solo dentro de una validacion temporal correcta cuando se llegue a correr `E10`.

## Columnas aptas como feature candidate

| column_name | block | descripcion | riesgo_leakage | comentario_metodologico |
| --- | --- | --- | --- | --- |
| cobertura_modelos_fila | contexto_desacuerdo | Proporcion de modelos disponibles respecto del pool incluido. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| consenso_direccion | contexto_desacuerdo | 1 si todas las direcciones predichas coinciden; 0 si no. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| desacuerdo_direccion | contexto_desacuerdo | 1 si existe desacuerdo de direccion entre modelos disponibles. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| desviacion_predicciones | contexto_desacuerdo | Desviacion estandar de predicciones disponibles. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| dispersion_direccion | contexto_desacuerdo | Numero de direcciones distintas relativo al total disponible. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| fila_completa_modelos_incluidos | contexto_desacuerdo | Indicador de disponibilidad total del pool principal de E10. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| max_diff_predicciones | contexto_desacuerdo | Diferencia maxima entre predicciones disponibles. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| max_predicciones | contexto_desacuerdo | Maximo de predicciones disponibles. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| mediana_predicciones | contexto_desacuerdo | Mediana de predicciones disponibles. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| min_predicciones | contexto_desacuerdo | Minimo de predicciones disponibles. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| n_direcciones_distintas | contexto_desacuerdo | Numero de direcciones distintas entre modelos disponibles. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| n_modelos_disponibles | contexto_desacuerdo | Conteo de modelos con prediccion disponible en la fila. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| numero_modelos_predicen_caida | contexto_desacuerdo | Numero de modelos que predicen caida. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| promedio_predicciones | contexto_desacuerdo | Promedio de predicciones disponibles. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| rango_predicciones | contexto_desacuerdo | Rango max-min de predicciones disponibles. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| share_modelos_predicen_caida | contexto_desacuerdo | Proporcion de modelos que predicen caida. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_abs_delta_1w | contexto_observable | Magnitud absoluta del ultimo cambio observado. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_delta_1w | contexto_observable | Cambio observado entre t y t-1. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_delta_2w | contexto_observable | Cambio observado entre t y t-2. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_mean_delta_4w | contexto_observable | Cambio medio reciente de 4 semanas. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_negative_delta_ratio_4w | contexto_observable | Proporcion reciente de cambios negativos en 4 semanas. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_positive_delta_ratio_4w | contexto_observable | Proporcion reciente de cambios positivos en 4 semanas. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_recent_fall_flag | contexto_observable | Bandera de que el ultimo cambio observado fue una caida. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_rolling_mean_4w | contexto_observable | Media movil de 4 semanas del target observada hasta t. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_rolling_std_4w | contexto_observable | Volatilidad reciente de 4 semanas del target observada hasta t. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_semana_iso | contexto_observable | Contexto temporal basico disponible en t. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_sentimiento_medios | contexto_observable | Sentimiento de medios observado en t. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_trend_vs_ma4 | contexto_observable | Separacion entre nivel actual y media movil de 4 semanas. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_v5_dispersion_neta | contexto_observable | Dispersion de variables tematicas netas observadas en t. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_v5_promedio_neto | contexto_observable | Promedio de variables tematicas netas observadas en t. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_y_lag1 | contexto_observable | Nivel observado una semana atras. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_y_lag2 | contexto_observable | Nivel observado dos semanas atras. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| ctx_y_lag4 | contexto_observable | Nivel observado cuatro semanas atras. | bajo | Observable en t y apta como feature contextual o de desacuerdo. |
| hist_abs_error_mean4_E1_v5_clean | historico_modelos | Promedio rolling shifted de error absoluto pasado de E1_v5_clean. | medio_controlado | Es util solo si se mantiene shift temporal estricto; asi evita usar el error de la misma fila. |
| hist_abs_error_mean4_E2_v3_clean | historico_modelos | Promedio rolling shifted de error absoluto pasado de E2_v3_clean. | medio_controlado | Es util solo si se mantiene shift temporal estricto; asi evita usar el error de la misma fila. |
| hist_abs_error_mean4_E3_v2_clean | historico_modelos | Promedio rolling shifted de error absoluto pasado de E3_v2_clean. | medio_controlado | Es util solo si se mantiene shift temporal estricto; asi evita usar el error de la misma fila. |
| hist_abs_error_mean4_E5_v4_clean | historico_modelos | Promedio rolling shifted de error absoluto pasado de E5_v4_clean. | medio_controlado | Es util solo si se mantiene shift temporal estricto; asi evita usar el error de la misma fila. |
| hist_abs_error_mean4_E7_v3_clean | historico_modelos | Promedio rolling shifted de error absoluto pasado de E7_v3_clean. | medio_controlado | Es util solo si se mantiene shift temporal estricto; asi evita usar el error de la misma fila. |
| hist_abs_error_mean4_E9_v2_clean | historico_modelos | Promedio rolling shifted de error absoluto pasado de E9_v2_clean. | medio_controlado | Es util solo si se mantiene shift temporal estricto; asi evita usar el error de la misma fila. |
| hist_caida_hit_mean4_E1_v5_clean | historico_modelos | Tasa rolling shifted de deteccion de caidas reales por E1_v5_clean. | medio_controlado | Sparsa pero valiosa para un selector orientado a riesgo; exige shift explicito y manejo de NaNs. |
| hist_caida_hit_mean4_E2_v3_clean | historico_modelos | Tasa rolling shifted de deteccion de caidas reales por E2_v3_clean. | medio_controlado | Sparsa pero valiosa para un selector orientado a riesgo; exige shift explicito y manejo de NaNs. |
| hist_caida_hit_mean4_E3_v2_clean | historico_modelos | Tasa rolling shifted de deteccion de caidas reales por E3_v2_clean. | medio_controlado | Sparsa pero valiosa para un selector orientado a riesgo; exige shift explicito y manejo de NaNs. |
| hist_caida_hit_mean4_E5_v4_clean | historico_modelos | Tasa rolling shifted de deteccion de caidas reales por E5_v4_clean. | medio_controlado | Sparsa pero valiosa para un selector orientado a riesgo; exige shift explicito y manejo de NaNs. |
| hist_caida_hit_mean4_E7_v3_clean | historico_modelos | Tasa rolling shifted de deteccion de caidas reales por E7_v3_clean. | medio_controlado | Sparsa pero valiosa para un selector orientado a riesgo; exige shift explicito y manejo de NaNs. |
| hist_caida_hit_mean4_E9_v2_clean | historico_modelos | Tasa rolling shifted de deteccion de caidas reales por E9_v2_clean. | medio_controlado | Sparsa pero valiosa para un selector orientado a riesgo; exige shift explicito y manejo de NaNs. |
| hist_dir_acc_mean4_E1_v5_clean | historico_modelos | Tasa rolling shifted de acierto de direccion reciente de E1_v5_clean. | medio_controlado | Apta como feature solo porque usa resultados ya observados de filas anteriores. |
| hist_dir_acc_mean4_E2_v3_clean | historico_modelos | Tasa rolling shifted de acierto de direccion reciente de E2_v3_clean. | medio_controlado | Apta como feature solo porque usa resultados ya observados de filas anteriores. |
| hist_dir_acc_mean4_E3_v2_clean | historico_modelos | Tasa rolling shifted de acierto de direccion reciente de E3_v2_clean. | medio_controlado | Apta como feature solo porque usa resultados ya observados de filas anteriores. |
| hist_dir_acc_mean4_E5_v4_clean | historico_modelos | Tasa rolling shifted de acierto de direccion reciente de E5_v4_clean. | medio_controlado | Apta como feature solo porque usa resultados ya observados de filas anteriores. |
| hist_dir_acc_mean4_E7_v3_clean | historico_modelos | Tasa rolling shifted de acierto de direccion reciente de E7_v3_clean. | medio_controlado | Apta como feature solo porque usa resultados ya observados de filas anteriores. |
| hist_dir_acc_mean4_E9_v2_clean | historico_modelos | Tasa rolling shifted de acierto de direccion reciente de E9_v2_clean. | medio_controlado | Apta como feature solo porque usa resultados ya observados de filas anteriores. |
| hist_loss_local_mean4_E1_v5_clean | historico_modelos | Promedio rolling shifted de perdida local pasada de E1_v5_clean. | medio_controlado | Resume desempeno operativo reciente del modelo sin mirar el error de la fila actual. |
| hist_loss_local_mean4_E2_v3_clean | historico_modelos | Promedio rolling shifted de perdida local pasada de E2_v3_clean. | medio_controlado | Resume desempeno operativo reciente del modelo sin mirar el error de la fila actual. |
| hist_loss_local_mean4_E3_v2_clean | historico_modelos | Promedio rolling shifted de perdida local pasada de E3_v2_clean. | medio_controlado | Resume desempeno operativo reciente del modelo sin mirar el error de la fila actual. |
| hist_loss_local_mean4_E5_v4_clean | historico_modelos | Promedio rolling shifted de perdida local pasada de E5_v4_clean. | medio_controlado | Resume desempeno operativo reciente del modelo sin mirar el error de la fila actual. |
| hist_loss_local_mean4_E7_v3_clean | historico_modelos | Promedio rolling shifted de perdida local pasada de E7_v3_clean. | medio_controlado | Resume desempeno operativo reciente del modelo sin mirar el error de la fila actual. |
| hist_loss_local_mean4_E9_v2_clean | historico_modelos | Promedio rolling shifted de perdida local pasada de E9_v2_clean. | medio_controlado | Resume desempeno operativo reciente del modelo sin mirar el error de la fila actual. |
| y_current | identidad_trazabilidad | Nivel observado en t, disponible al momento de predecir. | bajo | Es contexto observable en tiempo real y puede usarse como feature contextual. |
| caida_pred_E1_v5_clean | predicciones_base | Indicador de que E1_v5_clean predice caida segun el umbral operativo vigente. | bajo | Es particularmente valiosa para un gating orientado a riesgo y caidas. |
| caida_pred_E2_v3_clean | predicciones_base | Indicador de que E2_v3_clean predice caida segun el umbral operativo vigente. | bajo | Es particularmente valiosa para un gating orientado a riesgo y caidas. |
| caida_pred_E3_v2_clean | predicciones_base | Indicador de que E3_v2_clean predice caida segun el umbral operativo vigente. | bajo | Es particularmente valiosa para un gating orientado a riesgo y caidas. |
| caida_pred_E5_v4_clean | predicciones_base | Indicador de que E5_v4_clean predice caida segun el umbral operativo vigente. | bajo | Es particularmente valiosa para un gating orientado a riesgo y caidas. |
| caida_pred_E7_v3_clean | predicciones_base | Indicador de que E7_v3_clean predice caida segun el umbral operativo vigente. | bajo | Es particularmente valiosa para un gating orientado a riesgo y caidas. |
| caida_pred_E9_v2_clean | predicciones_base | Indicador de que E9_v2_clean predice caida segun el umbral operativo vigente. | bajo | Es particularmente valiosa para un gating orientado a riesgo y caidas. |
| direccion_pred_E1_v5_clean | predicciones_base | Direccion implicita de E1_v5_clean respecto a y_current (-1/0/1). | bajo | Es derivable de una prediccion disponible en tiempo real. |
| direccion_pred_E2_v3_clean | predicciones_base | Direccion implicita de E2_v3_clean respecto a y_current (-1/0/1). | bajo | Es derivable de una prediccion disponible en tiempo real. |
| direccion_pred_E3_v2_clean | predicciones_base | Direccion implicita de E3_v2_clean respecto a y_current (-1/0/1). | bajo | Es derivable de una prediccion disponible en tiempo real. |
| direccion_pred_E5_v4_clean | predicciones_base | Direccion implicita de E5_v4_clean respecto a y_current (-1/0/1). | bajo | Es derivable de una prediccion disponible en tiempo real. |
| direccion_pred_E7_v3_clean | predicciones_base | Direccion implicita de E7_v3_clean respecto a y_current (-1/0/1). | bajo | Es derivable de una prediccion disponible en tiempo real. |
| direccion_pred_E9_v2_clean | predicciones_base | Direccion implicita de E9_v2_clean respecto a y_current (-1/0/1). | bajo | Es derivable de una prediccion disponible en tiempo real. |
| pred_E1_v5_clean | predicciones_base | Prediccion OOF del modelo E1_v5_clean. | bajo | Es una salida base observable en tiempo real y principal insumo para un meta-selector o gating. |
| pred_E2_v3_clean | predicciones_base | Prediccion OOF del modelo E2_v3_clean. | bajo | Es una salida base observable en tiempo real y principal insumo para un meta-selector o gating. |
| pred_E3_v2_clean | predicciones_base | Prediccion OOF del modelo E3_v2_clean. | bajo | Es una salida base observable en tiempo real y principal insumo para un meta-selector o gating. |
| pred_E5_v4_clean | predicciones_base | Prediccion OOF del modelo E5_v4_clean. | bajo | Es una salida base observable en tiempo real y principal insumo para un meta-selector o gating. |
| pred_E7_v3_clean | predicciones_base | Prediccion OOF del modelo E7_v3_clean. | bajo | Es una salida base observable en tiempo real y principal insumo para un meta-selector o gating. |
| pred_E9_v2_clean | predicciones_base | Prediccion OOF del modelo E9_v2_clean. | bajo | Es una salida base observable en tiempo real y principal insumo para un meta-selector o gating. |
| pred_disponible_E1_v5_clean | predicciones_base | Indicador de disponibilidad de la prediccion de E1_v5_clean. | bajo | Puede ayudar a decidir entre modelos cuando el pool no esta completamente cubierto. |
| pred_disponible_E2_v3_clean | predicciones_base | Indicador de disponibilidad de la prediccion de E2_v3_clean. | bajo | Puede ayudar a decidir entre modelos cuando el pool no esta completamente cubierto. |
| pred_disponible_E3_v2_clean | predicciones_base | Indicador de disponibilidad de la prediccion de E3_v2_clean. | bajo | Puede ayudar a decidir entre modelos cuando el pool no esta completamente cubierto. |
| pred_disponible_E5_v4_clean | predicciones_base | Indicador de disponibilidad de la prediccion de E5_v4_clean. | bajo | Puede ayudar a decidir entre modelos cuando el pool no esta completamente cubierto. |
| pred_disponible_E7_v3_clean | predicciones_base | Indicador de disponibilidad de la prediccion de E7_v3_clean. | bajo | Puede ayudar a decidir entre modelos cuando el pool no esta completamente cubierto. |
| pred_disponible_E9_v2_clean | predicciones_base | Indicador de disponibilidad de la prediccion de E9_v2_clean. | bajo | Puede ayudar a decidir entre modelos cuando el pool no esta completamente cubierto. |

## Targets del selector

| column_name | descripcion | comentario_metodologico |
| --- | --- | --- |
| empate_mejor_modelo | Bandera de empate exacto/numericamente equivalente para el mejor modelo por perdida local. | Es target o label retrospectiva para investigar selectores; nunca feature del mismo problema. |
| empate_mejor_modelo_error_abs | Bandera de empate exacto/numericamente equivalente para el mejor modelo por error absoluto. | Es target o label retrospectiva para investigar selectores; nunca feature del mismo problema. |
| mejor_modelo_caida | Modelo que detecta la caida real con menor error absoluto; si no hubo caida o nadie la detecta, valor sentinela. | Es target o label retrospectiva para investigar selectores; nunca feature del mismo problema. |
| mejor_modelo_direccion | Modelo con direccion correcta y menor error absoluto; si ninguno acierta, valor sentinela. | Es target o label retrospectiva para investigar selectores; nunca feature del mismo problema. |
| mejor_modelo_error_abs | Modelo con menor error absoluto en la fila entre los disponibles. | Es target o label retrospectiva para investigar selectores; nunca feature del mismo problema. |
| mejor_modelo_loss_radar_local | Modelo con menor perdida local Radar en la fila. | Es target o label retrospectiva para investigar selectores; nunca feature del mismo problema. |
| mejor_modelo_mae_local | Alias operativo del mejor modelo por error absoluto local. | Es target o label retrospectiva para investigar selectores; nunca feature del mismo problema. |
| mejor_modelo_operativo | Selector retrospectivo jerarquico: primero caida, luego direccion, luego perdida local. | Es target o label retrospectiva para investigar selectores; nunca feature del mismo problema. |

## Columnas prohibidas para entrenamiento

| column_name | block | descripcion | comentario_metodologico |
| --- | --- | --- | --- |
| actual_caida | contexto_desacuerdo | Indicador de caida realizada bajo el umbral operativo del Radar. | Usa y_real y por tanto no puede ser feature online. |
| actual_delta | contexto_desacuerdo | Cambio realizado respecto de y_current. | Usa y_real y por tanto no puede ser feature online. |
| actual_direction | contexto_desacuerdo | Direccion realizada de la observacion. | Usa y_real y por tanto no puede ser feature online. |
| abs_error_E1_v5_clean | error_ex_post | Error absoluto realizado de E1_v5_clean. | Solo diagnostico retrospectivo; no puede entrar como feature del selector en la misma fila. |
| abs_error_E2_v3_clean | error_ex_post | Error absoluto realizado de E2_v3_clean. | Solo diagnostico retrospectivo; no puede entrar como feature del selector en la misma fila. |
| abs_error_E3_v2_clean | error_ex_post | Error absoluto realizado de E3_v2_clean. | Solo diagnostico retrospectivo; no puede entrar como feature del selector en la misma fila. |
| abs_error_E5_v4_clean | error_ex_post | Error absoluto realizado de E5_v4_clean. | Solo diagnostico retrospectivo; no puede entrar como feature del selector en la misma fila. |
| abs_error_E7_v3_clean | error_ex_post | Error absoluto realizado de E7_v3_clean. | Solo diagnostico retrospectivo; no puede entrar como feature del selector en la misma fila. |
| abs_error_E9_v2_clean | error_ex_post | Error absoluto realizado de E9_v2_clean. | Solo diagnostico retrospectivo; no puede entrar como feature del selector en la misma fila. |
| acierto_caida_E1_v5_clean | error_ex_post | Indicador retrospectivo de deteccion de caida de E1_v5_clean cuando hubo caida real. | Se alinea con la prioridad operativa del Radar, pero solo como diagnostico o como base de historicos shifted. |
| acierto_caida_E2_v3_clean | error_ex_post | Indicador retrospectivo de deteccion de caida de E2_v3_clean cuando hubo caida real. | Se alinea con la prioridad operativa del Radar, pero solo como diagnostico o como base de historicos shifted. |
| acierto_caida_E3_v2_clean | error_ex_post | Indicador retrospectivo de deteccion de caida de E3_v2_clean cuando hubo caida real. | Se alinea con la prioridad operativa del Radar, pero solo como diagnostico o como base de historicos shifted. |
| acierto_caida_E5_v4_clean | error_ex_post | Indicador retrospectivo de deteccion de caida de E5_v4_clean cuando hubo caida real. | Se alinea con la prioridad operativa del Radar, pero solo como diagnostico o como base de historicos shifted. |
| acierto_caida_E7_v3_clean | error_ex_post | Indicador retrospectivo de deteccion de caida de E7_v3_clean cuando hubo caida real. | Se alinea con la prioridad operativa del Radar, pero solo como diagnostico o como base de historicos shifted. |
| acierto_caida_E9_v2_clean | error_ex_post | Indicador retrospectivo de deteccion de caida de E9_v2_clean cuando hubo caida real. | Se alinea con la prioridad operativa del Radar, pero solo como diagnostico o como base de historicos shifted. |
| acierto_direccion_E1_v5_clean | error_ex_post | Indicador retrospectivo de acierto de direccion de E1_v5_clean. | Puede usarse como label diagnostica o para historicos shifted, nunca en la misma fila como feature. |
| acierto_direccion_E2_v3_clean | error_ex_post | Indicador retrospectivo de acierto de direccion de E2_v3_clean. | Puede usarse como label diagnostica o para historicos shifted, nunca en la misma fila como feature. |
| acierto_direccion_E3_v2_clean | error_ex_post | Indicador retrospectivo de acierto de direccion de E3_v2_clean. | Puede usarse como label diagnostica o para historicos shifted, nunca en la misma fila como feature. |
| acierto_direccion_E5_v4_clean | error_ex_post | Indicador retrospectivo de acierto de direccion de E5_v4_clean. | Puede usarse como label diagnostica o para historicos shifted, nunca en la misma fila como feature. |
| acierto_direccion_E7_v3_clean | error_ex_post | Indicador retrospectivo de acierto de direccion de E7_v3_clean. | Puede usarse como label diagnostica o para historicos shifted, nunca en la misma fila como feature. |
| acierto_direccion_E9_v2_clean | error_ex_post | Indicador retrospectivo de acierto de direccion de E9_v2_clean. | Puede usarse como label diagnostica o para historicos shifted, nunca en la misma fila como feature. |
| loss_local_E1_v5_clean | error_ex_post | Perdida local tipo Radar para E1_v5_clean en la fila-horizonte. | Sirve para construir labels retrospectivos mas operativos; no puede ser feature de la misma fila. |
| loss_local_E2_v3_clean | error_ex_post | Perdida local tipo Radar para E2_v3_clean en la fila-horizonte. | Sirve para construir labels retrospectivos mas operativos; no puede ser feature de la misma fila. |
| loss_local_E3_v2_clean | error_ex_post | Perdida local tipo Radar para E3_v2_clean en la fila-horizonte. | Sirve para construir labels retrospectivos mas operativos; no puede ser feature de la misma fila. |
| loss_local_E5_v4_clean | error_ex_post | Perdida local tipo Radar para E5_v4_clean en la fila-horizonte. | Sirve para construir labels retrospectivos mas operativos; no puede ser feature de la misma fila. |
| loss_local_E7_v3_clean | error_ex_post | Perdida local tipo Radar para E7_v3_clean en la fila-horizonte. | Sirve para construir labels retrospectivos mas operativos; no puede ser feature de la misma fila. |
| loss_local_E9_v2_clean | error_ex_post | Perdida local tipo Radar para E9_v2_clean en la fila-horizonte. | Sirve para construir labels retrospectivos mas operativos; no puede ser feature de la misma fila. |
| sq_error_E1_v5_clean | error_ex_post | Error cuadratico realizado de E1_v5_clean. | Solo diagnostico retrospectivo; prohibido como feature online. |
| sq_error_E2_v3_clean | error_ex_post | Error cuadratico realizado de E2_v3_clean. | Solo diagnostico retrospectivo; prohibido como feature online. |
| sq_error_E3_v2_clean | error_ex_post | Error cuadratico realizado de E3_v2_clean. | Solo diagnostico retrospectivo; prohibido como feature online. |
| sq_error_E5_v4_clean | error_ex_post | Error cuadratico realizado de E5_v4_clean. | Solo diagnostico retrospectivo; prohibido como feature online. |
| sq_error_E7_v3_clean | error_ex_post | Error cuadratico realizado de E7_v3_clean. | Solo diagnostico retrospectivo; prohibido como feature online. |
| sq_error_E9_v2_clean | error_ex_post | Error cuadratico realizado de E9_v2_clean. | Solo diagnostico retrospectivo; prohibido como feature online. |
| y_real | identidad_trazabilidad | Valor observado real del horizonte correspondiente. | Es el outcome realizado y solo puede usarse para evaluacion, diagnostico o construccion de labels retrospectivos. |

## Precaucion metodologica central

La separacion entre columnas observables en `t` y columnas que usan `y_real` de la misma fila es obligatoria. Si esta frontera se rompe, `E10` deja de ser un gating contextual defendible y pasa a tener leakage retrospectivo.
