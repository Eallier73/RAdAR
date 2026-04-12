# Resumen Micro-rama E1.1 Bayesian

Fecha de actualizacion: `2026-04-02`

## Objetivo

Registrar de forma trazable la verificacion tactica `E1.1` y dejar cerrada la lectura metodologica de esta micro-rama sin reabrir la familia principal `E1`.

## Alcance ejecutado

Corrida canónica:

- [E1_1_v1_bayesian_base_20260402_063714](/home/emilio/Documentos/RAdAR/experiments/runs/E1_1_v1_bayesian_base_20260402_063714)

Corrida descartada por regla de stop:

- `E1_1_v2_bayesian_control` no se ejecuto

## Implementacion

- Script usado: [run_e1_bayesian_ridge.py](/home/emilio/Documentos/RAdAR/src/modeling/run_e1_bayesian_ridge.py)
- Modelo: `BayesianRidge`
- `target_mode = nivel`
- `feature_mode = corr`
- `transform_mode = standard`
- `lags = 1,2,3,4,5,6`
- `horizons = 1,2,3,4`
- validacion externa: `walk-forward expanding`
- mismo dataset maestro y mismas metricas Radar que `E1`

Comando canónico:

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/src/modeling/run_e1_bayesian_ridge.py \
  --run-id E1_1_v1_bayesian_base \
  --reference-run-id E1_v5_clean \
  --extra-reference-run-ids E1_v4_clean,E1_v2_clean \
  --hypothesis-note bayesianridge_micro_branch_vs_ridge \
  --target-mode nivel \
  --feature-mode corr \
  --lags 1,2,3,4,5,6 \
  --transform-mode standard \
  --initial-train-size 40 \
  --horizons 1,2,3,4
```

## Tabla comparativa minima

| run_id | modelo | feature_mode | lags | feature_count_promedio | mae_promedio | rmse_promedio | direction_accuracy_promedio | deteccion_caidas_promedio | L_total_Radar |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `E1_v4_clean` | `ridge_tscv` | `corr` | `1,2,3,4` | 21.0 | 0.102876 | 0.132898 | 0.744357 | 0.765705 | 0.253277 |
| `E1_v5_clean` | `ridge_tscv` | `corr` | `1,2,3,4,5,6` | 30.0 | 0.102512 | 0.136512 | 0.743753 | 0.782323 | 0.243442 |
| `E1_1_v1_bayesian_base` | `bayesian_ridge` | `corr` | `1,2,3,4,5,6` | 30.0 | 0.111910 | 0.145335 | 0.734971 | 0.740657 | 0.264946 |

## Lectura por horizonte frente a `E1_v5_clean`

- `H1`: empeora
- `H2`: empeora
- `H3`: mejora parcial
- `H4`: empate tecnico, apenas peor

## Veredicto

Clasificacion metodologica:

- `no preferible`

Conclusion:

- `BayesianRidge` no redujo el techo practico observado en `Ridge`.
- La mejora parcial en `H3` no compensa el deterioro de `H1` y `H2`.
- La via lineal no muestra margen adicional serio bajo esta formulacion.

## Decision final

- cerrar aqui la micro-rama `E1.1 Bayesian`
- no correr `E1_1_v2_bayesian_control`
- no abrir `ARDRegression`
- no alterar el cierre principal de `E1`

## Artefactos clave

- [metricas_horizonte.json](/home/emilio/Documentos/RAdAR/experiments/runs/E1_1_v1_bayesian_base_20260402_063714/metricas_horizonte.json)
- [resumen_modeling_horizontes.json](/home/emilio/Documentos/RAdAR/experiments/runs/E1_1_v1_bayesian_base_20260402_063714/resumen_modeling_horizontes.json)
- [comparacion_vs_E1_v5_clean.json](/home/emilio/Documentos/RAdAR/experiments/runs/E1_1_v1_bayesian_base_20260402_063714/comparacion_vs_E1_v5_clean.json)
- [comparacion_vs_E1_v4_clean.json](/home/emilio/Documentos/RAdAR/experiments/runs/E1_1_v1_bayesian_base_20260402_063714/comparacion_vs_E1_v4_clean.json)
- [comparacion_vs_E1_v2_clean.json](/home/emilio/Documentos/RAdAR/experiments/runs/E1_1_v1_bayesian_base_20260402_063714/comparacion_vs_E1_v2_clean.json)
