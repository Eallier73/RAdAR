# Constructos de Representacion E12

Fecha de actualizacion: `2026-04-03`

Este documento fija los constructos nuevos de `E12` y explica por que son temporalmente validos.

## Regla general de validez

Toda feature de `E12` debe poder responder afirmativamente a esta pregunta:

> ¿Esta variable habria estado disponible de forma realista en el momento exacto en que el modelo debia predecir ese horizonte?

Las features de `E12` se construyen solo desde:

- predicciones archivadas por fecha/horizonte de runs canonicos previos;
- lags y deltas observables del target en `t`.

No se usan:

- etiquetas ex post de “modelo ganador por fila”;
- columnas de `E10`;
- recombinaciones ex post por horizonte;
- metricas futuras como features;
- seleccion de bases usando desempeno del tramo de evaluacion.

## Fuentes por variante

### `E12_v1_clean`

- runs fuente:
  - `E1_v5_clean`
  - `E5_v4_clean`
- objetivo: bloque minimo y parsimonioso

### `E12_v2_clean`

- runs fuente:
  - `E1_v5_clean`
  - `E5_v4_clean`
  - `E3_v2_clean`
  - `E7_v3_clean`
- objetivo: ampliar diversidad funcional sin convertir el sistema en stacking oculto

### `E12_v3_clean`

- runs fuente:
  - `E1_v5_clean`
  - `E5_v4_clean`
  - `E3_v2_clean`
  - `E7_v3_clean`
- objetivo: aislar el valor del desacuerdo entre bases sin bloque de regimen

## Bloques de constructos

## 1. Prediccion archivada

Features:

- `rep_pred_<run_id>`
- `rep_delta_<run_id>`

Definicion:

- `rep_pred_<run_id>`: prediccion numerica archivada del run canonico fuente, alineada por `fecha` y `horizonte`
- `rep_delta_<run_id>`: diferencia entre la prediccion archivada y `y_t`, para resumir el movimiento sugerido por esa base

Fuente:

- `predicciones_h*.csv` de runs canonicos previos

Momento temporal:

- historico alineado por `fecha` y `horizonte`; no requiere ver `y` futuro del fold actual

Intuicion:

- resume lecturas funcionales alternativas del problema dentro del mismo marco temporal

## 2. Consenso y desacuerdo entre bases

Features:

- `rep_spread_e1_e5`
- `rep_pred_mean_e1_e5`
- `rep_delta_mean_e1_e5`
- `rep_delta_std_e1_e5`
- `rep_pred_mean_all`
- `rep_pred_std_all`
- `rep_pred_range_all`
- `rep_delta_mean_all`
- `rep_delta_std_all`
- `rep_fall_share_all`
- `rep_direction_consensus_mean`
- `rep_pred_mean_nonlinear_tabular`
- `rep_spread_linear_vs_nonlinear`
- `rep_spread_temporal_vs_tabular`

Definicion:

- agregados simples de promedio, desviacion, rango y consenso direccional sobre el bloque de predicciones archivadas

Fuente:

- predicciones archivadas ya alineadas por fecha/horizonte

Momento temporal:

- disponibles solo cuando las predicciones historicas fuente existen para esa fila y horizonte

Intuicion:

- medir si las familias coinciden, si se contradicen, si aparece consenso bajista o si una lectura temporal discrepa de la tabular

## 3. Regimen observable en t

Features:

- `reg_obs_delta_lag1`
- `reg_obs_delta_lag2`
- `reg_obs_delta_lag3`
- `reg_obs_delta_mean_w3`
- `reg_obs_abs_delta_mean_w3`
- `reg_obs_delta_std_w3`
- `reg_obs_streak_signed_w3`

Definicion:

- estadisticas recientes del movimiento observado del target

Fuente:

- dataset maestro y lags de `y_t`

Momento temporal:

- completamente observable en `t`

Intuicion:

- describir si el sistema viene acelerando, desacelerando, entrando en racha o en volatilidad local

## Procedencia exacta

Los inventarios por run y horizonte quedan guardados en:

- [E12_v1_clean_20260403_075150](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v1_clean_20260403_075150)
- [E12_v2_clean_20260403_075843](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v2_clean_20260403_075843)
- [E12_v3_clean_20260403_080040](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v3_clean_20260403_080040)

Archivos relevantes:

- `inventario_columnas_representacion_h1.csv`
- `inventario_columnas_representacion_h2.csv`
- `inventario_columnas_representacion_h3.csv`
- `inventario_columnas_representacion_h4.csv`
- `inventario_columnas_representacion.csv`

## Juicio metodologico

Los constructos de `E12` son temporalmente defendibles, pero eso no implica valor promocionable.

Lectura final:

- la procedencia es limpia;
- la trazabilidad es fuerte;
- la hipotesis de representacion no quedo confirmada en esta primera apertura;
- el hallazgo parcial mas util es que el desacuerdo entre bases parece aportar mas que el bloque de regimen usado aqui.
