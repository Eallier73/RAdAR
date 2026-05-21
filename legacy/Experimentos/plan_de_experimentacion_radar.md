# Plan de Experimentacion Radar

Fecha de actualizacion: `2026-04-03`

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
  [resumen_metodologico_e1_1_bayesian.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e1_1_bayesian.md)
  [resumen_metodologico_e1_ridge.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e1_ridge.md)
  [resumen_metodologico_e2_huber.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e2_huber.md)
  [resumen_metodologico_e3_arboles.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e3_arboles.md)
  [resumen_metodologico_e4_boosting.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e4_boosting.md)
  [resumen_metodologico_e5_catboost.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e5_catboost.md)
  [resumen_metodologico_e6_arimax.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e6_arimax.md)
  [resumen_metodologico_e7_prophet.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e7_prophet.md)
  [resumen_metodologico_e8_hibrido_residual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e8_hibrido_residual.md)
  [resumen_metodologico_e9_stacking.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e9_stacking.md)
  [resumen_metodologico_e10_gating_contextual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e10_gating_contextual.md)
  [resumen_metodologico_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e11_dual.md)
  [resumen_metodologico_e12_representacion.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e12_representacion.md)
  [resumen_metodologico_clasificacion_c1_c4.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_clasificacion_c1_c4.md)
- Auditoria maestra retrospectiva:
  [resumen_auditoria_experimentos.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_auditoria_experimentos.md)
- Diccionario canonico de constructos:
  [diccionario_constructos_canonicos_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/diccionario_constructos_canonicos_radar.md)
- Actualizacion metodologica posterior a `E9_v2_clean`:
  [actualizacion_metodologica_post_e9_e10_e11.md](/home/emilio/Documentos/RAdAR/Experimentos/actualizacion_metodologica_post_e9_e10_e11.md)
- Informe canonico de saneamiento documental:
  [resumen_saneamiento_documental_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_saneamiento_documental_radar.md)
- Fase rectora de produccion controlada:
  [fase_produccion_controlada_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_radar.md)
- Politica de promocion futura:
  [politica_promocion_sistemas_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/politica_promocion_sistemas_radar.md)
- Consolidacion operativa posterior:
  [consolidacion_operativa_post_produccion_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/consolidacion_operativa_post_produccion_controlada.md)
- Fase operativa dual vigente:
  [fase_produccion_controlada_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_dual_radar.md)
- Politica operativa del sistema dual:
  [politica_operativa_sistema_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/politica_operativa_sistema_dual_radar.md)
- Preparacion formal para automatizacion:
  [preparacion_automatizacion_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/preparacion_automatizacion_radar.md)
- Verificacion de reproducibilidad dual:
  [verificacion_reproducibilidad_dual_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/verificacion_reproducibilidad_dual_controlada.md)
- Resumen metodologico de operacion controlada:
  [resumen_metodologico_operacion_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_operacion_controlada.md)
- Cierre formal de `E10`:
  [cierre_formal_e10_no_promocionable.md](/home/emilio/Documentos/RAdAR/Experimentos/cierre_formal_e10_no_promocionable.md)
- Especificacion futura de `E11`:
  [especificacion_futura_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/especificacion_futura_e11_dual.md)

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

## Fase vigente del proyecto

La expansion experimental del proyecto queda temporalmente cerrada.

La fase vigente ya no es abrir nuevas familias. La fase vigente es una **produccion controlada dual**.

Esto significa:

- la salida numerica principal queda congelada en `E1_v5_clean`
- la deteccion de caidas queda congelada en `E9_v2_clean`
- la lectura direccional queda congelada con politica fija `9-1-9-1`
- la operacion dual queda empaquetada y auditable
- la siguiente etapa formal del proyecto pasa a ser preparacion para automatizacion, no nueva exploracion por inercia

La capa experimental no se borra, pero deja de ser la prioridad operativa. Solo podria reabrirse bajo una nueva hipotesis fuerte, acotada y explicitamente documentada.

Benchmarks operativos vigentes:

- benchmark numerico puro: `E1_v5_clean`
- benchmark operativo de riesgo-direccion-caidas: `E9_v2_clean`
- politica direccional fija por horizonte: `H1=E9`, `H2=E1`, `H3=E9`, `H4=E1`

Lectura obligatoria:

- `E1_v5_clean` no reemplaza a `E9_v2_clean`
- `E9_v2_clean` no reemplaza a `E1_v5_clean`
- `E10` ya fue probado y queda cerrado para promocion bajo su formulacion actual
- `E11` ya fue abierta con tres variantes controladas y queda evaluada sin promocion en su primera apertura dual
- `E12` ya fue abierta, no produjo mejora defendible y no justifica expansion inmediata
- el sistema vigente no es un modelo unico sino un sistema compuesto / dual con asignacion funcional por salida

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

## Extension posterior del programa

La arquitectura original llegaba hasta `E9`. Despues de la evidencia acumulada en `E9_v2_clean`, el programa queda extendido formalmente con dos familias conceptuales nuevas:

10. `E10` meta-selector / gating contextual
11. `E11` arquitectura dual numerica + categorica

Importante:

- `E10` no reabre `E9`; la sucede con una pregunta distinta.
- `E11` no fue una continuidad informal de `E10`; se abrio como arquitectura distinta y controlada.
- `E11` ya no queda solo conceptual: su primera apertura dual ya fue ejecutada y no produjo una variante promocionable.

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

## Rama paralela de clasificacion

Ademas del frente principal de regresion, el proyecto ya abrio una rama paralela de clasificacion del movimiento del Radar.

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
- corridas ejecutadas: `C1_v1_clean`, `C1_v2_clean`, `C1_v3_clean`, `C2_v1_clean`, `C2_v2_clean`, `C2_v3_clean`
- familias con corrida real: `C1`, `C2`
- familias con infraestructura pero sin corrida: `C3`, `C4`
- prioridad actual: baja; la rama queda abierta pero no prioritaria

Organizacion actual de la documentacion:

- `09_clasificacion_radar/` como prompt rector de la rama
- `10_clasificacion_random_forest/` para `C1`
- `11_clasificacion_xgboost/` para `C2`
- `12_clasificacion_catboost/` para `C3`
- `13_clasificacion_lightgbm/` para `C4`

Documento de cierre de rama:

- [resumen_metodologico_clasificacion_c1_c4.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_clasificacion_c1_c4.md)

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
| `E8` hibridos residuales | abierta | `E8_v2_clean` | híbrido residual válido, pero no competitivo frente al bloque fuerte |
| `E9` stacking | pausada util | `E9_v2_clean` | mejor rama actual de riesgo-direccion-caidas; no reemplaza a E1 y queda en pausa metodologica |
| `E10` gating contextual | cerrada para promocion | `E10_v1_clean` | corrida real ya evaluada; no supera a selector fijo ni a benchmarks centrales y no procede promocion bajo su formulacion actual |
| `E11` dual numerica+categórica | evaluada sin promocion | `E11_v2_clean` | primera apertura dual ya ejecutada; agrega evidencia util, pero no desplaza a `E1_v5_clean` ni a `E9_v2_clean` |
| `E12` representacion por horizonte | evaluada sin promocion | `E12_v3_clean` | primera apertura de representacion enriquecida; deja hallazgo parcial sobre desacuerdo entre bases, pero no mejora a `E1_v5_clean` ni a `E9_v2_clean` |

### Estado resumido de la rama de clasificacion

| familia | estado actual | mejor run interno | lectura vigente |
|---|---|---|---|
| `C1` RandomForestClassifier | evaluada y pausada tempranamente | n/a | tres corridas reales, pero colapsaron a clase unica y no dejaron señal discriminativa util |
| `C2` XGBoostClassifier | evaluada y pausada tempranamente | `C2_v1_clean` | tres corridas reales y mismo colapso de clase unica observado en C1; no agrega señal útil |
| `C3` CatBoostClassifier | infraestructura preparada | n/a | runner y prompts listos, sin corrida real |
| `C4` LightGBMClassifier | infraestructura preparada | n/a | runner y prompts listos, sin corrida real |

### Referencias vigentes

- referente numerico puro principal: `E1_v5_clean` con `L_total_Radar = 0.243442`
- referente operativo de riesgo-direccion-caidas: `E9_v2_clean` con `L_total_Radar = 0.227510`, `direction_accuracy_promedio = 0.735847` y `deteccion_caidas_promedio = 0.916667`
- referencia parsimoniosa: `E1_v4_clean` con `0.253277`
- mejor no lineal tabular abierta: `E5_v4_clean` con `0.247788`
- mejor no lineal base previa: `E3_v2_clean` con `0.266387`
- mejor H2 y H4 por `loss_h` historico base: `E2_v3_clean`
- mejor H3 por `loss_h` historico base: `E1_v2_clean`

### Dualidad funcional vigente del Radar

La evidencia ya no permite pensar el proyecto como si tuviera una sola tarea predictiva homogenea.

El Radar queda formalmente leido en dos planos:

- tarea numerica: pronostico del porcentaje o nivel esperado
- tarea categórica / operativa: lectura de movimiento, direccion y especialmente deteccion de bajas

Conclusion metodologica explicita:

`E1_v5_clean` no reemplaza a `E9_v2_clean`, y `E9_v2_clean` no reemplaza a `E1_v5_clean`.
Ambos representan funciones distintas y complementarias dentro del Radar.
`E1_v5_clean` queda como mejor referente numerico puro.
`E9_v2_clean` queda como mejor referente actual de riesgo, direccion y caidas.
La arquitectura futura del Radar debe reconocer explicitamente esta dualidad funcional.

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

#### Verificacion tactica posterior

Despues del cierre principal de `E1`, se corrio una micro-rama diagnostica y de muy bajo costo:

- `E1_1_v1_bayesian_base`

Lectura:

- `BayesianRidge` se evaluo bajo el mismo marco temporal limpio de `E1_v5_clean`.
- No mejoro `L_total_Radar` frente a `E1_v5_clean`.
- Solo mostro una mejora parcial en `H3`, compensada por deterioro en `H1`, `H2` y sin ganancia material en `H4`.
- La evidencia no justifico abrir `E1_1_v2_bayesian_control`.

Decision:

- La micro-rama `E1.1 Bayesian` queda cerrada como verificacion util pero no preferible.
- El cierre metodologico principal de `E1` no cambia: `E1_v5_clean` sigue como mejor referente numerico puro.

Documento de trazabilidad especifica:

- [resumen_micro_rama_e1_1_bayesian.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_micro_rama_e1_1_bayesian.md)

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

Documento de cierre:

- [resumen_metodologico_e5_catboost.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e5_catboost.md)

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

Documento de cierre:

- [resumen_metodologico_e6_arimax.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e6_arimax.md)

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

Documento de cierre:

- [resumen_metodologico_e7_prophet.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e7_prophet.md)

### E8 Hibridos residuales

#### Lo planeado

`E8` debia probar una familia intermedia entre modelos base y stacking, corrigiendo residuales de forma auditable sin pegar manualmente ganadores por horizonte.

#### Lo que si se hizo

Se ejecutaron:

- `E8_v1_clean`
- `E8_v2_clean`
- `E8_v3_clean`

Lectura:

- `E8_v1_clean` mostro que un esquema `Ridge -> CatBoost residual` no fue suficiente.
- `E8_v2_clean` mejoro claramente a `E8_v1_clean` y quedo como campeon interno de la familia.
- `E8_v3_clean` colapso; `Prophet` como residual learner sobre `CatBoost` no fue una direccion util.
- aun el mejor hibrido (`E8_v2_clean`) quedo por debajo de `E4_v1_clean`, `E3_v2_clean`, `E1_v4_clean`, `E5_v4_clean` y `E1_v5_clean`.

Estado actual:

- `E8` queda abierta como familia intermedia y metodologicamente valida
- no se vuelve linea principal
- solo se justificaria una prueba adicional si hay una hipotesis residual muy acotada

Documento de cierre:

- [resumen_metodologico_e8_hibrido_residual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e8_hibrido_residual.md)

### E9 Stacking

#### Estado actual

- `E9` ya tiene:
  - tabla curada por horizonte
  - runner operativo
  - dos corridas limpias y trazables:
    - [E9_v1_clean_20260401_065743](/home/emilio/Documentos/RAdAR/Experimentos/runs/E9_v1_clean_20260401_065743)
    - [E9_v2_clean_20260401_070431](/home/emilio/Documentos/RAdAR/Experimentos/runs/E9_v2_clean_20260401_070431)
- la infraestructura preparatoria sigue siendo:
  - tabla maestra ampliada
  - `stacking_readiness`
  - `stacking_base_h1..h4`
  - [tabla_maestra_experimentos_radar_e9_curada.xlsx](/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar_e9_curada.xlsx)
  - [preparacion_tabla_e9_stacking_controlado.md](/home/emilio/Documentos/RAdAR/Experimentos/preparacion_tabla_e9_stacking_controlado.md)
- la primera apertura operativa de `E9` arrojo:
  - `E9_v1_clean = 0.268475`
  - `E9_v2_clean = 0.227510`
  - `E9_v1_clean` mostro una mejora puntual en `H3`
  - `E9_v2_clean` mejoro fuertemente la rama en `H1`, `H2` y `H4`, y quedo como campeon interno de la familia
  - `E9_v2_clean` no debe leerse como reemplazo numerico puro de `E1_v5_clean`, sino como la mejor referencia actual de riesgo-direccion-caidas

#### Lectura vigente

- `E9` ya no esta pendiente de wiring; ese trabajo ya se hizo.
- `E9_v2_clean` fue la unica corrida de la familia que produjo una mejora operativa seria, especialmente en deteccion de caidas y trade-off de riesgo.
- Esa mejora no se interpreta como victoria absoluta del stacking sobre Ridge, porque responde a una funcion distinta dentro del Radar.
- `E9` no se cierra como fallida, pero tampoco queda como ganadora global unica.
- La familia queda en pausa metodologica: util, no descartada y potencialmente reactivable mas adelante.

Documento de cierre:

- [resumen_metodologico_e9_stacking.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e9_stacking.md)

### E10 Gating / meta-selector contextual

#### Estado actual

- `E10` ya fue abierta formalmente y ya tiene una corrida canonica:
  - [E10_v1_clean_20260401_090439](/home/emilio/Documentos/RAdAR/Experimentos/runs/E10_v1_clean_20260401_090439)
- La infraestructura de datos de `E10` ya fue construida en una tabla derivada especifica y trazable:
  - `tabla_e10_meta_selector_base.csv`
  - `tabla_e10_meta_selector_base.xlsx`
  - `inventario_columnas_e10.csv`
  - `diccionario_tabla_e10.md`
  - `resumen_construccion_tabla_e10.md`
- Su pregunta ya no es "como promediar mejor los mismos modelos", sino "cuando conviene que tipo de salida o familia segun el contexto temporal y operativo".
- `E10` debe seguir siendo una familia distinta de `E9`:
  - `E9` = stacking clasico controlado
  - `E10` = seleccion o combinacion contextual, con trazabilidad fuerte y sin leakage

#### Lectura vigente

- `E10` ya cumplio la funcion de probar si un selector duro contextual podia desplazar de forma defendible a los referentes vigentes.
- `E10_v1_clean` resolvio la primera pregunta de apertura con un selector duro lineal y trazable:
  - el experimento fue metodologicamente limpio
  - no supero al selector fijo en el global
  - no supero a `E1_v5_clean`
  - no supero a `E9_v2_clean`
  - las accuracies del selector por horizonte fueron bajas
- En consecuencia, `E10` ya no esta en premodelado ni en incubacion promocionable. Queda cerrada para promocion bajo la formulacion probada.
- `E10` se conserva como antecedente metodologico util para la frontera futura, pero no como siguiente linea activa.

Documento de cierre:

- [resumen_metodologico_e10_gating_contextual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e10_gating_contextual.md)

### E11 Arquitectura dual numerica + categorica

#### Estado actual

- `E11` ya fue abierta con tres variantes controladas:
  - `E11_v1_clean`
  - `E11_v2_clean`
  - `E11_v3_clean`
- La mejor apertura interna fue `E11_v2_clean`.
- La familia no deja una variante promocionable todavia.
- `E11` ya no debe leerse como simple especificacion futura, pero tampoco como solucion vigente.

#### Definicion metodologica

La primera apertura de `E11` exploro una arquitectura con dos componentes distintos:

- componente numerico: estimacion del porcentaje, nivel o cambio esperado
- componente categorico / operativo: clasificacion de sube, baja o se mantiene

La evidencia de apertura deja esta lectura:

- la version ternaria simple `baja / se_mantiene / sube` siguio casi colapsada a estabilidad
- la version binaria `cae / no_cae` si dejo una señal operativa moderada
- la capa residual dual no mejoro el global frente a `E1_v5_clean`
- la autopsia posterior mostro que `+-0.5` era un threshold excesivo para la escala real del delta, por lo que la lectura ternaria no debe darse por refutada de forma estructural total

#### Diferencia conceptual frente a E10

- `E10` pregunta cuando conviene que familia o salida dentro de una arquitectura contextual.
- `E11` pregunta si el Radar necesita separar explicitamente la tarea numerica y la tarea categorica como dos problemas distintos y coordinados.

#### Decision vigente

- `E11` queda abierta como evidencia dual ya ejecutada.
- `E11` no queda promocionable.
- `E11_v2_clean` conserva valor como mejor apertura interna porque agrega detector binario de caidas sin deterioro numerico.
- `E11_v3_clean` no justifica todavia una expansion residual adicional.
- cualquier reapertura futura debe ser una reformulacion dual nueva y no un simple reciclaje de `E10`.

### E12 Representacion por horizonte

#### Estado actual

- `E12` ya fue abierta con tres variantes controladas:
  - `E12_v1_clean`
  - `E12_v2_clean`
  - `E12_v3_clean`
- La mejor apertura interna fue `E12_v3_clean`.
- La familia no deja una variante promocionable.
- `E12` no debe leerse como reapertura de `E9` ni como selector ex post disfrazado.

#### Definicion metodologica

La primera apertura de `E12` exploro una pregunta de representacion:

- si parte de la ventaja operativa observada en `E9_v2_clean`, sobre todo en `H1`, podia absorberse dentro de un `Ridge` simple y trazable;
- usando predicciones archivadas de bases heterogeneas, consensos, spreads y, cuando aplica, regimen observable en `t`.

La evidencia de apertura deja esta lectura:

- `E12_v1_clean` prueba un bloque minimo de representacion y empeora claramente frente a los benchmarks;
- `E12_v2_clean` amplia la diversidad funcional, pero agrega complejidad sin mejora defendible;
- `E12_v3_clean` aisla el desacuerdo entre bases y queda como mejor variante interna;
- ninguna variante mejora `H1` frente a `E1_v5_clean`;
- ninguna variante supera a `E9_v2_clean` en el mismo subset comun;
- la hipotesis fuerte de absorber la ventaja de `E9` via representacion no queda confirmada.

#### Decision vigente

- `E12` queda evaluada sin promocion.
- `E12_v3_clean` conserva valor como hallazgo parcial:
  - el desacuerdo entre bases parece aportar mas que el bloque de regimen usado aqui
  - pero la mejora no alcanza el umbral de expansion inmediata
- cualquier reapertura futura debe partir de una hipotesis de `H1` mas precisa y no de ampliar features por inercia.

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
- `E8` queda abierta como referencia híbrida residual secundaria, por encima de `E6` y `E7_v2`, pero sin desplazar a `E5_v4_clean`
- `E9` queda pausada como rama util de riesgo-direccion-caidas, con `E9_v2_clean` como campeon interno

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

El plan vigente deja una secuencia principal clara:

1. reconocer la dualidad funcional del Radar:
- `E1_v5_clean` como referente numerico puro
- `E9_v2_clean` como referente operativo de riesgo-direccion-caidas

2. mantener `E9` en pausa metodologica:
- util
- no descartada
- no ganadora absoluta

3. dejar `E10` cerrada para promocion bajo su formulacion actual:
- corrida real ya ejecutada
- hipotesis principal no confirmada
- conservar como antecedente metodologico, no como linea activa

4. mantener `E11` abierta sin promocion:
- primera apertura dual ya ejecutada
- mejor run interno `E11_v2_clean`
- sin evidencia suficiente para reemplazar la salida dual vigente

5. fijar la siguiente pregunta correcta antes de abrir una nueva familia:
- la autopsia `E1_v5_clean` vs `E9_v2_clean` sugiere que la ventaja operativa de `E9_v2_clean` se explica mas por representacion que por arquitectura pura
- la mejor recombinacion ex post por horizonte usa `E9` solo en `H1` y `E1` en `H2-H4`, pero no es promocionable
- la clasificacion ternaria solo deberia reabrirse en el futuro con thresholds recalibrados, no con `+-0.5`
- `E2` queda definitivamente cerrada sin expansion adicional
- `E12` ya probo una primera apertura limpia de representacion y no deja una mejora defendible; por tanto, no procede otra familia nueva por inercia

## Regla de lectura para futuras decisiones

Este plan no debe leerse como una lista de tareas mecanica, sino como una hoja de ruta con criterio de stop.

Una familia o subrama futura solo debe expandirse si:

- aporta mejora real sobre su baseline interno
- y ademas compite con las referencias vigentes

Hoy las referencias que guian cualquier apertura nueva son:

- `E1_v5_clean` como referente numerico puro principal
- `E9_v2_clean` como referente operativo principal de riesgo-direccion-caidas
- `E1_v4_clean` como referencia parsimoniosa
- `E5_v4_clean` como mejor no lineal tabular abierta
- `E3_v2_clean` como mejor referencia de bagging ya cerrada

## Resumen operativo final

- El proyecto ya no debe leerse como una busqueda de un unico ganador global.
- La evidencia sugiere una estructura funcional dual:
  - mejor referente numerico puro
  - mejor referente de riesgo-direccion-caidas
- La rama de clasificacion existe de forma real, pero hoy `C1` y `C2` ya fueron ejecutadas y ambas quedaron pausadas tempranamente por colapso del target.
- La capa explicativa transversal sigue siendo parcial intra-familia: hay seleccion de variables por horizonte en algunos runs, pero no una taxonomia homogenea de coeficientes, importancias o SHAP comparable entre familias.
- En consecuencia:
  - `E9` queda pausada como rama util pero no definitiva
  - `E10` queda cerrada para promocion tras `E10_v1_clean`
  - `E11` queda abierta como familia dual ya ejecutada, pero todavia no promocionable
  - `E12` queda evaluada sin promocion como primera familia de representacion por horizonte
  - la siguiente frontera razonable no es “otro algoritmo”, sino solo una futura hipotesis de representacion mas precisa si la evidencia justifica reabrir ese frente
