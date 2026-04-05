# Extractor de Medios para Radar

## Objetivo

Profesionalizar el componente de extracción de medios de Radar tomando `04_medios_extractor.py` como base técnica canónica y dejarlo listo para operación controlada, trazabilidad fuerte e integración futura con preprocessing y orquestación.

## Renombre y compatibilidad

- Nombre histórico: `04_medios_extractor.py`
- Nombre canónico nuevo: `media_extractor.py`
- Núcleo reusable: `media_extractor_core.py`

`04_medios_extractor.py` se conserva como wrapper de compatibilidad para no romper llamados existentes. El entrypoint recomendado a futuro es `media_extractor.py`.

## Responsabilidades

- Recibir parámetros de extracción.
- Generar o cargar queries.
- Consultar Google News RSS.
- Resolver la URL real del artículo.
- Descargar y extraer texto del artículo con la mejor estrategia disponible.
- Persistir datasets y artefactos de corrida.
- Generar summary, metadata, parámetros efectivos y manifest.
- Devolver estado final reusable por un orquestador.

## Alcance explícito

- Extrae artículos desde Google News RSS.
- Resuelve URLs de Google News hacia URLs finales.
- Descarga texto de artículo con `trafilatura` cuando está disponible y con fallback a `cloudscraper`, `requests` y opcionalmente Playwright.
- No hace NLP analítico, clasificación temática, sentimiento, consolidación multi-fuente ni modelado.

## Inputs principales

- `--since`
- `--before`
- `--medio`
- `--termino`
- `--queries-file`
- `--modo-queries`
- `--output-dir`
- `--cache-dir`
- `--run-id`
- `--log-level`
- `--overwrite`
- `--publish-canonical`
- `--omitir-semanas-existentes`
- `--ignore-cache`
- `--pausa`
- `--pausa-entre-queries`
- `--week-name-mode`
- `--use-playwright`
- `--max-results-per-query`
- `--max-articles-per-week`
- `--dry-run`
- `--config-file`

## Política de queries

Las queries pueden venir de:

1. `--queries-file`
2. generación por `--medio` + `--termino`
3. defaults de compatibilidad del extractor si no se sobreescriben esos argumentos

Modos:

- `compacto`: usa `OR` entre términos por medio.
- `combinado`: genera una query por combinación `termino + medio`.

## Política semanal

- `exact_range`
  - el nombre de carpeta usa exactamente `since` y `before`
  - la búsqueda usa exactamente `since` y `before`

- `canonical_monday_sunday`
  - el nombre de carpeta se alinea a lunes-domingo
  - la búsqueda sigue usando exactamente `since` y `before`

## Política de caché

Se cachean tres capas:

1. RSS: respuesta parseada de cada feed query.
2. Resolución de URL: mapping de URL Google News a URL final.
3. Artículo: resultado de extracción por URL resuelta.

Directorio default:

```text
<output_dir>/_cache_media_extractor/
```

Control:

- por default el caché se reutiliza
- `--ignore-cache` fuerza no reutilizarlo
- el uso real del caché se registra en `summary.json` y `metadata_run.json`

La resolución de URLs de Google News usa varias estrategias:

- decodificación base64 directa cuando el payload la contiene;
- fallback nativo vía `batchexecute` de Google News;
- `googlenewsdecoder` si el paquete está instalado;
- redirect HTTP como último intento.

## Uso de Playwright

- Solo se activa si el usuario pasa `--use-playwright`.
- Se inicializa explícitamente y falla de forma clara si el entorno no está listo.
- Se usa como fallback controlado cuando las estrategias HTTP no bastan.
- Queda registrado:
  - si estaba habilitado
  - si se inicializó
  - si realmente se usó
- qué artículos lo usaron

`trafilatura` es recomendada pero no obligatoria. Si no está instalada, el extractor sigue corriendo con extracción HTML básica y deja esa degradación registrada en logs y metadata.

## Outputs

Cada corrida produce al menos:

- `media_articles_<week_name>.csv`
- `rss_items_raw.csv`
- `urls_resueltas.csv`
- `descarga_articulos_summary.csv`
- `queries_summary.csv`
- `summary.json`
- `metadata_run.json`
- `parametros_run.json`
- `manifest.json`
- `errores_detectados.json` cuando aplica
- `run.log`

## Estructura de carpetas

```text
<output_dir>/
└── <week_name>/
    ├── runs/
    │   └── <run_id>_<timestamp>/
    │       ├── media_articles_<week_name>.csv
    │       ├── rss_items_raw.csv
    │       ├── urls_resueltas.csv
    │       ├── descarga_articulos_summary.csv
    │       ├── queries_summary.csv
    │       ├── summary.json
    │       ├── metadata_run.json
    │       ├── parametros_run.json
    │       ├── manifest.json
    │       ├── errores_detectados.json
    │       └── run.log
    ├── media_articles_<week_name>.csv
    ├── rss_items_raw.csv
    ├── urls_resueltas.csv
    ├── descarga_articulos_summary.csv
    ├── queries_summary.csv
    ├── summary.json
    ├── metadata_run.json
    ├── parametros_run.json
    ├── manifest.json
    └── errores_detectados.json
```

Los artefactos al nivel semanal solo se publican si se usa `--publish-canonical`.

## Política de errores y exit codes

- `0`: success
- `1`: partial_success
- `2`: failed por configuración
- `3`: failed por fuente/conectividad/runtime fatal de extracción
- `4`: failed por persistencia

Errores recuperables quedan registrados y no tumban toda la corrida si todavía es posible seguir.

## Ejemplo de uso

```bash
python3 Scripts/Extracting_Procesing/media_extractor.py \
  --since 2026-03-06 \
  --before 2026-03-13 \
  --medio site:milenio.com \
  --termino '"tampico"' \
  --modo-queries combinado \
  --output-dir /home/emilio/Documentos/RAdAR/Datos_RAdAR/Medios \
  --run-id media_semana_20260306 \
  --max-results-per-query 10 \
  --max-articles-per-week 20 \
  --log-level INFO
```

Con Playwright explícito:

```bash
python3 Scripts/Extracting_Procesing/media_extractor.py \
  --since 2026-03-06 \
  --before 2026-03-13 \
  --medio site:noticiasdetampico.mx \
  --termino '"tampico"' \
  --use-playwright \
  --output-dir /home/emilio/Documentos/RAdAR/Datos_RAdAR/Medios
```

## Integración con preprocessing

Este extractor está diseñado para dejar artefactos fuente y metadata suficiente para que otro paso:

- lea el CSV principal;
- use `queries_summary.csv` y `descarga_articulos_summary.csv` para control operativo;
- use `manifest.json` para localizar artefactos;
- continúe con limpieza/preprocessing sin tocar el extractor.

## Limitaciones conocidas

- La calidad del texto depende de la accesibilidad del sitio y del método que logre extraer contenido.
- Google News RSS puede devolver items sin `pubDate` parseable o con URLs difíciles de resolver.
- Playwright no se usa automáticamente; debe activarse explícitamente.
- El extractor no deduplica semánticamente contenidos entre queries.
