Prompt para el agente

Nombre de la tarea:
Validacion material de la operacion minima controlada post-W10 en Radar

Modo de trabajo exigido:
Ejecucion por etapas, con validacion explicita al cierre de cada etapa.
No avanzar a la siguiente si la anterior no quedo materialmente validada o si no dejaste evidencia suficiente.

0. Instruccion general

Estas trabajando dentro del proyecto Radar. No debes comportarte como si esta tarea partiera de cero. Debes respetar el historial metodologico, arquitectonico y operativo ya acumulado en el proyecto.

Tu mision en esta tarea no es experimentar, no es redisenar el modelado, y no es mejorar familias de modelos.

Tu mision es esta:

demostrar con una corrida real que la operacion minima controlada post-W10 funciona materialmente de punta a punta, partiendo del hecho de que las semanas nuevas ya fueron promocionadas a texto.

1. Restricciones absolutas
1.1 No reabrir modelado

No debes:

reentrenar modelos
recalibrar hiperparametros
redefinir benchmarks
modificar src/modeling/
cambiar artefactos canonicos congelados
correr nuevas familias experimentales
reinterpretar esta tarea como una fase de investigacion
1.2 No mezclar operacion con entrenamiento

Las semanas nuevas post-W10:

si deben entrar al flujo operativo
si deben entrar al dataset maestro operativo
si deben alimentar inferencia
si deben alimentar evaluacion operativa cuando ya exista valor observado
no deben incorporarse al entrenamiento del benchmark congelado en esta tarea
1.3 No romper la arquitectura existente

No debes:

inventar rutas si ya existen
duplicar modulos si ya hay equivalentes
meter esta logica dentro de pipeline_orchestrator.py salvo necesidad critica e ineludible
hacer un rediseno amplio del repo
mover scripts existentes "por limpieza" si no es indispensable
1.4 No avanzar sin evidencia

Cada etapa debe cerrar con:

verificacion material
artefactos
reporte breve
criterio de exito o falla

Si una etapa falla, detente, corrige lo minimo necesario, documenta y vuelve a validar.
No tapes errores con supuestos silenciosos.

2. Estado del proyecto que debes respetar
2.1 Corte historico y operacion post-W10

La definicion operativa vigente es esta:

2026-W10 es el ultimo corte historico validado
desde 2026-W11 en adelante entran semanas nuevas del mundo real
esas semanas si alimentan inferencia y evaluacion operativa
esas semanas no entran al entrenamiento del modelo congelado en esta etapa
2.2 Benchmarks congelados a usar

Debes respetar exactamente estos perfiles:

E1_v5_clean como campeon numerico vigente
E9_v2_clean como referente de riesgo

Para E9, debes respetar ademas sus dependencias historicas congeladas:

E2_v3_clean
E3_v2_clean
E5_v4_clean
E7_v3_clean

No cambies estos referentes.
No promociones otros.
No sustituyas artefactos canonicos.

2.3 Estado del insumo

Debes partir de este hecho ya dado:

las semanas post-W10 ya fueron promocionadas a texto

Eso significa:

no debes rehacer extraccion
no debes rehacer preprocesamiento a texto
salvo que detectes inconsistencia critica, la entrada de esta tarea es el texto ya listo
3. Objetivo exacto de esta tarea

Cerrar materialmente esta cadena:

texto post-W10 -> NLP -> dataset maestro -> inferencia con modelos congelados -> registro de emisiones -> tabla operativa de resultados

sin tocar el modelado canonico y sin reentrenar nada.

4. Logica temporal obligatoria que debes respetar

Debes trabajar bajo esta logica:

para la primera semana nueva disponible, el sistema usa el dataset maestro actualizado con el historico validado + esa semana nueva ya incorporada como input operativo
para la siguiente semana, usa el historico validado + las semanas nuevas ya incorporadas hasta ese punto
y asi sucesivamente
Precision critica

Eso no significa reentrenamiento incremental.
Significa unicamente que el dataset de entrada operativo va creciendo con nuevas semanas, mientras el modelo congelado permanece identico.

Debes dejar esto explicitamente validado al final:

las semanas nuevas entraron como input operativo
no entraron como datos de entrenamiento del benchmark congelado
5. Forma de ejecucion obligatoria

Debes ejecutar esta tarea en etapas estrictas.

ETAPA 1. Auditoria previa de disponibilidad y consistencia
Objetivo

Confirmar que existen las condiciones minimas reales para correr la primera validacion material post-W10.

Que debes verificar
Que semanas post-W10 existen ya en texto
Donde estan ubicadas
Que modulo o flujo NLP debe procesarlas
Que rutas usa la actualizacion del dataset maestro
Que comando o preset real activa la operacion post_w10_controlled
Que entorno debe usarse en cada tramo:
ops_python para NLP y parte operativa previa
modeling_python para refresh congelado, reconstruccion curada E9 y registro de emisiones
Que la reconstruccion de tabla_maestra_experimentos_radar_e9_curada.xlsx corra por el entorno correcto de modelado
Que los directorios de salida de artefactos esten correctamente resueltos
Que debes producir
un reporte breve de preflight
lista exacta de semanas disponibles
lista de comandos o entrypoints que vas a usar
confirmacion de que tramo vas a correr realmente:
preferentemente nlp -> modeling, dado que el texto ya existe
Criterio de exito

La etapa se considera exitosa si puedes afirmar con evidencia:

que semanas seran procesadas
con que flujo
con que entornos
y sin ambiguedad sobre donde quedaran los artefactos
Regla de stop

Si aqui detectas que no existe una ruta real y ejecutable para NLP -> dataset maestro -> inferencia -> registro, no avances.
Corrige el problema minimo necesario y vuelve a validar esta etapa.

ETAPA 2. Procesamiento NLP de semanas post-W10
Objetivo

Procesar en NLP las semanas nuevas ya promocionadas a texto.

Requisitos
usar el pipeline NLP canonico ya definido en el proyecto
no alterar definiciones metodologicas del material textual
no modificar criterios historicos que rompan comparabilidad
mantener trazabilidad por semana
Que debes guardar
logs
manifest o equivalente
resumen por semana procesada
errores por semana, si existen
Que debes reportar
semanas procesadas correctamente
semanas fallidas
productos NLP generados
rutas exactas de salida
Criterio de exito

La etapa se considera exitosa si las semanas post-W10 quedan materialmente convertidas en insumo estructurado apto para incorporarse al dataset maestro.

Regla de stop

Si el NLP no produce salidas utilizables para el dataset maestro, no avances.

ETAPA 3. Incorporacion al dataset maestro
Objetivo

Actualizar el dataset maestro operativo con las semanas nuevas ya procesadas por NLP.

Requisitos
preservar intacto el tramo historico validado hasta 2026-W10
incorporar solo las semanas nuevas post-W10
mantener formato compatible con el modelado congelado
verificar columnas esperadas por los benchmarks
Validaciones obligatorias
rango temporal antes y despues de la actualizacion
semanas nuevas efectivamente integradas
ausencia de ruptura estructural en columnas
compatibilidad con los modelos congelados
Que debes guardar
snapshot del dataset maestro previo, si la arquitectura ya lo permite
snapshot del dataset maestro actualizado, o al menos evidencia verificable del cambio
resumen de incorporacion por semana
Que debes reportar
semanas incorporadas
rango temporal final del dataset
validacion de compatibilidad estructural
Criterio de exito

La etapa se considera exitosa si el dataset maestro ya incluye las semanas post-W10 y sigue siendo consumible por la inferencia congelada.

Regla de stop

Si el dataset actualizado no puede ser leido por los perfiles congelados, no avances.

ETAPA 4. Refresh congelado e inferencia real
Objetivo

Ejecutar inferencia real con los benchmarks congelados sobre el dataset maestro ya actualizado.

Benchmarks obligatorios
E1_v5_clean
E9_v2_clean
Requisitos
no reentrenar
no ajustar hiperparametros
no modificar runner_module canonico
no alterar canonical_run_dir, metadata_path, parameters_path
usar exactamente la logica operativa ya montada para post_w10_controlled
Que debes validar
que semanas entraron como input operativo
que emisiones nuevas se generaron
para que horizontes
que semanas todavia no son evaluables por no existir aun el valor futuro observado
Que debes guardar
logs de inferencia
summary
manifest
snapshots necesarios
outputs de prediccion o equivalente reutilizado por el sistema
Criterio de exito

La etapa se considera exitosa si se generaron emisiones nuevas reales usando modelos congelados sobre dataset actualizado, sin reentrenamiento.

Regla de stop

Si detectas que la operacion esta intentando reentrenar, recalibrar o sustituir artefactos canonicos, detente y corrige de inmediato.

ETAPA 5. Registro formal de emisiones
Objetivo

Persistir correctamente las emisiones generadas.

Requisitos
usar la logica ya preparada para construir el registro formal
guardar registro_emisiones.csv
guardar registro_emisiones.json si aplica
mantener coherencia entre emision, benchmark usado, semana input, horizonte y artefactos asociados
Que debes validar
que las emisiones quedaron registradas
que cada emision tiene suficiente trazabilidad
que las rutas en manifest y snapshots coinciden con los artefactos reales
Criterio de exito

La etapa se considera exitosa si el registro de emisiones quedo materialmente poblado y auditable.

Regla de stop

Si la inferencia se genero pero no puede registrarse con trazabilidad suficiente, la operacion no se considera validada.

ETAPA 6. Tabla operativa de resultados
Objetivo

Dejar una tabla minima, clara y auditable que permita revisar que semanas entraron, que se predijo y que ya puede evaluarse.

Esto es obligatorio

Debes generar una tabla consolidada de resultados operativos.

Tabla 1: emisiones operativas

Debe incluir como minimo:

operation_id
run_timestamp
week_input
week_emission
horizonte
modelo_referente
prediccion_emitida
estado_evaluacion
valor_real_observado
error
direccion_predicha
direccion_real
deteccion_caida_predicha
deteccion_caida_real
observaciones
ruta_run_dir
ruta_registro_emisiones
ruta_manifest
Tabla 2: resumen agregado de corrida

Debe incluir como minimo:

semanas detectadas en texto
semanas procesadas por NLP
semanas incorporadas al dataset maestro
semanas con inferencia emitida
emisiones generadas por horizonte
emisiones pendientes de evaluacion
errores detectados
estatus final de la corrida
Reutilizacion

Si ya existe una estructura equivalente en el proyecto, reutilizala.
Si no existe, creala sin sobreingenieria, de forma simple y trazable.

Criterio de exito

La etapa se considera exitosa si queda una salida tabular suficiente para:

auditoria
revision manual
base de conexion futura a tablero
6. Artefactos obligatorios finales

Debes dejar trazabilidad bajo una ruta equivalente a:

artifacts/operations/post_w10/<operation_id>/

Con al menos estos artefactos:

manifest.json
summary.json
logs
snapshots
registro_emisiones.csv
registro_emisiones.json si aplica
tabla operativa de resultados
resumen agregado de corrida

Y el manifest debe fijar explicitamente:

canonical_run_dir
metadata_path
parameters_path
runner_module
7. Formato de reporte obligatorio al final

No quiero una salida vaga.
Quiero exactamente estos apartados:

1. Archivos creados o modificados

Lista exacta, con ruta.

2. Que ejecutaste realmente

Explica:

que semanas corriste
que tramo corriste
con que entornos
con que entrypoint o preset
3. Resultado por etapa

Para cada etapa, indicar:

exitosa / fallida / parcial
evidencia
artefactos principales
4. Estado del dataset maestro

Confirmar:

rango temporal final
semanas nuevas integradas
compatibilidad con inferencia congelada
5. Resultado de inferencia

Confirmar:

que emisiones se generaron
con que benchmarks
para que horizontes
que quedo pendiente de evaluacion
6. Registro de emisiones

Confirmar:

si quedo correctamente poblado
donde esta
si es auditable
7. Tabla operativa de resultados

Entregar ruta exacta y resumen de contenido.

8. Incidencias

Errores, supuestos, correcciones minimas y riesgos remanentes.

9. Validacion metodologica explicita

Responder si o no, con justificacion breve, a estas preguntas:

Las semanas nuevas entraron al flujo operativo?
Las semanas nuevas fueron incorporadas al dataset maestro?
Los modelos congelados usaron esas semanas como input?
Se evito completamente el reentrenamiento?
La secuencia temporal quedo preservada?
La operacion post-W10 quedo materialmente validada?
10. Veredicto final

Debes cerrar con una sola de estas opciones:

A. operacion minima post-W10 validada materialmente
B. operacion parcialmente validada, con fallas corregibles
C. operacion todavia no validada, requiere correcciones antes de uso real
8. Criterio de exito global

Esta tarea solo se considera bien hecha si puedes demostrar con evidencia que:

las semanas post-W10 ya en texto fueron procesadas por NLP
esas semanas quedaron incorporadas al dataset maestro
el modelo congelado leyo el dataset actualizado
se generaron predicciones nuevas
no hubo reentrenamiento
quedo registro formal de emisiones
quedo tabla operativa de resultados
y la arquitectura historica de Radar no se rompio
9. Instruccion final al agente

Actua con disciplina operativa, trazabilidad fuerte y criterio conservador.

No improvises.
No redisenes por gusto.
No abras nuevas lineas experimentales.
No confundas dataset operativo actualizado con entrenamiento incremental.

Tu mision aqui es una sola:

probar materialmente que Radar ya puede operar post-W10 con semanas reales, usando modelos congelados, registro formal de emisiones y una salida tabular auditable. Guarda este prompto donde corresponde y ejecuta
