Quiero que trabajes como agente técnico del proyecto Radar y ejecutes una tarea en DOS FASES:

FASE 1: cierre formal y documentado de la familia E2 (Huber)
FASE 2: preparación y arranque de la siguiente familia experimental dentro de la arquitectura por familias

IMPORTANTE
No quiero un análisis superficial ni solo una opinión.
Quiero trabajo operativo, trazable, consistente con el pipeline actual y con el refactor por familias.

CONTEXTO METODOLÓGICO QUE DEBES RESPETAR

El proyecto Radar ya tiene un marco experimental definido y no debes romperlo.

Debes respetar estrictamente:

- validación temporal correcta
- horizontes 1, 2, 3 y 4 semanas
- walk-forward expanding o equivalente correcto según la familia
- tuning interno temporal cuando aplique
- cálculo de métricas Radar ya existentes
- trazabilidad completa por corrida
- mismo dataset maestro
- compatibilidad con el tracker/grid actual
- no leakage
- no validación aleatoria simple
- no duplicar scripts por mini experimento
- sí un script por familia de modelo

La arquitectura objetivo es por familias, no por corridas individuales. Ya existe la instrucción de refactor para dejar scripts por familia con estructura homogénea y reutilización de helpers comunes. Debes seguir ese criterio. No regreses al esquema de un script nuevo por cada run. :contentReference[oaicite:2]{index=2}

ESTADO ACTUAL DEL PROYECTO

La familia E1 Ridge ya fue explorada y quedó cerrada como baseline lineal regularizado principal.
Debes tomar como referencias:

- E1_v5_clean como mejor Ridge limpio global por L_total_Radar
- E1_v4_clean como versión parsimoniosa y equilibrada

La instrucción previa del proyecto ya decía que, después de cerrar Ridge, el siguiente paso debía ser priorizar una familia no lineal, manteniendo exactamente el mismo marco de evaluación para comparabilidad. :contentReference[oaicite:3]{index=3}

La micro-rama diagnóstica de Huber ya quedó resuelta así:

- E2_v1_clean = baseline Huber limpio
- E2_v2_clean = control de convergencia
- E2_v3_clean = prueba sin memoria larga

Resultado final ya observado:

- E2_v2_clean descartó que el problema fuera solo convergencia
- E2_v3_clean mostró que memoria corta ayuda algo a Huber
- pero Huber sigue sin alcanzar a Ridge
- además E2_v3_clean sacrifica H3
- no hace falta correr E2_v4_clean
- decisión: cerrar formalmente E2 y pasar a la siguiente familia del plan original

Toma esto como decisión ya resuelta, no como hipótesis abierta. No reabras la discusión salvo que detectes un error objetivo en los artefactos existentes. :contentReference[oaicite:4]{index=4}

OBJETIVO GENERAL DE ESTA TAREA

1. Cerrar formalmente la familia E2 Huber en términos metodológicos, documentales y de trazabilidad.
2. Dejar listo el pipeline experimental para continuar con la siguiente familia.
3. Empezar la siguiente familia con el mismo marco limpio temporal y con script por familia, no por corrida.
4. Entregar tanto el cierre analítico como los cambios técnicos y los comandos exactos necesarios.

SIGUIENTE FAMILIA A PRIORIZAR

Quiero que el siguiente paso sea una familia no lineal.
Dentro de la arquitectura por familias ya definida, la prioridad operativa debe ser:

- E3 Random Forest como siguiente familia a dejar operable
y, si conviene por estructura, dejar también preparada la continuidad hacia:
- E4 XGBoost
- E5 CatBoost

Pero en esta tarea el foco principal es E3.

No inventes una nueva familia. Reutiliza la nomenclatura objetivo ya definida en el refactor. :contentReference[oaicite:5]{index=5}

LO QUE QUIERO QUE HAGAS EXACTAMENTE

========================
FASE 1. CIERRE FORMAL DE E2
========================

Quiero que hagas un cierre formal, explícito y documentado de la familia robusta E2.

Debes:

1. Revisar los artefactos ya existentes de:
   - E2_v1_clean
   - E2_v2_clean
   - E2_v3_clean

2. Confirmar que no hace falta correr E2_v4_clean.
   Solo podrías contradecir esto si encuentras evidencia metodológica fuerte de que la conclusión actual está mal. Si no la encuentras, debes sostener el cierre de E2. La instrucción vigente es detener la micro-rama. :contentReference[oaicite:6]{index=6}

3. Registrar oficialmente, con base en resultados y no en intuición:
   - ganador interno de E2: E2_v3_clean
   - pero familia no competitiva frente a E1_v5_clean
   - E2_v2_clean descarta hipótesis de convergencia como explicación principal
   - E2_v3_clean sugiere que lags 1..6 perjudicaban a Huber
   - aun corrigiendo memoria, Huber no se vuelve suficientemente competitivo
   - no se justifica seguir explorando E2

4. Actualizar donde corresponda el resumen metodológico, grid o artefacto de comparación consolidada, sin romper compatibilidad con el tracker actual.

5. Dejar explícitamente documentado:
   - que E2 fue evaluada bajo esquema limpio temporal
   - que no mostró ventaja suficiente frente a Ridge
   - que la familia queda cerrada
   - que E2_v4_clean queda cancelada y no ejecutada por decisión metodológica, no por olvido

6. Si existe un README, bitácora, carpeta de prompts o documento metodológico donde deba quedar constancia del cierre, actualízalo o crea el documento correspondiente usando la convención de nombres del proyecto.

7. No cambies retroactivamente resultados ya cerrados.

ENTREGABLE ANALÍTICO DE ESTA FASE

Quiero un bloque claro que responda, mínimo, estas preguntas:

- ¿Qué probó E2_v2_clean realmente?
- ¿Qué probó E2_v3_clean realmente?
- ¿Huber mejoró por memoria corta o por convergencia?
- ¿La mejora fue global o parcial?
- ¿Hubo mejora operativa o solo numérica?
- ¿Hay razón real para mantener viva la familia E2?
- ¿Cuál es el veredicto final formal sobre Huber dentro de Radar?

La interpretación debe usar criterios parecidos a los ya usados en Ridge:
- L_total_Radar
- desempeño por horizonte
- especial atención a H2 y H3
- direction_accuracy
- deteccion_caidas
- estabilidad
- parsimonia metodológica

========================
FASE 2. ARRANQUE DE LA SIGUIENTE FAMILIA
========================

Una vez cerrado E2, quiero que continúes con la siguiente familia no lineal bajo el esquema por familias.

Foco principal:
- dejar operable `run_e3_random_forest.py`
o el archivo equivalente consistente con la arquitectura ya definida

También quiero que, si la estructura lo permite, dejes sembrada la plantilla homogénea para:
- run_e4_xgboost.py
- run_e5_catboost.py

Pero E3 debe quedar como prioridad real de implementación.

REQUISITO CENTRAL DE DISEÑO

NO quiero un script nuevo por cada mini experimento.
SÍ quiero un script por familia con parámetros por CLI para lanzar variantes.

Debes seguir la arquitectura objetivo ya definida:
- parse_args()
- build_estimator()
- carga dataset maestro
- construcción model frame
- validación temporal correcta
- cálculo métricas Radar
- guardado predicciones
- guardado métricas
- registro en tracker
- finalize del run con trazabilidad suficiente :contentReference[oaicite:7]{index=7}

SCRIPT E3 QUE DEBE QUEDAR OPERABLE

Quiero que dejes `run_e3_random_forest.py` funcional o, si ya existe una variante muy cercana, la adaptes al estándar homogéneo.

Debe aceptar por CLI como mínimo:

- --run-id
- --target-mode   (nivel, delta)
- --lags
- --feature-mode  (all, corr, lasso si aplica)
- --initial-train-size
- --horizons
- y los hiperparámetros coherentes para Random Forest

Debes diseñar una CLI coherente, no caprichosa.

QUÉ DEBE REUTILIZAR

Reutiliza toda la lógica reusable ya existente o ya extraída a helpers comunes, por ejemplo:

- parse_lags
- helpers de selección y resumen de features
- lógica de comparación contra run de referencia
- cálculo de pérdida Radar total
- funciones comunes de guardado de artefactos
- tracker / experiment_logger
- data_master.py
- evaluation.py
- feature_engineering.py
- pipeline_common.py
- config.py

No dupliques código si puede ir a helpers comunes.
No rompas compatibilidad con E1 y E2.

VALIDACIÓN Y CUIDADO METODOLÓGICO PARA E3

Debes adaptar la validación a Random Forest de forma correcta, pero manteniendo comparabilidad con Radar.

Eso implica:

- misma lógica temporal externa
- nada de mezclar futuro y pasado
- si haces tuning, debe ser temporal y dentro del fold externo
- si Random Forest no requiere escalado, puedes omitirlo, pero debes documentarlo como decisión metodológica, no dejarlo implícito
- si `feature_mode=corr` o `lasso` dependen de train fold, debes mantener esa restricción
- si algún modo no es metodológicamente correcto todavía, dilo claramente y deja la plantilla preparada

NO quiero atajos metodológicamente dudosos.

CORRIDAS INICIALES QUE QUIERO LISTAS PARA E3

Quiero que propongas y dejes listas, como mínimo, dos corridas iniciales comparables y limpias para la familia E3.

Ejemplo de estilo esperado:
- una versión base razonable
- una variante que cambie una sola cosa importante

No abras una explosión combinatoria todavía.
Quiero una rama inicial, controlada y trazable.

Debes explicar:
- qué cambia en cada una
- qué hipótesis prueba
- por qué ese orden de exploración tiene sentido

ARTEFACTOS OBLIGATORIOS PARA E3

La nueva familia debe guardar como mínimo:

- metadata_run.json
- parametros_run.json
- metricas_horizonte.json
- resumen_modeling_horizontes.json
- predicciones_h1.csv
- predicciones_h2.csv
- predicciones_h3.csv
- predicciones_h4.csv

Y cualquier artefacto adicional necesario para trazabilidad, por ejemplo:
- features seleccionadas por horizonte
- tuning por horizonte
- comparación contra referencia
si eso ya forma parte del estándar de familia tabular. :contentReference[oaicite:8]{index=8}

COMPARABILIDAD OBLIGATORIA

Toda nueva corrida de E3 debe ser comparable al menos contra:

- E1_v4_clean
- E1_v5_clean
- E2_v3_clean

Quiero que el agente deje explícito cuál de esas versiones será la referencia principal y por qué.

Mi sugerencia metodológica:
- usar E1_v5_clean como referencia principal global
- y E1_v4_clean como referencia parsimoniosa
pero si ves un motivo técnico sólido para ajustar eso, explícalo.

RESTRICCIONES

- No inventes rutas si ya hay módulos equivalentes en el proyecto.
- No cambies la lógica metodológica central de Radar.
- No metas validación aleatoria simple.
- No uses información futura para selección de variables.
- No ajustes transformaciones con test.
- No corras E2_v4_clean.
- No generes ramas laterales innecesarias.
- No declares ganadora una familia por una sola métrica aislada.
- No cambies nombres de archivos sin necesidad fuerte.
- Si algo no puede quedar totalmente funcional, déjalo como plantilla consistente y documentada, pero dilo con honestidad. :contentReference[oaicite:9]{index=9} :contentReference[oaicite:10]{index=10}

FORMATO DE ENTREGA QUE QUIERO

Quiero que me entregues TODO organizado EXACTAMENTE así:

1. Resumen ejecutivo
   - qué cerraste
   - qué dejaste listo
   - qué sigue

2. Cierre formal de E2
   - archivos revisados
   - archivos creados o modificados
   - conclusión metodológica final
   - justificación de por qué E2_v4_clean no se corre

3. Cambios técnicos realizados para la arquitectura por familias
   - lista de archivos creados o modificados
   - explicación breve de la función de cada archivo
   - helpers nuevos o refactorizados

4. Nueva familia E3
   - script principal creado o adaptado
   - parámetros CLI soportados
   - lógica de entrenamiento y validación
   - artefactos generados
   - qué quedó funcional y qué quedó como plantilla

5. Plan inicial de corridas E3
   - nombre sugerido de las corridas
   - hipótesis de cada una
   - comandos exactos de terminal para correrlas

6. Comparación y referencias
   - contra qué runs se comparará E3
   - por qué esas referencias son las correctas

7. Riesgos o puntos metodológicos delicados
   - cualquier decisión discutible
   - cualquier limitación actual
   - cualquier punto que deba vigilarse antes de expandir E3

8. Veredicto operativo final
   - familia cerrada
   - familia abierta
   - siguiente paso recomendado

IMPORTANTE SOBRE EL TONO Y EL NIVEL DE DETALLE

Quiero una respuesta en español claro, detallada y rigurosa.
No quiero frases vagas como “se podría”, “quizá”, “tal vez” si puedes tomar una decisión razonada.
Quiero postura técnica.
Si algo es inferencia, márcalo como inferencia.
Si algo no se pudo implementar bien, dilo sin suavizarlo.
Si algo quedó como plantilla, dilo explícitamente.
Si modificas código, quiero scripts completos o bloques suficientemente completos para ejecutarse sin adivinar piezas.

CRITERIO DE ÉXITO

El trabajo estará bien hecho si al final ocurre esto:

1. E2 queda oficialmente cerrada, documentada y fuera de expansión.
2. El proyecto queda alineado con la arquitectura por familias.
3. Existe un script E3 consistente con esa arquitectura.
4. E3 puede correrse desde terminal sin editar código a mano.
5. La nueva familia conserva comparabilidad total con E1/E2.
6. Queda claro cuál es el siguiente experimento concreto a ejecutar.

Empieza revisando el código y los artefactos actuales, no inventando desde cero.
Primero cierra E2.
Luego deja E3 listo.