Prompt para el agente

Nombre de la tarea:
Corrección estricta de la separación entrenamiento/inferencia en post_w10_controlled

Propósito:
Eliminar de manera definitiva cualquier reentrenamiento implícito dentro del flujo post_w10_controlled, para que la operación post-W10 use solo inferencia predict-only sobre artefactos congelados y no vuelva a ejecutar fit() sobre el dataset maestro actualizado.

0. Instrucción general

Estás trabajando dentro del proyecto Radar.
No debes tratar esta tarea como un refactor amplio del proyecto ni como una fase experimental.

Tu misión aquí es una sola:

corregir técnicamente la implementación actual de post_w10_controlled para que separe de forma dura y verificable entrenamiento vs inferencia.

La definición metodológica ya está resuelta:

las semanas nuevas post-W10 sí deben entrar al dataset maestro operativo,
sí deben alimentar inferencia,
no deben entrar al entrenamiento del benchmark congelado en esta tarea.

El problema ya detectado no es conceptual sino técnico:
la implementación actual de post_w10_controlled todavía reutiliza rutas que pasan por fit() sobre el dataset actualizado.

Debes corregir eso.

1. Restricciones absolutas
1.1 No reabrir investigación

No debes:

rediseñar familias de modelos
correr nuevos experimentos
modificar decisiones metodológicas ya cerradas
reinterpretar esta tarea como una mejora de desempeño
1.2 No romper benchmarks congelados

Debes respetar exactamente estos perfiles operativos:

E1_v5_clean como campeón numérico vigente
E9_v2_clean como referente de riesgo

Y para E9, respetar sus dependencias históricas ya fijadas.

1.3 No entrenar en post-W10

En post_w10_controlled debe quedar prohibido:

fit()
tuning interno
selección de variables recalculada sobre datos nuevos
reconstrucción de folds
backtest experimental
reserialización de un modelo recalculado sobre semanas nuevas
1.4 No hacer un refactor innecesariamente grande

Haz el cambio mínimo pero suficiente para lograr una separación real entre:

ruta experimental/research
ruta de inferencia congelada

No muevas archivos por estética.
No reestructures el repo salvo necesidad directa para resolver el problema.

2. Diagnóstico ya conocido que debes asumir

La situación actual es esta:

post_w10_controlled fue montado para operar con semanas nuevas post-W10
conceptualmente eso está bien
pero técnicamente la implementación actual todavía reutiliza rutas pensadas para modelado experimental
esas rutas vuelven a pasar por fit() sobre el dataset actualizado
por tanto, hoy no existe una separación suficientemente dura entre entrenamiento e inferencia

Tu trabajo es corregir exactamente ese bloqueo.

3. Objetivo técnico exacto

Lograr que la operación post-W10 funcione bajo esta secuencia:

dataset maestro actualizado con semanas nuevas -> construcción de input de inferencia -> carga de artefacto congelado -> transform() si aplica -> predict() únicamente -> registro de emisiones

y que nunca entre a una ruta que haga fit().

4. Qué debes entregar funcionalmente

Debes dejar resuelto esto:

una ruta de inferencia congelada predict-only
una separación clara respecto a la ruta experimental
validaciones de esquema/artefactos antes de predecir
bloqueo explícito de cualquier camino que intente entrenar dentro de post_w10_controlled
evidencia de que al menos E1_v5_clean puede operar sin fit()
evaluación honesta de si E9_v2_clean ya puede operar igual o si aún requiere completar su paquete de inferencia
5. Etapas obligatorias
ETAPA 1. Auditoría de rutas que hoy disparan entrenamiento
Objetivo

Ubicar exactamente dónde post_w10_controlled termina reutilizando una ruta que hace fit().

Qué debes hacer
localizar el entrypoint real de post_w10_controlled
seguir la cadena de llamadas hasta identificar:
qué función entra a modelado
qué función llama fit()
qué parte del flujo experimental está siendo reutilizada indebidamente
documentar la ruta exacta:
archivo
función
motivo por el que esa función pertenece a training/research y no a inferencia
Qué debes entregar
lista de archivos y funciones involucradas
diagrama breve o explicación secuencial del flujo actual
punto exacto donde se rompe la separación entrenamiento/inferencia
Criterio de éxito

La etapa se considera exitosa si puedes señalar con precisión qué llamada o bloque está haciendo que post_w10_controlled vuelva a entrenar.

Regla de stop

No avances a corregir nada si no identificaste exactamente dónde ocurre el fit().

ETAPA 2. Diseño mínimo de la ruta predict-only
Objetivo

Definir una ruta nueva o corregida que permita inferencia congelada sin entrenamiento.

Requisitos

Debes separar al menos estos componentes:

Modo A: research / experimental

Puede hacer:

fit()
validación temporal
tuning
evaluación experimental
tracker experimental
Modo B: inferencia congelada / operación

Debe hacer solamente:

cargar artefactos congelados
validar contrato de features
construir input nuevo
aplicar transformaciones ya ajustadas si existen
ejecutar predict()
registrar emisiones
Qué debes definir
qué módulo o función hará load_frozen_profile(...)
qué módulo o función hará validate_inference_schema(...)
qué módulo o función hará predict_with_frozen_model(...)
qué wrapper usará post_w10_controlled
Criterio de éxito

La etapa se considera exitosa si existe un diseño concreto donde la ruta de inferencia ya no dependa del runner experimental.

ETAPA 3. Implementación de la ruta predict-only para E1_v5_clean
Objetivo

Dejar completamente operable al menos el benchmark E1_v5_clean en modo inferencia congelada.

Requisitos

Debes lograr que E1_v5_clean pueda:

cargar sus artefactos congelados
validar columnas/features esperadas
aplicar el transformador correcto si lo hubo
ejecutar solo predict()
devolver predicciones listas para emisión
Si faltan artefactos de inferencia

Si descubres que hoy no existe un paquete suficiente de inferencia, debes construirlo o dejarlo formalizado de forma mínima y trazable.

Ese paquete debe incluir, como mínimo, si aplica:

artefacto serializado del modelo
transformador serializado o pipeline congelado
lista de features esperadas
metadatos de entrenamiento relevantes
horizonte
target_mode
lags
orden de columnas o esquema equivalente
Importante

No debes reentrenar con semanas post-W10 para “crear” estos artefactos.
Debes partir del benchmark congelado ya existente.

Criterio de éxito

La etapa se considera exitosa si E1_v5_clean ya puede correr inferencia post-W10 sin llamar fit().

ETAPA 4. Evaluación y corrección del caso E9_v2_clean
Objetivo

Determinar con rigor si E9_v2_clean ya puede operar como inferencia congelada real o si todavía no.

Qué debes revisar
si existen artefactos suficientes para stacking congelado
si están congeladas las predicciones base / meta-modelo / contrato de ensamblado
si la tabla curada E9 puede reconstruirse sin reentrenar nada
si hoy el flujo E9 está rehaciendo pasos que implican fit()
Posibles salidas válidas
A. E9 queda también operativo en predict-only

Perfecto. Déjalo funcionando.

B. E9 no queda todavía inferible sin retraining

Entonces debes decirlo con claridad, no simular que quedó resuelto, y dejar:

diagnóstico exacto
qué artefacto falta
qué capa debe congelarse después
por qué no sería metodológicamente correcto usarlo aún en post-W10
Criterio de éxito

La etapa se considera exitosa si el estado real de E9_v2_clean queda diagnosticado y, si es viable, corregido; si no es viable todavía, debe quedar documentado sin ambigüedad.

ETAPA 5. Blindaje técnico de post_w10_controlled
Objetivo

Evitar que el problema vuelva a ocurrir silenciosamente.

Debes implementar una protección explícita

Si el perfil es post_w10_controlled, el sistema debe:

entrar a la ruta predict-only
y fallar de forma explícita si intenta entrar a cualquier rama de entrenamiento
Formas válidas

Puedes hacerlo mediante:

separación de módulos
guard clauses
validaciones de modo de ejecución
excepciones explícitas
restricciones del wrapper operativo
Lo importante

No basta con “confiar” en que no se llamará fit().
Debe quedar protegido por código.

Criterio de éxito

La etapa se considera exitosa si ya no es posible que post_w10_controlled reuse silenciosamente una ruta de entrenamiento.

ETAPA 6. Validación material mínima
Objetivo

Demostrar que la corrección funciona de verdad.

Debes correr una validación controlada pequeña

No una campaña completa necesariamente, pero sí una prueba material suficiente para comprobar:

que el dataset maestro actualizado se puede usar como input
que la ruta de inferencia carga artefactos congelados
que se ejecuta predict() solamente
que no se ejecuta fit()
que las predicciones pueden pasar al registro de emisiones
Qué debes dejar como evidencia
logs
rutas de artefactos cargados
semanas usadas como input
predicciones emitidas
confirmación explícita de ausencia de entrenamiento
Criterio de éxito

La etapa se considera exitosa si puedes demostrar con evidencia que la inferencia post-W10 ya funciona sin reentrenamiento, al menos para E1_v5_clean.

6. Requisitos de diseño técnico
6.1 Congelar contrato de features

No basta con congelar el modelo.
Debes congelar también el contrato de entrada, incluyendo si aplica:

columnas requeridas
orden de columnas
lags esperados
horizonte
target_mode
transform_mode
columnas derivadas obligatorias

Antes de predecir, debes validar este esquema.

6.2 No recalcular selección de features sobre semanas nuevas

Si el modelo operativo depende de features seleccionadas, esas features deben venir ya congeladas como parte del perfil de inferencia.

No debes usar semanas nuevas para recalcular:

correlaciones
selección lasso
tuning de alpha
nada equivalente
6.3 Reutilizar estructura existente cuando convenga

Si módulos como frozen_profiles.py, frozen_inference.py, launcher o wrappers ya existen, reutilízalos.
Pero si internamente siguen entrando a training, corrígelos.

7. Archivos esperados o equivalentes

No inventes nombres si ya existe estructura equivalente, pero en esencia debe quedar resuelto algo equivalente a:

módulo de carga de perfil congelado
módulo de validación de esquema de inferencia
módulo predict-only
ajuste del wrapper post_w10_controlled
artefactos o metadata de inferencia por benchmark
documentación breve de la separación training vs predict-only
8. Qué debes entregar al final

Quiero exactamente estos apartados:

1. Diagnóstico del problema
dónde estaba el fit()
por qué ocurría
qué ruta experimental estaba siendo reutilizada
2. Archivos creados o modificados

Lista exacta con ruta y función de cada archivo.

3. Qué cambió en la arquitectura

Explica brevemente cómo quedó separada:

ruta experimental
ruta de inferencia congelada
4. Estado de E1_v5_clean

Confirmar si ya quedó operable en predict-only.

5. Estado de E9_v2_clean

Confirmar si:

ya quedó operable en predict-only, o
todavía no, y por qué
6. Validación material

Explica qué prueba corriste y qué evidencias dejó.

7. Garantía metodológica

Responder explícitamente:

¿se eliminó el reentrenamiento dentro de post_w10_controlled?
¿las semanas nuevas siguen entrando al dataset maestro?
¿las semanas nuevas se usan solo como input de inferencia?
¿la ruta post-W10 quedó ya separada del training experimental?
8. Veredicto final

Debes cerrar con una de estas opciones:

A. separación fit/predict corregida y validada
B. separación corregida parcialmente; E1 listo, E9 todavía incompleto
C. problema identificado pero todavía no resuelto
9. Criterio de éxito global

El trabajo solo se considera bien hecho si puedes demostrar estas tres cosas:

el dataset maestro sí puede crecer con semanas nuevas
el benchmark sí puede usar esas semanas como input
post_w10_controlled ya no vuelve a pasar por fit() sobre datos nuevos

La prueba decisiva es esta:

si deshabilitas el código de entrenamiento, la inferencia post-W10 debe seguir funcionando.

Si no ocurre eso, entonces la separación todavía no quedó bien hecha.

10. Instrucción final

Actúa con criterio conservador, precisión técnica y honestidad metodológica.

No maquilles el problema.
No simules congelamiento donde aún hay retraining.
No declares listo a E9_v2_clean si todavía depende de rehacer fitting.
Corrige primero lo esencial.
Prioriza dejar impecable el patrón predict-only en E1_v5_clean y úsalo como referencia fuerte para el resto.

Tu misión aquí es una sola:

convertir post_w10_controlled en una operación de inferencia congelada real, no en un entrenamiento disfrazado.
