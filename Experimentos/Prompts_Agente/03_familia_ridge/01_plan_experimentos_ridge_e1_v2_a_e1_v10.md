Quiero que continúes la familia de experimentos E1 del proyecto Radar, donde el modelo base es RidgeCV, y generes las siguientes versiones experimentales de manera ordenada, trazable y metodológicamente defendible.

CONTEXTO GENERAL
Ya existe una línea de base dentro de E1:



Ahora quiero que sigas con nuevas versiones de Ridge para responder preguntas metodológicas concretas, sin cambiar de familia de modelo.

REGLA GENERAL
Cada nueva versión debe cambiar SOLO una dimensión principal a la vez, o como máximo una combinación muy justificada. No quiero experimentos confusos donde no se pueda saber qué causó una mejora o empeoramiento.

OBJETIVO DE ESTA ETAPA
Explorar si Ridge mejora al modificar:
1. la memoria temporal (lags)
2. la transformación de variables
3. la parsimonia / selección de variables
4. el target
5. la ponderación o evaluación Radar
sin abandonar la familia lineal regularizada

ARQUITECTURA ESPERADA
Debes trabajar sobre el script de familia ya existente o refactorizado, idealmente:
- run_e1_ridge.py

Debe aceptar por argumentos CLI como mínimo:
- --run-id
- --target-mode        (nivel, delta)
- --feature-mode       (all, corr, lasso)
- --lags               (ej. 1,2,3,4 o 1,2,3,4,5,6)
- --transform-mode     (none, standard, robust, winsor)
- --initial-train-size
- --horizons
- cualquier otro parámetro adicional necesario para control experimental

IMPORTANTE
No debes cambiar de algoritmo. Sigue siendo RidgeCV.
No debes cambiar la validación temporal. Debe seguir siendo walk-forward o equivalente temporal correcto.
No debes usar validación aleatoria simple.
No debes meter leakage en selección de variables, transformaciones o preparación del target.

NUEVAS VERSIONES A IMPLEMENTAR

-----------------------------------
E1_v2
-----------------------------------
Diseño:
- modelo = RidgeCV
- target_mode = nivel
- feature_mode = all
- lags = 1,2,3,4
- transform_mode = standard

Hipótesis:
Esta corrida debe funcionar como baseline lineal regularizado limpio y trazable dentro de la nueva arquitectura por familia. La expectativa es que capture una señal base útil del sistema Radar, especialmente en los horizontes donde la dinámica sea relativamente estable y suficientemente explicable por relaciones lineales entre lags y variables temáticas.

Preguntas metodológicas:
- ¿RidgeCV, usando todas las variables y lags 1..4, logra establecer un baseline sólido y comparable para la familia E1?
- ¿La señal contenida en el dataset maestro es suficientemente fuerte como para que un modelo lineal regularizado produzca resultados operativamente útiles?
- ¿Los horizontes de 1, 2, 3 y 4 semanas responden de forma parecida o hay uno claramente más favorable para la familia Ridge?
- ¿Este baseline lineal sirve solo como referencia mínima o ya muestra potencial como contendiente serio dentro del banco de modelos?

Sentido dentro del proyecto:
E1_v2 no busca ser todavía la mejor versión posible de Ridge, sino dejar una línea base formal, homogénea y totalmente comparable para que después podamos evaluar con claridad si cambios en target o selección de variables producen mejoras reales.

-----------------------------------
E1_v3
-----------------------------------
Diseño:
- modelo = RidgeCV
- target_mode = delta
- feature_mode = all
- lags = 1,2,3,4
- transform_mode = standard

Hipótesis:
Si el problema principal del baseline no está tanto en el nivel absoluto del índice sino en la dificultad para captar el movimiento, entonces cambiar el target de nivel a delta podría mejorar la detección de tendencia y el comportamiento en horizontes intermedios, especialmente donde el modelo necesite reaccionar mejor a cambios semanales.

Preguntas metodológicas:
- ¿Predecir delta en vez de nivel mejora la capacidad del modelo para captar la dirección del cambio?
- ¿El cambio de target ayuda especialmente al horizonte de 2 semanas o a los horizontes donde el baseline lineal muestre debilidad en tendencia?
- ¿La mejora en dinámica viene acompañada de una pérdida importante en error numérico de nivel?
- ¿Trabajar sobre delta permite que Ridge se adapte mejor a un sistema donde la opinión pública se mueve por cambios, no solo por niveles acumulados?
- ¿Esta formulación convierte a Ridge en un modelo más sensible a virajes y caídas, o simplemente agrega ruido?

Sentido dentro del proyecto:
E1_v3 busca responder si parte del problema metodológico de la familia Ridge está en cómo definimos el target. No cambia el algoritmo ni la estructura base del experimento; solo cambia la pregunta que se le hace al modelo: predecir valor futuro o predecir cambio futuro.

-----------------------------------
E1_v4
-----------------------------------
Diseño:
- modelo = RidgeCV
- target_mode = nivel
- feature_mode = corr
- lags = 1,2,3,4
- transform_mode = standard

Hipótesis:
Si usar todas las variables mete ruido, redundancia o inestabilidad, entonces una versión más parsimoniosa basada en filtro por correlación podría mejorar el comportamiento del modelo, sobre todo en tendencia, detección de caídas y estabilidad general de la pérdida Radar.

Preguntas metodológicas:
- ¿Reducir el espacio de variables mediante un filtro por correlación mejora el desempeño global del baseline Ridge?
- ¿La parsimonia mejora especialmente los horizontes intermedios donde un exceso de variables podría estar introduciendo ruido?
- ¿El filtro por correlación conserva la señal útil o elimina variables que sí aportaban capacidad predictiva?
- ¿Una versión más simple del modelo resulta más estable, interpretable y competitiva?
- ¿La mejora potencial proviene de quitar ruido o de reducir multicolinealidad innecesaria entre variables temáticas?

Sentido dentro del proyecto:
E1_v4 busca evaluar si el problema de Ridge no está en la familia lineal en sí, sino en el exceso de variables. Esta corrida prueba si una reducción controlada y metodológicamente correcta del espacio de features mejora la utilidad operativa del modelo sin cambiar de algoritmo.

========================
E1_v5
========================
Diseño:
- modelo = RidgeCV
- target_mode = nivel
- feature_mode = all
- lags = 1,2,3,4,5,6
- transform_mode = standard

Hipótesis:
Evaluar si ampliar memoria temporal mejora el desempeño, especialmente en horizontes intermedios como H2 y H3.

Pregunta metodológica:
¿El hueco observado en H2 se debe a que 4 lags son insuficientes?

Notas:
Debes documentar claramente cuántas features finales produce esta configuración.

========================
E1_v6
========================
Diseño:
- modelo = RidgeCV
- target_mode = delta
- feature-mode = corr
- lags = 1,2,3,4
- transform_mode = standard

Hipótesis:
Evaluar si combinar target delta con reducción de ruido por correlación mejora la detección de cambios, especialmente en H2.

Pregunta metodológica:
¿La combinación de target dinámico + parsimonia corrige el problema de tendencia que vimos en H2?

Notas:
Documentar claramente cómo se hace la selección por correlación y cómo se evita leakage.

========================
E1_v7
========================
Diseño:
- modelo = RidgeCV
- target_mode = nivel
- feature_mode = lasso
- lags = 1,2,3,4
- transform_mode = standard

Hipótesis:
Evaluar si una selección más agresiva de variables mejora robustez y simplifica el modelo.

Pregunta metodológica:
¿Ridge mejora si antes se limpia el espacio de variables con una selección más dura?

Notas:
Si implementas feature_mode=lasso, documenta con precisión:
- cómo se seleccionan las variables
- en qué tramo temporal
- con qué criterio
- cómo se evita fuga de información

Si aún no existe el helper para esto, créalo de forma reusable.

========================
E1_v8
========================
Diseño:
- modelo = RidgeCV
- target_mode = nivel
- feature_mode = all
- lags = 1,2,3,4
- transform_mode = robust

Hipótesis:
Evaluar si un escalado robusto o tratamiento más resistente a outliers mejora la estabilidad de Ridge.

Pregunta metodológica:
¿El problema de algunos horizontes se debe a sensibilidad a valores extremos?

Notas:
Si usas robust scaling o winsorización, debe quedar totalmente documentado y aplicado sin romper la trazabilidad.

========================
E1_v9
========================
Diseño:
- modelo = RidgeCV
- target_mode = delta
- feature_mode = all
- lags = 1,2,3,4,5,6
- transform_mode = standard

Hipótesis:
Evaluar si target delta + memoria más larga mejora la dinámica de corto y mediano plazo.

Pregunta metodológica:
¿La combinación de cambio + mayor memoria temporal captura mejor los movimientos del IAD?

========================
E1_v10
========================
Diseño:
- modelo = RidgeCV
- target_mode = nivel
- feature_mode = corr
- lags = 1,2,3,4,5,6
- transform_mode = standard

Hipótesis:
Evaluar si una combinación de mayor memoria y menor ruido mejora la familia Ridge sin cambiar de algoritmo.

Pregunta metodológica:
¿Ridge puede volverse competitivo solo ajustando memoria + reducción de ruido?

PRINCIPIO DE IMPLEMENTACION
Antes de correr todas las versiones, debes verificar que el script soporte correctamente:
- target_mode
- feature_mode
- lags configurables
- transform_mode configurable
- guardado de artefactos
- cálculo de métricas Radar por horizonte
- cálculo de L_total_Radar a nivel corrida

SALIDAS OBLIGATORIAS POR RUN
Cada corrida debe guardar:

- metadata_run.json
- parametros_run.json
- metricas_horizonte.json
- resumen_modeling_horizontes.json
- predicciones_h1.csv
- predicciones_h2.csv
- predicciones_h3.csv
- predicciones_h4.csv

METRICAS OBLIGATORIAS POR HORIZONTE
Como mínimo:
- horizonte_sem
- mae
- rmse
- direccion_accuracy
- deteccion_caidas
- l_num
- l_trend
- l_risk
- l_tol
- loss_h

METRICAS OBLIGATORIAS A NIVEL RUN
- L_total_Radar
- idealmente L_coh si ya está implementado
- estado
- comentarios
- notas_config

REQUISITO CLAVE DE COMPARACION
Al final no quiero solo corridas aisladas.
Quiero una tabla comparativa consolidada entre:

- E1_v2
- E1_v3
- E1_v4
- E1_v5
- E1_v6
- E1_v7
- E1_v8
- E1_v9
- E1_v10

La tabla debe incluir como mínimo:
- run_id
- target_mode
- feature_mode
- transform_mode
- lags
- feature_count promedio o por horizonte
- mae_promedio
- direccion_accuracy_promedio
- deteccion_caidas_promedio
- L_total_Radar
- observacion_breve

INTERPRETACION QUE DEBE ENTREGAR EL AGENTE
Quiero además una lectura analítica, no solo técnica.
El agente debe responder:

1. ¿Cuál versión de Ridge fue la mejor globalmente?
2. ¿Cuál fue la mejor para H2?
3. ¿Cuál fue la mejor para H3?
4. ¿Agregar lags ayudó o metió ruido?
5. ¿Target delta ayudó realmente o no?
6. ¿Reducir variables ayudó o empeoró?
7. ¿Las transformaciones robustas aportaron algo?
8. ¿Ridge sigue siendo solo baseline o ya se vuelve contendiente serio?
9. ¿Cuál versión de Ridge debería pasar a la siguiente ronda como representante de la familia E1?

RESTRICCIONES METODOLOGICAS
- No uses información futura para seleccionar variables.
- No uses toda la muestra para definir filtros si luego vas a validar temporalmente.
- Si una decisión metodológica es una aproximación, declárala explícitamente.
- Si alguna versión no puede implementarse de forma correcta todavía, dilo con honestidad y deja la plantilla lista.
- No inventes métricas que no existan en el pipeline; si hace falta implementarlas, hazlo de forma explícita.

ENTREGABLES
Quiero que me devuelvas:

1. los archivos modificados o creados
2. explicación breve de qué cambió en el script Ridge
3. comandos exactos para correr cada versión:
   - E1_v5
   - E1_v6
   - E1_v7
   - E1_v8
   - E1_v9
   - E1_v10
4. una tabla comparativa consolidada
5. una interpretación metodológica breve pero clara
6. una recomendación final sobre cuál versión Ridge conservar

CRITERIO DE EXITO
El trabajo estará bien hecho si:
- puedo correr las nuevas versiones desde terminal sin editar el código manualmente
- quedan registradas en el tracker y en el grid
- son comparables entre sí
- respetan la lógica temporal del proyecto Radar
- permiten decidir si Ridge merece seguir compitiendo contra Huber, Random Forest, XGBoost o modelos híbridos


CRITERIOS DE DECISION PARA LA FAMILIA RIDGE (E1)

No quiero solo que ejecutes corridas. Quiero que además tomes una postura analítica provisional después de cada versión, usando criterios de decisión claros.

OBJETIVO
Determinar si cada nueva versión de Ridge:
1. mejora realmente el desempeño global,
2. mejora un horizonte crítico sin destruir los demás,
3. o solo cambia métricas de forma cosmética.

REGLA GENERAL
No debes declarar ganadora una versión solo porque mejora una métrica aislada.
La decisión debe considerar:
- L_total_Radar
- comportamiento por horizonte
- dirección
- detección de caídas
- estabilidad del modelo
- costo de complejidad metodológica adicional

PRIORIDAD DE EVALUACION
En este orden:
1. L_total_Radar
2. desempeño en H2 y H3
3. estabilidad de H1 y H4
4. direccion_accuracy
5. deteccion_caidas
6. interpretabilidad y parsimonia

RAZON DE ESTA PRIORIDAD
H2 y H3 son especialmente importantes porque el sistema Radar parece depender mucho de la dinámica intermedia. Sin embargo, no acepto una mejora en H2 o H3 si destruye gravemente H1 o H4.

REGLAS ESPECIFICAS DE DECISION

1. Si una nueva versión mejora claramente L_total_Radar y además mejora H2 sin deteriorar severamente H1, H3 o H4:
- marcarla como "mejora real"
- conservarla como candidata principal dentro de la familia Ridge

2. Si una nueva versión mejora H2 pero empeora fuertemente H1 y/o H3:
- NO declararla automáticamente ganadora
- marcarla como "trade-off dudoso"
- explicar si la mejora en H2 compensa o no el deterioro en otros horizontes

3. Si una nueva versión mejora H3 pero no mejora H2:
- marcarla como "mejora parcial"
- evaluar si confirma que la señal fuerte de Ridge está más en 3 semanas que en 2
- no promoverla como versión final sin revisar el equilibrio completo

4. Si una nueva versión reduce MAE pero empeora direccion_accuracy o deteccion_caidas:
- marcarla como "mejora numérica no operativa"
- dejar claro que para Radar eso no basta

5. Si una nueva versión mejora direccion_accuracy y deteccion_caidas aunque el MAE no cambie mucho:
- tratarla como mejora potencialmente valiosa
- revisar especialmente impacto en L_trend y L_risk

6. Si una nueva versión empeora L_total_Radar aunque mejore una métrica aislada:
- clasificarla como no preferible en términos globales

7. Si dos versiones salen muy cercanas:
- preferir la más simple, más estable y más interpretable
- especialmente si la diferencia numérica es pequeña

8. Si una versión con target delta mejora claramente H2 pero vuelve inestable la reconstrucción de nivel o empeora demasiado H1/H4:
- clasificarla como útil para entender dinámica, pero no necesariamente como mejor versión global

9. Si una versión con feature_mode=corr mejora estabilidad o L_total_Radar:
- considerarla una señal de que había ruido o redundancia en el set completo
- anotar explícitamente que la parsimonia ayudó

10. Si una versión con más lags mejora H3 pero empeora H1:
- interpretarlo como evidencia de que la memoria más larga ayuda al mediano plazo pero puede meter rezago o ruido en corto plazo
- no concluir automáticamente que más lags es mejor en general

11. Si una versión robusta mejora poco o nada respecto a la estándar:
- concluir provisionalmente que el problema principal no parece ser outliers

12. Si ninguna versión de Ridge mejora de forma clara:
- concluir que la familia Ridge sirve como baseline serio pero probablemente no como ganadora final
- recomendar avanzar a Huber, Random Forest o XGBoost

FORMATO DE INTERPRETACION DESPUES DE CADA RUN
Después de cada corrida nueva, quiero una mini lectura con esta estructura:

- Qué cambió respecto a la versión anterior
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

REGLA DE STOP
Si después de E1_v2, E1_v3 y E1_v4 ninguna mejora claramente al baseline, NO sigas corriendo más versiones Ridge automáticamente.
Primero entrega análisis comparativo y recomendación.

REGLA DE CONTINUIDAD
Solo tiene sentido seguir con E1_v5+ si ocurre al menos una de estas condiciones:
- E1_v3 mejora claramente H2 o L_total_Radar
- E1_v4 mejora claramente estabilidad o métricas operativas
- hay evidencia de que Ridge todavía tiene margen de mejora metodológica

Si no se cumple ninguna, sugiere cerrar la familia Ridge como baseline y pasar a E2.

SALIDA FINAL ESPERADA
Quiero que al final de E1_v2, E1_v3 y E1_v4 me digas claramente una de estas tres cosas:

A. Ridge todavía merece más exploración
B. Ridge ya alcanzó su techo práctico
C. Ridge no gana globalmente, pero sí aporta una versión útil como benchmark fuerte