## Nombre

Implementacion y corrida canonica de `E10_v1_clean`

## Objetivo

Abrir la primera corrida operativa de `E10` como meta-selector duro retrospectivo, por horizonte, con control metodologico estricto y comparacion explicita contra:

- `selector_fijo`
- `E1_v5_clean`
- `E9_v2_clean`

## Definicion de la corrida

- familia: `E10`
- run_id: `E10_v1_clean`
- tabla canonicamente usada: `tabla_e10_meta_selector_base.csv`
- target selector: `mejor_modelo_loss_radar_local`
- modelo meta: `LogisticRegression` lineal regularizado
- validacion: `walk-forward expanding`
- salida final del sistema: prediccion numerica heredada del modelo base seleccionado

## Reglas no negociables

- usar solo columnas marcadas como `feature_candidate`
- prohibir `forbidden_for_training`, `diagnostic_only`, `target_selector` e `id`
- no usar informacion futura
- no usar targets retrospectivos como features
- no reabrir la curacion E10
- no complicar el meta-modelo

## Benchmark fijo obligatorio

Construir un benchmark trivial por horizonte usando solo el tramo de entrenamiento disponible en cada fold:

- ordenar modelos base por `mean(loss_local_train)`
- elegir siempre el mejor modelo disponible en test segun ese ranking

## Artefactos obligatorios

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `resumen_ejecucion.md`
- `comparacion_vs_benchmarks.json`
- `predicciones_h1.csv` a `predicciones_h4.csv`
- `columnas_entrenamiento_h1.csv` a `columnas_entrenamiento_h4.csv`
- `columnas_excluidas_h1.csv` a `columnas_excluidas_h4.csv`
- `metricas_h1.json` a `metricas_h4.json`
- `selector_trace_h1.json` a `selector_trace_h4.json`
- `matriz_confusion_h1.json` a `matriz_confusion_h4.json`

## Cierre esperado

La corrida debe responder si la tabla E10 actual contiene señal suficiente para meta-seleccion dura sin leakage y si la mejora frente a un selector fijo y frente a los benchmarks centrales es:

- real
- parcial
- fragil
- o todavia no justificable
