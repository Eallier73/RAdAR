Nombre: Autopsia E1_vs_E9 + recombinación por horizonte + recalibración categórica + verificación táctica E2

Vas a ejecutar una fase analítica y experimental corta, estrictamente controlada, posterior a E11. No vas a abrir una rama nueva por inercia ni por cumplimiento ciego del calendario. Vas a responder, con evidencia empírica y trazabilidad completa, cuál es la siguiente pregunta que merece una corrida real.

Contexto ya establecido y que debes respetar

1. E1_v5_clean sigue siendo el benchmark numérico puro vigente:
- family = E1
- feature_mode = corr
- lags = 1,2,3,4,5,6
- L_total_Radar = 0.243442
- benchmark numérico puro vigente

2. E9_v2_clean sigue siendo el benchmark operativo vigente:
- family = E9
- feature_mode = tabla curada
- lags = n/a
- L_total_Radar = 0.227510
- deteccion_caidas_promedio = 0.916667
- benchmark operativo vigente

3. E11 ya fue evaluada y no desplazó a ninguno de los dos benchmarks:
- E11_v1_clean preserva exactamente E1_v5_clean
- E11_v2_clean preserva exactamente E1_v5_clean y agrega capa binaria útil pero no promocionable
- E11_v3_clean cambia el forecast final y empeora levemente el global
- la clasificación ternaria con movement_threshold = 0.5 quedó casi colapsada a se_mantiene
- no hay evidencia de mejora real frente a E1_v5_clean
- no hay evidencia de mejora real frente a E9_v2_clean

4. La conclusión metodológica vigente es esta:
- el problema central no es “encontrar otro algoritmo”
- el problema central es identificar qué pregunta merece la siguiente corrida
- antes de abrir E12 o de reactivar cualquier familia, hay que entender por qué E9_v2_clean detecta caídas tan bien
- y hay que verificar si existe viabilidad real para una recombinación por horizonte entre los benchmarks actuales

Objetivo de esta fase

No vas a optimizar modelos todavía.
No vas a abrir una familia nueva todavía.
No vas a promocionar nada todavía.

Vas a producir evidencia estructurada para responder cuatro preguntas:

A. ¿Por qué E9_v2_clean supera operativamente a E1_v5_clean, especialmente en detección de caídas?
B. ¿Existe una recombinación ex post por horizonte entre E1_v5_clean y E9_v2_clean que supere a ambos en L_total_Radar?
C. ¿La mala performance de la clasificación ternaria en E11 se debe en buena medida a umbrales mal calibrados?
D. ¿E2/Huber merece expansión posterior o solo cierre rápido como verificación táctica?

Orden obligatorio de trabajo

FASE 1. AUTOPSIA COMPARATIVA E1_v5_clean VS E9_v2_clean
FASE 2. RECOMBINACIÓN EX POST POR HORIZONTE
FASE 3. ANÁLISIS DE DISTRIBUCIÓN DEL DELTA PARA RECALIBRAR THRESHOLDS
FASE 4. VERIFICACIÓN TÁCTICA CORTA DE E2
FASE 5. ACTUALIZACIÓN DOCUMENTAL Y DECISIÓN FORMAL DE SIGUIENTE PASO

No alteres este orden.
No empieces E2 antes de terminar la autopsia, la recombinación y la recalibración.
No abras E12.
No abras nuevas familias.
No hagas tuning exploratorio libre.

FASE 1. AUTOPSIA COMPARATIVA E1_v5_clean VS E9_v2_clean

Propósito

Determinar si la ventaja operativa de E9_v2_clean proviene principalmente de la arquitectura de stacking o de la representación de features contenida en la tabla curada.

Tareas obligatorias

1. Recupera los artefactos canónicos completos de:
- E1_v5_clean
- E9_v2_clean

2. Trabaja por horizonte h1, h2, h3, h4 con sus predicciones reales alineadas por fecha, y_true, y_pred y cualquier artefacto comparable disponible.

3. Construye una autopsia comparativa con al menos estos bloques:

a) Comparación global por horizonte
- mae
- rmse
- direction_accuracy
- deteccion_caidas
- loss_h
- contribución al L_total_Radar

b) Comparación por episodios de caída
Debes identificar explícitamente los episodios donde el target real cae.
Para esos episodios calcula por modelo y horizonte:
- número de episodios
- recall de caída
- precisión sobre caídas si aplica
- error medio en episodios de caída
- error medio fuera de episodios de caída
- falsos negativos de caída
- falsos positivos de caída

c) Comparación por signo del cambio real
Separa al menos:
- semanas de caída
- semanas de subida
- semanas de relativa estabilidad si la estructura de datos lo permite

d) Comparación de dispersión y severidad del error
- distribución de error absoluto
- percentiles del error absoluto
- error en cola alta
- casos donde E9 gana claramente
- casos donde E1 gana claramente

e) Comparación de cobertura temporal
No te limites al promedio.
Identifica si la superioridad de E9 está concentrada en:
- uno o dos horizontes
- pocos episodios críticos
- o una mejora estable a lo largo del tiempo

4. Debes producir un análisis interpretativo, no solo tablas.
Tu pregunta central es:
“¿La superioridad operativa de E9 parece explicarse más por representación de features que por arquitectura?”

No puedes afirmar causalidad fuerte.
Sí puedes emitir un juicio técnico razonado del tipo:
- “la evidencia sugiere”
- “la pauta observada es consistente con”
- “la hipótesis más parsimoniosa es”

5. Busca evidencia específica de si E9 mejora sobre todo en:
- anticipación de cambios de signo
- detección de secuencias de deterioro
- reducción de falsos negativos en caídas
- o simple compensación promedio del error

6. Si la tabla curada de E9 contiene constructos especiales o agregados que no existen en E1, debes describirlos de manera técnica y trazable.
No inventes constructos.
No adivines.
Extrae la información de artefactos reales y del código/builders reales.

Entregables mínimos de Fase 1

- autopsia_e1_v5_vs_e9_v2.md
- autopsia_e1_v5_vs_e9_v2.csv o .xlsx con tablas comparativas
- resumen_ejecutivo_autopsia_e1_vs_e9.md
- inventario_fuentes_autopsia_e1_vs_e9.md

FASE 2. RECOMBINACIÓN EX POST POR HORIZONTE

Propósito

Medir si una combinación ex post por horizonte entre E1_v5_clean y E9_v2_clean tendría viabilidad operativa suficiente para justificar más adelante una familia de selector por horizonte.

Esto NO es un modelo nuevo.
Esto NO es promocionable.
Esto es un análisis de viabilidad.

Reglas estrictas

1. No entrenes nada.
2. No alteres predicciones.
3. No hagas blending continuo.
4. Solo usa predicciones ya existentes de los benchmarks canónicos.

Tareas obligatorias

1. Construye todas las combinaciones razonables por horizonte entre:
- E1_v5_clean
- E9_v2_clean

Es decir, para h1, h2, h3, h4, cada horizonte puede tomar la predicción de E1 o de E9.
Eso produce 2^4 combinaciones.
Evalúalas todas.

2. Para cada combinación calcula:
- mae_promedio
- rmse_promedio
- direction_accuracy_promedio
- deteccion_caidas_promedio
- L_total_Radar
- métricas por horizonte
- diferencia contra E1_v5_clean
- diferencia contra E9_v2_clean

3. Identifica:
- mejor combinación por L_total_Radar
- mejor combinación por detección de caídas
- mejor combinación por trade-off global si existe
- si alguna combinación supera simultáneamente a ambos benchmarks en L_total_Radar
- si la ganancia potencial está concentrada en uno o dos horizontes

4. Debes dejar clarísimo en la documentación:
- que este análisis es ex post
- que no es promocionable
- que no demuestra capacidad prospectiva
- que solo sirve para evaluar si vale la pena diseñar un selector por horizonte

5. Si ninguna combinación supera de forma convincente a ambos benchmarks, debes decirlo explícitamente y recomendar no abrir todavía una familia de selector por horizonte.

Entregables mínimos de Fase 2

- analisis_recombinacion_ex_post_horizontes_e1_e9.md
- recombinacion_horizontes_e1_e9.csv o .xlsx
- resumen_viabilidad_selector_por_horizonte.md

FASE 3. ANÁLISIS DE DISTRIBUCIÓN DEL DELTA PARA RECALIBRAR THRESHOLDS CATEGÓRICOS

Propósito

Determinar si el fracaso de la clasificación ternaria en E11_v1_clean se explica en buena medida por mala calibración del threshold y no necesariamente por inviabilidad estructural de la tarea.

Contexto obligatorio a respetar

En E11_v1_clean se usó:
- target_mode_cls = direction_3clases
- movement_threshold = 0.5

Y la clase quedó casi colapsada a se_mantiene.
No debes volver a asumir que ±0.5 es un buen threshold.
Primero debes mirar la distribución empírica real.

Tareas obligatorias

1. Extrae del dataset maestro o de la fuente canónica del target:
- la serie de nivel
- el delta semanal real que corresponda a la tarea categórica

2. Calcula y documenta como mínimo:
- media
- mediana
- desviación estándar
- percentiles 5, 10, 25, 50, 75, 90, 95
- proporción de cambios cercanos a cero
- histograma o tabla de frecuencias
- magnitud típica del movimiento semanal absoluto

3. Simula varios thresholds plausibles, por ejemplo:
- ±0.10
- ±0.15
- ±0.20
- ±0.25
- ±0.30
- ±0.40
- ±0.50

No te cases con esa lista si los datos sugieren otra más adecuada, pero debe haber barrido razonable y documentado.

4. Para cada threshold calcula:
- distribución de clases resultante
- porcentaje de baja
- porcentaje de se_mantiene
- porcentaje de sube
- grado de desbalance

5. Debes producir una recomendación técnica explícita:
- threshold descartable
- threshold plausible para pruebas futuras
- threshold preferente si existe
- y justificación empírica

6. No corras todavía una nueva familia categórica.
Solo deja la base técnica lista para decidir si una reapertura futura de clasificación ternaria tendría sentido.

Entregables mínimos de Fase 3

- analisis_distribucion_delta_iad.md
- sensibilidad_thresholds_clasificacion.csv o .xlsx
- recomendacion_thresholds_e11_o_futura_clasificacion.md

FASE 4. VERIFICACIÓN TÁCTICA CORTA DE E2 / HUBER

Propósito

Honrar el plan experimental sin permitir que E2 absorba tiempo de investigación desproporcionado.

Hipótesis de trabajo

La hipótesis no es “Huber va a romper el techo”.
La hipótesis es más modesta:
“Huber puede verificar rápidamente si una robustificación lineal frente a outliers cambia algo relevante; si no lo hace, se cierra sin expansión.”

Reglas estrictas

1. E2 debe correrse como verificación táctica breve.
2. No abras una rama larga.
3. No hagas grid grande.
4. No hagas tuning expansivo.
5. Mantén comparabilidad máxima con E1.

Diseño sugerido y obligatorio salvo imposibilidad técnica real

Debes abrir una micro-rama E2 con muy pocas corridas, idealmente 2 o 3 como máximo, manteniendo comparable la base de E1:
- target_mode = nivel
- horizontes = 1,2,3,4
- validación walk-forward limpia
- sin leakage
- sin snooping
- con trazabilidad completa
- usando el mismo marco de evaluación canónico

Busca una verificación táctica del tipo:
- una versión base comparable a E1_v5_clean
- una versión más parsimoniosa si aplica
- y, solo si está técnicamente justificado, una tercera variante menor

No conviertas E2 en nueva rama principal.
No improvises veinte variaciones.
No declares “mejora” por un horizonte aislado sin leer el L_total_Radar y el perfil completo.

Criterio de lectura

- Si E2 no mejora de forma creíble el balance global, debe quedar cerrada rápido.
- Si E2 muestra mejora marginal ambigua, no se promociona automáticamente.
- Solo si E2 mostrara una mejora clara y robusta contra benchmarks vigentes podría merecer expansión posterior, pero no asumas eso de antemano.

Entregables mínimos de Fase 4

- run_e2_huber.py si no existe o adaptación limpia si ya existe infraestructura parcial
- 01_apertura_e2_verificacion_tactica.md
- resumen_resultados_e2_verificacion_tactica.md
- corridas reales registradas y auditadas
- regeneración completa de tabla maestra, inventarios y documentación afectada

FASE 5. DECISIÓN FORMAL DE SIGUIENTE PASO

Una vez terminadas las cuatro fases anteriores, debes producir una decisión explícita, argumentada y operativa sobre cuál es el siguiente paso correcto del proyecto.

Las opciones razonables a evaluar son estas, y debes pronunciarte sobre ellas:

Opción A
No abrir nada todavía y cerrar esta fase con aprendizaje analítico suficiente.

Opción B
Abrir una variante E1_v6_clean o equivalente lineal usando representación inspirada en tabla curada, solo si la autopsia realmente sugiere que la ventaja de E9 proviene sobre todo de representación y no solo de arquitectura.

Opción C
Abrir una futura E12 centrada en representación de features, no en algoritmo:
- interacciones
- régimen
- duración de rachas
- velocidad
- delta de delta
- features externas nuevas
- u otros constructos de segundo orden justificables

Opción D
Reabrir una rama categórica futura con thresholds recalibrados, solo si la distribución empírica demuestra que el colapso de E11_v1 fue en buena medida un problema de umbral y no una invalidez estructural total.

Opción E
Cerrar E2 sin expansión y dejar constancia formal de por qué.

Debes emitir una recomendación final única, jerarquizada y defendible.

Restricciones metodológicas absolutas

1. Prohibido leakage temporal.
2. Prohibido usar información futura en features, selección, limpieza o recombinación.
3. Prohibido snooping disfrazado de “análisis manual”.
4. Prohibido promocionar análisis ex post como si fueran evidencia prospectiva.
5. Prohibido mezclar artefactos no canónicos con canónicos sin dejarlo explícito.
6. Prohibido abrir nuevas familias por intuición si la evidencia de esta fase no lo respalda.
7. Prohibido editar retrospectivamente la historia metodológica del proyecto para que “suene mejor”.
8. Prohibido presentar recombinaciones ex post como benchmark vigente.
9. Prohibido confundir valor analítico con valor promocionable.
10. Prohibido sacrificar trazabilidad por velocidad.

Actualizaciones documentales obligatorias

Debes actualizar, si aplica y solo con evidencia real, los documentos canónicos afectados:
- plan_de_experimentacion_radar.md
- bitacora_experimental_radar.md
- README.md
- fase_produccion_controlada_radar.md
- consolidacion_operativa_post_produccion_controlada.md
- politica_promocion_sistemas_radar.md
- politica_promocion_sistemas_radar.json
- resumen_metodologico o equivalentes pertinentes
- build_experiments_master_table.py si alguna nueva salida analítica formal debe integrarse
- inventarios y auditorías maestras correspondientes

No ensucies la documentación.
No dupliques archivos sin necesidad.
No abras documentos paralelos redundantes.
Si actualizas un documento canónico, debe ser para dejar una huella metodológica útil, precisa y consistente con todo lo ya trabajado.

Formato de cierre obligatorio

Al final debes entregar un informe de cierre con esta estructura:

1. Qué se hizo
2. Qué evidencia nueva apareció
3. Qué quedó refutado
4. Qué quedó plausible
5. Qué no debe hacerse todavía
6. Qué siguiente paso recomiendas
7. Qué archivos creaste
8. Qué archivos actualizaste
9. Qué artefactos regeneraste
10. Qué partes, si alguna, quedan explícitamente no promocionables

Criterio final de calidad

Esta fase será considerada correcta solo si al terminar queda más claro:
- por qué E9 gana operativamente
- si una recombinación por horizonte vale siquiera la pena
- si la clasificación ternaria murió por mal umbral o por inviabilidad más profunda
- y si E2 merece algo más que una verificación táctica

Si no dejas esas cuatro respuestas mucho más claras que al inicio, la fase no habrá servido.
