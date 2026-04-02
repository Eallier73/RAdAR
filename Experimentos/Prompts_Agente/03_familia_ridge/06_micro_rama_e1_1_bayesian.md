# Micro-rama E1.1 v1 Bayesian

Objetivo:

- abrir una subrama tactica y corta dentro de `E1`
- probar si `BayesianRidge` extrae algo mas de senal lineal util que `Ridge`
- mantener comparabilidad estricta con el marco limpio temporal del proyecto

Diseno base:

- run canonico: `E1_1_v1_bayesian_base`
- modelo: `BayesianRidge`
- `target_mode = nivel`
- `feature_mode = corr`
- `transform_mode = standard`
- `lags = 1,2,3,4,5,6`
- `horizons = 1,2,3,4`
- validacion: `walk-forward expanding`

Referencias obligatorias:

- `E1_v5_clean`
- `E1_v4_clean`
- `E1_v2_clean`

Regla de stop:

- si `E1_1_v1_bayesian_base` no mejora de forma clara a `E1_v5_clean`, la micro-rama se cierra de inmediato
- solo si muestra senal real se autoriza una unica corrida adicional:
  - `E1_1_v2_bayesian_control`

Restricciones:

- no abrir familia principal nueva
- no correr `ARDRegression`
- no abrir tuning amplio
- no romper comparabilidad con el pipeline temporal comun
