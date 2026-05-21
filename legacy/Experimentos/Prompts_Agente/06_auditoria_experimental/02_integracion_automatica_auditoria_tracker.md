Prompt para el agente: integración automática de auditoría al tracker y cierre reproducible de runs

## Contexto y continuidad

Estamos trabajando sobre el pipeline experimental del proyecto Radar, donde ya existe una infraestructura funcional para registrar corridas en el grid y guardar artefactos por run.

Estado actual confirmado:

- Ya existe `experiment_logger.py` con:
  - `RadarExperimentTracker`
  - `RunContext`
  - `start_run(...)`
  - `finalize(...)`
  - escritura de artefactos y métricas al workbook maestro
- Ya existe `pipeline_common.py` con el flujo común de experimentos tabulares y con cierre vía `run.finalize(...)`
- Ya existe `backfill_runs.py` para reparar o retrocargar resultados desde runs previos
- Ya existe `build_experiments_master_table.py` y ya genera correctamente:
  - `tabla_maestra_experimentos_radar.csv`
  - `tabla_maestra_experimentos_radar.xlsx`
  - `inventario_experimentos_radar.json`
  - `resumen_auditoria_experimentos.md`

La auditoría más reciente confirmó que:

- sí hay evidencia de especialización por horizonte;
- `E1_v5_clean` sigue siendo campeón global;
- `E1_v4_clean` domina H1;
- `E2_v3_clean` domina H2 y H4;
- `E1_v2_clean` domina H3;
- ya hay base metodológica para pensar en ensamblado por horizonte;
- pero todavía falta estandarizar artefactos explicativos entre familias;
- y conviene automatizar la regeneración de la auditoría al cierre de cada run.

## Objetivo de esta tarea

Implementar la integración automática de la auditoría maestra al flujo de cierre de experimentos, de modo que **después de cada run completo** se regenere automáticamente la tabla maestra y sus entregables derivados, sin depender de ejecución manual posterior.

La meta no es correr nuevos modelos. La meta es **mejorar la infraestructura de trazabilidad y cierre**, manteniendo compatibilidad con el pipeline actual.

## Alcance exacto

Quiero que hagas una intervención técnica limpia, mínima pero robusta, para que el cierre normal de un run deje actualizado también el inventario/auditoría global de experimentos.

Eso implica:

1. localizar el punto correcto de integración en el flujo actual;
2. conectar ahí la ejecución de `build_experiments_master_table.py` o, preferentemente, su lógica reutilizable;
3. evitar romper compatibilidad con scripts ya existentes;
4. manejar fallos de forma segura;
5. dejar evidencia clara en código y, si aplica, en comentarios o logs.

## Instrucciones de trabajo

### 1. Audita primero el flujo real antes de modificar

Antes de tocar código, identifica con precisión:

- dónde se llama hoy `run.finalize(...)`;
- si el mejor punto de integración es:
  - dentro de `RunContext.finalize(...)`,
  - dentro de `RadarExperimentTracker.log_run(...)`,
  - o en otro punto más adecuado;
- si `build_experiments_master_table.py` está implementado como script monolítico o si ya puede refactorizarse parcialmente para ser invocado desde Python sin shelling-out.

No hagas un parche ciego. Primero entiende la arquitectura real y decide el punto de integración más limpio.

### 2. Prefiere reutilización programática sobre subprocess si es razonable

Quiero que priorices esta jerarquía:

**Opción preferida**
- refactorizar `build_experiments_master_table.py` para exponer una función reusable, algo del tipo:
  - `build_experiments_master_table(...)`
  - o `regenerate_master_audit(...)`
- y llamarla directamente desde el tracker

**Opción aceptable**
- si el script está demasiado acoplado como CLI y refactorizarlo implicaría demasiado riesgo, entonces usa una invocación controlada desde Python
- pero solo si justificas que era la opción más segura y menos invasiva

No hagas subprocess por comodidad si una refactorización pequeña y limpia lo vuelve invocable como librería.

### 3. Mantén compatibilidad hacia atrás

El cambio no debe romper:

- corridas existentes;
- scripts de familia ya escritos;
- `backfill_runs.py`;
- el uso actual de `RadarExperimentTracker`;
- el cierre normal de runs aunque la auditoría falle.

Regla clave:

**si la regeneración de la auditoría falla, el run principal debe seguir quedando registrado como exitoso** y el fallo de auditoría debe reportarse de forma trazable, no matar toda la corrida.

Es decir:
- el registro del run es crítico;
- la auditoría automática es importante, pero secundaria.

### 4. Diseña manejo de errores explícito

Implementa manejo de errores claro para la nueva automatización.

Quiero distinguir al menos estos escenarios:

- el run se registró bien y la auditoría también;
- el run se registró bien pero la auditoría falló;
- el run quedó parcial/abortado antes del cierre y por tanto no corresponde regenerar auditoría;
- el script o función de auditoría no está disponible o lanza excepción.

No ocultes errores silenciosamente.

Idealmente:
- captura excepción;
- deja mensaje claro en consola/log;
- no corrompe workbook ni artefactos;
- no impide que el `finalize` principal termine.

### 5. No ejecutes modelos nuevos

No corras ningún experimento de modelado.

Solo puedes, si hace falta:
- ejecutar pruebas de infraestructura;
- correr el script de auditoría;
- simular un cierre o validar contra runs existentes;
- verificar que los entregables se regeneran.

Pero no lances nuevas corridas de E1/E2/E3/E4.

### 6. Conserva enfoque de trazabilidad

Este cambio debe reforzar la lógica de reproducibilidad del proyecto.

Si tiene sentido, deja explícito en el código o comentarios:

- que la tabla maestra se regenera al cierre de runs completos;
- qué artefactos produce;
- qué pasa si falla la regeneración;
- qué se considera “run completo” para disparar el update.

### 7. Evalúa si conviene agregar bandera de control

Analiza si conviene introducir una bandera configurable, por ejemplo algo tipo:

- `auto_refresh_master_table=True` en el tracker;
- o un parámetro opcional en `finalize(...)`;
- o una constante/config de proyecto.

No la agregues por reflejo. Evalúa si aporta flexibilidad real.

Mi preferencia:
- que el comportamiento por defecto sea útil para producción;
- pero que exista una forma limpia de desactivarlo si se necesita debugging o mantenimiento.

### 8. Considera coherencia con estados de corrida

La auditoría reciente dejó claro que necesitamos distinguir mejor entre estados como:

- completo
- parcial
- abortado
- cancelado_metodologicamente

Aunque esta tarea no necesariamente debe rediseñar todo el sistema de estados, sí quiero que revises si la integración automática:

- debe correr solo para `estado="corrido"`,
- o también para otros estados cerrados,
- o si hace falta dejar preparado el terreno para una taxonomía mejor más adelante.

No expandas alcance innecesariamente, pero tampoco ignores este punto.

## Entregables esperados

Quiero que entregues:

### A. Cambios de código
Los archivos realmente modificados, con cambios funcionales y limpios.

### B. Explicación técnica breve pero precisa
Explica:

- qué punto del flujo elegiste para integrar la auditoría;
- por qué ese punto fue el correcto;
- si optaste por llamada programática o subprocess y por qué;
- cómo manejaste errores;
- cómo garantizaste compatibilidad hacia atrás.

### C. Validación
Debes validar el cambio con evidencia concreta. Por ejemplo:

- que al cerrar un run o simular el flujo se regeneran:
  - CSV
  - XLSX
  - JSON
  - resumen Markdown
- o, si no puedes simular un run limpio completo sin tocar demasiado, al menos demostrar que la función integrada se ejecuta correctamente sobre el inventario ya existente.

### D. Resumen operativo final
Un cierre breve con:
- qué quedó listo;
- qué limitaciones quedan;
- qué recomendarías después como siguiente paso lógico.

## Criterios de aceptación

Consideraré bien resuelta la tarea solo si se cumple todo esto:

1. el run principal sigue cerrando correctamente;
2. la auditoría maestra se regenera automáticamente tras el cierre de runs completos;
3. el fallo de auditoría no rompe el cierre del run;
4. el cambio no depende de intervención manual posterior;
5. el código queda entendible, mantenible y coherente con la arquitectura existente;
6. no se corrieron modelos nuevos;
7. la validación es concreta, no solo declarativa.

## Restricciones

- No rehagas todo el tracker si no es necesario.
- No metas refactors cosméticos amplios.
- No cambies nombres ni contratos públicos sin necesidad fuerte.
- No inventes nuevos flujos si el actual ya soporta bien la integración.
- No dejes la solución en pseudocódigo: debe quedar implementada.
- No te limites a decir qué harías: haz el cambio.

## Criterio de diseño preferido

Quiero una solución con esta prioridad:

1. robustez
2. continuidad con el pipeline actual
3. claridad arquitectónica
4. mínima invasión
5. extensibilidad futura

## Siguiente paso esperado después de esta tarea

Esta tarea no cierra todo el frente metodológico. Solo deja lista la infraestructura.

Después de esto, el siguiente paso lógico será estandarizar artefactos explicativos por horizonte entre familias, especialmente:

- coeficientes comparables para lineales,
- importancias para árboles,
- y resúmenes homogéneos por horizonte.

No implementes eso todavía salvo que sea estrictamente necesario para no romper nada. Solo deja el sistema listo para que ese paso futuro sea más fácil.

## Forma de respuesta que quiero

Respóndeme con esta estructura:

1. **Diagnóstico del punto de integración**
2. **Cambios implementados**
3. **Archivos modificados**
4. **Validación realizada**
5. **Riesgos o limitaciones**
6. **Siguiente paso recomendado**

Si durante la revisión detectas un problema arquitectónico serio que haga inconveniente integrar la auditoría justo ahora, no te detengas en abstracto: propón y ejecuta la alternativa mínima viable más sólida.
