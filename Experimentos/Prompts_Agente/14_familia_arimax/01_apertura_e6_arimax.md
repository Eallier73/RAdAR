# Apertura Estrictamente Controlada de E6 tras cierre practico de E5

Continua el pipeline experimental del proyecto Radar con la familia `E6 = ARIMAX`, sin improvisar, sin abrir ramas extra y sin alterar el marco metodologico ya establecido.

## Punto exacto de continuidad

La familia `E5 = CatBoost` ya llego a un punto suficientemente maduro como para dejar un campeon interno claro:

- `E5_v4_clean`
- modelo: `catboost_regressor`
- `target_mode = nivel`
- `feature_mode = all`
- `lags = 1,2,3,4,5,6`
- validacion temporal comparable al resto
- tuning temporal interno acotado
- `L_total_Radar = 0.247788`

Lectura ya establecida de `E5`:

- `E5` si funciono
- `E5_v4_clean` es el campeon interno de la familia
- CatBoost es la mejor familia no lineal tabular del proyecto hasta ahora
- `E5_v4_clean` supera a `E1_v4_clean`
- `E5_v4_clean` supera a `E3_v2_clean`
- `E5_v4_clean` supera a `E4_v1_clean`
- `E5_v4_clean` no supera a `E1_v5_clean`
- la segunda ola focal de tuning ya no mejoro de forma util
- no conviene seguir con microvariantes en la misma zona de hiperparametros

Por tanto, el siguiente paso operativo no es seguir exprimiendo `E5`, sino abrir la siguiente familia del plan con una hipotesis distinta.

## Familia a abrir

Debes abrir:

- `E6 = ARIMAX`
- runner objetivo: `run_e6_arimax.py`

No inventes otra nomenclatura.
No abras una rama paralela con otro nombre.
No trates `E6` como variante de `E5`.
`E6` es una familia nueva y debe quedar claramente separada como familia de series de tiempo con exogenas dentro de la arquitectura por familias del proyecto.

## Objetivo del experimento

Quiero una apertura limpia, comparable y metodologicamente muy disciplinada para evaluar si una formulacion de series de tiempo con exogenas puede competir con los mejores resultados tabulares ya observados en Radar.

Las metas concretas son:

- evaluar si una estructura autoregresiva explicita mejora la modelacion temporal del indice;
- aprovechar exogenas del Radar sin perder comparabilidad con las familias previas;
- medir si ARIMAX ofrece una lectura mas estable en horizontes intermedios y largos;
- probar si una familia de series con exogenas puede aportar valor operativo real, no solo ajuste numerico;
- comparar formalmente contra:
  - `E1_v5_clean`
  - `E1_v4_clean`
  - `E5_v4_clean`
  - `E3_v2_clean`
  - `E4_v1_clean`

## Hipotesis metodologica

La hipotesis de apertura de `E6` es esta:

Los modelos tabulares ya demostraron que existe senal predictiva util en el problema Radar, pero no modelan de forma explicita la dinamica autoregresiva del proceso. `ARIMAX` podria capturar mejor la estructura temporal del indice al combinar memoria autoregresiva con variables exogenas, y eso podria traducirse en una mejora de estabilidad o desempeno operativo, especialmente en `H2`, `H3` y `H4`.

Lo que quiero probar no es solo si baja `MAE`.
Quiero saber si una familia temporal estructurada puede volverse competitiva dentro del criterio Radar completo.

## Restricciones

- validacion temporal estricta y comparable;
- cero leakage;
- cero validacion aleatoria;
- no `auto_arima` masivo;
- no mezclar muchos cambios a la vez;
- exactamente dos corridas:
  - `E6_v1_clean`
  - `E6_v2_clean`

## Corridas requeridas

### E6_v1_clean

- `target_mode = nivel`
- `feature_mode = corr`
- `lags = 1,2,3,4,5,6`
- `horizons = 1,2,3,4`
- baseline `ARIMAX` interpretable

Comando objetivo:

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e6_arimax.py \
  --run-id E6_v1_clean \
  --reference-run-id E1_v5_clean \
  --extra-reference-run-ids E1_v4_clean,E5_v4_clean,E3_v2_clean,E4_v1_clean \
  --hypothesis-note arimax_baseline_corr \
  --target-mode nivel \
  --feature-mode corr \
  --lags 1,2,3,4,5,6 \
  --initial-train-size 40 \
  --horizons 1,2,3,4 \
  --ar-order 1 \
  --diff-order 0 \
  --ma-order 1 \
  --trend c
```

### E6_v2_clean

Mantener todo igual y cambiar solo una cosa importante.
Preferencia: ampliar exogenas de `corr` a `all`.

Comando objetivo:

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e6_arimax.py \
  --run-id E6_v2_clean \
  --reference-run-id E1_v5_clean \
  --extra-reference-run-ids E1_v4_clean,E5_v4_clean,E3_v2_clean,E4_v1_clean,E6_v1_clean \
  --hypothesis-note arimax_all_vs_corr \
  --target-mode nivel \
  --feature-mode all \
  --lags 1,2,3,4,5,6 \
  --initial-train-size 40 \
  --horizons 1,2,3,4 \
  --ar-order 1 \
  --diff-order 0 \
  --ma-order 1 \
  --trend c
```

## Formato de cierre esperado

La entrega final debe quedar estructurada asi:

- `A. Que hiciste`
- `B. Resultado de las corridas`
- `C. Interpretacion`
- `D. Veredicto`
- `E. Siguiente paso recomendado`

