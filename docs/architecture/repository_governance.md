# Repository Governance

Documento autoritativo de gobierno del repositorio RAdAR.
Vigente para la rama `feature/restructuracion-arquitectonica-repo`.

## 1. Premisa metodológica

Esta rama se audita como arquitectura canónica ya operable, pero todavía sin scheduler cerrado.

Por lo tanto:

- sí se exige limpieza estructural, fronteras duras y verdad documental
- sí se exige una capa operativa explícita, trazable y reanudable en `src/operations/`
- no se exige todavía scheduling ni automatización periódica

## 2. Estado real: implementado vs reservado

### Implementado hoy

- extracción activa por fuente
- preprocessing y normalización de insumos
- NLP activo
- modelado reusable
- orquestación operativa controlada
- tracking y reporting experimental
- separación entre datos, artifacts, documentación, experimentación y legacy

### Reservado o posterior

- scheduling
- automatización periódica
- generador final de reporte

Decisión vigente sobre `src/operations/`:

- capa operativa implementada para coordinación manual controlada del pipeline

## 3. Taxonomía oficial

Cada archivo del repositorio debe pertenecer a una sola categoría:

| Categoría | Ruta raíz | Contenido permitido |
| --- | --- | --- |
| código activo canónico | `src/` | módulos y scripts vigentes |
| datos canónicos | `data/` | insumos y datasets reproducibles |
| runtime técnico | `artifacts/` | logs, cache, estado, workdirs |
| documentación estructural u operativa | `docs/` | gobierno, arquitectura, operación, migración |
| experimentación / investigación / prompts / auditoría experimental | `experiments/` | evidencia metodológica y runs históricos |
| legado | `legacy/` | material histórico fuera del flujo canónico |

Si un archivo no cabe inequívocamente en una sola de estas categorías, está mal ubicado.

## 4. Fronteras duras por carpeta

### `src/`

- solo código activo
- sin logs, cache, sesiones, datasets ni archivos de auditoría tabular

### `data/`

- solo datos canónicos o declarados como tales
- sin estado técnico, logs ni workdirs

### `artifacts/`

- solo runtime técnico
- se versionan únicamente plantillas, ejemplos y marcadores mínimos

### `docs/`

- documentación gobernante
- no investigación metodológica experimental

### `experiments/`

- evidencia experimental
- no código fuente activo
- no runtime transversal

### `legacy/`

- histórico preservado
- no nuevas implementaciones

## 5. Reglas específicas de `src/`

| Ruta | Rol vigente |
| --- | --- |
| `src/extraction/` | adquisición por fuente |
| `src/preprocessing/` | promoción y normalización |
| `src/nlp/` | variables textuales, diccionarios y clasificación |
| `src/modeling/` | núcleo técnico vigente de modelado |
| `src/shared/` | utilitarios transversales mínimos |
| `src/operations/` | orquestación operativa controlada |

### Regla para `src/operations/`

- la carpeta coordina operación canónica manual, no experimentación libre
- debe persistir estado, manifiestos, logs y JSON homogéneo por etapa
- no mezcla scheduler con orquestador

## 6. Naming canónico

### Regla general

Para todo lo activo y gobernante:

- minúsculas
- ASCII
- snake_case
- sin acentos
- sin espacios
- sin nombres ambiguos

### Excepciones explícitas y acotadas

Estas excepciones son válidas solo porque representan convenciones técnicas o evidencia histórica:

- `README.md`
- tokens ISO `yyyy-mm-dd` dentro de nombres semanales canónicos
- IDs de corrida en `experiments/runs/`
- nombres históricos preservados dentro de `legacy/`
- documentos o evidencias históricas ya existentes dentro de `experiments/`

Fuera de esas excepciones, la regla general es obligatoria.

## 7. Política de runtime

### Va en `artifacts/`

- `artifacts/logs/preprocessing/*.csv`
- caches de extracción
- sesiones autenticadas
- workdirs intermedios de extracción

### No va en git

- `artifacts/state/x_state.json`
- logs generados por ejecución
- workdirs vivos de extracción
- caches regenerables

## 8. Política de datos

`data/raw/radar_weekly_flat/` es el raw semanal canónico.

Los nombres de archivo canónicos por fuente son:

- `<semana>_facebook.csv`
- `<semana>_twitter.csv`
- `<semana>_youtube.csv`
- `<semana>_medios.txt`

`facebook_extractor_apify_tampico.py` no escribe dato canónico final.
Produce artefactos intermedios en `artifacts/runs/extraction/facebook/`.
La promoción a CSV canónico de Facebook se hace después en preprocessing.

## 9. Política de `experiments/`

- `prompts/`, `research/`, `audit/` y `runs/` son válidos
- `audit/backups/` es la única zona permitida para backups físicos
- `runs/` es evidencia, no runtime técnico reutilizable
- rutas viejas o nombres históricos dentro de documentos experimentales no gobiernan la arquitectura actual

## 10. Compatibilidad y migración

- no se permiten aliases de raíz activos como `Scripts/`, `Experimentos/`, `Datos_RAdAR/` o `Datos_RadaR_Texto/`
- `src/nlp/experiment_logger.py` es un wrapper explícito y documentado; no un duplicado silencioso
- `docs/migration/path_migration_table.csv` debe leerse como ledger histórico de la migración desde la estructura previa, no como especificación exhaustiva del naming final vigente
