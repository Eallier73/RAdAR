# Resumen de Ejecucion

## Run

- `run_id`: `E1_1_v1_bayesian_base`
- `run_dir`: `/home/emilio/Documentos/RAdAR/Experimentos/runs/E1_1_v1_bayesian_base_20260402_063714`
- `script`: [run_e1_bayesian_ridge.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e1_bayesian_ridge.py)

## Hipotesis

Verificar si `BayesianRidge` extrae una mejora lineal util frente a `Ridge` bajo el mismo marco temporal limpio y sin abrir una nueva familia principal.

## Configuracion

- modelo: `BayesianRidge`
- `target_mode = nivel`
- `feature_mode = corr`
- `transform_mode = standard`
- `lags = 1,2,3,4,5,6`
- `horizons = 1,2,3,4`
- validacion: `walk-forward expanding`
- referencias: `E1_v5_clean`, `E1_v4_clean`, `E1_v2_clean`

## Resultado global

- `E1_1_v1_bayesian_base = 0.264946`
- `E1_v5_clean = 0.243442`
- `E1_v4_clean = 0.253277`
- `E1_v2_clean = 0.261239`

## Lectura

- `H1`: empeora frente a `E1_v5_clean`
- `H2`: empeora frente a `E1_v5_clean`
- `H3`: mejora parcial
- `H4`: empate tecnico, apenas peor

## Decision

- no ejecutar `E1_1_v2_bayesian_control`
- cerrar `E1.1 Bayesian` como micro-rama util pero no preferible
- mantener intacto el cierre principal de `E1`
