# Prompt para el agente: ampliar tabla maestra y rankings por métrica específica en cada horizonte

## Contexto y continuidad

Ya existe una auditoría retrospectiva de experimentos Radar y ya se construyó una tabla maestra comparativa con entregables como CSV, Excel, JSON y resumen Markdown. Esa auditoría ya permitió identificar:

- runs reales por familia;
- mejores runs globales y por horizonte;
- evidencia de especialización por horizonte;
- base metodológica preliminar para pensar en un ensamblado por horizonte.

Sin embargo, la tabla actual todavía se queda corta para análisis fino, porque aunque ya muestra rankings agregados, **no deja ver de forma completa, para cada horizonte y para cada métrica específica, cuál es la mejor corrida**.

Eso es un faltante importante, porque el Radar no se evalúa solo por una pérdida global. Necesitamos poder inspeccionar de manera directa, por horizonte y por dimensión operativa, quién gana en:

- `mae`
- `rmse`
- `direction_accuracy`
- `deteccion_caidas`
- `loss_h`

Y además distinguir claramente entre:

- mejor corrida por métrica en H1
- mejor corrida por métrica en H2
- mejor corrida por métrica en H3
- mejor corrida por métrica en H4

La meta de esta tarea no es correr modelos nuevos. La meta es **hacer más completa, útil y analíticamente correcta la tabla maestra comparativa**.

## Objetivo de esta tarea

Quiero que amplíes el sistema de auditoría / consolidación experimental para que la salida final permita ver, de manera explícita y ordenada:

1. cuál es la mejor corrida por horizonte en cada métrica específica;
2. el ranking completo de corridas por horizonte para cada métrica, no solo el primer lugar;
3. una vista utilizable para análisis metodológico y para toma de decisiones sobre:
   - campeón global,
   - especialistas por horizonte,
   - y posibles ensamblados futuros.

## Problema detectado en la versión actual

La tabla existente y sus hojas resumen sí sirven para:

- ver el mejor global;
- ver algunos ganadores por horizonte;
- ver una lectura resumida por dimensiones.

Pero me parecen incompletas porque no responden de forma suficientemente explícita preguntas del tipo:

- ¿Cuál fue la mejor corrida en `mae` para H1?
- ¿Cuál fue la mejor en `rmse` para H1?
- ¿Cuál fue la mejor en `direction_accuracy` para H1?
- ¿Cuál fue la mejor en `deteccion_caidas` para H1?
- ¿Cuál fue la mejor en `loss_h` para H1?

Y lo mismo para H2, H3 y H4.

Necesito que esto quede visible de forma directa en los entregables, sin tener que reconstruirlo manualmente desde la hoja principal.

## Alcance exacto

No quiero rehacer desde cero toda la auditoría.

Quiero que extiendas el proceso ya existente para que produzca, además de la tabla maestra principal, **rankings completos y claros por métrica y por horizonte**.

La solución debe integrarse al flujo actual de construcción de la tabla maestra, idealmente dentro del mismo script que ya genera los entregables consolidados, o en utilerías muy cercanas si eso deja una arquitectura más limpia.

## Qué debes hacer

### 1. Mantener la tabla maestra base

Debes conservar la tabla maestra existente, una fila por run, con sus columnas ya consolidadas por horizonte y globales.

No elimines información ya útil.
No simplifiques la tabla.
La tabla base debe seguir funcionando como inventario consolidado de runs.

### 2. Agregar una capa de rankings detallados por métrica y horizonte

Debes construir una salida donde se pueda ver, explícitamente, para cada horizonte (`H1`, `H2`, `H3`, `H4`) y para cada métrica:

- `mae`
- `rmse`
- `direction_accuracy`
- `deteccion_caidas`
- `loss_h`

el ranking de runs correspondiente.

### 3. Respetar el sentido correcto de optimización por métrica

Esto es crítico.

Debes ordenar y seleccionar ganadores usando el criterio correcto según la métrica:

#### Métricas donde menor es mejor
- `mae`
- `rmse`
- `loss_h`
- `L_total_Radar`

#### Métricas donde mayor es mejor
- `direction_accuracy`
- `deteccion_caidas`

No quiero errores de interpretación aquí.
El agente debe ser explícito en el código y en la salida acerca del sentido de optimización de cada métrica.

### 4. Construir vistas útiles, no solo un “top 1”

No basta con guardar solo el mejor run por métrica.
Quiero que quede también el ranking completo o al menos suficientemente amplio para análisis.

Idealmente, para cada combinación horizonte+métrica, debe quedar una tabla con:

- posición / rank
- run_id
- family
- model
- valor de la métrica
- status_run
- observacion_breve (si existe)
- opcionalmente `L_total_Radar` para contexto

Esto es importante porque a veces la diferencia entre primer y segundo lugar puede ser marginal y metodológicamente relevante.

### 5. Actualizar el Excel maestro con hojas nuevas o ampliadas

Quiero que el Excel maestro quede más completo.

Como mínimo, además de la hoja base, debe incluir una o ambas de estas opciones:

#### Opción preferida: hoja larga y explícita
Una hoja nueva, por ejemplo:

`ranking_metricas_por_horizonte`

Con estructura tipo:

- horizonte
- metrica
- sentido_optimizacion
- rank
- run_id
- family
- model
- valor_metrica
- status_run
- L_total_Radar
- comentario / observacion

Esta opción es muy poderosa porque permite filtrar y ordenar fácilmente en Excel.

#### Opción complementaria: hoja resumen compacta
Otra hoja, por ejemplo:

`ganadores_por_metrica_horizonte`

Donde cada fila sea una combinación de horizonte y métrica, con columnas como:

- horizonte
- metrica
- sentido_optimizacion
- mejor_run_id
- mejor_family
- mejor_model
- mejor_valor
- segundo_run_id
- segundo_valor
- tercer_run_id
- tercer_valor

Esto ayudaría a lectura ejecutiva rápida.

Mi preferencia es que generes ambas:
- una hoja larga analítica;
- y una hoja compacta ejecutiva.

### 6. Mantener y mejorar la hoja de ranking_dimensiones

La hoja `ranking_dimensiones` actual no debe desaparecer, pero sí debe quedar claramente subordinada a esta nueva lógica más detallada.

Quiero que revises si esa hoja:

- se puede enriquecer,
- o se debe mantener como resumen ejecutivo,
- mientras las hojas nuevas hacen el desglose fino.

No la dejes redundante o ambigua.

### 7. Asegurar coherencia con runs parciales o incompletos

Si un run no tiene una métrica específica para cierto horizonte:

- no lo inventes;
- no lo mezcles;
- no lo rankees en esa combinación horizonte+métrica.

Pero sí debe seguir apareciendo en la tabla maestra general si es un run real auditado.

Quiero reglas claras:

- un run entra al ranking de una métrica si tiene valor válido para esa métrica;
- si no lo tiene, queda fuera solo de ese ranking específico;
- eso debe ser consistente y trazable.

### 8. Cuidar empates y casos casi idénticos

Si hay empates exactos o métricas prácticamente idénticas, no quiero que eso quede oculto.

Debes:

- conservar el orden de ranking de manera estable y reproducible;
- documentar el criterio de desempate, si existe;
- y, si aplica, dejar en el resumen cuando haya líneas de runs virtualmente empatadas.

No necesito una teoría compleja de empates, pero sí coherencia técnica.

### 9. Actualizar el resumen Markdown

El resumen de auditoría debe ampliarse para contestar explícitamente, además de lo ya existente:

- mejor run en `mae` por horizonte;
- mejor run en `rmse` por horizonte;
- mejor run en `direction_accuracy` por horizonte;
- mejor run en `deteccion_caidas` por horizonte;
- mejor run en `loss_h` por horizonte.

Idealmente con una estructura tipo:

#### H1
- mejor en mae: ...
- mejor en rmse: ...
- mejor en direction_accuracy: ...
- mejor en deteccion_caidas: ...
- mejor en loss_h: ...

#### H2
...

Y así con H3 y H4.

También quiero que señales si:
- un mismo run domina múltiples métricas en un mismo horizonte;
- distintos horizontes favorecen distintos runs;
- y si las diferencias parecen reforzar la hipótesis de especialistas por horizonte.

### 10. Mantener compatibilidad con la automatización futura

Este cambio debe quedar listo para convivir con la integración automática al tracker ya planteada antes. Es decir:

- no diseñes esto como un análisis manual aislado;
- déjalo integrado al proceso regular de generación de tabla maestra;
- de modo que cuando se regenere la auditoría, también se regeneren estas nuevas hojas / rankings.

No hace falta resolver en esta tarea toda la automatización del tracker si no está ya integrada, pero sí dejar la construcción lista para eso.

## Productos de salida esperados

Debes regenerar y/o actualizar, como mínimo:

### 1. CSV maestro
La tabla principal consolidada, si corresponde.

### 2. Excel maestro ampliado
Debe incluir al menos:

- `runs_consolidados`
- `ranking_por_horizonte`
- `ranking_dimensiones`
- `inventario_runs`

Y además nuevas hojas como:

- `ranking_metricas_por_horizonte`
- `ganadores_por_metrica_horizonte`

### 3. JSON de inventario
Si aplica mantenerlo igual, mantenlo.
Si agregas una estructura complementaria para rankings, hazlo solo si tiene sentido y no complica innecesariamente.

### 4. Resumen Markdown ampliado
Debe incorporar el desglose de ganadores por métrica y por horizonte.

## Reglas metodológicas

### A. No corras modelos nuevos
No quiero nuevas corridas de E1, E2, E3 o siguientes familias.

### B. No inventes valores
Todo debe salir de artefactos reales ya consolidados.

### C. No cambies arbitrariamente el criterio de evaluación
Respeta el sentido de cada métrica.

### D. No escondas faltantes
Si un run carece de cierta métrica, debe quedar claro.

### E. No dejes la mejora solo en la narrativa
La mejora principal debe verse en los archivos de salida, especialmente en el Excel.

## Criterios de aceptación

Consideraré la tarea bien resuelta solo si:

1. la tabla maestra base sigue existiendo y no pierde información;
2. el Excel final permite ver claramente, por cada horizonte y cada métrica, cuál fue la mejor corrida;
3. también permite ver más que solo el top 1;
4. `direction_accuracy` y `deteccion_caidas` quedan tratadas como métricas de primera clase, no secundarias;
5. el sentido de optimización de cada métrica está bien implementado;
6. runs parciales o con métricas faltantes se manejan correctamente;
7. el resumen Markdown refleja el nuevo desglose;
8. no se corrieron modelos nuevos.

## Entregables que quiero en la respuesta final del agente

Quiero que el agente me responda con esta estructura:

1. **Diagnóstico de por qué la tabla actual era incompleta**
2. **Cambios implementados**
3. **Archivos modificados**
4. **Nuevas hojas / nuevas vistas agregadas**
5. **Validación realizada**
6. **Ganadores por métrica y por horizonte detectados**
7. **Limitaciones o casos especiales**
8. **Siguiente mejora recomendada**

## Criterio conceptual de esta ampliación

La tabla maestra ya no debe ser solo un inventario de runs ni solo un ranking global.

Debe volverse una herramienta analítica que permita responder directamente:

- quién gana en cada métrica,
- en qué horizonte,
- con qué familia,
- y si la superioridad depende del tipo de criterio evaluado.

Eso es indispensable para decidir después si conviene:

- un campeón único global,
- especialistas por horizonte,
- o una futura arquitectura compuesta del Radar.
