# Continuacion estrictamente controlada de E4 tras E4_v1_clean

## Punto exacto de continuidad

Ya existe una apertura formal de `E4` y ya se corrio el baseline:

- `E4_v1_clean`
- modelo: `xgboost_regressor`
- `target_mode = nivel`
- `feature_mode = all`
- `lags = 1,2,3,4,5,6`
- `initial_train_size = 40`
- `horizons = 1,2,3,4`
- sin escalado
- sin tuning interno
- validacion externa temporal `walk-forward expanding`

Resultado de `E4_v1_clean`:

- `L_total_Radar = 0.283934`

Referencias vigentes:

- `E1_v5_clean = 0.243442`
- `E1_v4_clean = 0.253277`
- `E3_v2_clean = 0.266387`
- `E4_v1_clean = 0.283934`

## Objetivo

Correr exactamente dos variantes adicionales de `E4`, una para probar si el problema fue el exceso de variables y otra para probar si el problema fue la definicion del target.

No abrir mas de dos corridas.
No improvisar nuevas variantes.
No hacer tuning adicional.
No cambiar el marco experimental.

## Corridas obligatorias

### `E4_v2_clean`

Mantener todo igual que `E4_v1_clean` y cambiar solo:

- `feature_mode = corr`

Hipotesis:

Si el mal desempeno de `E4_v1_clean` se debio a ruido excesivo por usar `feature_mode=all`, entonces una version mas parsimoniosa con `feature_mode=corr` deberia generalizar mejor.

### `E4_v3_clean`

Mantener todo igual que `E4_v1_clean` y cambiar solo:

- `target_mode = delta`

Hipotesis:

Si boosting se adapta mejor a cambios y giros que a niveles absolutos, entonces `target_mode=delta` deberia mejorar especialmente metricas operativas y horizontes intermedios.

## Regla de control experimental

- `E4_v2_clean` cambia solo `feature_mode`
- `E4_v3_clean` cambia solo `target_mode`

Queda prohibido:

- combinar `feature_mode=corr` con `target_mode=delta`
- abrir `E4_v4_clean`
- abrir variantes con otros hiperparametros
- abrir tuning interno
- abrir subramas adicionales

## Restricciones metodologicas

Conservar exactamente:

- validacion externa `walk-forward expanding`
- horizontes `1,2,3,4`
- mismo dataset maestro
- misma construccion de `model frame`
- misma evaluacion Radar
- mismo calculo de `L_total_Radar`
- misma trazabilidad de artefactos
- comparabilidad directa con `E4_v1_clean`, `E3_v2_clean`, `E1_v4_clean` y `E1_v5_clean`

Queda prohibido:

- validacion aleatoria
- fuga temporal
- uso de informacion futura en seleccion o evaluacion
- tuning con el test externo
- maquillar la lectura de resultados

## Hiperparametros fijos

Mantener exactamente:

- `n_estimators = 300`
- `learning_rate = 0.05`
- `max_depth = 3`
- `subsample = 0.8`
- `colsample_bytree = 0.8`
- `min_child_weight = 3`
- `reg_alpha = 0.0`
- `reg_lambda = 1.0`
- `random_state = 42`

## Script

Usar:

- `run_e4_xgboost.py`

## Comandos

### `E4_v2_clean`

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e4_xgboost.py \
  --run-id E4_v2_clean \
  --reference-run-id E1_v5_clean \
  --extra-reference-run-ids E1_v4_clean,E3_v2_clean,E4_v1_clean \
  --hypothesis-note boosting_corr_vs_all \
  --target-mode nivel \
  --feature-mode corr \
  --lags 1,2,3,4,5,6 \
  --initial-train-size 40 \
  --horizons 1,2,3,4 \
  --n-estimators 300 \
  --learning-rate 0.05 \
  --max-depth 3 \
  --subsample 0.8 \
  --colsample-bytree 0.8 \
  --min-child-weight 3 \
  --reg-alpha 0.0 \
  --reg-lambda 1.0 \
  --random-state 42
```

### `E4_v3_clean`

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e4_xgboost.py \
  --run-id E4_v3_clean \
  --reference-run-id E1_v5_clean \
  --extra-reference-run-ids E1_v4_clean,E3_v2_clean,E4_v1_clean \
  --hypothesis-note boosting_delta_vs_nivel \
  --target-mode delta \
  --feature-mode all \
  --lags 1,2,3,4,5,6 \
  --initial-train-size 40 \
  --horizons 1,2,3,4 \
  --n-estimators 300 \
  --learning-rate 0.05 \
  --max-depth 3 \
  --subsample 0.8 \
  --colsample-bytree 0.8 \
  --min-child-weight 3 \
  --reg-alpha 0.0 \
  --reg-lambda 1.0 \
  --random-state 42
```

## Analisis obligatorio

Comparar explicitamente:

- `E1_v5_clean`
- `E1_v4_clean`
- `E3_v2_clean`
- `E4_v1_clean`
- `E4_v2_clean`
- `E4_v3_clean`

Respuestas requeridas:

- si `E4_v2_clean` mejora a `E4_v1_clean`
- si `E4_v3_clean` mejora a `E4_v1_clean`
- si alguna supera a `E3_v2_clean`
- si alguna alcanza o supera a `E1_v4_clean`
- si alguna alcanza o supera a `E1_v5_clean`
- cual variante aporta mas y en que horizonte
- si ayudo mas reducir variables o cambiar el target
- si `E4` sigue viva o queda cerrada

## Orden de lectura

Priorizar interpretacion en este orden:

1. `L_total_Radar`
2. desempeno en `H2` y `H3`
3. estabilidad en `H1` y `H4`
4. `direction_accuracy`
5. `deteccion_caidas`
6. parsimonia / complejidad

## Criterios de decision

### `E4` sigue viva

Solo si alguna variante:

- mejora de forma clara a `E4_v1_clean`
- y ademas supera a `E3_v2_clean`

### `E4` mejora internamente pero no compite

Si alguna variante:

- mejora a `E4_v1_clean`
- pero no supera a `E3_v2_clean`

### `E4` se cierra

Si ninguna variante:

- mejora de forma sustantiva a `E4_v1_clean`
- o ninguna supera a `E3_v2_clean`

Entonces `E4` queda cerrada con evidencia suficiente.
