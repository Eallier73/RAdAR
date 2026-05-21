Objetivo del experimento

Quiero una corrida limpia, comparable y bien cerrada para probar si ExtraTreesRegressor puede superar el desempeño observado hasta ahora en la familia no lineal.

Las metas concretas son:

- conservar la señal útil que apareció en la familia de árboles, especialmente en H3;
- intentar mejorar H4, sobre todo en:
  - direction_accuracy
  - deteccion_caidas
- evaluar si la mayor aleatoriedad de ExtraTrees ayuda a captar mejor relaciones no lineales con menos sesgo;
- comparar formalmente contra:
  - E3_v1_clean
  - E3_v2_clean si ya existe al momento de correr
  - E2_v3_clean
  - E1_v4_clean
  - E1_v5_clean

Hipótesis metodológica

La hipótesis de E3_v3_clean es esta:

Random Forest mostró que sí hay señal no lineal útil, pero puede estar quedándose corto en flexibilidad o sensibilidad operativa.
ExtraTrees, al inyectar más aleatoriedad en los splits, podría reducir parte de la rigidez del bosque y capturar mejor interacciones complejas, mejorando especialmente horizontes donde importa detectar cambio de dirección y caídas.

Lo que quiero probar no es solo si baja MAE, sino si la familia de árboles puede volverse más útil para Radar en términos de comportamiento operativo.

Modelo a usar

Usa:

- ExtraTreesRegressor

No uses RandomForest en esta corrida. Debe quedar claramente separada como experimento nuevo dentro de la misma familia de árboles.

Diseño experimental

Parámetros base que deben mantenerse comparables

Mantén, salvo donde se indique lo contrario:

- validación externa: walk-forward expanding
- horizontes: 1, 2, 3, 4
- target_mode = nivel
- lags = 1,2,3,4,5,6
- pipeline limpio y comparable con E1/E2/E3
- mismo esquema de logging, artefactos y comparaciones
- reproducibilidad explícita con random_state

Feature mode

La preferencia inicial es:

- feature_mode = corr

Quiero aislar principalmente el efecto del cambio de algoritmo, no mezclar al mismo tiempo algoritmo + universo de features.

Solo cambia a all si encuentras una razón técnica fuerte y la dejas claramente documentada. En principio, mantener corr es lo preferible.

Configuración sugerida para ExtraTrees

Quiero una configuración deliberada, no una búsqueda caótica.

Usa una configuración base razonable orientada a darle flexibilidad al modelo, por ejemplo en esta dirección:

- n_estimators = 600
- max_depth = None o una profundidad amplia si ves que conviene acotarla
- min_samples_split = 2
- min_samples_leaf = 1
- max_features = sqrt o 0.5, pero decide una sola configuración principal y justifícala
- bootstrap = False salvo que tengas una razón clara para activarlo
- random_state fijo

No quiero grid masivo ni tuning desordenado.
Quiero una corrida interpretable: una apuesta metodológica clara.

Si el runner actual ya permite parametrizar esto elegantemente, reutilízalo. Si no, adapta o crea el runner mínimo necesario sin ensuciar el pipeline.

Qué debes tocar en código

Haz los cambios mínimos necesarios para que la corrida quede bien integrada al proyecto.

Puedes:

- crear un runner específico para árboles si hace falta;
- reutilizar estructura existente de E3 si ya está limpia;
- mover helpers comunes a utilería compartida si detectas duplicación;
- mantener compatibilidad con la organización de artefactos ya usada.

No rompas corridas previas.
No metas cambios laterales innecesarios.

Qué debes ejecutar

Corre la corrida completa con run_id = E3_v3_clean y documenta el comando exacto ejecutado.

La corrida debe producir, como mínimo:

- metadata_run.json
- parametros_run.json
- metricas_horizonte.json
- resumen_modeling_horizontes.json
- predicciones_h1.csv a predicciones_h4.csv
- features_seleccionadas_h1.csv a features_seleccionadas_h4.csv si aplica la selección
- archivos de comparación contra:
  - E3_v1_clean
  - E3_v2_clean si ya existe
  - E2_v3_clean
  - E1_v4_clean
  - E1_v5_clean

Si el comparador actual solo acepta una referencia a la vez, genera varias comparaciones por separado, como se ha venido haciendo.

Criterios de evaluación

Quiero evaluación completa con lógica Radar, no lectura reducida a MAE.

Debes reportar por horizonte:

- mae
- rmse
- direction_accuracy
- deteccion_caidas
- loss_h

Y globalmente:

- L_total_Radar

Regla de lectura

Interpreta el resultado con esta jerarquía:

- primero L_total_Radar;
- luego comportamiento en H3 y H4;
- después deteccion_caidas;
- luego direction_accuracy;
- al final errores numéricos.

No presentes como “mejora” algo que solo mejora décimas de MAE pero empeora el comportamiento operativo.

Preguntas que debes responder al cerrar la corrida

Quiero respuestas explícitas y ordenadas a estas preguntas:

- ¿E3_v3_clean mejora a E3_v1_clean?
- ¿E3_v3_clean mejora a E3_v2_clean?
  Si E3_v2 aún no existe al momento de correr, dilo explícitamente.
- ¿La mejora, si existe, viene por H3, por H4, o solo por error numérico?
- ¿ExtraTrees mejora la detección de caídas respecto a Random Forest?
- ¿E3_v3_clean supera a E2_v3_clean?
- ¿E3_v3_clean supera a E1_v4_clean?
- ¿E3_v3_clean supera a E1_v5_clean?
- ¿La familia de árboles sigue viva como candidata fuerte o ya conviene pasar a otra familia no lineal?

Formato de entrega esperado

La entrega final debe venir estructurada así:

A. Qué hiciste
- archivos modificados
- qué implementaste
- por qué esos cambios responden a la hipótesis
- comando exacto ejecutado

B. Resultado de la corrida
- tabla resumida por horizonte
- L_total_Radar
- comparaciones clave contra runs anteriores

C. Interpretación
- qué patrón apareció
- dónde mejora
- dónde empeora
- si ExtraTrees aporta algo distinto frente a Random Forest

D. Veredicto

Con una etiqueta clara, por ejemplo:

- mejora real
- mejora parcial
- sin mejora
- empeora

E. Siguiente paso recomendado

Con recomendación explícita, por ejemplo:

- seguir con E3_v4 afinando ExtraTrees;
- cerrar árboles y pasar a Gradient Boosting;
- probar HistGradientBoosting;
- probar otra familia no lineal.

Restricciones importantes

- no introducir leakage;
- no cambiar el esquema correcto de validación temporal;
- no mezclar demasiados cambios a la vez;
- no inflar conclusiones;
- no ocultar deterioros por horizonte;
- si hay trade-off, dilo con claridad;
- si ExtraTrees no aporta mejora sustantiva, reconócelo sin forzar narrativa.

Criterio de decisión si el resultado es mixto

Si el resultado sale ambiguo, usa esta lógica:

- si mejora L_total_Radar y además aporta algo en H3/H4, es avance real;
- si solo mejora MAE/RMSE pero no mejora dirección/caídas, no es avance relevante para Radar;
- si mejora claramente H4 sin destruir H3, vale la pena seguir la línea;
- si empeora H3 y H4, la familia ExtraTrees queda debilitada.

Descripción conceptual del experimento

Quiero que el experimento quede descrito así:

E3_v3_clean = ExtraTrees como variante de árboles más aleatoria para evaluar si una mayor flexibilidad mejora el desempeño operativo de Radar, especialmente en H3/H4 y detección de caídas.
