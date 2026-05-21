# Transicion de Ridge Limpio a Huber Limpio

## Objetivo

Construir y correr la familia `E2` (`Huber` / regresion robusta) respetando exactamente la disciplina metodologica que ya quedo validada en Ridge limpio. No quiero un experimento "parecido"; quiero la continuacion directa del pipeline limpio de `E1`.

## Punto de partida obligatorio

Tomar como referencia tecnica principal:

- el script `run_e1_ridge_clean.py`
- la logica de evaluacion temporal limpia en `evaluation.py`
- el `experiment_logger.py`
- el mismo dataset maestro y la misma estructura de artefactos

## Referencia experimental concreta

Usar como baseline de comparacion principal:

- `E1_v5_clean` como mejor Ridge global

y secundariamente:

- `E1_v4_clean` como Ridge mas parsimonioso

## Configuracion base que debe heredarse inicialmente de `E1_v5_clean`

- `target_mode = nivel`
- `feature_mode = corr`
- `lags = 1,2,3,4,5,6`
- `transform_mode = standard`
- `horizons = 1,2,3,4`
- `initial_train_size = 40`
- `inner_splits = 3`
- validacion externa = `walk-forward expanding`
- mismo dataset maestro
- misma funcion de perdida Radar
- mismo calculo de metricas por horizonte
- mismo esquema de logging al grid y carpeta `runs`

## Muy importante: continuidad metodologica y control de leakage

Quiero que el agente preserve explicitamente las mismas barreras anti-leakage que ya se introdujeron en Ridge limpio.

Reglas obligatorias:

1. Prohibido hacer tuning global con toda la serie antes del walk-forward.
2. Prohibido seleccionar features usando informacion del fold de test.
3. Prohibido ajustar escalado, winsorizacion u otra transformacion con datos futuros.
4. Todo lo que dependa de los datos debe calcularse solo con el `train` disponible en cada fold externo.
5. Si Huber necesita tuning de hiperparametros, ese tuning debe ocurrir dentro del fold externo, no fuera.

## Implementacion esperada

1. Crear un nuevo script:

- `run_e2_huber_clean.py`

2. Ese script debe reutilizar al maximo el esqueleto de `run_e1_ridge_clean.py`:

- `parse_args`
- loop por horizontes
- armado de `modeling_df`
- guardado de predicciones
- guardado de features seleccionadas
- guardado de resumen por horizonte
- guardado de tuning por fold externo
- logging al grid y a `run summary`
- snapshot del script
- `parametros_run.json`
- `metadata_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`

3. No reescribir innecesariamente logica ya resuelta.
Reutilizar funciones existentes del pipeline para:

- construccion de dataset
- ingenieria de features
- evaluacion de metricas
- logging
- calculo de `loss_h`
- guardado de artefactos

4. Si hace falta una nueva funcion en `evaluation.py` para Huber, crearla por analogia con la de Ridge limpio, no con logica paralela improvisada.

## Como debe tratarse el tuning en Huber

Huber no tiene `alpha` como Ridge, pero si puede requerir ajuste de hiperparametros robustos.
Explorar al menos:

- `epsilon`

y, si el estimador lo usa de forma relevante:

- `alpha`
- `max_iter`
- `tol`

Diseno esperado:

- construir una grilla razonable y pequena para no sobrecomplicar
- usar seleccion temporal interna con `TimeSeriesSplit` dentro del `train` de cada fold externo
- elegir el mejor set de hiperparametros con la misma metrica interna usada en Ridge limpio, inicialmente `MAE`
- guardar una traza de tuning por fold externo, equivalente a `alpha_tuning_horizontes.json`, pero adaptada a Huber

Nombre sugerido del artefacto de tuning:

- `huber_tuning_horizontes.json`

## Sobre feature selection

No cambiar todavia la estrategia base.
Para la primera corrida Huber:

- mantener `feature_mode = corr`
- calcular el filtro `corr` dentro de cada fold externo usando solo `train`
- si hay resumen de features por horizonte, conservarlo igual que en Ridge

No quiero en esta etapa:

- `feature_mode = l1`
- `feature_mode = lasso`
- cambios experimentales adicionales

Primero quiero aislar el efecto del cambio de familia: Ridge vs Huber.

## Sobre transformacion y robustez

Mantener inicialmente:

- `transform_mode = standard`

Pero quiero que el agente revise una cosa:

- confirmar si la winsorizacion actual se calcula dentro del `train` por fold o fuera
- si detecta que se calcula antes del walk-forward usando toda la serie, marcarlo explicitamente como riesgo de leakage y corregirlo antes de correr `E2`
- si ya esta encapsulada dentro del `train` de cada fold, conservarla

Esto es importante:
la robustez de Huber no debe mezclarse con una fuga silenciosa en preprocessing. Primero verificar, luego correr.

## Run inicial que debe construirse

Quiero una primera version base de Huber equivalente al mejor Ridge actual:

- `run_id = E2_v1_clean`
- `target_mode = nivel`
- `feature_mode = corr`
- `lags = 1,2,3,4,5,6`
- `transform_mode = standard`
- `horizons = 1,2,3,4`
- `initial_train_size = 40`
- `inner_splits = 3`
- `tuning_metric interno = mae`

## Que artefactos debe producir obligatoriamente

Por run:

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `huber_tuning_horizontes.json`
- `comparacion_vs_E1_v5_clean.json`

Por horizonte:

- `predicciones_h1.csv`
- `predicciones_h2.csv`
- `predicciones_h3.csv`
- `predicciones_h4.csv`

Si aplica seleccion de variables:

- `features_seleccionadas_h1.csv`
- `features_seleccionadas_h2.csv`
- `features_seleccionadas_h3.csv`
- `features_seleccionadas_h4.csv`

## Trazabilidad en grid

Registrar `E2_v1_clean` en el grid con:

- `experiment_id = E2`
- `family = robusto`
- `model = huber_tscv` o nombre equivalente consistente
- comentarios claros de que es:
  `"Huber limpio con tuning temporal interno"`
- `notas_config` completas con:
  hiperparametros probados,
  `tuning_metric`,
  `inner_splits`,
  `target_mode`,
  `feature_mode`,
  `transform_mode`,
  `lags`,
  `selected_feature_count_avg`

## Comparacion obligatoria que debe entregar

No quiero solo la corrida.
Quiero comparacion consolidada entre:

- `E1_v5_clean`
- `E1_v4_clean`
- `E2_v1_clean`

La tabla comparativa debe incluir:

- `run_id`
- `family`
- `model`
- `target_mode`
- `feature_mode`
- `transform_mode`
- `lags`
- `feature_count_prom`
- `mae_promedio`
- `rmse_promedio`
- `direction_accuracy_promedio`
- `deteccion_caidas_promedio`
- `L_total_Radar`
- `observacion_breve`

## Preguntas analiticas que debe responder el agente

1. ?Huber mejora realmente a Ridge o solo cambia marginalmente?
2. ?La robustez ayuda especialmente en `H2` o `H3`?
3. ?Huber mejora `direction_accuracy` y deteccion de caidas?
4. ?Huber reduce sensibilidad a semanas anomalas?
5. ?La mejora, si existe, es operativa o solo numerica?
6. ?Huber desplaza a `E1_v5_clean` como nuevo mejor baseline limpio?
7. ?Se justifica seguir abriendo una mini-rama `E2_v2`, `E2_v3`, etc., o pasar a la siguiente familia?

## Criterio de decision

No declarar victoria por una sola metrica.
Priorizar:

1. `L_total_Radar`
2. desempeno en `H2` y `H3`
3. estabilidad de `H1` y `H4`
4. `direction_accuracy`
5. `deteccion_caidas`
6. parsimonia y trazabilidad

## Condicion de calidad antes de dar por valida la corrida

Antes de correr, el agente debe revisar y declarar explicitamente:

- que no hay leakage en tuning
- que no hay leakage en seleccion de features
- que no hay leakage en transformaciones estadisticas
- que partes se reutilizaron de Ridge
- que partes si se cambiaron especificamente para Huber

## Formato de entrega que quiero del agente

1. Que reutilizo exactamente del pipeline Ridge
2. Que cambio exactamente para Huber
3. Que reviso respecto a leakage
4. Comando exacto ejecutado
5. `Run_id` final
6. Tabla comparativa
7. Lectura metodologica
8. Decision final: seguir afinando Huber o pasar a la siguiente familia
