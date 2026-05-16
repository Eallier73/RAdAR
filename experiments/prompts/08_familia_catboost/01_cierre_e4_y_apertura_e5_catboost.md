Prompt para el agente
Nombre: Cierre formal de E4 y apertura de E5 CatBoost

## Objetivo general de esta tarea

1. Cerrar formalmente la familia `E4` en terminos metodologicos, documentales y de trazabilidad.
2. Confirmar con base en resultados que no se justifica seguir expandiendo `E4` base.
3. Dejar el proyecto correctamente alineado con la continuidad real del plan por familias.
4. Empezar la familia `E5` CatBoost con el mismo marco limpio temporal y con script por familia, no por corrida.
5. Dejar explicitamente reconocidas como familias pendientes previas al stacking:
   - `run_e6_arimax.py`
   - `run_e7_prophet.py`
   - `run_e8_hibrido_residuales.py`
6. Entregar tanto el cierre analitico como los cambios tecnicos y los comandos exactos necesarios.

## Contexto metodologico que debe respetarse

El proyecto Radar ya tiene un marco experimental definido y no debe romperse.

Se debe respetar estrictamente:

- validacion temporal correcta
- horizontes `1, 2, 3 y 4`
- `walk-forward expanding` o equivalente correcto segun la familia
- tuning interno temporal cuando aplique
- calculo de metricas Radar ya existentes
- trazabilidad completa por corrida
- mismo dataset maestro
- compatibilidad con el tracker/grid actual
- no leakage
- no validacion aleatoria simple
- no duplicar scripts por mini experimento
- si un script por familia de modelo

La arquitectura objetivo es por familias, no por corridas individuales.

## Estado vigente del proyecto

Tomar como referencias consolidadas:

- `E1_v5_clean` como mejor Ridge limpio global por `L_total_Radar`
- `E1_v4_clean` como referencia parsimoniosa y equilibrada
- `E2_v3_clean` como mejor Huber interno, pero familia cerrada
- `E3_v2_clean` como mejor familia no lineal base actual
- `E4_v1_clean` como mejor run interno de `E4`
- `E4_v2_clean` no mejoro a `E4_v1_clean`
- `E4_v3_clean` deterioro fuertemente la familia
- `E4` quedo cerrada con evidencia suficiente
- la infraestructura de auditoria y preparacion para stacking ya esta lista, pero todavia no se abre `E9`

## Decision sobre continuidad de familias

No anadir por ahora una familia nueva fuera del plan original.

Si continuar con las familias pendientes ya previstas en la arquitectura por familias.

Las familias pendientes a considerar antes de stacking son:

- `run_e5_catboost.py`
- `run_e6_arimax.py`
- `run_e7_prophet.py`
- `run_e8_hibrido_residuales.py`

Solo se puede contradecir esto si aparece un hueco metodologico muy fuerte y demostrable.

## Prioridad operativa de continuidad

La prioridad de esta tarea debe quedar definida asi:

1. cerrar formalmente `E4`
2. dejar operable `E5` CatBoost como siguiente familia a correr
3. dejar explicitamente mapeada la continuidad metodologica hacia `E6`, `E7` y `E8`
4. no abrir stacking todavia en esta tarea

## Orden correcto de familias pendientes

Tras cerrar `E4`, el orden de continuidad recomendado debe quedar explicitamente asentado asi:

1. `E5` CatBoost
2. `E6` ARIMAX
3. `E7` Prophet
4. `E8` hibrido residual
5. `E9` stacking

Papel metodologico de cada una:

- `E5` CatBoost: no lineal tabular alternativo a Random Forest y XGBoost
- `E6` ARIMAX: serie temporal con estructura autoregresiva y variables exogenas
- `E7` Prophet: baseline temporal estructurado con tendencia/estacionalidad y eventual regresion exogena si aplica
- `E8` hibrido residual: combinacion secuencial entre modelo base y correccion del error
- `E9` stacking: meta-modelo final una vez contrastadas suficientes familias base

## Fase 1. Cierre formal de E4

Revisar los artefactos ya existentes de:

- `E4_v1_clean`
- `E4_v2_clean`
- `E4_v3_clean`

Confirmar que no hace falta correr mas variantes base inmediatas de `E4`.

Registrar oficialmente:

- ganador interno de `E4`: `E4_v1_clean`
- `E4_v2_clean` no justifica seguir por `feature_mode=corr`
- `E4_v3_clean` muestra que `target_mode=delta` deteriora fuertemente esta familia en su formulacion actual
- `E4` muestra senal no lineal, pero no suficiente para desplazar a `E1_v5_clean`
- `E4` tampoco desplaza a `E3_v2_clean` como mejor no lineal base actual
- no se justifica seguir explorando `E4` base con pequenas variantes cosmeticas

Dejar explicitamente documentado:

- que `E4` fue evaluada bajo esquema limpio temporal
- que no mostro ventaja suficiente frente a Ridge
- que tampoco supero a la mejor no lineal base disponible
- que la familia queda cerrada en su rama base actual
- que no se cancelan futuras ideas de boosting en abstracto, pero si se cierra la rama `E4` base ya explorada

## Fase 2. Arranque de la siguiente familia

Dejar operable `run_e5_catboost.py` o adaptarlo al estandar actual.

Debe aceptar por CLI como minimo:

- `--run-id`
- `--target-mode`
- `--feature-mode`
- `--lags`
- `--initial-train-size`
- `--horizons`
- `--reference-run-id`
- `--iterations`
- `--depth`
- `--learning-rate`
- `--l2-leaf-reg`
- `--subsample` si aplica
- `--loss-function` si aplica
- `--random-seed`

El diseno debe conservar:

- estructura homogenea de familia
- `parse_args()`
- `build_estimator()`
- carga de dataset maestro
- construccion del model frame
- validacion temporal correcta
- calculo de metricas Radar
- guardado de predicciones
- guardado de metricas
- registro en tracker
- `finalize` del run con trazabilidad suficiente

## Corridas iniciales que deben quedar listas

Como minimo, deben quedar listas:

### `E5_v1_clean`

- `target_mode=nivel`
- `feature_mode=all`
- `lags=1,2,3,4,5,6`
- `horizons=1,2,3,4`
- CatBoost base razonable y conservador

### `E5_v2_clean`

- mismo diseno que `E5_v1_clean`
- cambiando solo `feature_mode=corr`

No abrir `target_mode=delta` en esta etapa salvo razon metodologica fuerte.

## Comparabilidad obligatoria

Toda nueva corrida de `E5` debe ser comparable al menos contra:

- `E1_v4_clean`
- `E1_v5_clean`
- `E2_v3_clean`
- `E3_v2_clean`
- `E4_v1_clean`

Referencias esperadas:

- `E1_v5_clean` como referencia principal global
- `E1_v4_clean` como referencia parsimoniosa
- `E3_v2_clean` como referencia no lineal base vigente
- `E4_v1_clean` como referencia de boosting ya explorado
- `E2_v3_clean` como referencia robusta historica

## Restricciones

- No inventar rutas si ya hay modulos equivalentes.
- No cambiar la logica metodologica central de Radar.
- No usar validacion aleatoria.
- No usar informacion futura para seleccion de variables.
- No seguir expandiendo `E4` base.
- No abrir stacking en esta tarea.
- No abrir una familia nueva fuera del plan.

## Entregables esperados

La respuesta final debe incluir:

1. resumen ejecutivo
2. cierre formal de `E4`
3. cambios tecnicos realizados para la arquitectura por familias
4. nueva familia `E5`
5. plan inicial de corridas `E5`
6. comparacion y referencias
7. riesgos o puntos metodologicos delicados
8. veredicto operativo final

## Criterio de exito

El trabajo estara bien hecho si:

- `E4` queda oficialmente cerrada y fuera de expansion base
- el proyecto queda alineado con la arquitectura por familias
- existe un script `E5` consistente con esa arquitectura
- `E5` puede correrse desde terminal sin editar codigo a mano
- la nueva familia conserva comparabilidad total con `E1/E2/E3/E4`
- queda claro cual es el siguiente experimento concreto a ejecutar
- queda explicito que no hizo falta anadir una familia nueva fuera del plan
