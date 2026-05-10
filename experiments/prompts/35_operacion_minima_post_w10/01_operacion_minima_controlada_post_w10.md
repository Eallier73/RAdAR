# Prompt para el agente — Puesta en operación mínima controlada del sistema Radar con datos del mundo real

## Rol

Actúa como arquitecto técnico principal y responsable de endurecimiento operativo del proyecto RAdAR.

Tu tarea no es seguir experimentando ni rediseñando el sistema.

Tu tarea es **poner en operación mínima controlada** el sistema canónico ya congelado, de forma profesional, trazable y compatible con la historia metodológica del proyecto.

## Contexto obligatorio que debes respetar

El proyecto ya pasó por una fase extensa de:

* extracción,
* limpieza,
* NLP,
* construcción del dataset maestro,
* modelado,
* comparación experimental,
* congelamiento de benchmark canónico.

Esto significa que:

* **el modelo canónico ya está definido y congelado**,
* **no se va a cambiar**,
* **no se va a reentrenar como parte de esta tarea**,
* **no se van a promover nuevas familias ni nuevas versiones**,
* **no se va a reabrir la discusión metodológica del modelado**.

Además:

* la etapa de extracción y limpieza ya fue probada operativamente,
* la etapa de NLP ya quedó alineada con el proceso que se aplicó al material de entrenamiento,
* el material histórico que soporta el tramo validado llega hasta la semana que inicia el **2026-03-02**, es decir, **2026-W10**,
* a partir de ahí ya existen datos del mundo real disponibles en texto hasta la fecha actual,
* pero todavía **no está montada la operación formal post-W10**,
* tampoco está resuelta todavía la capa final de tablero conectado, análisis automatizado, documento y presentación.

## Decisión estratégica ya tomada

Debes trabajar bajo esta regla, sin reinterpretarla:

### Regla 1

**Sí se puede y sí se debe empezar a operar con datos del mundo real antes de tener lista la capa de tablero, análisis y reportes.**

### Regla 2

Lo que sí debe quedar resuelto antes de operar es la **cadena canónica mínima hasta inferencia y registro**.

### Regla 3

La capa de:

* tablero,
* interpretación,
* documento,
* presentación

**no es prerequisito para arrancar operación mínima**, pero sí debe quedar reconocida como la siguiente etapa natural del sistema.

## Objetivo principal de esta tarea

Dejar lista la **operación mínima controlada** del sistema Radar desde el tramo post-2026-W10, sin tocar el modelo congelado y sin rehacer metodología.

Eso implica dejar cerrada y operable la cadena:

**recopilación congelada -> preprocesamiento congelado -> NLP congelado -> dataset maestro congelado en su definición -> inferencia con modelo canónico congelado -> registro formal de emisiones**

## Objetivo secundario

Dejar preparada la transición hacia la siguiente capa del sistema:

**tablero conectado -> interpretación asistida -> documento -> presentación**

pero sin exigir que esa parte quede ya completamente construida para arrancar operación real.

---

# Principio rector

## No confundir “sistema completo ideal” con “mínimo operativo real”

No quiero que frenes la entrada a mundo real porque todavía no existe:

* tablero final,
* análisis automatizado,
* prompt de interpretación,
* generación de documento,
* generación de presentación.

Eso vendrá después.

Lo que sí quiero es que el sistema ya pueda:

1. consumir semanas nuevas reales,
2. transformarlas con la tubería congelada,
3. correr el modelo canónico congelado,
4. generar predicciones,
5. guardar esas predicciones con trazabilidad suficiente.

---

# Alcance exacto de la tarea

## Parte A — Formalizar el congelamiento operativo integral

No basta con el modelo congelado.
Debes reconocer y documentar que queda congelada la línea canónica completa de producción:

### 1. Recopilación de material

Debe quedar congelado:

* universo de fuentes
* reglas por fuente
* ventanas temporales semanales
* criterio de corte semanal
* reglas de muestreo si aplican
* cobertura esperada
* manejo de errores parciales
* estructura de almacenamiento raw

### 2. Preprocesamiento

Debe quedar congelado:

* script canónico
* reglas de limpieza
* reglas de normalización
* segmentación
* deduplicación
* remoción o conservación de caracteres
* formato de salida texto

### 3. NLP

Debe quedar congelado:

* sentimiento
* diccionarios temáticos vigentes
* scoring temático
* exclusiones metodológicas
* normalización de temas
* unión hacia ML

### 4. Dataset maestro

Debe quedar congelado:

* definición del dataset
* columnas
* target
* features
* lags
* naming
* archivo final que consume el modelo

### 5. Modelo canónico

Debe quedar congelado:

* artefacto/modelo oficial
* versión
* parámetros operativos
* horizontes de salida
* lógica de inferencia

### 6. Registro de resultados

Debe quedar definido:

* qué se guarda por corrida
* dónde se guarda
* cómo se identifica cada emisión
* cómo se distinguirá entre emisión pendiente de evaluar y emisión evaluada

## Importante

No te pido aquí inventar una política conceptual abstracta.
Te pido aterrizar esto al repo y a la operación real del proyecto.

---

## Parte B — Dejar operable la salida mínima hasta inferencia

La operación mínima debe quedar capaz de hacer esto:

1. tomar nuevas semanas reales ya disponibles en texto,
2. recorrer la tubería congelada,
3. actualizar el dataset maestro,
4. correr inferencia con el modelo canónico congelado,
5. guardar resultados,
6. dejar evidencia trazable de la emisión.

## Esto sí es obligatorio antes de arrancar

Si esto no queda listo, no se puede decir que Radar ya entró en operación real.

---

## Parte C — Resolver el tramo post-W10

Debes trabajar explícitamente con la frontera:

* histórico validado hasta **2026-W10**
* operación real desde **2026-W11** en adelante

Tu tarea debe dejar claro cómo se procederá con el tramo que ya existe en texto desde **2026-W11 hasta la fecha actual**.

## Regla operativa

Debes proponer e implementar la base para un **backfill operativo controlado** desde `2026-W11` hasta la semana más reciente disponible.

### Ojo:

Esto **no** es para reentrenar.
Esto **no** es para cambiar modelo.
Esto **no** es para rediseñar la metodología.

Es para:

* correr la tubería canónica congelada sobre semanas reales nuevas,
* generar las predicciones que correspondan bajo el régimen ya congelado,
* dejar el historial operativo inicial.

---

## Parte D — No construir todavía la capa final, pero sí dejarla correctamente ubicada

Debes dejar explícito que el sistema completo todavía tiene una etapa posterior no implementada o incompleta:

### Etapa posterior pendiente

* tablero conectado o corregido
* actualización del tablero con resultados de inferencia
* interpretación del tablero mediante prompt preestablecido
* generación de documento
* generación de presentación

## Pero regla clave:

No debes hacer depender el arranque operativo mínimo de que esa capa ya exista.

Sí debes:

* identificarla,
* documentarla,
* ubicarla como siguiente etapa,
* señalar sus dependencias,
* dejar claro qué falta para cerrarla.

---

# Lo que debes hacer exactamente

## Fase 1 — Auditoría técnica del estado actual

Debes revisar con seriedad el estado actual del repo y del flujo operativo para responder estas preguntas:

1. ¿Qué parte de la cadena canónica ya está realmente operable?
2. ¿Qué parte está operable pero no documentada?
3. ¿Qué parte está congelada en la práctica pero no formalizada?
4. ¿Qué falta para que exista operación mínima real?
5. ¿Qué artefacto exacto representa hoy el modelo canónico congelado?
6. ¿Qué script o secuencia exacta lleva del texto al dataset maestro final?
7. ¿Qué script o mecanismo exacto ejecuta hoy la inferencia del modelo canónico?
8. ¿Cómo se están guardando hoy las salidas, si es que ya se guardan?
9. ¿Qué falta para poder correr el tramo 2026-W11 -> hoy de manera controlada?

## Entregable de esta fase

Un diagnóstico serio, no complaciente, de:

* listo
* parcialmente listo
* faltante
* riesgoso
* ambiguo

---

## Fase 2 — Diseñar la operación mínima canónica post-W10

Debes dejar definida la arquitectura operativa mínima, con nombres de etapas, entradas, salidas y responsables técnicos.

Como mínimo debe incluir:

### Etapa 1

Ingreso de semana nueva o lote de semanas nuevas

### Etapa 2

Ejecución de recopilación congelada o consumo del material ya recopilado

### Etapa 3

Ejecución de preprocesamiento congelado

### Etapa 4

Ejecución de NLP congelado

### Etapa 5

Reconstrucción/actualización del dataset maestro

### Etapa 6

Inferencia con modelo canónico congelado

### Etapa 7

Registro formal de resultados emitidos

## Debes dejar claro:

* si esto se corre por script secuencial,
* si requiere un runner nuevo,
* si requiere wrappers,
* o si basta con un runner/orquestador simple de operación.

## Restricción

No inventes una sobreingeniería absurda.
Pero tampoco dejes una pseudo-operación manual sin trazabilidad.

---

## Fase 3 — Implementar lo mínimo necesario

Debes hacer el cambio mínimo necesario para que la operación mínima exista de verdad.

Eso puede incluir, si hace falta:

* un runner nuevo de operación
* wrappers de etapa
* helpers de registro
* carpeta nueva de operación
* README operativo
* bitácora de cambios
* estructura para emisiones

## Pero debes respetar estas reglas:

* no romper la arquitectura existente
* no reabrir modelado
* no cambiar lógica congelada
* no rehacer extracción, preprocesamiento o NLP si ya funcionan
* no duplicar scripts si basta con envolverlos
* no inventar rutas si ya existe convención real
* no mover archivos históricamente sensibles salvo necesidad fuerte

---

## Fase 4 — Dejar registro formal de emisiones

Esto es obligatorio.

Necesitas definir e implementar un esquema claro para guardar cada emisión operativa.

Cada emisión debe registrar, como mínimo:

* fecha de corrida
* timestamp
* semana o lote base procesado
* tramo cubierto
* versión del pipeline congelado
* versión o identificador del modelo canónico
* dataset maestro usado o snapshot/referencia
* predicciones H1, H2, H3, H4
* estado:

  * emitido
  * pendiente de evaluación
  * parcialmente evaluable
  * evaluado
* comentarios operativos
* rutas a artefactos relevantes

## Si todavía no existe una estructura adecuada

Debes crearla.

Por ejemplo, podrías dejar algo equivalente a:

* carpeta `Operacion/`
* subcarpeta `emisiones/`
* subcarpeta `logs/`
* subcarpeta `snapshots/`
* archivo índice o bitácora maestro

No tomes esto como obligación literal.
Debes adaptarlo a la estructura real del repo.

---

## Fase 5 — Preparar backfill operativo post-W10

Debes dejar lista la base para correr el tramo:

**2026-W11 -> semana actual**

con el sistema congelado.

## No necesitas necesariamente ejecutar todas las semanas si esta tarea se centra en dejar la estructura lista,

pero sí debes dejar:

* la lógica exacta para hacerlo,
* el comando o punto de entrada,
* el criterio de partición por semanas,
* qué artefactos se generarán,
* cómo se evitará confusión entre histórico validado y operación real.

## Debe quedar clarísimo:

* histórico validado hasta W10
* operación post-W10 a partir de W11
* sin cambio de benchmark
* sin cambio de metodología

---

## Fase 6 — Documentar la etapa posterior pendiente

Debes documentar claramente que todavía falta una capa posterior del sistema:

### Capa pendiente de explotación analítica

1. conexión/modificación del tablero
2. refresco del tablero con datos vigentes
3. lectura del tablero mediante prompt canónico para agente
4. generación de documento
5. generación de presentación

## Debes dejar claro:

* que esta capa no bloquea el arranque operativo mínimo,
* pero sí es la siguiente fase natural del proyecto,
* y que el tablero actual existe pero requiere trabajo,
* y que aún no hay análisis ni generación automática de reportes.

---

# Archivos y artefactos que quiero como entregables

## 1. Documento maestro de operación mínima

Debes crear un documento nuevo, con nombre claro y profesional, por ejemplo:

* `README_operacion_minima_post_w10.md`
  o
* `operacion_controlada_radar_post_w10.md`

Debe incluir:

* contexto
* frontera W10/W11
* qué está congelado
* qué sí cambia cada semana
* flujo completo hasta inferencia
* esquema de emisiones
* esquema de backfill operativo
* etapa posterior pendiente de tablero/reportes

## 2. Bitácora de cambios

Obligatoria.

Debes crear o actualizar un archivo como:

* `bitacora_cambios_operacion_post_w10.md`
  o equivalente

Y registrar:

* archivo creado o modificado
* tipo de cambio
* motivo
* impacto
* compatibilidad
* pendientes

## 3. Runner o punto de entrada operativo

Debe quedar explícito qué se ejecuta para:

* procesar semanas nuevas
* correr inferencia
* registrar salida

## 4. Registro o estructura de emisiones

Debe quedar implementada o al menos operativamente lista.

## 5. Validación final

Debes cerrar con verificación explícita de:

* que el sistema puede operar sin tablero final,
* que la cadena hasta inferencia está cerrada,
* que no se tocó el modelo congelado,
* que el tramo post-W10 puede empezar a correrse.

---

# Restricciones duras

## No hagas esto

* no cambies el modelo
* no cambies benchmark
* no metas nueva experimentación
* no rehagas features
* no cambies target
* no rediseñes NLP
* no cambies recopilación o preprocesamiento salvo para formalizar o encapsular la versión ya congelada
* no supongas que tablero/reportes son prerequisito de arranque
* no intentes resolver toda la capa final de comunicación en esta tarea
* no mezcles operación con investigación

## Sí debes hacer esto

* formalizar congelamiento integral
* cerrar operación mínima
* dejar trazabilidad
* preparar backfill post-W10
* documentar capa pendiente de tablero/reportes
* registrar todos los cambios

---

# Criterios de éxito

La tarea estará bien hecha solo si al final ocurre esto:

1. queda claro qué parte del sistema ya puede entrar a mundo real,
2. queda formalizado qué está congelado de extremo a extremo,
3. existe una cadena operativa mínima real hasta inferencia,
4. existe registro formal de emisiones,
5. puede iniciarse el tramo post-W10 sin esperar a tablero/reportes,
6. la capa de tablero e interpretación queda correctamente reconocida como siguiente fase, no como bloqueo actual.

---

# Orden de trabajo obligatorio

## Etapa A

Auditar el estado real del repo y del flujo congelado.

## Etapa B

Formalizar qué queda congelado y qué no.

## Etapa C

Diseñar la operación mínima post-W10.

## Etapa D

Implementar lo mínimo necesario para que exista punto de entrada operativo + registro.

## Etapa E

Documentar el esquema de emisiones y backfill.

## Etapa F

Documentar la capa posterior pendiente: tablero, interpretación, documento, presentación.

## Etapa G

Entregar:

* archivos creados o modificados
* README operativo
* bitácora de cambios
* punto de entrada
* estructura de emisiones
* validación final
* pendientes y riesgos

---

# Instrucción final

Sé estricto.
No maquilles huecos.
No uses lenguaje ambiguo.
No vendas como “operativo” algo que todavía sea manual, frágil o sin trazabilidad.
Pero tampoco bloquees el arranque por ausencia de tablero o reporting final.

Tu misión es dejar a Radar en **modo de operación mínima controlada sobre datos del mundo real**, no en modo de “sistema ideal imaginario”.
