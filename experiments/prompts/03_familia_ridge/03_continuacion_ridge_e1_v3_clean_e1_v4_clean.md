Quiero que continúes la familia de experimentos E1 del proyecto Radar dentro de la familia Ridge, pero actualizando el plan experimental con base en un hallazgo metodológico ya confirmado.

CONTEXTO ACTUALIZADO
Ya se reconstruyó E1_v2 eliminando fuga temporal en la selección de alpha. La nueva versión oficial es:

- E1_v2_clean = Ridge + target nivel + feature_mode all + lags 1,2,3,4 + transform standard
- validación externa walk-forward expanding
- tuning interno temporal de alpha dentro de cada fold externo
- sin leakage temporal en tuning, scaling, selección o preparación

Hallazgo ya validado:
- E1_v2_clean corrige la fuga metodológica de E1_v2 original
- el impacto empírico fue pequeño/marginal
- E1_v2 original no queda invalidado históricamente, pero E1_v2_clean pasa a ser la referencia metodológica oficial vigente

IMPORTANTE
A partir de ahora:
- NO usar E1_v2 original como benchmark principal
- SÍ usar E1_v2_clean como baseline oficial de comparación
- Mantener E1_v2 original solo como antecedente histórico documentado

OBJETIVO DE ESTA ETAPA
Cerrar correctamente la fase inicial de comparación metodológica de la familia Ridge antes de expandir el grid completo.

Eso significa responder primero estas dos preguntas:

1. ¿Cambiar el target de nivel a delta mejora realmente la familia Ridge?
2. ¿Reducir variables con feature_mode=corr mejora realmente la familia Ridge?

Por tanto, en esta etapa NO quiero correr todavía toda la familia E1_v5...E1_v10.
Primero quiero que implementes, corras y analices:

- E1_v3_clean
- E1_v4_clean

y luego decidas si se justifica seguir.

REGLA GENERAL
Cada nueva versión debe cambiar SOLO una dimensión principal respecto al baseline E1_v2_clean.

No quiero cambios múltiples confusos.
No quiero leakage.
No quiero validación aleatoria.
No quiero selección de variables usando información futura.

ARQUITECTURA ESPERADA
Debes trabajar sobre el script de familia ya existente o su equivalente limpio, por ejemplo:
- run_e1_ridge_clean.py
o un script familia equivalente correctamente refactorizado

Debe aceptar por CLI como mínimo:
- --run-id
- --target-mode        (nivel, delta)
- --feature-mode       (all, corr, lasso)
- --lags               (ej. 1,2,3,4 o 1,2,3,4,5,6)
- --transform-mode     (none, standard, robust, winsor)
- --initial-train-size
- --horizons
- --inner-splits
- --alpha-selection-metric
- cualquier otro parámetro de control experimental necesario

REQUISITO METODOLOGICO CRITICO
La selección de alpha debe seguir siendo temporal e interna a cada fold externo.

Es decir:
- en cada fold externo, alpha se selecciona solo con train_data
- el test_data externo nunca participa en selección de alpha
- cualquier scaler, selector o transformador debe ajustarse solo con entrenamiento
- si hay selección de variables por correlación o lasso, debe hacerse de manera temporalmente correcta dentro del fold correspondiente

NO se permite:
- elegir alpha con toda la muestra
- calcular filtros de correlación con información futura
- seleccionar variables una sola vez con todos los datos y luego validar temporalmente
- ajustar transformaciones con train+test

VERSIONES A IMPLEMENTAR Y CORRER EN ESTA ETAPA

===================================
E1_v3_clean
===================================
Diseño:
- modelo = Ridge
- target_mode = delta
- feature_mode = all
- lags = 1,2,3,4
- transform_mode = standard
- misma validación externa walk-forward expanding
- mismo esquema limpio de tuning temporal interno para alpha

Hipótesis:
Si parte de la debilidad del baseline no está en el nivel absoluto sino en la dificultad para captar el movimiento, entonces cambiar el target de nivel a delta podría mejorar la detección de tendencia, especialmente en horizontes intermedios como H2 y H3.

Preguntas metodológicas:
- ¿Predecir delta en vez de nivel mejora direction_accuracy?
- ¿Mejora H2 o H3 de forma operativamente relevante?
- ¿La mejora dinámica viene acompañada de una pérdida excesiva en error numérico?
- ¿Delta vuelve más sensible al modelo ante virajes y caídas o solo agrega ruido?

Sentido dentro del proyecto:
E1_v3_clean prueba si la limitación de Ridge está en la definición del target más que en la familia lineal en sí.

===================================
E1_v4_clean
===================================
Diseño:
- modelo = Ridge
- target_mode = nivel
- feature_mode = corr
- lags = 1,2,3,4
- transform_mode = standard
- misma validación externa walk-forward expanding
- mismo esquema limpio de tuning temporal interno para alpha

Hipótesis:
Si usar todas las variables mete ruido, redundancia o inestabilidad, entonces una versión más parsimoniosa basada en correlación podría mejorar el desempeño global y/o la estabilidad del modelo, sobre todo en H2 y H3.

Preguntas metodológicas:
- ¿Reducir variables mediante un filtro por correlación mejora L_total_Radar?
- ¿Mejora los horizontes intermedios?
- ¿Conserva la señal útil o elimina información valiosa?
- ¿La parsimonia mejora la estabilidad, interpretabilidad y competitividad?

Sentido dentro del proyecto:
E1_v4_clean prueba si el problema no es Ridge, sino el exceso de variables.

REQUISITO ESPECIAL PARA feature_mode=corr
Debes documentar explícitamente:
- cómo se calcula el filtro por correlación
- sobre qué tramo temporal se calcula
- si se hace por fold externo o por fold interno
- cómo se evita leakage
- cuántas variables quedan por horizonte o en promedio

Si la implementación exacta más limpia requiere aplicar el filtro dentro del entrenamiento de cada fold externo, hazlo así.
Si requiere helper reusable, créalo.

ORDEN DE EJECUCION
Ejecuta en este orden:

1. verificar que el pipeline limpio soporte correctamente:
   - target_mode
   - feature_mode
   - tuning temporal interno de alpha
   - transformaciones dentro de pipeline
   - guardado de artefactos
   - métricas Radar por horizonte
   - L_total_Radar a nivel run

2. correr E1_v3_clean

3. analizar E1_v3_clean contra E1_v2_clean

4. correr E1_v4_clean

5. analizar E1_v4_clean contra E1_v2_clean y contra E1_v3_clean

6. aplicar regla de stop antes de pasar a E1_v5+

SALIDAS OBLIGATORIAS POR RUN
Cada corrida debe guardar como mínimo:

- metadata_run.json
- parametros_run.json
- metricas_horizonte.json
- resumen_modeling_horizontes.json
- predicciones_h1.csv
- predicciones_h2.csv
- predicciones_h3.csv
- predicciones_h4.csv
- alpha_tuning_horizontes.json

Si aplica selección de variables:
- features_seleccionadas_h1.csv
- features_seleccionadas_h2.csv
- features_seleccionadas_h3.csv
- features_seleccionadas_h4.csv
o un artefacto equivalente bien documentado

METRICAS OBLIGATORIAS POR HORIZONTE
Como mínimo:
- horizonte_sem
- mae
- rmse
- direction_accuracy
- deteccion_caidas
- l_num
- l_trend
- l_risk
- l_tol
- loss_h

METRICAS OBLIGATORIAS A NIVEL RUN
- L_total_Radar
- estado
- comentarios
- notas_config
- feature_count promedio o por horizonte

COMPARACION OBLIGATORIA EN ESTA ETAPA
Quiero una tabla comparativa consolidada solo entre:

- E1_v2_clean
- E1_v3_clean
- E1_v4_clean

La tabla debe incluir como mínimo:
- run_id
- target_mode
- feature_mode
- transform_mode
- lags
- feature_count promedio o por horizonte
- mae_promedio
- rmse_promedio
- direction_accuracy_promedio
- deteccion_caidas_promedio
- L_total_Radar
- observacion_breve

INTERPRETACION QUE DEBE ENTREGAR EL AGENTE
No quiero solo corridas técnicas.
Quiero una lectura analítica que responda:

1. ¿E1_v3_clean mejora realmente al baseline o solo cambia cosméticamente?
2. ¿E1_v4_clean mejora realmente al baseline o solo simplifica sin ganar desempeño?
3. ¿Cuál de las tres versiones es mejor globalmente?
4. ¿Cuál es mejor para H2?
5. ¿Cuál es mejor para H3?
6. ¿Target delta ayudó realmente?
7. ¿La parsimonia por correlación ayudó realmente?
8. ¿Ridge ya muestra potencial serio o sigue siendo solo baseline útil?
9. ¿Se justifica seguir a E1_v5, E1_v6, E1_v7, E1_v8, E1_v9 y E1_v10?

CRITERIOS DE DECISION
No declarar ganadora una versión por una sola métrica aislada.
La evaluación debe priorizar:

1. L_total_Radar
2. desempeño en H2 y H3
3. estabilidad de H1 y H4
4. direction_accuracy
5. deteccion_caidas
6. interpretabilidad y parsimonia

REGLAS DE LECTURA
1. Si una versión mejora claramente L_total_Radar y además mejora H2 sin deteriorar severamente H1/H3/H4:
- marcarla como "mejora real"

2. Si una versión mejora H2 pero empeora mucho H1 y/o H3:
- marcarla como "trade-off dudoso"

3. Si una versión mejora H3 pero no H2:
- marcarla como "mejora parcial"

4. Si mejora MAE pero empeora direction_accuracy o deteccion_caidas:
- marcarla como "mejora numérica no operativa"

5. Si mejora direction_accuracy y deteccion_caidas aunque MAE cambie poco:
- tratarla como mejora potencialmente valiosa

6. Si empeora L_total_Radar aunque mejore algo aislado:
- clasificarla como "no preferible"

7. Si dos versiones salen muy cercanas:
- preferir la más simple, estable e interpretable

REGLA DE STOP
MUY IMPORTANTE:
Después de correr y analizar E1_v3_clean y E1_v4_clean, NO sigas automáticamente con E1_v5...E1_v10.

Primero debes decidir si hubo una mejora clara respecto a E1_v2_clean.

Si ninguna de las dos mejora claramente al baseline:
- detener expansión automática de la familia Ridge
- concluir provisionalmente que Ridge sirve como baseline serio pero no muestra todavía evidencia suficiente para justificar expansión completa
- recomendar pasar a otra familia o replantear la siguiente fase

Si alguna de las dos sí mejora claramente:
- entonces sí recomendar explícitamente continuar con las siguientes versiones más complejas:
  - E1_v5
  - E1_v6
  - E1_v7
  - E1_v8
  - E1_v9
  - E1_v10

FORMATO DE INTERPRETACION DESPUES DE CADA RUN
Después de cada corrida nueva quiero esta mini lectura:

- Qué cambió respecto a E1_v2_clean
- Qué mejoró
- Qué empeoró
- Impacto en H1, H2, H3 y H4
- Impacto en L_total_Radar
- Veredicto provisional:
  - mejora real
  - mejora parcial
  - trade-off dudoso
  - no preferible
  - baseline útil pero superado

ENTREGABLES
Quiero que me devuelvas:

1. archivos modificados o creados
2. explicación breve de qué cambió en el script Ridge limpio
3. comandos exactos para correr:
   - E1_v3_clean
   - E1_v4_clean
4. tabla comparativa consolidada entre E1_v2_clean, E1_v3_clean y E1_v4_clean
5. interpretación metodológica breve pero clara
6. recomendación final:
   - continuar con E1_v5+ o detener expansión Ridge

CRITERIO DE EXITO
El trabajo estará bien hecho si:
- puedo correr las nuevas versiones desde terminal sin editar código manualmente
- quedan comparables entre sí
- respetan completamente la lógica temporal del proyecto Radar
- el análisis final permite decidir si la familia Ridge merece expansión o si debe quedarse como baseline metodológico serio pero limitado