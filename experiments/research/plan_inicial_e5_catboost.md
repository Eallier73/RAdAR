# Plan Inicial E5 CatBoost

Fecha: `2026-03-30`

## Objetivo

Abrir la familia `E5` CatBoost bajo el mismo marco limpio temporal del proyecto Radar y contrastarla directamente contra:

- `E1_v5_clean`
- `E1_v4_clean`
- `E3_v2_clean`
- `E4_v1_clean`
- `E2_v3_clean`

## Corrida ejecutada

### E5_v1_clean

Configuracion:

- modelo: `catboost_regressor`
- target_mode: `nivel`
- feature_mode: `all`
- lags: `1,2,3,4,5,6`
- horizons: `1,2,3,4`
- initial_train_size: `40`
- iterations: `300`
- depth: `5`
- learning_rate: `0.05`
- l2_leaf_reg: `3.0`
- subsample: `0.8`
- loss_function: `RMSE`
- random_seed: `42`
- sin escalado
- sin tuning interno
- sin variables categoricas explicitas

Comando:

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/src/modeling/run_e5_catboost.py \
  --run-id E5_v1_clean \
  --reference-run-id E1_v5_clean \
  --extra-reference-run-ids E1_v4_clean,E2_v3_clean,E3_v2_clean,E4_v1_clean \
  --hypothesis-note catboost_base_tabular_all \
  --target-mode nivel \
  --feature-mode all \
  --lags 1,2,3,4,5,6 \
  --initial-train-size 40 \
  --horizons 1,2,3,4 \
  --iterations 300 \
  --depth 5 \
  --learning-rate 0.05 \
  --l2-leaf-reg 3.0 \
  --subsample 0.8 \
  --loss-function RMSE \
  --random-seed 42
```

Resultado global:

- `L_total_Radar = 0.255259`

Lectura inicial:

- mejora a `E3_v2_clean`
- mejora a `E4_v1_clean`
- queda muy cerca de `E1_v4_clean`
- no supera a `E1_v5_clean`

## Siguiente corrida recomendada

### E5_v2_clean

Hipotesis:

Si CatBoost esta captando demasiado ruido con `feature_mode=all`, entonces una version mas parsimoniosa con `feature_mode=corr` podria mejorar estabilidad sin romper la senal que ya aparecio en `E5_v1_clean`.

Diseno:

- igual a `E5_v1_clean`
- cambia solo `feature_mode=corr`

Comando:

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/src/modeling/run_e5_catboost.py \
  --run-id E5_v2_clean \
  --reference-run-id E1_v5_clean \
  --extra-reference-run-ids E1_v4_clean,E2_v3_clean,E3_v2_clean,E4_v1_clean,E5_v1_clean \
  --hypothesis-note catboost_corr_vs_all \
  --target-mode nivel \
  --feature-mode corr \
  --lags 1,2,3,4,5,6 \
  --initial-train-size 40 \
  --horizons 1,2,3,4 \
  --iterations 300 \
  --depth 5 \
  --learning-rate 0.05 \
  --l2-leaf-reg 3.0 \
  --subsample 0.8 \
  --loss-function RMSE \
  --random-seed 42
```

## Decision abierta de la familia

- `E5` queda abierta
- `E5_v1_clean` ya justifica continuar con al menos una variante controlada mas
- no hay justificacion para abrir `target_mode=delta` en esta etapa
