# Apertura E8 Hibrido Residual

Quiero que abras e implementes la familia `E8 = hibrido residual` dentro del pipeline experimental de Radar con comparabilidad estricta contra `E1-E7`.

## Objetivo

Evaluar si un esquema de dos etapas:

`y_pred_final = y_pred_base + y_pred_residual`

puede mejorar a un modelo base fuerte sin introducir leakage temporal ni selection snooping.

## Regla metodologica central

La familia `E8` no puede construirse pegando a mano los mejores horizontes historicos. Debe definirse como una regla reproducible previa y evaluarse como una nueva familia completa bajo:

- `walk-forward expanding`
- mismos horizontes `1,2,3,4`
- mismo dataset maestro
- mismas metricas Radar
- mismo `L_total_Radar`
- misma trazabilidad por run

## Restriccion critica

El learner residual debe entrenarse con residuales temporalmente validos. Esta prohibido usar residuales in-sample optimistas como target del segundo modelo.

## Variantes canonicas

### E8_v1_clean

- base: `E1_v5_clean` o configuracion equivalente reproducible
- residual learner: `CatBoost`
- hipotesis: Ridge deja no linealidad remanente aprovechable

### E8_v2_clean

- base: `E5_v4_clean` o configuracion equivalente reproducible
- residual learner: `Ridge` parsimonioso
- hipotesis: CatBoost deja residuales mas suaves que un segundo modelo simple puede corregir

### E8_v3_clean

- base: `E5_v4_clean` o equivalente reproducible
- residual learner: `Prophet` parsimonioso o variante temporal controlada
- hipotesis: parte del error remanente conserva estructura temporal o changepoints

## Artefactos minimos por run

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `predicciones_h1.csv` a `predicciones_h4.csv`
- `predicciones_base_h1.csv` a `predicciones_base_h4.csv`
- `predicciones_residual_h1.csv` a `predicciones_residual_h4.csv`
- `residuales_entrenamiento_h1.csv` a `residuales_entrenamiento_h4.csv`
- artefactos de comparacion contra referencias

## Regla de honestidad

Si el residual learner no agrega valor real, la conclusion correcta es cerrar o dejar en pausa la familia, no seguir ajustando hasta que gane.
