# Plan Inicial E3 Random Forest

Fecha: 2026-03-23

## Referencias de comparacion

- principal: `E1_v5_clean`
- secundaria parsimoniosa: `E1_v4_clean`
- referencia robusta cerrada: `E2_v3_clean`

La referencia principal es `E1_v5_clean` porque sigue siendo el mejor baseline limpio global por `L_total_Radar`.

## Corridas iniciales propuestas

### E3_v1_clean

Configuracion base:

- `target_mode=nivel`
- `feature_mode=corr`
- `lags=1,2,3,4,5,6`
- `initial_train_size=40`
- `horizons=1,2,3,4`
- `n_estimators=400`
- `max_depth=6`
- `min_samples_leaf=2`
- `min_samples_split=4`
- `max_features=sqrt`

Hipotesis:

Abrir la familia no lineal con una version comparable al mejor Ridge global, manteniendo parsimonia por correlacion y memoria larga.

### E3_v2_clean

Configuracion:

Todo identico a `E3_v1_clean`, salvo:

- `feature_mode=all`

Hipotesis:

Random Forest puede beneficiarse de una base de predictores mas amplia que Ridge y Huber, aprovechando no linealidades e interacciones que un filtro `corr` podria descartar.

## Regla de comparacion

No declarar victoria por una sola metrica.

Priorizar:

1. `L_total_Radar`
2. `H2` y `H3`
3. estabilidad de `H1` y `H4`
4. `direction_accuracy`
5. `deteccion_caidas`

## Continuidad

Si `E3_v1_clean` o `E3_v2_clean` muestran margen real frente a Ridge, la continuidad natural es:

- `E4_v1_clean` XGBoost
- `E5_v1_clean` CatBoost
