Prompt para el agente: auditoría retrospectiva y tabla maestra comparativa por horizonte

Quiero que hagas una tarea de auditoría retrospectiva y consolidación experimental sobre los experimentos de modelado ya existentes en el proyecto Radar. En esta etapa no quiero que corras nuevos modelos. Quiero que busques, identifiques, reconstruyas y documentes los resultados reales ya producidos, aunque estén dispersos en distintas carpetas o con distintos niveles de completitud.

La meta es construir una tabla maestra comparativa por horizonte, útil para:

saber cuántos experimentos reales existen hasta ahora;
comparar familias y corridas;
identificar mejores runs por horizonte;
evaluar si ya hay base para futuros modelos compuestos por horizonte;
y dejar un sistema que pueda seguir actualizándose en adelante.
1. Objetivo general

Revisa todos los resultados experimentales existentes en el proyecto y reconstruye el inventario real de runs corridos, especialmente de las familias:

E1 = Ridge
E2 = Huber
E3 = árboles / no lineales

No asumas que las notas, conversaciones o resúmenes previos están completos o actualizados.
Tu fuente principal debe ser la evidencia real en disco.

2. Qué debes hacer
A. Buscar runs reales existentes

Debes localizar todos los experimentos que efectivamente tengan artefactos de salida y por tanto cuenten como corridas reales.

No te bases solo en nombres mencionados en notas.
Cuenta como run real únicamente aquel para el que encuentres evidencia suficiente, por ejemplo archivos como:

metadata_run.json
parametros_run.json
metricas_horizonte.json
resumen_modeling_horizontes.json
predicciones_h1.csv a predicciones_h4.csv
comparaciones contra otros runs
otros artefactos claramente asociados a una corrida terminada o parcialmente terminada

Para cada run identificado, registra:

run_id
familia
modelo
ruta o carpeta del run
qué artefactos existen realmente
qué artefactos faltan
B. Reconstruir el inventario experimental real

Necesito que determines con precisión:

cuántos experimentos E1 existen realmente;
cuántos experimentos E2 existen realmente;
cuántos experimentos E3 existen realmente;
cuántos experimentos corridos existen en total;
cuáles están completos y cuáles incompletos;
cuáles fueron planeados pero no realmente corridos.

Si detectas discrepancias entre lo planeado y lo efectivamente corrido, debes señalarlo con claridad.

C. Extraer métricas por horizonte

Para cada run real que encuentres, debes extraer y consolidar, por cada uno de los 4 horizontes:

mae
rmse
direction_accuracy
deteccion_caidas
loss_h

Y globalmente:

L_total_Radar

Si algún run no contiene todos los campos, registra lo disponible y marca explícitamente los faltantes.

3. Marco de evaluación que debes respetar

Toma en cuenta que el Radar no es solo una regresión numérica. Tiene 4 horizontes y cada experimento debe poder leerse, al menos, en estas dimensiones:

A. Dimensión numérica

Qué tan bien predice el valor del índice.

Usa aquí principalmente:

mae
rmse
loss_h
L_total_Radar
B. Dimensión de dirección

Qué tan bien predice si el índice:

sube,
baja,
o se mantiene.

La métrica clave aquí es:

direction_accuracy

No la trates como secundaria. Es central para la utilidad operativa del Radar.

C. Dimensión de detección de deterioro

Qué tan bien detecta caídas, descensos o deterioros relevantes.

La métrica clave aquí es:

deteccion_caidas

Tampoco es secundaria.
En Radar, detectar una baja importante puede ser tan o más valioso que reducir un poco el error numérico.

4. Implicación práctica para la tabla comparativa

La tabla maestra no debe servir solo para contestar “qué modelo tuvo menor error”, sino también para ver:

qué run es mejor por horizonte;
qué run es mejor en dirección por horizonte;
qué run es mejor en detección de caídas por horizonte;
qué familia parece más fuerte en corto, mediano o largo plazo.

Además, la tabla debe dejar base para una futura decisión metodológica sobre si conviene:

un campeón único global,
o una arquitectura compuesta con distintos modelos por horizonte.
5. Tabla maestra que debes construir

Quiero una tabla consolidada, una fila por experimento, con columnas mínimas como estas:

run_id
family
model
target_mode
feature_mode
transform_mode
lags
feature_count_prom
H1_mae
H1_rmse
H1_direction_accuracy
H1_deteccion_caidas
H1_loss
H2_mae
H2_rmse
H2_direction_accuracy
H2_deteccion_caidas
H2_loss
H3_mae
H3_rmse
H3_direction_accuracy
H3_deteccion_caidas
H3_loss
H4_mae
H4_rmse
H4_direction_accuracy
H4_deteccion_caidas
H4_loss
L_total_Radar
observacion_breve
status_run

Para status_run, usa categorías como:

completo
parcial
inconsistente

Si alguna columna no aplica o no existe para ciertos runs, mantenla y deja un valor controlado consistente (null, vacío o equivalente).

6. Productos de salida que debes generar

Genera como mínimo estos entregables:

1. CSV maestro

Por ejemplo:

tabla_maestra_experimentos_radar.csv
2. Excel maestro

Por ejemplo:

tabla_maestra_experimentos_radar.xlsx

Con al menos estas hojas:

Hoja 1: runs_consolidados

La tabla maestra completa.

Hoja 2: ranking_por_horizonte

Con ranking de mejores runs por horizonte usando loss_h como criterio principal.

Debe incluir al menos:

mejor H1
mejor H2
mejor H3
mejor H4
mejor global por L_total_Radar
Hoja 3: ranking_dimensiones

Con una vista resumida por horizonte de:

mejor run en dimensión numérica
mejor run en direction_accuracy
mejor run en deteccion_caidas
mejor run global del horizonte por loss_h
Hoja 4: inventario_runs

Con columnas tipo:

run_id
family
model
path_run
metadata_run
metricas_horizonte
parametros_run
predicciones
comparaciones
status_artifactos
comentario
3. JSON de inventario

Por ejemplo:

inventario_experimentos_radar.json
4. Resumen en markdown

Por ejemplo:

resumen_auditoria_experimentos.md

Donde expliques:

qué runs encontraste,
cuáles faltan,
cuáles están incompletos,
qué inconsistencias detectaste,
cuál es el mejor run global,
cuál es el mejor por horizonte,
y qué patrón preliminar emerge entre familias.
7. Reglas de reconstrucción
A. No inventes información

Si algo no está en los artefactos reales, no lo supongas.

B. Prioriza evidencia en disco

Si hay contradicción entre notas narrativas y archivos reales, da prioridad a los archivos reales.

C. No descartes automáticamente corridas parciales

Inclúyelas si contienen información útil, pero marca claramente su estado.

D. Sé estricto con run_id

No mezcles corridas parecidas por nombre.
Cada fila debe corresponder a un run_id real identificado.

E. Si hay múltiples carpetas o duplicados del mismo run

Resuelve cuál es la versión válida usando criterios como:

completitud de artefactos,
timestamps,
consistencia interna.

Y documenta la decisión.

8. Rutas y zonas a inspeccionar

Debes buscar en todas las rutas razonables donde puedan existir outputs de modelado y comparaciones:

carpetas de outputs
carpetas de runs
subcarpetas por familia
artefactos históricos
archivos sueltos de comparación
cualquier estructura intermedia que se haya usado durante la evolución del proyecto

La meta es reconstruir la historia experimental real, no asumir que ya está perfectamente ordenada.

9. Validaciones que debes hacer

Antes de cerrar el trabajo, valida:

que no haya runs duplicados en la tabla maestra;
que cada métrica por horizonte corresponda al run correcto;
que L_total_Radar coincida con el archivo fuente cuando exista;
que el ranking por horizonte esté ordenado por loss_h ascendente;
que el ranking global esté ordenado por L_total_Radar ascendente;
que el ranking por dimensiones use correctamente:
error numérico,
direction_accuracy,
deteccion_caidas.

Si detectas anomalías, documenta el problema en el resumen final.

10. Qué análisis interpretativo debes incluir

Además de consolidar datos, quiero una lectura breve pero precisa sobre:

cuál es el mejor run global encontrado hasta ahora;
cuál es el mejor run en H1;
cuál es el mejor run en H2;
cuál es el mejor run en H3;
cuál es el mejor run en H4;
qué runs destacan más por dirección;
qué runs destacan más por detección de caídas;
si hay evidencia de que distintos horizontes favorecen distintas familias;
si ya se justifica metodológicamente pensar en una futura familia de ensamblado por horizonte.

No exageres conclusiones. Si la evidencia todavía es débil o el inventario está incompleto, dilo claramente.

11. Sobre la explicación de por qué cambia cada horizonte

En esta etapa no es obligatorio construir todavía una métrica homogénea de “peso de variables” comparable entre todos los modelos.

Eso se puede dejar para una etapa posterior.

Pero sí debes dejar sembrado en el resumen metodológico que el objetivo final del Radar no es solo anticipar el valor del índice, sino también poder mostrar, para cada horizonte:

qué se espera que pase;
si sube, baja o se mantiene;
y eventualmente cuál parece ser el motivo del cambio.

Por tanto, si encuentras artefactos ya disponibles que puedan servir después para explicar los cambios por horizonte, como por ejemplo:

features seleccionadas,
importancias de variables,
coeficientes,
resúmenes por horizonte,

debes inventariarlos y mencionarlos, sin forzar todavía una comparación homogénea entre familias.

12. Qué preguntas debes responder al final

Tu entrega final debe responder explícitamente:

¿Cuántos experimentos reales encontraste de E1, E2 y E3?
¿Cuántos experimentos reales hay en total?
¿Qué runs están completos y cuáles parciales?
¿Cuál es el mejor run global por L_total_Radar?
¿Cuál es el mejor run por cada horizonte?
¿Qué runs son más fuertes en direction_accuracy?
¿Qué runs son más fuertes en deteccion_caidas?
¿Hay suficiente base para empezar a pensar en un ensamblado por horizonte?
¿Qué huecos de documentación o de artefactos encontraste?
¿Qué conviene automatizar desde ahora para que esta tabla se siga actualizando sola?
13. Qué cambios de código puedes hacer

Si hace falta, puedes crear o adaptar un script utilitario, por ejemplo algo como:

backfill_runs.py
build_experiments_master_table.py
audit_experiment_outputs.py

También puedes reutilizar o ampliar utilerías existentes si eso evita duplicación y deja el proceso reutilizable.

El resultado debe quedar limpio y fácil de volver a correr después.

14. Criterio metodológico de esta tarea

Este trabajo debe ejecutarse como una auditoría técnica experimental, no como un simple scraping superficial de archivos.

Eso implica:

rigor en la identificación de runs;
consistencia en métricas;
trazabilidad de fuentes;
prudencia ante faltantes;
y utilidad real para la siguiente fase del proyecto.
15. Resultado conceptual esperado

Al terminar, quiero que quede construida una base retrospectiva que permita:

comparar corridas de distintas familias;
identificar mejores runs por horizonte;
identificar mejores runs por dirección y por detección de caídas;
decidir si conviene un campeón global o especialistas por horizonte;
y usar esta tabla como insumo para una futura arquitectura compuesta del Radar.
16. Nombre conceptual de la tarea

Puedes describir esta tarea como:

Auditoría retrospectiva y consolidación de experimentos Radar para construir tabla maestra comparativa por horizonte y por dimensiones operativas.
