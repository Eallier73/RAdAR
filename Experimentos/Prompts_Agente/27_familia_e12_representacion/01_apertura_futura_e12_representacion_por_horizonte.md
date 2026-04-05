Nombre: Apertura futura E12 representacion por horizonte

Quiero que prepares y ejecutes la apertura de una nueva familia experimental del proyecto Radar llamada `E12`, pero con una restricción metodológica central:

E12 no es una familia para “probar otro algoritmo”.
E12 es una familia para probar una hipótesis de representación.

Debes trabajar en continuidad estricta con toda la evidencia ya consolidada del proyecto, especialmente la fase analítica posterior a E11, donde ya quedó documentado lo siguiente:

1. En el subset común, `E1_v5_clean` y `E9_v2_clean` quedan casi empatados en el global, por lo que la ventaja de E9 no es una dominancia homogénea de arquitectura.
2. La ventaja operativa de `E9_v2_clean` se concentra sobre todo en `H1`.
3. La mejor recombinación ex post por horizonte fue `9111` (E9 en H1, E1 en H2-H4), pero quedó explícitamente marcada como no promocionable.
4. La lectura canónica de esa autopsia es que la ganancia probable está más en la diversidad de representación de las bases que en el meta-modelo de stacking como tal.
5. La fase cerró además con la conclusión de que no debe abrirse una familia nueva por inercia, sino solo con una hipótesis precisa y defendible.

Con base en eso, la misión de E12 es esta:

probar de manera limpia, temporalmente correcta y trazable si una representación enriquecida con señales provenientes de bases heterogéneas puede mejorar el desempeño, especialmente en `H1`, sin deteriorar el comportamiento de `H2-H4`.

IMPORTANTE
E12 no debe nacer como una excusa para reciclar E9 ex post.
E12 no debe convertir la recombinación `9111` en sistema promocionable.
E12 no debe abrir un selector ex post por horizonte.
E12 no debe reabrir E10.
E12 no debe mezclar en la misma corrida varias preguntas metodológicas al mismo tiempo.
E12 no debe meter leakage ni snooping de ninguna forma.
E12 no debe usar información fuera del punto temporal disponible en cada fold.
E12 no debe derivar features desde predicciones de evaluación futura ni desde tablas ya curadas con conocimiento ex post de desempeño.

OBJETIVO SUSTANTIVO DE E12

La hipótesis sustantiva que quiero que pongas a prueba es esta:

“Si la ventaja observada en E9 proviene principalmente de diversidad de representación y no del meta-modelo en sí, entonces un modelo simple, estable y trazable alimentado con features enriquecidas derivadas de salidas base heterogéneas debería capturar parte de la mejora de H1 sin perder la robustez de E1 en H2-H4.”

Dicho de otro modo:
E12 debe probar si la señal útil de E9 puede absorberse dentro de una formulación más simple y defendible, usando enriquecimiento de representación en lugar de complejidad arquitectónica.

PREGUNTA METODOLÓGICA CENTRAL

La pregunta que E12 debe responder es:

¿la mejora operativa observada en H1 puede reproducirse parcialmente mediante features enriquecidas de representación, manteniendo un modelo base simple y limpio, sin necesidad de stacking promocionable ni de selección ex post por horizonte?

SUBPREGUNTAS

1. ¿Una representación enriquecida mejora `H1` respecto a `E1_v5_clean`?
2. ¿Esa mejora, si aparece, se logra sin empeorar de forma importante `H2-H4`?
3. ¿La mejora proviene de señales de desacuerdo, diversidad o régimen entre modelos base?
4. ¿La mejora es estable o solo un artefacto frágil del corto plazo?
5. ¿La ganancia se ve en `L_total_Radar`, o solo en componentes específicos como `direction_accuracy` y `deteccion_caidas`?
6. ¿La representación enriquecida ayuda más a leer arranques inmediatos que trayectorias medias?
7. ¿vale la pena abrir luego una segunda rama más rica de representación, o la hipótesis queda agotada en esta primera apertura?

ALCANCE DE E12

E12 debe ser una familia de representación controlada, no una familia de exploración caótica.

La apertura debe ser corta, disciplinada y con variantes pocas pero muy informativas.

No quiero diez experimentos apenas diferenciados.
Quiero pocas corridas, muy limpias, donde se pueda atribuir causalidad metodológica.

ARQUITECTURA GENERAL

Debes construir E12 con este principio:

- mantener el mismo marco de evaluación temporal del proyecto
- preservar comparabilidad estricta con E1–E11
- usar como modelo principal una familia simple y ya conocida
- enriquecer las features de entrada con información derivada de modelos base o de su desacuerdo, pero solo de manera temporalmente válida

La familia principal sugerida para esta apertura es:

- `Ridge` como modelo base principal de E12

Opcionalmente, si la infraestructura ya quedó muy reusable y no rompe comparabilidad ni trazabilidad, puedes permitir como variante secundaria un modelo lineal robusto equivalente, pero la apertura principal debe girar alrededor de una base simple y regularizada.

No abras aquí XGBoost, CatBoost ni meta-modelos complejos.
La pregunta no es si otro algoritmo gana.
La pregunta es si la representación gana.

INSUMOS PERMITIDOS

Puedes construir features enriquecidas solo a partir de insumos que sean temporalmente válidos dentro de cada fold externo y cada horizonte.

Ejemplos de insumos permitidos, siempre que se construyan correctamente dentro del pipeline temporal:

1. predicciones OOF o pseudo-OOF de modelos base ya definidos para el tramo de entrenamiento
2. predicciones históricas alineadas por fecha, solo cuando estén disponibles sin contaminar evaluación
3. medidas de desacuerdo entre bases:
   - rango
   - desviación estándar
   - distancia entre predicción lineal y no lineal
   - spread entre familia lineal y familia no lineal
4. features de régimen observables en t:
   - volatilidad reciente del target
   - magnitud reciente de cambios
   - estabilidad o inercia local
   - magnitud de rezagos recientes
5. indicadores de contexto derivados solo de datos observables en t
6. features de consenso o conflicto entre modelos base, siempre construidas sin usar el y futuro

INSUMOS PROHIBIDOS

Queda prohibido usar cualquier variable o construcción que incorpore conocimiento ex post del fold de evaluación o de la fila futura.

Ejemplos explícitamente prohibidos:

1. usar el mejor modelo por fila definido con base en error futuro
2. usar etiquetas como “modelo ganador por observación” construidas con conocimiento del target futuro
3. usar columnas derivadas de la tabla E10 o de cualquier tabla operativa que haya sido curada con criterio ex post para selección por fila
4. usar combinaciones horizontales tipo `9111` como sistema entrenable promocionable
5. usar métricas de performance futura como feature
6. recalcular selección de bases usando el comportamiento del mismo tramo de evaluación
7. usar predicciones base generadas con entrenamiento que vea el futuro del fold correspondiente
8. cualquier forma de leakage entre horizontes, entre folds o entre tablas auxiliares y evaluación

PRINCIPIO DE CONSTRUCCIÓN

Toda feature enriquecida debe poder responder afirmativamente a esta pregunta:

“¿esta variable habría estado disponible de forma realista en el momento exacto en que el modelo debía predecir ese horizonte?”

Si la respuesta es no, no se usa.

ESTÁNDAR DE VALIDACIÓN

Debes mantener exactamente el marco metodológico ya canónico del proyecto:

- validación externa temporal tipo walk-forward expanding
- mismos horizontes `1,2,3,4`
- mismo dataset base canónico
- mismas métricas de evaluación
- misma función de pérdida Radar
- misma lógica de trazabilidad por horizonte
- mismas reglas de guardado de artefactos y logging

No uses validación aleatoria.
No uses KFold estándar.
No uses mezcla temporal.
No uses tuning que vea el futuro.

SELECCIÓN DE FEATURES Y PREPROCESAMIENTO

Cualquier transformación o selección debe quedar encapsulada dentro del pipeline temporal correcto.

Si agregas features de representación:
- documenta exactamente cómo se calculan
- documenta en qué momento del pipeline se calculan
- documenta qué insumos usan
- documenta por qué no introducen leakage
- documenta si dependen de predicciones base y cómo se generan esas predicciones dentro del fold

Si una feature requiere una predicción base:
debe quedar claro si es:
- predicción entrenada solo con pasado disponible
- predicción OOF en train
- predicción forward válida para test

No se aceptan shortcuts opacos.

ENTREGABLES TÉCNICOS OBLIGATORIOS

Debes crear o actualizar los componentes necesarios para que E12 quede como una familia legítima y auditable dentro del proyecto.

Eso incluye, según corresponda:

1. runner principal nuevo, por ejemplo:
   - `run_e12_representacion.py`
   o un nombre equivalente claro y consistente

2. helpers reutilizables si hacen falta para:
   - generar features de representación
   - alinear predicciones base temporalmente
   - calcular spreads / desacuerdos
   - construir variables de régimen observables

3. integración completa con:
   - `experiment_logger.py`
   - `pipeline_common.py`
   - tablas maestras y auditoría retrospectiva
   - README técnico
   - bitácora experimental
   - plan de experimentación

4. artefactos por run:
   - predicciones por horizonte
   - métricas por horizonte
   - features seleccionadas o usadas por horizonte
   - configuración exacta del run
   - inventario de columnas enriquecidas
   - documentación de procedencia de cada constructo nuevo
   - resumen metodológico del run
   - comparación contra benchmarks vigentes

DOCUMENTACIÓN DE CONSTRUCTOS

Esto es especialmente importante.

Toda nueva feature de representación debe quedar registrada con una tabla o documento que explique:

- nombre de la feature
- definición exacta
- fórmula o procedimiento
- fuente
- momento temporal en que existe
- por qué es válida sin leakage
- intuición sustantiva de qué intenta capturar
- horizonte al que se aplica, si no aplica a todos

No quiero columnas opacas tipo `meta_signal_1`, `score_mix_2`, etc., sin explicación metodológica.

BENCHMARKS DE COMPARACIÓN OBLIGATORIOS

E12 no se evalúa en abstracto.
Debes compararlo explícitamente contra los benchmarks vigentes y relevantes.

Comparación mínima obligatoria contra:

1. `E1_v5_clean` como benchmark numérico lineal principal
2. `E9_v2_clean` como referencia operativa de diversidad / stacking
3. si aplica y la comparación es pertinente, `E1_v4_clean` como referencia parsimoniosa

La comparación debe dejar claro:

- global `L_total_Radar`
- desempeño por horizonte
- comportamiento en `H1`
- trade-off en `H2-H4`
- direction accuracy
- detección de caídas
- si la mejora es global o localizada
- si la mejora viene a costa de degradar otros horizontes

VARIANTES INICIALES DE E12

Quiero una apertura corta de tres variantes, cuidadosamente diferenciadas.

========================
E12_v1_clean
========================

Rol:
baseline de representación mínima enriquecida

Diseño:
- modelo base simple y regularizado
- usar dataset canónico base
- agregar solo un bloque pequeño y muy defendible de features de representación
- ese bloque debe ser el más parsimonioso posible

Sugerencia de contenido:
- predicción base lineal de referencia
- una o pocas señales de desacuerdo entre familias base
- una o pocas señales de régimen observable en t

Hipótesis:
si una pequeña capa de representación extra ya logra mejorar H1 sin dañar H2-H4, entonces la lectura de la autopsia es correcta y la ventaja de E9 sí puede estar en la representación.

Pregunta específica:
¿un enriquecimiento parsimonioso y defendible captura parte de la ventaja de corto plazo sin introducir complejidad innecesaria?

========================
E12_v2_clean
========================

Rol:
variante de representación ampliada

Diseño:
- misma base que E12_v1_clean
- ampliar de forma controlada el bloque de representación
- incorporar más señales de diversidad o desacuerdo entre bases, pero sin volver esto un stacking disfrazado

Hipótesis:
si la ganancia proviene de diversidad funcional real entre familias, una representación más rica debería mejorar más H1 o estabilizar la mejora.

Pregunta específica:
¿una capa más rica de representación mejora realmente o solo mete ruido y sobreajuste?

Restricción:
debe seguir siendo claramente una familia de representación, no un meta-modelo de stacking oculto.

========================
E12_v3_clean
========================

Rol:
variante de control / stress test metodológico

Diseño:
- misma lógica general
- introducir una modificación única y claramente interpretable para tensionar la hipótesis
- por ejemplo:
  - quitar señales de régimen y dejar solo desacuerdo entre modelos
  o
  - quitar desacuerdo y dejar solo régimen
  o
  - usar una versión más parsimoniosa de selección sobre el bloque enriquecido

Hipótesis:
esta corrida debe ayudar a identificar de dónde proviene la señal útil, no solo si “más features” ayudan.

Pregunta específica:
¿la mejora potencial viene del desacuerdo entre modelos, del régimen temporal observable, o simplemente de haber ampliado el espacio de entrada?

NOTA:
elige una sola de esas lógicas para E12_v3_clean y documenta por qué esa tensión metodológica era la más informativa.

QUÉ NO QUIERO EN ESTAS TRES VARIANTES

- no abrir tuning masivo
- no abrir docenas de hiperparámetros
- no abrir árboles, boosting o deep learning
- no abrir clasificación todavía
- no mezclar regresión y clasificación en la misma familia
- no convertir esta etapa en reedición de E9
- no usar umbrales ternarios aquí
- no vender una mejora ex post por horizonte como si fuera evidencia prospectiva

CRITERIOS DE LECTURA DE RESULTADOS

Quiero que la interpretación final responda con disciplina estas preguntas:

1. ¿E12 mejora de forma real y defendible a `E1_v5_clean`?
2. ¿la mejora se concentra en `H1`?
3. ¿esa mejora preserva razonablemente `H2-H4`?
4. ¿E12 captura parte de la ventaja operativa de E9 sin heredar toda su complejidad?
5. ¿la señal parece venir de representación y no solo de casualidad experimental?
6. ¿vale la pena expandir E12 o debe cerrarse rápido?

REGLAS DE DECISIÓN

Debes dejar por escrito desde el principio estas reglas:

1. Si E12 no mejora de forma clara y defendible frente a `E1_v5_clean`, no se expande por inercia.
2. Si E12 mejora solo H1 pero destruye `H2-H4`, eso debe registrarse como hallazgo parcial, no como promoción automática.
3. Si E12 captura una parte relevante de la ventaja de H1 sin deterioros fuertes, entonces sí justifica una segunda micro-rama futura.
4. Si la mejora aparece solo en combinaciones difíciles de defender o poco trazables, no se promociona.
5. Ninguna variante de E12 debe promocionarse solo por parecerse ex post a `9111`.
6. Toda mejora debe leerse contra comparadores homogéneos y bajo el mismo subset cuando corresponda.

NO PROMOCIÓN EX ANTE

Deja explícito desde la apertura que:

- E12 nace como familia exploratoria controlada
- ninguna combinación ex post por horizonte promociona nada
- ninguna sensibilidad favorable aislada promociona nada
- ningún run de E12 se considera candidato operativo sin pasar por comparación completa, trazabilidad y lectura metodológica consolidada

ARCHIVOS A CREAR O ACTUALIZAR

Quiero que, además de correr la familia, actualices o crees lo necesario para dejar continuidad documental impecable:

- prompt guardado de apertura de E12
- actualización en `plan_de_experimentacion_radar.md`
- actualización en `bitacora_experimental_radar.md`
- actualización en `README.md`
- documentación específica de constructos de representación
- resumen metodológico de apertura de E12
- resultados auditables por run y por horizonte
- incorporación retrospectiva a tablas maestras y grid, si corresponde

SALIDA ESPERADA

Al final necesito que entregues:

1. qué implementaste exactamente
2. qué variantes corriste
3. qué features nuevas construiste
4. por qué son válidas temporalmente
5. qué resultados obtuvo cada variante por horizonte y global
6. comparación contra `E1_v5_clean` y `E9_v2_clean`
7. lectura metodológica disciplinada
8. recomendación única:
   - cerrar E12
   - expandir E12
   - o dejarlo como hallazgo parcial sin promoción

TONO METODOLÓGICO

Trabaja con máxima disciplina experimental.
No maquilles resultados.
No vendas como “modelo superior” algo que solo sea una señal parcial.
No confundas hipótesis de representación con victoria arquitectónica.
No metas atajos.
No sacrifiques trazabilidad por rapidez.

En una frase:

E12 debe servir para probar si la ventaja observada en E9 puede ser absorbida por una representación enriquecida, temporalmente válida y metodológicamente defendible, dentro de un modelo más simple y trazable, especialmente para capturar mejor `H1` sin perder la robustez de `H2-H4`.
