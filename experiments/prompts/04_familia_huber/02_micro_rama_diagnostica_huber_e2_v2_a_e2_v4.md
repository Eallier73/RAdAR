# Micro-rama Diagnostica de Huber

## Objetivo

Abrir una micro-rama diagnostica de Huber, estrictamente controlada y comparable, para responder si el mal resultado de `E2_v1_clean` se debe a:

1. convergencia incompleta
2. memoria larga (`lags 1..6`)
3. combinacion `feature_mode=corr` con `lags 1..6`

## Principio de continuidad

Estas corridas deben reutilizar exactamente la infraestructura limpia ya validada:

- `run_e2_huber_clean.py`
- evaluacion temporal limpia
- `walk-forward expanding`
- tuning interno temporal por fold externo
- mismo dataset maestro
- misma funcion de perdida Radar
- mismo `experiment_logger`
- mismo formato de artefactos y logging al grid

## Control de leakage

Antes de correr cualquier version:

- revisar `transform_mode=standard`
- revisar si existe winsorizacion u otra transformacion adicional
- confirmar que `feature_mode=corr` se calcula con solo train por fold externo
- confirmar que `modeling_df` no incorpora informacion futura por desplazamientos incorrectos

No se permite:

- tuning global fuera del walk-forward
- seleccion de features con informacion del test
- ajuste de escalado o transformaciones con datos futuros

## Corridas de la micro-rama

### E2_v2_clean

Control de convergencia.

Mantener todo igual a `E2_v1_clean`, salvo:

- ampliar `max_iter`
- explorar una grilla minima de `tol`

Sugerencia minima:

- `max_iter = 5000`
- `tol in [1e-4, 1e-3]`

### E2_v3_clean

Prueba sin memoria larga.

Mantener todo igual a `E2_v1_clean`, salvo:

- `lags = 1,2,3,4`

### E2_v4_clean

Prueba con base completa de predictores.

Mantener todo igual a `E2_v1_clean`, salvo:

- `feature_mode = all`

## Regla de oro

Cada corrida cambia una sola cosa importante:

- `E2_v2_clean`: convergencia
- `E2_v3_clean`: lags
- `E2_v4_clean`: feature_mode

No abrir subvariantes.

## Artefactos obligatorios

Por cada corrida:

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `huber_tuning_horizontes.json`
- `comparacion_vs_E1_v5_clean.json`
- `comparacion_vs_E2_v1_clean.json`

Y por horizonte:

- `predicciones_h1.csv`
- `predicciones_h2.csv`
- `predicciones_h3.csv`
- `predicciones_h4.csv`
- `features_seleccionadas_h1.csv`
- `features_seleccionadas_h2.csv`
- `features_seleccionadas_h3.csv`
- `features_seleccionadas_h4.csv`

## Comparacion consolidada esperada

Comparar:

- `E1_v4_clean`
- `E1_v5_clean`
- `E2_v1_clean`
- `E2_v2_clean`
- `E2_v3_clean`
- `E2_v4_clean`

## Preguntas analiticas

1. ?`E2_v2_clean` demuestra que el problema era convergencia?
2. ?`E2_v3_clean` sugiere que Huber funciona mejor con memoria corta?
3. ?`E2_v4_clean` sugiere que Huber estaba siendo perjudicado por `feature_mode=corr`?
4. ?Alguna version de Huber se vuelve competitiva contra `E1_v5_clean`?
5. ?Alguna version de Huber supera sustantivamente a `E1_v4_clean`?
6. ?Hay mejora operativa o solo numerica?
7. ?Hay razon real para seguir explorando Huber despues de estas tres corridas?

## Decision final esperada

Si ninguna corrida cumple una mejora clara y defendible:

- cerrar formalmente `E2`
- documentar que Huber fue evaluado bajo esquema limpio temporal y no mostro ventaja suficiente
- pasar a la siguiente familia del plan original
