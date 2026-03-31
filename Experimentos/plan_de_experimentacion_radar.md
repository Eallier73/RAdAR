# Plan de Experimentacion Radar

Fecha de actualizacion: `2026-03-30`

## Proposito

Este documento convierte el prompt original de arquitectura experimental en un plan vivo del proyecto Radar. Su funcion no es reemplazar:

- el grid experimental,
- la tabla maestra,
- la bitacora,
- ni los artefactos por run.

Su funcion es dejar por escrito:

- que se planeo originalmente,
- que si se ejecuto,
- que se cerro o se cancelo,
- por que cambio el rumbo en cada etapa,
- y cual es el plan vigente que sigue guiando los siguientes experimentos.

## Fuentes usadas para este plan

- Prompt base de arquitectura por familias:
  [01_refactor_pipeline_experimentos_por_familias.md](/home/emilio/Documentos/RAdAR/Experimentos/Prompts_Agente/01_pipeline_arquitectura/01_refactor_pipeline_experimentos_por_familias.md)
- Bitacora narrativa:
  [bitacora_experimental_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/bitacora_experimental_radar.md)
- Cierres metodologicos por familia:
  [resumen_metodologico_e1_ridge.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e1_ridge.md)
  [resumen_metodologico_e2_huber.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e2_huber.md)
  [resumen_metodologico_e3_arboles.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e3_arboles.md)
  [resumen_metodologico_e4_boosting.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e4_boosting.md)
- Auditoria maestra retrospectiva:
  [resumen_auditoria_experimentos.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_auditoria_experimentos.md)

## Principios que no cambiaron

Aunque el rumbo experimental si cambio varias veces, la disciplina metodologica base no cambio. Los experimentos vigentes deben conservar:

- validacion temporal correcta
- horizontes `1,2,3,4`
- `walk-forward expanding` o equivalente temporal correcto
- comparabilidad entre familias
- mismo dataset maestro
- metricas Radar por horizonte
- `L_total_Radar`
- trazabilidad por run y por artefacto
- prohibicion de leakage en tuning, seleccion y transformaciones

## Arquitectura original planeada

El prompt base definio una arquitectura por familias, no por corridas individuales.

Familias planeadas originalmente:

1. `E1` lineal regularizado
2. `E2` robusto
3. `E3` arboles / bagging
4. `E4` boosting
5. `E5` CatBoost
6. `E6` series de tiempo con exogenas tipo ARIMAX
7. `E7` Prophet
8. `E8` hibridos / residuales
9. `E9` stacking / ensembles

Scripts previstos en la arquitectura:

- `run_e1_ridge.py`
- `run_e2_huber.py`
- `run_e3_random_forest.py`
- `run_e4_xgboost.py`
- `run_e5_catboost.py`
- `run_e6_arimax.py`
- `run_e7_prophet.py`
- `run_e8_hibrido_residuales.py`
- `run_e9_stacking.py`

El plan original, por tanto, no era quedarse solo en Ridge. La idea era recorrer familias comparables bajo un mismo marco experimental y terminar con una capa hibrida / stacking.

## Rama paralela planificada de clasificacion

Ademas del frente principal de regresion, el proyecto ya deja planificada una rama paralela de clasificacion del movimiento del Radar.

Esta rama todavia no se ejecuto, pero queda documentada y trazable.

Familias previstas:

1. `C1` RandomForestClassifier
2. `C2` XGBoostClassifier
3. `C3` CatBoostClassifier
4. `C4` LightGBMClassifier

Objetivo:

- clasificar el cambio futuro del Radar en bandas politicamente interpretables
- mantener la misma disciplina temporal y de tracker
- dejar base comparable para una futura discusion de costos asimetricos, clasificacion ordinal o integracion con stacking

Estado actual:

- rama documentada: si
- runners por familia preparados: si
- prompts guardados: si
- corridas ejecutadas: no

Organizacion actual de la documentacion:

- `09_clasificacion_radar/` como prompt rector de la rama
- `10_clasificacion_random_forest/` para `C1`
- `11_clasificacion_xgboost/` para `C2`
- `12_clasificacion_catboost/` para `C3`
- `13_clasificacion_lightgbm/` para `C4`

## Secuencia real ejecutada hasta hoy

### Estado resumido por familia

| familia | estado actual | mejor run interno | lectura vigente |
|---|---|---|---|
| `E1` Ridge | cerrada | `E1_v5_clean` | mejor baseline global vigente |
| `E2` Huber | cerrada | `E2_v3_clean` | no competitiva frente a Ridge |
| `E3` bagging | cerrada en rama base | `E3_v2_clean` | mejor no lineal base vigente |
| `E4` Boosting | cerrada | `E4_v1_clean` | no supero a bagging ni a Ridge |
| `E5` CatBoost | abierta y madura | `E5_v4_clean` | mejor no lineal tabular actual; supera a E1_v4 pero no a E1_v5 |
| `E6` ARIMAX | debilitada | `E6_v1_clean` | apertura débil; `all` empeoró frente a `corr` |
| `E7` Prophet | abierta | `E7_v3_clean` | supera a E6 pero sigue por detrás del bloque contendiente |
| `E8` hibridos residuales | no iniciada | n/a | pendiente |
| `E9` stacking | no iniciada como modelo | n/a | preparada a nivel infraestructura |

### Referencias vigentes

- mejor global: `E1_v5_clean` con `L_total_Radar = 0.243442`
- referencia parsimoniosa: `E1_v4_clean` con `0.253277`
- mejor no lineal tabular abierta: `E5_v4_clean` con `0.247788`
- mejor no lineal base previa: `E3_v2_clean` con `0.266387`
- mejor H2 y H4 por `loss_h`: `E2_v3_clean`
- mejor H3 por `loss_h`: `E1_v2_clean`

## Que se planeo y que paso realmente

### E1 Ridge

#### Lo planeado

La familia `E1` se planeo originalmente con una secuencia amplia:

- `E1_v2`
- `E1_v3`
- `E1_v4`
- `E1_v5`
- `E1_v6`
- `E1_v7`
- `E1_v8`
- `E1_v9`
- `E1_v10`

La logica era explorar, sin salir de Ridge:

- target `nivel` vs `delta`
- `feature_mode` `all`, `corr`, `lasso`
- memoria temporal corta vs larga
- `transform_mode` `standard`, `robust`, `winsor`

#### Lo que si se hizo

Se ejecutaron y quedaron registrados:

- `E1_v1` y `E1_v2` historicos
- `E1_v2_clean`
- `E1_v3_clean`
- `E1_v4_clean`
- `E1_v5_clean`

#### Lo que no se hizo y por que

- `E1_v6_clean` y equivalentes `E1_v6..E1_v10` no se ejecutaron.

Motivo:

- `E1_v5_clean` ya dejo a Ridge cerca de su techo practico.
- `E1_v4_clean` y `E1_v5_clean` respondieron las preguntas mas importantes de la familia:
  - parsimonia
  - target
  - memoria larga
- seguir abriendo `E1_v6..E1_v10` dejaba de ser la mejor inversion marginal frente a abrir nuevas familias.

Decision formal:

- `E1` queda cerrada como familia explorada suficientemente.
- `E1_v5_clean` queda como mejor baseline global.
- `E1_v4_clean` queda como referencia parsimoniosa.

### E2 Huber

#### Lo planeado

Despues de Ridge, el plan original seguia con la familia robusta `E2`.

La micro-rama diagnostica de `E2` llego a contemplar:

- `E2_v1_clean`
- `E2_v2_clean`
- `E2_v3_clean`
- `E2_v4_clean`

#### Lo que si se hizo

Se ejecutaron:

- `E2_v1_clean`
- `E2_v2_clean`
- `E2_v3_clean`

#### Lo que no se hizo y por que

- `E2_v4_clean` no se ejecuto.

Motivo:

- `E2_v2_clean` descarto que el problema principal fuera convergencia.
- `E2_v3_clean` mostro que la memoria corta ayudaba algo.
- aun asi Huber siguio claramente por debajo de Ridge.
- ya no habia justificacion metodologica fuerte para abrir una cuarta corrida en la misma familia.

Decision formal:

- `E2` queda cerrada.
- `E2_v3_clean` es solo el ganador interno, no un nuevo baseline global.

### E3 Arboles tipo bagging

#### Lo planeado

La apertura de no lineales se planteo como familia `E3`, con idea de probar:

- baseline `Random Forest`
- variante con universo amplio de features
- variante mas aleatoria (`ExtraTrees`)
- y eventualmente una continuacion solo si aparecia una senal util real

#### Lo que si se hizo

Se ejecutaron:

- `E3_v1_clean`
- `E3_v2_clean`
- `E3_v3_clean`

#### Lo que no se hizo y por que

- `E3_v4` no se ejecuto.

Motivo:

- `E3_v2_clean` ya resolvio la pregunta principal de la familia: `Random Forest` funciona mejor con `feature_mode=all`.
- `E3_v3_clean` no mejoro a `E3_v2_clean`.
- seguir abriendo mas bagging sin una nueva hipotesis fuerte ya no estaba justificado.

Decision formal:

- `E3` queda cerrada en su rama base.
- `E3_v2_clean` queda como mejor run interno y mejor referencia no lineal base vigente.

### E4 Boosting

#### Lo planeado

Tras confirmar que la no linealidad si servia, `E4` se abrio para probar si boosting podia mejorar a bagging:

- `E4_v1_clean` baseline
- una variante parsimoniosa
- una variante `delta`
- y solo despues decidir si valia la pena expandir la familia

#### Lo que si se hizo

Se ejecutaron:

- `E4_v1_clean`
- `E4_v2_clean`
- `E4_v3_clean`

#### Lo que no se hizo y por que

- no se abrieron mas variantes
- no existe una continuacion tipo `E4_v4_clean`

Motivo:

- `E4_v1_clean` no supero a `E3_v2_clean`
- `E4_v2_clean` empeoro el global
- `E4_v3_clean` deterioro fuerte la familia con `target_mode=delta`
- ya habia evidencia suficiente para cerrar `E4` sin seguir forzando boosting

Decision formal:

- `E4` queda cerrada con evidencia suficiente.

### E5 CatBoost

#### Lo planeado

`E5` estaba prevista como la siguiente familia tabular no lineal del plan original, despues de `E4`, y antes de `E6`, `E7`, `E8` y `E9`.

#### Lo que si se hizo

Se ejecutaron:

- `E5_v1_clean`
- `E5_v2_clean`
- `E5_v3_clean`
- `E5_v4_clean`
- `E5_v5_clean`

Lectura consolidada:

- `E5_v4_clean` quedo como campeon interno de la familia.
- `E5_v4_clean` supero a `E1_v4_clean`, `E3_v2_clean` y `E4_v1_clean`.
- `E5_v4_clean` no supero a `E1_v5_clean`.
- `E5_v2_clean`, `E5_v3_clean` y `E5_v5_clean` no mejoraron al campeon.

Estado actual:

- `E5` queda abierta pero ya madura
- `E5_v4_clean` es la referencia no lineal tabular vigente
- nuevas corridas solo se justifican con hipotesis distintas, no con microvariantes locales

### E6 ARIMAX

#### Lo planeado

`E6` debia probar una familia temporal estructurada con exogenas, distinta de los tabulares y comparable con ellos bajo el mismo marco de validacion.

#### Lo que si se hizo

Se ejecutaron:

- `E6_v1_clean`
- `E6_v2_clean`

Lectura:

- `E6_v1_clean` fue una apertura debil.
- `E6_v2_clean` empeoro todavia mas.
- la parsimonia exogena ayudo frente a `all`, pero no volvio competitiva a la familia.

Estado actual:

- `E6` queda debilitada
- no es la linea principal para seguir
- conserva valor potencial solo como referencia temporal o pieza futura de hibridos

### E7 Prophet

#### Lo planeado

`E7` debia probar una familia temporal estructurada alternativa a `ARIMAX`, con foco en tendencia y changepoints, pero sin relajar la disciplina temporal del proyecto.

#### Lo que si se hizo

Se ejecutaron:

- `E7_v1_clean`
- `E7_v2_clean`
- `E7_v3_clean`

Lectura:

- `E7_v1_clean` abrio de forma decorosa, mejorando con claridad a `E6`.
- `E7_v2_clean` colapso con `feature_mode=all`; la amplitud exogena metio mucho ruido.
- `E7_v3_clean` mejoro un poco a `E7_v1_clean` con mas flexibilidad en changepoints, sobre todo en `H2/H3`.
- aun asi `E7` no alcanzo al bloque contendiente formado por `E1_v5_clean`, `E1_v4_clean`, `E5_v4_clean` y `E3_v2_clean`.

Estado actual:

- `E7` queda abierta como familia intermedia
- supera a `E6`, pero no desplaza a las referencias principales

### E8 Hibridos y E9 Stacking

#### Lo planeado

Estas familias si estaban dentro de la arquitectura original y siguen siendo la continuacion natural del plan.

#### Estado actual

- `E8` sigue pendiente, no cancelada
- `E9` no se ejecuto como modelo, pero su infraestructura preparatoria ya existe parcialmente via:
  - tabla maestra ampliada
  - `stacking_readiness`
  - `stacking_base_h1..h4`

## Por que cambio el rumbo del plan

El plan original no se abandono por desorden, sino por evidencia experimental acumulada.

### Cambio 1: primero limpiar antes de expandir

Antes de abrir muchas familias, hubo que reconstruir un baseline limpio y comparable, especialmente en Ridge.

Eso cambio el orden real de ejecucion porque:

- no servia comparar familias nuevas contra un baseline con dudas metodologicas
- primero habia que fijar una referencia limpia

### Cambio 2: cerrar familias cuando ya respondieron su pregunta

No se continuo automaticamente con todas las corridas planeadas.

Se aplico una regla mas fuerte:

- si una familia ya respondio la hipotesis principal y no se volvio competitiva, se cierra
- no se estira una familia solo por completar una secuencia nominal de runs

Por eso se cerraron:

- `E1` antes de `E1_v6..E1_v10`
- `E2` sin correr `E2_v4_clean`
- `E3` sin abrir `E3_v4`
- `E4` sin abrir mas boosting base

### Cambio 3: de explorar familias a preparar stacking

La auditoria mostro algo importante:

- distintos horizontes favorecen distintos runs
- no siempre gana la misma familia en `H1`, `H2`, `H3` y `H4`

Eso cambio la prioridad.

En vez de seguir abriendo familias sin control, se paso a construir:

- tabla maestra robusta
- ranking por horizonte
- ranking por metricas
- cobertura de predicciones
- readiness para stacking

La consecuencia es que el plan vigente ya no es solo "abrir mas modelos", sino decidir con mas criterio entre:

- abrir otra familia base
- o empezar la capa de hipermodelo por horizonte

## Estado actual del plan que sigue guiando el proyecto

### Familias cerradas

- `E1` Ridge
- `E2` Huber
- `E4` Boosting

### Familias no lineales de referencia vigentes

- `E3` queda cerrada en su rama base y conserva valor historico como referencia de bagging mediante `E3_v2_clean`
- `E5` queda abierta y madura mediante `E5_v4_clean` como mejor no lineal tabular actual
- `E7` queda abierta como referencia temporal estructurada secundaria, por encima de `E6` pero por debajo del bloque contendiente

### Infraestructura ya preparada

- pipeline por familias
- tracker con auditoria automatica
- tabla maestra experimental
- rankings por horizonte y por metrica
- catalogo de runs
- cobertura de predicciones
- `stacking_readiness`
- `stacking_base_h1..h4`

### Siguiente paso razonable

El plan vigente deja dos rutas validas:

1. Ruta de continuidad base inmediata
- correr `E5_v2_clean` para aislar si `feature_mode=corr` mejora o empeora CatBoost
- luego decidir si `E5` merece expansion real

2. Ruta de infraestructura / hipermodelo
- estandarizar artefactos explicativos por horizonte
- usar `stacking_base_h1..h4`
- abrir formalmente la familia `E9` stacking

3. Ruta de exploracion de la siguiente familia base pendiente
- despues de `E5`, abrir `E6` ARIMAX
- mantener luego la continuidad hacia `E7` y `E8`

## Regla de lectura para futuras decisiones

Este plan no debe leerse como una lista de tareas mecanica, sino como una hoja de ruta con criterio de stop.

Una familia o subrama futura solo debe expandirse si:

- aporta mejora real sobre su baseline interno
- y ademas compite con las referencias vigentes

Hoy las referencias que guian cualquier apertura nueva son:

- `E1_v5_clean` como campeon global
- `E1_v4_clean` como referencia parsimoniosa
- `E5_v1_clean` como mejor no lineal tabular abierta
- `E3_v2_clean` como mejor referencia de bagging ya cerrada

## Resumen operativo final

- El prompt original de arquitectura si sigue vigente en su estructura por familias.
- Lo que cambio fue la secuencia real de profundizacion, guiada por evidencia y no por completar corridas por inercia.
- Las familias no ejecutadas no quedaron olvidadas; quedaron diferidas o canceladas con motivo explicito.
- La fase actual del proyecto ya esta mejor preparada para decidir entre abrir `E5` o pasar a `E9` stacking con base real.
