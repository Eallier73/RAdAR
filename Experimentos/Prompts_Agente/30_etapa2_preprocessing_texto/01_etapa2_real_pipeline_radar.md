# Etapa 2 Real del Pipeline Radar

Quiero que implementes la etapa 2 real del pipeline Radar y no una versión inventada o simplificada.

## Instrucción general

Debes trabajar contra la estructura real actual del proyecto.

No quiero que asumas una arquitectura teórica.
No quiero que inventes carpetas, nombres de archivos, etapas o flujos distintos.
No quiero que reformules el problema.

Tienes que construir la etapa 2 tal como realmente funciona el sistema hoy:

- la etapa 1 ya baja material de 4 fuentes,
- lo guarda como `.csv` dentro de la estructura real del proyecto,
- y la etapa 2 debe recuperar esos `.csv`, convertirlos a `.txt`, limpiarlos con la lógica histórica del corpus y archivarlos por fuente + semana ISO en la ruta de texto correspondiente.

## Flujo real obligatorio

La lógica correcta es esta y debes respetarla exactamente.

### Etapa 1 ya existente

La etapa 1 deja datos en:

`/home/emilio/Documentos/RAdAR/Datos_RAdAR`

Dentro de esa ruta existen 4 carpetas, una por fuente.
Dentro de cada carpeta de fuente hay carpetas por semana.
Dentro de cada carpeta semanal hay:

- artefactos de trazabilidad,
- y un `.csv` canónico con los datos extraídos de esa fuente para esa semana.

### Etapa 2 que debes construir

La etapa 2 debe:

- localizar el `.csv` canónico de cada fuente/semana,
- leerlo correctamente,
- extraer el material textual correcto,
- convertirlo a corpus `.txt`,
- aplicar la limpieza histórica exacta,
- reconstruir el texto en bloques consecutivos de 30 palabras,
- y archivarlo en:

`/home/emilio/Documentos/RAdAR/Datos_RadaR_Texto`

dentro de la carpeta correspondiente a la fuente.

### Ejemplo de destino

Si la fuente es Facebook, el `.txt` debe guardarse en una ruta equivalente a:

`/home/emilio/Documentos/RAdAR/Datos_RadaR_Texto/Facebook_Semana_Texto`

con nombre de archivo por semana ISO como en el sistema actual, por ejemplo:

- `24_40_facebook.txt`
- `24_41_facebook.txt`
- `24_42_facebook.txt`

Debes respetar la convención real del proyecto.
No inventes otro patrón si ya existe uno consolidado.

## Prohibiciones explícitas

No hagas ninguna de estas cosas.

- No partas de `material_comentarios.txt` y `material_institucional.txt` como si esa fuera la estructura real.
- No supongas una carpeta semanal única con `.txt` ya listos.
- No inventes una nueva arquitectura de carpetas si la actual ya resuelve el flujo.
- No mezcles esta etapa con NLP.
- No hagas sentimiento, temas, clasificación, embeddings ni features analíticas.
- No “mejores” la limpieza por criterio personal.
- No cambies la lógica histórica del corpus.
- No alteres silenciosamente nombres de archivos ni convenciones de semana.
- No asumas qué columna textual usar sin revisar los `.csv` reales.
- No elijas un `.csv` arbitrario si en una carpeta hay más de uno: debes resolver la canonicidad y documentarla.

Si encuentras ambigüedad, la resuelves revisando la estructura real y la documentas.
No improvisas.

## Objetivo exacto de esta etapa

Esta etapa no es NLP.

Esta etapa es únicamente:

`CSV canónico por fuente/semana -> TXT limpio canónico por fuente/semana`

Eso es todo.

## Requisito metodológico crítico

Debes conservar la lógica histórica de limpieza del corpus porque esa lógica alimentó modelos previos y no se puede alterar sin romper comparabilidad.

Debes conservar exactamente:

- reemplazo de acentos y caracteres especiales a ASCII,
- minúsculas,
- eliminación de URLs,
- eliminación de puntuación,
- eliminación de dígitos,
- limpieza específica según fuente,
- deduplicación exacta conservando orden,
- concatenación del material limpio,
- y reconstrucción en bloques consecutivos de 30 palabras por línea.

## Regla obligatoria sobre los bloques de 30 palabras

Esto no es opcional.
No es un parámetro decorativo.
Es parte de la lógica histórica canónica.

Secuencia exacta obligatoria:

1. leer texto desde el `.csv`,
2. normalizar según la fuente,
3. eliminar vacíos,
4. deduplicar conservando orden,
5. concatenar todo el material en un flujo continuo,
6. reconstruir ese flujo en líneas de 30 palabras.

No debes reinterpretarlo como:

- 30 palabras por fila del csv,
- 30 palabras por comentario,
- máximo 30 palabras por registro,
- división independiente por fila original.

La lógica correcta es:

`flujo total concatenado del corpus limpio -> bloques consecutivos de 30 palabras`

Default obligatorio:

`--words-per-line=30`

No quiero `None` como default.
No quiero que eso quede ambiguo.

## Tarea técnica obligatoria antes de codificar

Antes de implementar, debes revisar la estructura real y dejar resuelto esto:

### 1. Cómo localizar el `.csv` canónico por fuente/semana

Debes determinar:

- patrón de nombre,
- criterio de selección,
- qué hacer si hay varios `.csv`,
- qué hacer si falta el `.csv`.

### 2. Qué columna o columnas textuales usar por fuente

Debes revisar los `.csv` reales y documentar:

- Facebook: qué columna textual entra al corpus
- Twitter: qué columna textual entra al corpus
- YouTube: qué columna textual entra al corpus
- Medios: qué columna textual entra al corpus

Si una fuente necesita combinar varias columnas, debes hacerlo explícito y justificado.

### 3. Cómo recuperar la semana ISO

Debes resolver correctamente:

- si la semana viene del nombre de la carpeta,
- del nombre del archivo,
- de una columna del `.csv`,
- o de una combinación de esas señales.

Debes documentar cómo armas el nombre final del `.txt`.

## Arquitectura esperada

No quiero un script monolítico.

Quiero una arquitectura mínima, profesional y reusable.

### Archivos esperados

Como mínimo:

- `run_stage2_text_preprocessing.py`
- `stage2_text_common.py`

Y si hace falta separar claramente:

- `text_normalizers.py`
- `csv_text_extraction.py`
- `preprocessing_audit.py`

No fragmentes por gusto.
Pero sí separa responsabilidades reales.

## Responsabilidades del runner principal

El runner principal debe hacer exactamente esto:

- `parse_args()`
- descubrir fuentes disponibles
- descubrir semanas disponibles por fuente
- localizar el `.csv` canónico
- validar selección del `.csv`
- leer el `.csv`
- extraer el texto desde la columna o columnas correctas
- normalizar según la fuente
- eliminar vacíos
- deduplicar conservando orden
- concatenar el corpus
- reconstruir líneas de 30 palabras
- guardar el `.txt` en la carpeta correcta de texto por fuente
- generar auditoría
- generar resumen de corrida
- salir con mensajes claros y trazables

## Requisitos de escritura de salida

No debes tocar destructivamente la extracción original.

El `.csv` de entrada se deja intacto.

### Modo de operación esperado

El comportamiento principal debe ser archivar el `.txt` limpio en la carpeta destino de texto por fuente.

Solo si existe un `.txt` previo y el usuario lo indica, puedes permitir reemplazo controlado.

Modos mínimos:

- `archive`
- `overwrite-text`

No quiero un modo que sobrescriba el `.csv` original.
Eso está prohibido.

## CLI obligatoria

El runner debe aceptar, como mínimo:

- `--datos-radar-dir`
- `--datos-texto-dir`
- `--sources`
- `--weeks`
- `--words-per-line`
- `--output-mode`
- `--run-id`
- `--dry-run`
- `--skip-missing`
- `--save-audit`

Defaults esperados:

- `--words-per-line=30`
- `--output-mode=archive`

## Requisitos de auditoría

Cada corrida debe dejar trazabilidad seria.

Artefactos mínimos obligatorios:

- `metadata_run.json`
- `parametros_run.json`
- `resumen_preprocessing.json`
- `auditoria_preprocessing.json`

Además, por cada fuente/semana procesada, debes registrar al menos:

- fuente
- semana
- carpeta de entrada
- carpeta de salida
- ruta del `.csv` origen
- nombre del `.txt` generado
- columnas textuales utilizadas
- filas leídas del `.csv`
- filas con texto útil
- filas vacías descartadas
- duplicados removidos
- total de palabras del corpus final
- total de líneas del `.txt`
- valor aplicado de `words_per_line`
- criterio usado para resolver el `.csv` canónico
- si hubo `skip`, `warning` o `error`

Si además generas `auditoria_archivos.csv`, mejor.

## Requisitos de documentación

Debes dejar documentado explícitamente:

1. Qué hace esta etapa.
   Puente entre extracción estructurada en `.csv` y corpus textual limpio `.txt`.
2. Qué no hace.
   No hace NLP ni análisis semántico.
3. Qué columnas usa cada fuente.
   Esto debe quedar negro sobre blanco.
4. Cómo detecta la semana ISO.
   Y cómo arma el nombre final del archivo.
5. Qué comportamiento histórico conserva.
   Especialmente:
   - limpieza por fuente,
   - deduplicación,
   - concatenación,
   - bloques de 30 palabras.
6. Qué decisiones tomaste por ambigüedad real.
   Por ejemplo:
   - selección del `.csv` canónico,
   - columnas textuales combinadas,
   - conflictos de nombres,
   - carpetas faltantes.

## Compatibilidad histórica obligatoria

No cambies nada que altere la forma histórica del corpus, salvo mejoras de estructura, robustez, trazabilidad y operación.

Debe quedar preservado:

- la lógica de limpieza,
- la lógica de deduplicación,
- la lógica de concatenación,
- la lógica de bloques de 30 palabras,
- y la convención de nombrado por semana/fuente.

## Entregables obligatorios

Quiero que me devuelvas:

1. Lista de archivos creados o modificados.
   Con explicación breve y concreta de la función de cada uno.
2. Scripts completos.
   No pseudocódigo. No fragmentos. No bosquejos.
3. Explicación breve de la arquitectura final.
   Sin rollo. Clara y operativa.
4. Comandos exactos de terminal.
   Debes incluir ejemplos para:
   - una fuente y una semana,
   - una fuente y varias semanas,
   - todas las fuentes para una semana,
   - todas las semanas disponibles,
   - dry-run.
5. Nota de compatibilidad histórica.
   Qué se preservó exactamente.
6. Nota de límites.
   Qué queda fuera porque eso ya corresponde a NLP.

## Criterio de éxito

Tu trabajo solo se considera correcto si:

- encuentra correctamente los `.csv` canónicos reales,
- usa las columnas textuales correctas por fuente,
- genera `.txt` por fuente + semana ISO,
- guarda esos `.txt` en la carpeta correcta,
- respeta el formato de nombre existente,
- conserva la limpieza histórica,
- conserva los bloques consecutivos de 30 palabras,
- no toca destructivamente la extracción,
- genera auditoría completa,
- y puede correrse por CLI sin editar código manualmente.

## Regla final

No rehagas el pipeline.
No reimagines el flujo.
No simplifiques algo que ya está resuelto en la estructura real.
No inventes comportamiento.

Haz exactamente la etapa 2 real del proyecto Radar, con disciplina operativa, trazabilidad y fidelidad metodológica.

Si detectas inconsistencias en la estructura real, las documentas y las resuelves de la forma más conservadora posible.
Pero no te salgas del flujo real del proyecto.

## Aclaraciones posteriores cerradas

1. Facebook debe salir del archivo:

   `facebook_institutional_raw_<semana>.csv`

   Ejemplo:

   `facebook_institutional_raw_2026-03-09_semana_09marzo_15marzo_26.csv`

   Debe usar posts y comentarios juntos desde ese CSV canónico.

2. En `Datos_RAdAR` había 4 carpetas de fuentes y además semanas sueltas en la raíz.
   Eso se corrigió moviendo las carpetas semanales legacy a:

   `/home/emilio/Documentos/RAdAR/Datos_RAdAR/Juntos`

   La etapa 2 vigente debe trabajar contra las 4 carpetas por fuente.
