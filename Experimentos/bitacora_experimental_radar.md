# Bitácora Experimental Radar

## Propósito

Esta bitácora resume, en lenguaje operativo, qué se hizo, qué se decidió y en qué rama quedó cada bloque principal del pipeline experimental. No sustituye:

- el grid experimental,
- la tabla maestra,
- ni los artefactos por run.

Su función es servir como capa narrativa corta para ubicarse rápido.

## Estado actual

- Fecha de actualizacion: `2026-04-03`
- Rama de trabajo actual: `main`
- Referente numerico puro vigente: `E1_v5_clean` con `L_total_Radar=0.243442`
- Referente operativo vigente de riesgo-direccion-caidas: `E9_v2_clean` con `L_total_Radar=0.227510`
- Mejor no lineal tabular abierta: `E5_v4_clean` con `L_total_Radar=0.247788`
- Estado actual de `E10`: `cerrada para promocion bajo su formulacion actual` con [E10_v1_clean_20260401_090439](/home/emilio/Documentos/RAdAR/Experimentos/runs/E10_v1_clean_20260401_090439)
- Estado actual de `E11`: `evaluada sin promocion en su primera apertura dual` con [E11_v2_clean_20260403_051823](/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v2_clean_20260403_051823) como mejor apertura interna
- Estado actual de `E12`: `evaluada sin promocion como hallazgo parcial de representacion` con [E12_v3_clean_20260403_080040](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v3_clean_20260403_080040) como mejor apertura interna
- Estado actual de clasificacion: `C1` y `C2` ejecutadas y pausadas tempranamente; `C3-C4` con infraestructura preparada pero sin corridas
- Fase vigente oficial: [fase_produccion_controlada_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_dual_radar.md)
- Politica operativa vigente:
  - salida numerica principal: `E1_v5_clean`
  - deteccion de caidas: `E9_v2_clean`
  - direction por horizonte: `H1=E9`, `H2=E1`, `H3=E9`, `H4=E1`
- Siguiente paso recomendado hoy: no abrir una familia nueva; cerrar la fase operativa dual y pasar a automatizacion controlada
- Plan rector vigente:
  - [plan_de_experimentacion_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/plan_de_experimentacion_radar.md)
- Tabla maestra vigente:
  - [tabla_maestra_experimentos_radar.xlsx](/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar.xlsx)
  - [tabla_maestra_experimentos_radar.csv](/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar.csv)
- Fase vigente:
  - [fase_produccion_controlada_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_dual_radar.md)

## Documentos canónicos de referencia

- familias `E1-E4`:
  - [resumen_metodologico_e1_1_bayesian.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e1_1_bayesian.md)
  - [resumen_metodologico_e1_ridge.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e1_ridge.md)
  - [resumen_metodologico_e2_huber.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e2_huber.md)
  - [resumen_metodologico_e3_arboles.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e3_arboles.md)
  - [resumen_metodologico_e4_boosting.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e4_boosting.md)
- familias `E5-E12`:
  - [resumen_metodologico_e5_catboost.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e5_catboost.md)
  - [resumen_metodologico_e6_arimax.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e6_arimax.md)
  - [resumen_metodologico_e7_prophet.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e7_prophet.md)
  - [resumen_metodologico_e8_hibrido_residual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e8_hibrido_residual.md)
  - [resumen_metodologico_e9_stacking.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e9_stacking.md)
  - [resumen_metodologico_e10_gating_contextual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e10_gating_contextual.md)
  - [resumen_metodologico_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e11_dual.md)
  - [resumen_metodologico_e12_representacion.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e12_representacion.md)
  - [constructos_representacion_e12.md](/home/emilio/Documentos/RAdAR/Experimentos/constructos_representacion_e12.md)
- clasificacion:
  - [resumen_metodologico_clasificacion_c1_c4.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_clasificacion_c1_c4.md)
- constructos:
  - [diccionario_constructos_canonicos_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/diccionario_constructos_canonicos_radar.md)
- produccion controlada:
  - [fase_produccion_controlada_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_radar.md)
  - [fase_produccion_controlada_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_dual_radar.md)
  - [resumen_metodologico_operacion_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_operacion_controlada.md)
  - [politica_operativa_sistema_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/politica_operativa_sistema_dual_radar.md)
  - [preparacion_automatizacion_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/preparacion_automatizacion_radar.md)
  - [verificacion_reproducibilidad_dual_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/verificacion_reproducibilidad_dual_controlada.md)
  - [politica_promocion_sistemas_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/politica_promocion_sistemas_radar.md)
  - [consolidacion_operativa_post_produccion_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/consolidacion_operativa_post_produccion_controlada.md)
  - [cierre_formal_e10_no_promocionable.md](/home/emilio/Documentos/RAdAR/Experimentos/cierre_formal_e10_no_promocionable.md)
  - [especificacion_futura_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/especificacion_futura_e11_dual.md)

## Línea de tiempo

### 2026-04-03 | Cierre experimental y apertura formal de fase operativa dual

- Se cierra temporalmente la expansion experimental del proyecto.
- Se congela formalmente el sistema operativo compuesto vigente:
  - salida numerica principal: `E1_v5_clean`
  - deteccion de caidas: `E9_v2_clean`
  - direction por horizonte: `9-1-9-1`
- Se implementa [run_sistema_dual_operativo_radar.py](/home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_sistema_dual_operativo_radar.py) para empaquetar salidas canonicas del sistema dual.
- Se verifico reproducibilidad fuerte con reejecuciones controladas:
  - [E1_v5_operativo_rebuild_v2_20260403_092120](/home/emilio/Documentos/RAdAR/Experimentos/runs/E1_v5_operativo_rebuild_v2_20260403_092120)
  - [E9_v2_operativo_rebuild_20260403_092042](/home/emilio/Documentos/RAdAR/Experimentos/runs/E9_v2_operativo_rebuild_20260403_092042)
- Se fijan rutas operativas estables en:
  - `/home/emilio/Documentos/RAdAR/Experimentos/operacion_dual_controlada/paquete_vigente/`
- Documentos canonicos nuevos:
  - [fase_produccion_controlada_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_dual_radar.md)
  - [politica_operativa_sistema_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/politica_operativa_sistema_dual_radar.md)
  - [preparacion_automatizacion_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/preparacion_automatizacion_radar.md)
  - [verificacion_reproducibilidad_dual_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/verificacion_reproducibilidad_dual_controlada.md)

Decision:

- la expansion experimental queda temporalmente cerrada;
- el sistema vigente ya no se describe solo como “benchmarks operativos”, sino como sistema dual funcional congelado;
- la siguiente etapa formal pasa a ser automatizacion controlada, no nuevas corridas experimentales.

### 2026-04-03 | Apertura controlada E12 representacion por horizonte

- Se implemento [run_e12_representacion.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e12_representacion.py) como runner unico de familia con tres modos:
  - `minimal`
  - `expanded`
  - `disagreement_only`
- Se corrieron:
  - [E12_v1_clean_20260403_075150](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v1_clean_20260403_075150)
  - [E12_v2_clean_20260403_075843](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v2_clean_20260403_075843)
  - [E12_v3_clean_20260403_080040](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v3_clean_20260403_080040)
- Documentos canonicos:
  - [resumen_metodologico_e12_representacion.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e12_representacion.md)
  - [constructos_representacion_e12.md](/home/emilio/Documentos/RAdAR/Experimentos/constructos_representacion_e12.md)
  - [resumen_resultados_e12_apertura_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_resultados_e12_apertura_controlada.md)
- Resultado:
  - `E12_v1_clean` y `E12_v2_clean` empeoran con claridad frente a `E1_v5_clean` y `E9_v2_clean`
  - `E12_v3_clean` queda como mejor variante interna, lo que sugiere que el desacuerdo entre bases aporta mas que el bloque de regimen usado en esta apertura
  - ninguna variante mejora `H1`, que era la hipotesis central de la familia
  - ninguna variante supera a los benchmarks vigentes en el mismo subset comun

Decision:

- `E12` queda evaluada sin promocion;
- la familia deja un hallazgo parcial util, no una mejora defendible;
- no procede expansion inmediata.

### 2026-04-03 | Autopsia E1 vs E9 + recombinacion ex post + recalibracion de thresholds + verificacion tactica E2

- Se corrio [analyze_post_e11_decision_phase.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/analyze_post_e11_decision_phase.py) para ejecutar en un solo paso:
  - autopsia comparativa `E1_v5_clean` vs `E9_v2_clean`
  - recombinacion ex post por horizonte
  - sensibilidad de thresholds categoricos
- Se generaron:
  - [autopsia_e1_v5_vs_e9_v2.md](/home/emilio/Documentos/RAdAR/Experimentos/autopsia_e1_v5_vs_e9_v2.md)
  - [analisis_recombinacion_ex_post_horizontes_e1_e9.md](/home/emilio/Documentos/RAdAR/Experimentos/analisis_recombinacion_ex_post_horizontes_e1_e9.md)
  - [analisis_distribucion_delta_iad.md](/home/emilio/Documentos/RAdAR/Experimentos/analisis_distribucion_delta_iad.md)
  - [decision_formal_siguiente_paso_post_e11.md](/home/emilio/Documentos/RAdAR/Experimentos/decision_formal_siguiente_paso_post_e11.md)
- Hallazgos:
  - `E9_v2_clean` no domina el subset comun completo; su ventaja operativa se concentra sobre todo en `H1`
  - la pauta observada es mas consistente con una ventaja de representacion que con una ventaja puramente arquitectonica
  - la mejor recombinacion ex post usa `E9` en `H1` y `E1` en `H2-H4`, pero no es promocionable
  - `+-0.5` queda descartado como threshold ternario razonable; `+-0.15` queda como valor preferente para una futura reapertura prudente
- Se cerro la verificacion tactica de `E2` sin nuevas corridas:
  - [resumen_resultados_e2_verificacion_tactica.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_resultados_e2_verificacion_tactica.md)
  - la evidencia ya existente en `E2_v1_clean`, `E2_v2_clean` y `E2_v3_clean` fue suficiente para ratificar el cierre formal de la familia

Decision:

- no abrir `E12` todavia por inercia
- no promocionar recombinaciones ex post ni recalibraciones aisladas
- mantener `E1_v5_clean` + `E9_v2_clean` como salida dual vigente
- fijar como siguiente pregunta seria una futura familia centrada en representacion de features, no en algoritmo

Nota de actualizacion:

- esa recomendacion se ejecuto despues el mismo `2026-04-03` en la apertura controlada de `E12`; el documento conserva valor historico, pero ya no describe el estado mas reciente.

### 2026-04-03 | Apertura dual controlada de E11

- Se implemento [run_e11_dual.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e11_dual.py) como runner unico de familia con tres modos:
  - `parallel`
  - `fall_detector`
  - `residual_dual`
- Se corrieron:
  - [E11_v1_clean_20260403_051406](/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v1_clean_20260403_051406)
  - [E11_v2_clean_20260403_051823](/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v2_clean_20260403_051823)
  - [E11_v3_clean_20260403_051823](/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v3_clean_20260403_051823)
- Resultado:
  - `E11_v1_clean` conserva exactamente el bloque numerico de `E1_v5_clean`, pero la tarea ternaria sigue casi colapsada a `se_mantiene`
  - `E11_v2_clean` conserva exactamente el bloque numerico de `E1_v5_clean` y agrega una capa binaria `cae / no_cae` con señal moderada
  - `E11_v3_clean` intenta corregir residuales y no mejora el global frente a `E1_v5_clean`
- Documento canonico:
  - [resumen_metodologico_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e11_dual.md)

Decision:

- `E11` deja de ser solo especificacion futura y pasa a familia dual ya ejecutada
- `E11` no queda promocionable todavia
- `E11_v2_clean` se conserva como mejor apertura interna
- la salida dual vigente sigue siendo `E1_v5_clean` + `E9_v2_clean`

### 2026-04-03 | Apertura y cierre temprano de C2 XGBoostClassifier

- Se corrigio la utilidad comun de clasificacion para remapear IDs de clase por fold y permitir entrenamiento limpio de `XGBoostClassifier` sin leakage cuando el train temprano no contiene todas las clases globales.
- Se corrieron:
  - [C2_v1_clean_20260403_040434](/home/emilio/Documentos/RAdAR/Experimentos/runs/C2_v1_clean_20260403_040434)
  - [C2_v2_clean_20260403_040456](/home/emilio/Documentos/RAdAR/Experimentos/runs/C2_v2_clean_20260403_040456)
  - [C2_v3_clean_20260403_040509](/home/emilio/Documentos/RAdAR/Experimentos/runs/C2_v3_clean_20260403_040509)
- Las tres variantes replicaron exactamente el mismo resultado de `C1`:
  - `L_total_Clasificacion = 0.483333`
  - `recall_baja_fuerte = 0.0`
  - `recall_baja_total = 0.0`
  - clase efectiva unica en evaluacion por horizonte

Decision:

- `C2` deja de ser infraestructura preparada y pasa a familia evaluada y pausada tempranamente;
- la evidencia refuerza que el cuello de botella sigue siendo el target categorico, no el clasificador;
- no procede abrir `C3` o `C4` por inercia.

### 2026-04-02 | Consolidacion operativa post-produccion controlada

- Se endurecio la rutina operativa de benchmarks vigentes con validacion automatizada de integridad.
- Se dejo un reporte reproducible de auditoria operativa de benchmarks en:
  - [auditoria_benchmarks_operativos_controlados.md](/home/emilio/Documentos/RAdAR/Experimentos/auditoria_benchmarks_operativos_controlados.md)
  - [auditoria_benchmarks_operativos_controlados.json](/home/emilio/Documentos/RAdAR/Experimentos/auditoria_benchmarks_operativos_controlados.json)
- Se volvio aplicable la politica de promocion con una version estructurada en JSON.
- `E10` quedo cerrado formalmente para promocion bajo su formulacion actual.
- `E11` quedo especificada como arquitectura futura, sin ejecucion.

Decision:

- los benchmarks vigentes `E1_v5_clean` y `E9_v2_clean` quedan congelados y auditados para operacion controlada;
- `E10` queda fuera de promocion y ya no sigue como rama incubada;
- `E11` quedaba fuera de ejecucion en ese momento; ese estado fue superado por la apertura dual controlada del `2026-04-03`.

### 2026-04-02 | Cierre formal de E10

- Se fijo el cierre formal de `E10` como rama no promocionable bajo su formulacion actual.
- El documento canonico de cierre queda en:
  - [cierre_formal_e10_no_promocionable.md](/home/emilio/Documentos/RAdAR/Experimentos/cierre_formal_e10_no_promocionable.md)
- Se amarro el cierre a la evidencia comparativa real de [E10_v1_clean_20260401_090439](/home/emilio/Documentos/RAdAR/Experimentos/runs/E10_v1_clean_20260401_090439):
  - `E10_v1_clean = 0.271220`
  - `selector_fijo = 0.265229`
  - `E1_v5_clean = 0.217866`
  - `E9_v2_clean = 0.227510`
- Se registro explicitamente que las accuracies del selector por horizonte fueron bajas.

Decision:

- `E10` se conserva como evidencia historica util;
- `E10` no queda en observacion promocionable;
- `E10` no es benchmark vigente;
- la siguiente frontera real pasa a ser `E11`; ese estado luego se materializo en la apertura dual controlada del `2026-04-03`.

### 2026-04-02 | Fase de Produccion Controlada

- Se formalizo una fase de produccion controlada sin declarar un modelo final unico.
- Se reconocio explicitamente la dualidad funcional vigente del Radar:
  - `E1_v5_clean` como benchmark numerico puro
  - `E9_v2_clean` como benchmark operativo de riesgo-direccion-caidas
- Se separaron conceptualmente:
  - capa experimental
  - capa operativa controlada
  - capa futura dual `E11`
- Se dejo registro operativo canonico en:
  - [fase_produccion_controlada_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_radar.md)
  - [politica_promocion_sistemas_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/politica_promocion_sistemas_radar.md)
  - [registro_operacion_controlada_radar.json](/home/emilio/Documentos/RAdAR/Experimentos/registro_operacion_controlada_radar.json)

Decisión:

- el proyecto ya madura hacia operacion comparativa controlada
- todavia no existe una produccion predictiva final unificada
- `E10` sigue como evidencia contextual fragil
- `E11` era todavia arquitectura futura no ejecutada en esa fecha; esa condicion luego fue superada por la apertura dual controlada del `2026-04-03`

### 2026-03-21 | E1 Ridge limpio

- Se reconstruyó `E1_v2_clean` como baseline metodológico oficial sin leakage temporal.
- Se corrió `E1_v3_clean` para probar `target_mode=delta`.
- Se corrió `E1_v4_clean` para probar `feature_mode=corr`.
- Se corrió `E1_v5_clean` para probar memoria larga con `lags=1..6`.

Decisión:

- `E1_v5_clean` quedó como mejor Ridge limpio global con `L_total_Radar=0.243442`.
- `E1_v4_clean` quedó como referencia parsimoniosa con `L_total_Radar=0.253277`.
- `Ridge` quedó cerrada como baseline lineal regularizado principal.

Rama asociada:

- `feature/e1-ridge`

Documentos clave:

- [resumen_metodologico_e1_ridge.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e1_ridge.md)

### 2026-04-02 | Micro-rama E1.1 Bayesian

- Se implemento y corrio [E1_1_v1_bayesian_base_20260402_063714](/home/emilio/Documentos/RAdAR/Experimentos/runs/E1_1_v1_bayesian_base_20260402_063714) como verificacion tactica de muy bajo costo dentro de la via lineal.
- El modelo usado fue [run_e1_bayesian_ridge.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e1_bayesian_ridge.py), reutilizando el mismo `walk-forward expanding`, el mismo `target_mode=nivel`, `feature_mode=corr`, `transform_mode=standard` y `lags=1..6`.

Resultado:

- `E1_1_v1_bayesian_base = 0.264946`
- `E1_v5_clean = 0.243442`
- `E1_v4_clean = 0.253277`

Lectura:

- `BayesianRidge` no mejoro el global frente a `Ridge`.
- Solo mostro una mejora parcial en `H3`, insuficiente para compensar el deterioro en `H1` y `H2`.
- La micro-rama no cambia el cierre principal de `E1`.

Decision:

- no correr `E1_1_v2_bayesian_control`
- cerrar `E1.1 Bayesian` como verificacion util pero no preferible

Documento de cierre:

- [resumen_micro_rama_e1_1_bayesian.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_micro_rama_e1_1_bayesian.md)

### 2026-03-23 | E2 Huber limpio

- Se abrió `E2_v1_clean` como baseline robusto.
- Se corrió `E2_v2_clean` como control de convergencia.
- Se corrió `E2_v3_clean` como prueba de memoria corta (`lags=1..4`).

Resultados:

- `E2_v1_clean`: `0.301907`
- `E2_v2_clean`: `0.301920`
- `E2_v3_clean`: `0.286465`

Decisión:

- `E2_v2_clean` descartó convergencia como explicación principal.
- `E2_v3_clean` mejoró internamente a Huber, pero no alcanzó a Ridge.
- `E2` quedó cerrada.

Rama asociada:

- `feature/e2-huber`

Documento clave:

- [resumen_metodologico_e2_huber.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e2_huber.md)

### 2026-03-23 a 2026-03-25 | E3 árboles tipo bagging

- Se abrió `E3_v1_clean` con `Random Forest` y `feature_mode=corr`.
- Se corrió `E3_v2_clean` con `Random Forest` y `feature_mode=all`.
- Se corrió `E3_v3_clean` con `ExtraTrees`.

Resultados:

- `E3_v1_clean`: `0.280892`
- `E3_v2_clean`: `0.266387`
- `E3_v3_clean`: `0.287289`

Decisión:

- `E3_v2_clean` quedó como mejor run interno de la familia E3.
- `ExtraTrees` no aportó mejora relevante.
- La familia `E3` sí mostró señal no lineal real, pero no desplazó a Ridge.

Rama asociada:

- `feature/e3-random-forest`

Documento asociado:

- [plan_inicial_e3_random_forest.md](/home/emilio/Documentos/RAdAR/Experimentos/plan_inicial_e3_random_forest.md)

### 2026-03-25 | E4 Boosting

- Se abrió `E4_v1_clean` con `xgboost_regressor`, `feature_mode=all`, `target_mode=nivel`.
- Se corrió `E4_v2_clean` cambiando solo `feature_mode=corr`.
- Se corrió `E4_v3_clean` cambiando solo `target_mode=delta`.

Resultados:

- `E4_v1_clean`: `0.283934`
- `E4_v2_clean`: `0.297343`
- `E4_v3_clean`: `0.424774`

Decisión:

- `E4_v2_clean` no mejoró a `E4_v1_clean`.
- `E4_v3_clean` deterioró la familia de forma fuerte.
- `E4` quedó cerrada con evidencia suficiente en su rama base.
- La continuidad metodológica vuelve a `E5`, `E6`, `E7`, `E8` y solo después `E9`.

Rama asociada:

- `feature/e4-boosting`

### 2026-03-25 a 2026-03-30 | Auditoría maestra y preparación para stacking

- Se construyó el script [build_experiments_master_table.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/build_experiments_master_table.py).
- Se integró la regeneración automática de la auditoría al cierre de runs completos.
- Se amplió la tabla maestra con:
  - `runs_catalogo`
  - `metricas_por_horizonte_long`
  - `stacking_readiness`
  - `cobertura_predicciones`
  - `stacking_base_h1..h4`

Decisión:

- La infraestructura quedó lista para una futura familia de meta-modelado o stacking por horizonte.
- Aún falta estandarizar artefactos explicativos entre familias.

Rama asociada:

- `feature/auditoring-and-stacking`

### 2026-03-30 | E5 CatBoost

- Se ajustó `run_e5_catboost.py` al estándar de familias tabulares.
- Se abrió `E5_v1_clean` con `CatBoostRegressor`, `target_mode=nivel`, `feature_mode=all`, `lags 1..6`.
- Se corrió `E5_v2_clean` para aislar `feature_mode=corr`.
- Se corrió `E5_v3_clean` para bajar `depth`.
- Se abrió una ruta de tuning temporal interno acotado con `E5_v4_clean`.
- Se corrió `E5_v5_clean` como segunda ola focal de tuning.

Resultados:

- `E5_v1_clean`: `0.255259`
- `E5_v2_clean`: `0.261819`
- `E5_v3_clean`: `0.261319`
- `E5_v4_clean`: `0.247788`
- `E5_v5_clean`: `0.264427`

Decisión:

- `E5_v4_clean` queda como campeón interno de la familia.
- `E5_v4_clean` supera a `E1_v4_clean`, `E3_v2_clean` y `E4_v1_clean`.
- `E5_v4_clean` no supera a `E1_v5_clean`.
- `E5_v2_clean`, `E5_v3_clean` y `E5_v5_clean` no mejoraron al campeón.
- La familia `E5` queda abierta pero ya madura, con un ganador interno claro.

Rama asociada:

- `feature/e4-boosting`

### 2026-03-30 | E6 ARIMAX

- Se alineó `run_e6_arimax.py` al estándar del pipeline por familias.
- Se abrió `E6_v1_clean` con `SARIMAX(1,0,1)` y `feature_mode=corr`.
- Se corrió `E6_v2_clean` cambiando solo el universo exógeno a `feature_mode=all`.

Resultados:

- `E6_v1_clean`: `0.370318`
- `E6_v2_clean`: `0.445769`

Decisión provisional:

- `E6_v1_clean` fue una apertura débil, muy por debajo de `E5_v4_clean`, `E1_v4_clean` y `E1_v5_clean`.
- `E6_v2_clean` empeoró todavía más; ampliar exógenas no ayudó.
- La parsimonia exógena sí fue menos mala que `all`, pero la familia no quedó competitiva.
- `ARIMAX` mostró además muchos warnings de convergencia en la estimación por fold externo.
- La familia `E6` queda debilitada y deja de ser línea principal; si reaparece, tendría que ser con una sola hipótesis nueva muy controlada o como insumo de híbridos.

### 2026-03-30 | E7 Prophet con exógenas

- Se alineó `run_e7_prophet.py` al estándar del pipeline por familias.
- Se abrió `E7_v1_clean` como baseline parsimonioso con `feature_mode=corr`.
- Se corrió `E7_v2_clean` cambiando solo el universo exógeno a `feature_mode=all`.
- Se corrió `E7_v3_clean` manteniendo `feature_mode=corr` y subiendo `changepoint_prior_scale` de `0.05` a `0.20`.

Resultados:

- `E7_v1_clean`: `0.325502`
- `E7_v2_clean`: `0.681992`
- `E7_v3_clean`: `0.321328`

Decisión:

- `Prophet` supera con claridad a `E6`, pero no entra al bloque contendiente del proyecto.
- `feature_mode=all` colapsó la familia; la amplitud exógena metió ruido y elevó muchísimo los errores numéricos.
- mayor flexibilidad en changepoints ayudó un poco frente al baseline (`E7_v3_clean > E7_v1_clean`), sobre todo en `H2/H3`, pero no volvió competitiva a la familia frente a `E5_v4_clean`, `E1_v4_clean` o `E3_v2_clean`.
- `E7` queda como familia intermedia: útil como referencia temporal estructurada, no como línea principal.

### 2026-04-01 | E8 híbrido residual

- Se rehízo `run_e8_hibrido_residuales.py` para que el learner residual ya no vea residuales in-sample optimistas.
- La familia quedó definida como una arquitectura de dos etapas con:
  - modelo base
  - residuales OOF temporales dentro de cada fold externo
  - learner residual
  - reconstrucción `y_pred_final = y_pred_base + y_pred_residual`
- Se corrieron tres variantes canónicas:
  - `E8_v1_clean`: base `Ridge`, residual `CatBoost`
  - `E8_v2_clean`: base `CatBoost`, residual `Ridge`
  - `E8_v3_clean`: base `CatBoost`, residual `Prophet`

Resultados:

- `E8_v1_clean`: `0.336482`
- `E8_v2_clean`: `0.285721`
- `E8_v3_clean`: `0.627755`

Decisión:

- `E8_v2_clean` fue el mejor híbrido residual de apertura.
- el espejo `CatBoost -> Ridge residual` sí agregó valor frente a `E8_v1_clean`, pero no superó a `E4_v1_clean`, `E3_v2_clean`, `E1_v4_clean`, `E5_v4_clean` ni `E1_v5_clean`.
- `E8_v3_clean` colapsó; usar `Prophet` como residual learner sobre `CatBoost` no fue una dirección útil.
- `E8` queda como familia intermedia: metodológicamente válida y auditable, pero sin mejora suficiente para volverse nueva línea principal.

### 2026-04-01 | Curacion de tabla base para E9 stacking controlado

- Se amplió el builder [build_experiments_master_table.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/build_experiments_master_table.py) para generar una copia curada y versionada de la tabla maestra orientada a `E9`.
- Se creó el workbook:
  - [tabla_maestra_experimentos_radar_e9_curada.xlsx](/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar_e9_curada.xlsx)
- Se generó la nota metodológica:
  - [preparacion_tabla_e9_stacking_controlado.md](/home/emilio/Documentos/RAdAR/Experimentos/preparacion_tabla_e9_stacking_controlado.md)
- La curacion dejó:
  - constructos explicitos por run
  - bases finales `E9_base_h1..h4`
  - reservas documentadas por horizonte
  - exclusiones metodologicamente justificadas

Decision:

- `E9` queda preparada a nivel de tabla curada y bases pequenas por horizonte.
- El nucleo final recomendado para `E9` gira alrededor de `E1_v5_clean` y `E5_v4_clean`, con rotacion controlada de `E3_v2_clean`, `E2_v3_clean` y `E7_v3_clean`.
- `E8_v2_clean` queda solo como reserva puntual y no como candidato principal.
- La siguiente implementacion ya no necesita mas curacion de tabla; necesita adaptar `run_e9_stacking.py` para consumir estas hojas curadas.

### 2026-04-01 | E9 stacking clasico controlado

- Se reescribio [run_e9_stacking.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e9_stacking.py) para que deje de usar el stacking tabular generico anterior.
- El nuevo runner:
  - lee directamente [tabla_maestra_experimentos_radar_e9_curada.xlsx](/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar_e9_curada.xlsx),
  - consume `E9_base_h1..h4`,
  - restringe por default a `fila_completa == True`,
  - reconstruye `y_current` desde el dataset maestro solo para evaluar metricas Radar,
  - y hace tuning temporal interno de `alpha` para un meta-modelo `Ridge`.
- Se corrio [E9_v1_clean_20260401_065743](/home/emilio/Documentos/RAdAR/Experimentos/runs/E9_v1_clean_20260401_065743).

Resultados:

- `E9_v1_clean`: `0.268475`

Lectura:

- `E9_v1_clean` no mejora al mejor modelo individual global del proyecto.
- Tampoco mejora al mejor base comun dentro del subset curado del propio stacking (`E1_v5_clean` y `E5_v4_clean` siguen mejores).
- El ensemble solo aporta una mejora puntual en `H3`; en `H1`, `H2` y `H4` queda por debajo del mejor base del horizonte.
- El tuning de `alpha` mostro regularizacion muy alta en buena parte de los folds, lo que sugiere que el meta-modelo encontro poca senal adicional mas alla de un promedio fuertemente encogido.

Decision:

- `E9` queda abierta, pero esta primera apertura no justifica declararla nueva familia lider.
- La lectura correcta es `trade-off dudoso`: mejora local en `H3`, pero no mejora global defendible frente a `E1_v5_clean` ni `E5_v4_clean`.
- Si la familia continua, el siguiente paso ya no debe ser meter mas bases sin control, sino abrir una sola hipotesis nueva y contenida o pasar a una familia posterior tipo `E10` contextual.

### 2026-04-01 | Decision metodologica posterior a E9_v2_clean

- Se corrio [E9_v2_clean_20260401_070431](/home/emilio/Documentos/RAdAR/Experimentos/runs/E9_v2_clean_20260401_070431) con `Huber` como meta-modelo, misma tabla curada, mismas columnas y mismas filas completas que `E9_v1_clean`.

Resultados:

- `E9_v2_clean`: `0.227510`

Lectura:

- `E9_v2_clean` mejora de forma clara la rama `E9`.
- La mejora viene sobre todo por una lectura operativa mas fuerte en:
  - deteccion de caidas
  - direccion
  - trade-off de riesgo en `H1-H2`
- Esa mejora no debe leerse como reemplazo simple de `E1_v5_clean`.

Decision:

- `E1_v5_clean` queda como mejor referente numerico puro observado hasta ahora.
- `E9_v2_clean` queda como mejor referente actual orientado a riesgo, direccion y caidas.
- La diferencia entre ambos no se registra como contradiccion sino como dualidad funcional del Radar.
- `E9` queda util, no descartada, no ganadora absoluta y en pausa metodologica.
- `E10` pasa a ser la siguiente linea activa del proyecto.
- `E11` queda abierta formalmente solo como familia conceptual futura, todavia no ejecutable.

Documento asociado:

- [actualizacion_metodologica_post_e9_e10_e11.md](/home/emilio/Documentos/RAdAR/Experimentos/actualizacion_metodologica_post_e9_e10_e11.md)

### 2026-03-30 | Rama planificada de clasificacion C1-C4

- Se dejo documentada una rama paralela de clasificacion del movimiento del Radar.
- Se reorganizo la documentacion en un prompt rector y una carpeta por familia:
  - `09_clasificacion_radar/`
  - `10_clasificacion_random_forest/`
  - `11_clasificacion_xgboost/`
  - `12_clasificacion_catboost/`
  - `13_clasificacion_lightgbm/`
- Se dejaron preparados los runners por familia:
  - `run_c1_random_forest_classifier.py`
  - `run_c2_xgboost_classifier.py`
  - `run_c3_catboost_classifier.py`
  - `run_c4_lightgbm_classifier.py`
- Se guardo un prompt operativo por familia:
  - `C1` RandomForestClassifier
  - `C2` XGBoostClassifier
  - `C3` CatBoostClassifier
  - `C4` LightGBMClassifier
- Se dejo explicitado que cualquier futura implementacion debe registrar todo con `RadarExperimentTracker` igual que en regresion.

Estado:

- documentada y trazable
- scripts preparados
- nota historica original: en este punto todavia no habia corridas ejecutadas registradas en la bitacora

Actualizacion posterior de estado:

- `C1` si tuvo tres corridas canonicas el mismo 2026-03-30:
  - [C1_v1_clean_20260330_085747](/home/emilio/Documentos/RAdAR/Experimentos/runs/C1_v1_clean_20260330_085747)
  - [C1_v2_clean_20260330_085846](/home/emilio/Documentos/RAdAR/Experimentos/runs/C1_v2_clean_20260330_085846)
  - [C1_v3_clean_20260330_085854](/home/emilio/Documentos/RAdAR/Experimentos/runs/C1_v3_clean_20260330_085854)
- Las tres corridas empataron por colapso del target a clase unica y no dejaron señal discriminativa util.
- `C1` queda evaluada y pausada tempranamente.
- `C2`, `C3` y `C4` siguen solo con infraestructura y prompts preparados, sin corrida real.

Documento asociado:

- [plan_inicial_clasificacion_radar_c1_c4.md](/home/emilio/Documentos/RAdAR/Experimentos/plan_inicial_clasificacion_radar_c1_c4.md)

## 2026-04-01 | Construccion de tabla operativa E10

Se construyo la infraestructura de datos especifica para `E10` como familia de meta-seleccion / gating contextual, sin correr todavia un modelo final de la familia.

Artefactos principales generados:

- [tabla_e10_meta_selector_base.csv](/home/emilio/Documentos/RAdAR/Experimentos/tabla_e10_meta_selector_base.csv)
- [tabla_e10_meta_selector_base.xlsx](/home/emilio/Documentos/RAdAR/Experimentos/tabla_e10_meta_selector_base.xlsx)
- [inventario_columnas_e10.csv](/home/emilio/Documentos/RAdAR/Experimentos/inventario_columnas_e10.csv)
- [diccionario_tabla_e10.md](/home/emilio/Documentos/RAdAR/Experimentos/diccionario_tabla_e10.md)
- [resumen_construccion_tabla_e10.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_construccion_tabla_e10.md)

Pool base incluido:

- `E1_v5_clean`
- `E2_v3_clean`
- `E3_v2_clean`
- `E5_v4_clean`
- `E7_v3_clean`
- `E9_v2_clean`

Pool explicitamente excluido de la tabla canonica E10:

- `E1_v4_clean`
- `E4_v1_clean`
- `E6_v1_clean`
- `E8_v2_clean`

Lectura metodologica dejada por escrito:

- la tabla E10 es distinta de la base usada por `E9`;
- la unidad de analisis canonica es `fila-horizonte`;
- se separaron features observables, diagnosticos retrospectivos, targets del selector y columnas prohibidas para entrenamiento;
- la base quedo `utilizable con reservas` tanto para selector duro como para gating blando;
- la principal limitacion de solapamiento completo proviene de `E9_v2_clean`.

Estado:

- `E10` deja de estar "no iniciada" en sentido de infraestructura;
- queda en estado de premodelado;
- no se corrio todavia ningun `run` canonico de `E10`.

Nota de actualizacion posterior:

- Esta entrada conserva el estado de la fase de infraestructura.
- Posteriormente si se corrio [E10_v1_clean_20260401_090439](/home/emilio/Documentos/RAdAR/Experimentos/runs/E10_v1_clean_20260401_090439), por lo que `E10` ya no debe leerse hoy como premodelado.

## 2026-04-01 | E10_v1_clean meta-selector duro

- Se implemento y corrio [E10_v1_clean_20260401_090439](/home/emilio/Documentos/RAdAR/Experimentos/runs/E10_v1_clean_20260401_090439) como primera corrida canonica de `E10`.
- El runner [run_e10_meta_selector.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e10_meta_selector.py) usa solo columnas permitidas de la tabla E10, validacion `walk-forward expanding`, `LogisticRegression` regularizado y reconstruccion numerica final a partir del modelo base seleccionado.

Resultados:

- `E10_v1_clean`: `0.271220`

Lectura:

- `E10_v1_clean` fue metodologicamente limpio, pero no competitivo.
- No supero al selector fijo en el global.
- No supero a `E1_v5_clean`.
- No supero a `E9_v2_clean`.
- La señal mas util aparecio en `H4`, con aportes parciales en `H2-H3`, pero sin mejora global defendible.

Decision historica:

- Esta entrada conserva la lectura inmediatamente posterior a la corrida.
- El estado canonico posterior ya no es `modelado inicial fragil`, sino `cerrada para promocion bajo su formulacion actual`.
- Ver cierre vigente en [cierre_formal_e10_no_promocionable.md](/home/emilio/Documentos/RAdAR/Experimentos/cierre_formal_e10_no_promocionable.md).

## Lectura consolidada vigente

- Referente numerico puro principal: `E1_v5_clean`
- Referente operativo de riesgo-direccion-caidas: `E9_v2_clean`
- Referencia parsimoniosa: `E1_v4_clean`
- Mejor H2 y H4 por `loss_h`: `E2_v3_clean`
- Mejor H3 por `loss_h`: `E1_v2_clean`
- Mejor familia no lineal base de bagging: `E3_v2_clean`
- Mejor familia no lineal tabular abierta: `E5_v4_clean`
- Familias cerradas: `E1`, `E2`, `E4`
- Familias abiertas o vigentes como referencia: `E3`, `E5`, `E7`, `E8` y `E9`
- `E10` ya fue abierta formalmente y queda cerrada para promocion, no en premodelado
- La clasificacion ya no debe describirse como solo planificada: `C1` tuvo corridas reales; `C2-C4` siguen sin corrida
- La capa explicativa transversal sigue siendo parcial intra-familia: hay seleccion de variables por horizonte en algunos runs, pero no coeficientes/importancias/SHAP homologados entre familias

## Próximo paso lógico

Nota de alcance:

- Esta lectura quedo superada por la apertura dual controlada de `E11` del `2026-04-03`.
- El estado canonico posterior debe leerse hoy junto con [resumen_metodologico_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e11_dual.md).

- En esa lectura, `E9` quedaba en pausa metodologica: util, pero no definitiva.
- En esa lectura, `E10` ya no seguia como familia activa para promocion.
- En esa lectura, `E11` quedaba solo planificada.

Secuencia vigente:

1. mantener `E1_v5_clean` como benchmark numerico puro principal;
2. mantener `E9_v2_clean` como benchmark operativo de riesgo-direccion-caidas;
3. cerrar `E10` para promocion bajo su formulacion actual;
4. reservar `E11` como familia futura explicitamente dual.
