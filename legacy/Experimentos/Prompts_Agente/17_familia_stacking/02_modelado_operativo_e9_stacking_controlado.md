# Instruccion para el agente: modelado operativo de E9 sobre tabla curada

Quiero que implementes la primera version operativa de la familia `E9` del proyecto Radar como `stacking` clasico controlado por horizonte, usando la tabla ya curada para `E9` y manteniendo continuidad metodologica total con el resto del pipeline experimental.

## Contexto ya resuelto y que NO debes reabrir

La fase de curacion de `E9` ya quedo cerrada.
No quiero que vuelvas a discutir que runs entran o salen salvo que detectes una inconsistencia tecnica grave.

La logica ya definida es:

- `E9` en esta etapa = stacking clasico controlado
- NO es gating contextual
- NO es mezcla oportunista ex post
- NO es `E10`

La tabla curada ya existe y debe tratarse como insumo oficial de esta etapa.

## Fuente de datos para E9

Debes leer directamente la copia curada:

- `tabla_maestra_experimentos_radar_e9_curada.xlsx`

Y usar como fuente por horizonte las hojas:

- `E9_base_h1`
- `E9_base_h2`
- `E9_base_h3`
- `E9_base_h4`

Cada hoja ya contiene, como minimo:

- `fecha`
- `y_true`
- columnas de prediccion por modelo base
- `n_modelos_disponibles`
- `fila_completa`
- `cobertura_modelos_fila`

## Candidatos ya aprobados por horizonte

### H1
- `E1_v5_clean`
- `E5_v4_clean`
- `E3_v2_clean`
- `E2_v3_clean`

### H2
- `E1_v5_clean`
- `E5_v4_clean`
- `E2_v3_clean`
- `E7_v3_clean`

### H3
- `E1_v5_clean`
- `E5_v4_clean`
- `E3_v2_clean`
- `E7_v3_clean`

### H4
- `E1_v5_clean`
- `E5_v4_clean`
- `E3_v2_clean`
- `E2_v3_clean`

No debes cambiar esta base principal en esta etapa.

## Objetivo metodologico

Construir un ensemble de stacking sobrio, defendible y trazable, que aprenda una combinacion estable de modelos base por horizonte, sin leakage, sin overfitting y sin complejidad innecesaria.

La pregunta no es que modelo gana por fila. La pregunta es:

- si una combinacion regularizada de buenos modelos base mejora el desempeno Radar frente a correr cada modelo por separado.

## Regla central

Primera version `E9` = conservadora.

Eso implica:

- meta-modelo simple
- pocos modelos base
- solo predicciones OOF
- sin variables contextuales adicionales
- sin gating
- sin reglas oportunistas aprendidas con informacion futura

## Diseno requerido

Debes crear o adaptar:

- `run_e9_stacking.py`

y dejarlo plenamente alineado al pipeline por familias del proyecto.

Debe seguir una estructura homogenea y trazable:

1. `parse_args()`
2. carga de tabla curada E9
3. seleccion de hoja por horizonte
4. construccion de dataset de stacking
5. validacion temporal walk-forward expanding
6. entrenamiento del meta-modelo en cada fold
7. generacion de predicciones OOF del ensemble
8. calculo de metricas Radar por horizonte
9. guardado de artefactos
10. registro completo en tracker y finalize del run

## Regla critica de limpieza metodologica

NO debes entrenar el meta-modelo usando filas incompletas en esta primera version.

La primera version de `E9` debe trabajar solo con:

- `fila_completa == True`

Razon:

- evita imputaciones arbitrarias
- evita sesgos raros por arranque desigual entre modelos
- deja una linea base limpia de stacking clasico

## Meta-modelo inicial obligatorio

La primera version debe usar un meta-modelo simple y regularizado.

Ruta preferida:

- `Ridge`

Ruta aceptable:

- `Huber`

No usar en esta primera corrida:

- `XGBoost`
- `CatBoost`
- `RandomForest`
- redes
- modelos complejos de mezcla

## Features del meta-modelo

Para esta primera version, por horizonte, las unicas features deben ser las columnas de prediccion base de los candidatos aprobados para ese horizonte.

No anadir todavia:

- fecha codificada
- disagreement features
- contexto temporal
- spreads entre modelos
- ranking por fila
- banderas externas

## Target del meta-modelo

Usar:

- `y_true`

como target directo del ensemble por horizonte.

## Validacion obligatoria

La validacion debe ser:

- temporal
- expanding
- comparable con el resto del proyecto

No usar:

- `shuffle`
- `KFold` aleatorio
- `train/test` random
- CV estandar sin respeto temporal

## Tuning del meta-modelo

Si el meta-modelo es Ridge:

- hacer tuning interno temporal de `alpha` dentro de cada fold externo
- exactamente igual en espiritu a la familia Ridge limpia
- el test externo no participa en el tuning

Grid sugerido:

- `np.logspace(-4, 4, 40)`

Metrica de tuning preferida:

- `mae`

## Parametros CLI esperados

Como minimo:

- `--run-id`
- `--reference-run-id`
- `--table-path`
- `--horizons`
- `--initial-train-size`
- `--meta-model`
- `--alpha-grid-size`
- `--inner-splits`
- `--alpha-selection-metric`
- `--use-only-complete-rows`

Defaults razonables:

- `meta-model = ridge`
- `use-only-complete-rows = true`

## Artefactos obligatorios por run

Quiero como minimo:

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `predicciones_h1.csv`
- `predicciones_h2.csv`
- `predicciones_h3.csv`
- `predicciones_h4.csv`
- `alpha_tuning_horizontes.json`
- `stacking_features_h1.csv`
- `stacking_features_h2.csv`
- `stacking_features_h3.csv`
- `stacking_features_h4.csv`

## Regla interpretativa

No declarar exito de `E9` por una sola metrica aislada.

La lectura debe priorizar:

1. `L_total_Radar`
2. desempeno en `H2` y `H3`
3. estabilidad de `H1` y `H4`
4. `direction_accuracy`
5. `deteccion_caidas`

## Criterio de exito

El trabajo estara bien hecho si:

- `E9` se puede correr desde terminal sin editar manualmente el script
- usa directamente la tabla curada por horizonte
- mantiene trazabilidad completa
- evita leakage
- produce una comparacion clara contra los mejores modelos base
- permite decidir si `E9` merece continuidad o si hay que pasar directamente a `E10`
