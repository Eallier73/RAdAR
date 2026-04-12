# Auditoria, Correccion y Consolidacion Final de Extractores W10-W14

Quiero que audites, corrijas y consolides la carpeta
`Scripts/Extracting_Procesing/automation/extractors` del proyecto Radar bajo un
estándar serio de producción controlada, trazabilidad fuerte, legibilidad
documental, validación operativa útil e integración futura al resto del
sistema.

No quiero una revisión superficial.
No quiero una reestructuración cosmética.
Quiero una fase de corrección fina y validación operativa real sobre una
arquitectura que ya va bien encaminada, pero que todavía no debe darse por
cerrada.

## Diagnóstico General de Partida

La carpeta ya muestra una reestructuración seria y claramente mejor que el
estado anterior. Ya no está en lógica de scripts sueltos, sino en una
arquitectura con:

- wrappers canónicos
- cores reutilizables
- archivos canónicos por fuente
- READMEs específicos
- contratos de salida más claros
- mejor alineación con la lógica general de Radar

Mi diagnóstico de partida es este:

- estado general: bien encaminado, con arquitectura ya profesionalizada
- estado de cierre: todavía no lo considero cerrado
- etapa correcta: precongelamiento operativo

La razón es simple: la capa de extractores ya refleja casi todas las decisiones
estratégicas que hemos tomado, pero todavía hay ajustes de consistencia,
legibilidad documental y validación operativa que conviene corregir antes de
entregar esto como base definitiva del sistema.

Por lo tanto, la instrucción general no es rehacer toda la carpeta.
La instrucción general es:

- conservar la arquitectura actual
- corregir problemas transversales de legibilidad y consistencia
- validar corridas mínimas por fuente con valor operativo real
- cerrar huecos documentales
- dejar congelado el contrato de salida de cada extractor

## Regla Central de Validación

La validación de corridas no debe hacerse con ventanas artificiales ni con
pruebas sin valor operativo.

Quiero que la validación se convierta en backfill útil.

No quiero corridas a lo wey.
No quiero semanas arbitrarias.
No quiero pruebas desechables.

Quiero que toda validación funcional sirva para recuperar material real faltante
del sistema.

Para evitar ambigüedad con cortes previos y dejar el calendario perfectamente
claro, a partir de este momento el tramo de validación/backfill debe comenzar en
la semana ISO 2026-W10 y terminar en la semana ISO 2026-W14.

Debes trabajar exactamente estas semanas:

- 2026-W10: 2 de marzo al 8 de marzo de 2026
- 2026-W11: 9 de marzo al 15 de marzo de 2026
- 2026-W12: 16 de marzo al 22 de marzo de 2026
- 2026-W13: 23 de marzo al 29 de marzo de 2026
- 2026-W14: 30 de marzo al 5 de abril de 2026

No quiero que tomes como punto de partida semanas híbridas o cortes parciales
anteriores.
Quiero que el tramo canónico de validación quede limpio, completo y fácil de
seguir: W10, W11, W12, W13 y W14.

Toda corrida de validación debe tener doble función:

1. validar técnicamente el extractor
2. producir material real que no tenemos todavía

## Lógica de Trabajo General

La lógica de trabajo debe ser esta:

1. Auditar el estado actual de la carpeta
   `Scripts/Extracting_Procesing/automation/extractors` frente a los problemas
   analizados y las decisiones tomadas.
2. Revisar cada extractor, cada core, cada wrapper, cada README y cada archivo
   canónico de queries/páginas.
3. Detectar inconsistencias, riesgos, piezas incompletas, problemas de
   trazabilidad, problemas de legibilidad documental y cualquier desviación
   respecto al estándar definido.
4. Corregir primero los problemas estructurales y documentales que puedan
   afectar corridas reales.
5. Después ejecutar validación funcional solo como backfill real para las
   semanas 2026-W10 a 2026-W14.
6. Todo material generado en esas corridas debe quedar como output operativo
   real, no como prueba desechable.
7. Registrar por fuente y por semana:
   - qué semana se corrió
   - si fue backfill nuevo
   - qué extractor se usó
   - qué artefactos se generaron
   - qué problemas aparecieron
   - qué quedó pendiente si alguna corrida no pudo cerrarse

## Matriz de Auditoría por Componente

### 1) Facebook Institucional

Estado: sólido.
Alineación con decisiones: alta.

#### Qué sí está bien

La base histórica quedó bien explicitada y la implementación profesional ya vive
en:

- `facebook_institutional_extractor.py`
- `facebook_institutional_extractor_core.py`

El alcance quedó correctamente restringido a Facebook institucional de Tampico,
con las dos páginas canónicas:

- `MonicaVillarreal`
- `GobiernoTampico`

La lógica de sampling durante extracción quedó expresada con:

- cap semanal de 100 comentarios por página
- semilla 42
- selección de posts previa a comentarios
- corte al alcanzar cap

También quedó explícito que se absorbió del otro script solo lógica útil de
enriquecimiento del post padre y que se descartó:

- el scraping adicional caro
- la dependencia de CSV intermedio

#### Problemas o riesgos detectados

- El README está bien en contenido, pero se ve mal renderizado: nombres de
  outputs y estructuras de carpetas aparecen con placeholders deformados como
  `facebook_institutional_raw_.csv` y `//runs/_/`. Eso no rompe la lógica, pero
  sí degrada la documentación operativa.
- El archivo `facebook_institutional_pages_canonical.csv` parece estar
  serializado en una sola línea, lo cual es funcionalmente tolerable pero poco
  mantenible y poco auditable para edición humana.

#### Acción obligatoria para agente

- Pulir README y ejemplos para que rendericen correctamente.
- Reescribir `facebook_institutional_pages_canonical.csv` con saltos de línea
  reales.
- Validar con una corrida corta real que el cap semanal por página se esté
  aproximando bien sin sobrecoste.

#### Validación operativa que quiero para Facebook

La validación real debe correrse sobre semanas ISO W10 a W14.
No quiero pruebas fuera de ese tramo.

Además, recuerda que este extractor debe seguir respetando la lógica que ya
definimos:

- Facebook aquí es solo institucional
- no es para medios
- el sampling debe ocurrir durante la extracción, no después
- el contrato histórico de comparabilidad debe preservarse, aunque Facepager
  haya dejado de funcionar

No quiero que cambies esa arquitectura.
Quiero que la consolides y la pruebes con backfill real útil.

### 2) Medios

Estado: sólido.
Alineación con decisiones: alta.

#### Qué sí está bien

Quedó clara la transición desde `04_medios_extractor.py` hacia:

- wrapper canónico
- core reutilizable
- archivo de queries canónicas

La responsabilidad quedó bien definida:

- RSS
- resolución de URLs
- extracción de artículo
- persistencia
- trazabilidad

sin mezclar NLP/modelado.

También se documentó bien:

- política de queries
- política semanal
- caché en tres capas
- uso controlado de Playwright como fallback

#### Problemas o riesgos detectados

- No pude verificar con confianza el contenido legible de
  `media_queries_canonical.csv`; existe en la carpeta, pero conviene auditarlo
  manualmente porque es una pieza crítica del contrato operativo.
- Aquí el mayor riesgo ya no es arquitectónico, sino operativo: si Playwright
  se activa demasiado, el extractor podría encarecerse o volverse más frágil. El
  README lo contempla, pero eso hay que medirlo con corridas reales.

#### Acción obligatoria para agente

- Revisar `media_queries_canonical.csv` línea por línea.
- Agregar, si no existe ya, una nota o contador más visible del porcentaje de
  artículos que terminan usando Playwright.
- Correr una prueba de humo con y sin `--use-playwright`.

#### Validación operativa que quiero para medios

También debe aprovecharse el tramo W10 a W14.
No quiero una prueba abstracta; quiero que, en la medida de lo posible, esa
validación produzca material real faltante de medios dentro de esas semanas.

### 3) Twitter

Estado: bien encaminado.
Alineación con decisiones: media-alta.

#### Qué sí está bien

Se formalizó la transición desde `02_twitter_extractor_Tampico.py` a wrapper
canónico + core.

En el core ya no aparecen residuos de CDMX en defaults visibles: el
`DEFAULT_OUTPUT_DIR` apunta a `Datos_RAdAR/Twitter`, y el archivo de sesión está
externalizado en `Scripts/state/x_state.json`.

Las queries canónicas visibles coinciden con lo acordado para Tampico y ya no
incluyen:

- `presidenta municipal`

El contrato de salida y los artefactos están bien definidos:

- CSV principal
- raw JSONL
- summary
- metadata
- parámetros
- manifest
- errores

#### Problemas o riesgos detectados

- Igual que en YouTube y Facebook, el archivo `twitter_queries_canonical.txt`
  está serializado como una sola línea, lo que complica revisión humana y
  edición controlada.
- El principal riesgo aquí sigue siendo de robustez frente a la UI de X, no de
  arquitectura. Eso no se ve mal en el repo, pero sí exige validación
  operativa.
  El core depende claramente de Playwright y de una sesión persistida.

#### Acción obligatoria para agente

- Reescribir `twitter_queries_canonical.txt` en formato una-query-por-línea.
- Confirmar con corrida real que la sesión persistida y la expansión de texto
  funcionan de manera estable.
- Añadir, si aún no existe, una prueba mínima de validación de selectores o una
  alerta clara cuando X cambie de estructura.

#### Validación operativa que quiero para Twitter

La validación debe correrse en W10 a W14 y servir como backfill real.
No quiero un smoke test sin valor.
Quiero que si Twitter funciona, el output de esas semanas quede ya incorporado
como material operativo real del sistema.

### 4) YouTube

Estado: bien encaminado.
Alineación con decisiones: media-alta.

#### Qué sí está bien

Se formalizó la transición desde `01_youtube_extractor_Tampico.py` a wrapper
canónico + core.

El objetivo quedó claro:

- extractor puro
- reusable
- parametrizable
- trazable
- orquestable

En el README ya quedó documentado:

- uso de API key por entorno
- queries externas/canónicas
- separación con preprocessing

#### Problemas o riesgos detectados

- `youtube_queries_canonical.txt` también aparece en una sola línea. Funciona,
  pero es pobre para mantenimiento profesional.
- No pude confirmar con el mismo detalle que en Facebook la estructura fina del
  contrato de salida, aunque el wrapper/core y el README sí apuntan en la
  dirección correcta.

#### Acción obligatoria para agente

- Reescribir `youtube_queries_canonical.txt` en formato legible y auditable.
- Validar una corrida corta para confirmar que el flujo con `YOUTUBE_API_KEY` y
  comentarios top-level está produciendo exactamente los artefactos
  documentados.
- Revisar README para asegurar que ejemplos de outputs y estructura de carpetas
  no tengan placeholders truncados.

#### Validación operativa que quiero para YouTube

Igual que en el resto: la validación debe aprovechar el tramo W10 a W14 y
producir material real faltante.

## Problemas Transversales Detectados

### A. Documentación con render pobre

Varios README están informativamente bien, pero presentan tramos con
placeholders o formatos rotos en outputs y rutas. Eso afecta usabilidad
operativa y puede confundir al agente o a cualquiera que intente correrlos
después.

#### Corrección obligatoria

- Normalizar todos los README con bloques Markdown bien renderizados.
- Revisar ejemplos de carpetas y archivos para que incluyan nombres completos
  reales.
- Homogeneizar estilo, tono y formato entre README de fuentes.

### B. Archivos canónicos poco legibles

Los archivos canónicos visibles para Facebook, Twitter y YouTube aparecen en una
sola línea. Eso es un defecto de mantenibilidad más que de lógica, pero sí
conviene corregirlo antes de congelar.

#### Corrección obligatoria

- Reescribir CSV/TXT canónicos con saltos de línea reales.
- Mantener un formato uniforme:
  - CSV: una fila por entidad/query.
  - TXT: una query por línea.

### C. Madurez desigual por fuente

Facebook y medios están más explícitamente aterrizados en README y reglas
metodológicas. Twitter y YouTube ya quedaron bien encaminados, pero requieren
más validación práctica que rediseño.

#### Criterio de trabajo

No quiero que esto se resuelva rehaciendo la arquitectura.
Quiero que se resuelva con:

- corrección fina
- validación útil
- cierre documental
- congelamiento de contrato de salida

## Prioridad de Corrección para el Agente

### Prioridad alta

1. Corregir render y legibilidad de READMEs.
2. Reescribir archivos canónicos en formato legible.
3. Validar Facebook institucional con corrida corta real contra cap semanal y
   costo.
4. Validar Twitter con sesión persistida real.

### Prioridad media

5. Auditar `media_queries_canonical.csv`.
6. Medir cuántos artículos de medios están cayendo en fallback Playwright.
7. Validar YouTube con una corrida corta real y comprobar artefactos.

### Prioridad baja

8. Homogeneizar aún más estilo de documentación y ejemplos CLI entre fuentes.

## Dictamen General que Debes Respetar

La carpeta no está mal.
Al contrario, está bastante avanzada y ya refleja las decisiones correctas.

Lo que necesita ahora no es otra reestructuración total, sino una fase de:

- corrección fina
- validación operativa real
- cierre documental
- congelamiento de contrato por extractor

No quiero que destruyas la arquitectura actual.
Quiero que la consolides.

## Instrucción de Validación Operativa Real

Insisto en esto:

La validación funcional debe hacerse como backfill real sobre:

- 2026-W10: 2 al 8 de marzo
- 2026-W11: 9 al 15 de marzo
- 2026-W12: 16 al 22 de marzo
- 2026-W13: 23 al 29 de marzo
- 2026-W14: 30 de marzo al 5 de abril

Toda corrida que hagas en esta fase debe producir output operativo real útil.

No quiero corridas de prueba sobre semanas aleatorias.
No quiero ventanas de laboratorio.
No quiero simulaciones innecesarias.

Quiero que toda validación sirva simultáneamente para:

- comprobar que el extractor funciona
- recuperar material real faltante
- dejar trazabilidad de lo que quedó cubierto por semana y por fuente

## Entregables

Quiero que me devuelvas, al final del trabajo:

1. lista de archivos revisados
2. lista de archivos corregidos
3. problemas detectados por extractor
4. correcciones aplicadas por extractor
5. problemas transversales corregidos
6. semanas ISO realmente corridas por fuente
7. artefactos reales generados por semana y por fuente
8. incidencias encontradas en cada corrida
9. pendientes reales que no hayan podido cerrarse
10. nota final sobre si la carpeta ya puede considerarse congelable como capa de
    extractores o si todavía requiere una ronda adicional

## Restricciones

- No rehagas la arquitectura desde cero.
- No abras nuevas líneas de diseño innecesarias.
- No conviertas esta fase en refactorización ornamental.
- No ejecutes validaciones sin valor operativo real.
- No rompas la separación entre extracción y preprocessing.
- No cambies la lógica metodológica ya acordada por fuente.
- No dejes sin documentar ninguna corrección relevante.
- No cierres la carpeta como lista si todavía detectas huecos importantes.

## Forma de Trabajar

Quiero que trabajes en este orden:

1. auditar carpeta completa
2. corregir problemas documentales y de legibilidad
3. corregir problemas estructurales menores detectados
4. validar por fuente usando backfill real W10-W14
5. registrar todo lo generado
6. devolver cierre técnico de auditoría/corrección

No quiero improvisación.
Quiero una consolidación seria, rigurosa y profesional de esta capa de
extractores.
