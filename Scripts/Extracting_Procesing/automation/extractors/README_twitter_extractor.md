# Extractor de X/Twitter para Radar

## Objetivo

Convertir `02_twitter_extractor_Tampico.py` en un componente profesional de extracción para Radar: reusable, parametrizable, trazable y orquestable, manteniendo su alcance como extractor puro de X/Twitter.

## Renombre y compatibilidad

- Nombre histórico: `02_twitter_extractor_Tampico.py`
- Wrapper canónico para CLI: `Scripts/Extracting_Procesing/twitter_extractor.py`
- Módulo real de automatización: `Scripts/Extracting_Procesing/automation/extractors/twitter_extractor.py`
- Núcleo reusable: `Scripts/Extracting_Procesing/automation/extractors/twitter_extractor_core.py`
- Archivo de queries canónicas: `Scripts/Extracting_Procesing/automation/extractors/twitter_queries_tampico.txt`

`02_twitter_extractor_Tampico.py` se conserva como wrapper histórico para no romper llamados existentes. La automatización real vive en `automation/extractors/` y el nombre recomendado para CLI queda como `twitter_extractor.py`.

## Responsabilidades

- Recibir parámetros de extracción.
- Cargar o validar una sesión persistida de X/Twitter.
- Cargar queries canónicas o queries externas.
- Ejecutar búsquedas live en X/Twitter.
- Extraer tweets visibles y replies cuando se habilitan.
- Expandir texto truncado cuando la interfaz lo permite.
- Persistir datasets y artefactos de corrida.
- Generar `summary.json`, `metadata_run.json`, `parametros_run.json` y `manifest.json`.
- Devolver un estado final reusable por un orquestador.

## Alcance explícito

- Extrae tweets visibles desde la interfaz web de X/Twitter con Playwright.
- Usa sesión persistida vía `x_state.json`.
- Soporta replies como capacidad opcional del extractor.
- No hace NLP analítico, clasificación, scoring, sentimiento, consolidación multi-fuente ni modelado.
- No deja residuos semánticos de CDMX ni usa la query ambigua `"presidenta municipal"`.

## Inputs principales

- `--since`
- `--until`
- `--queries-file`
- `--query`
- `--output-dir`
- `--session-state-file`
- `--run-id`
- `--log-level`
- `--overwrite`
- `--publish-canonical`
- `--week-name-mode`
- `--max-scrolls`
- `--max-tweets-per-query`
- `--max-replies-per-tweet`
- `--headless` / `--headed`
- `--pause`
- `--include-replies` / `--no-replies`
- `--dry-run`

## Política de queries

Las queries pueden venir de:

1. `--queries-file`
2. `--query` repetido por CLI
3. el archivo canónico `twitter_queries_tampico.txt`

Las queries canónicas por default son:

- `to:MonicaVTampico`
- `from:MonicaVTampico`
- `to:TampicoGob`
- `from:TampicoGob`
- `@TampicoGob`
- `@MonicaVTampico`

La query `"presidenta municipal"` queda explícitamente fuera de la versión canónica.

## Política semanal

- `exact_range`
  - el nombre de carpeta usa exactamente `since` y `until`
  - la búsqueda usa exactamente `since` y `until`

- `canonical_monday_sunday`
  - el nombre de carpeta se alinea a lunes-domingo
  - la búsqueda sigue usando exactamente `since` y `until`

## Política de sesión

- El extractor usa por default `Scripts/state/x_state.json`.
- Puede cambiarse con `--session-state-file`.
- Si el archivo no existe o no contiene JSON válido, la corrida falla con error fatal controlado.
- Si la sesión parece expirada y X redirige a login, la corrida falla con error fatal controlado.
- `metadata_run.json` y `summary.json` registran la ruta de sesión, si se usó y si la validación de sesión pasó.

## Uso de Playwright

- Playwright es obligatorio para corridas reales.
- `--dry-run` permite validar configuración y artefactos sin requerir Playwright operativo.
- `--headless` deja el navegador en modo headless.
- `--headed` fuerza modo visible para debugging.
- Si Playwright no está instalado o el browser no puede abrirse, la corrida falla con error fatal controlado.
- `metadata_run.json` y `summary.json` registran si Playwright estuvo disponible, si se usó y si la corrida fue headless.

## Outputs

Cada corrida produce al menos:

- `twitter_data_<week_name>.csv`
- `tweets_raw.jsonl`
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
    │       ├── twitter_data_<week_name>.csv
    │       ├── tweets_raw.jsonl
    │       ├── queries_summary.csv
    │       ├── summary.json
    │       ├── metadata_run.json
    │       ├── parametros_run.json
    │       ├── manifest.json
    │       ├── errores_detectados.json
    │       └── run.log
    ├── twitter_data_<week_name>.csv
    ├── tweets_raw.jsonl
    ├── queries_summary.csv
    ├── summary.json
    ├── metadata_run.json
    ├── parametros_run.json
    ├── manifest.json
    └── errores_detectados.json
```

Los artefactos semanales solo se publican si se usa `--publish-canonical`.

## Política de errores y exit codes

- `0`: success
- `1`: partial_success
- `2`: failed por configuración
- `3`: failed por sesión, Playwright, navegación o plataforma
- `4`: failed por persistencia

Errores recuperables por query, tweet o reply quedan registrados y no derriban toda la corrida si todavía es posible seguir.

## Ejemplo de uso

```bash
python3 Scripts/Extracting_Procesing/twitter_extractor.py \
  --since 2026-03-03 \
  --until 2026-03-09 \
  --output-dir /home/emilio/Documentos/RAdAR/Datos_RAdAR/Twitter \
  --session-state-file /home/emilio/Documentos/RAdAR/Scripts/state/x_state.json \
  --run-id twitter_semana_20260303 \
  --max-scrolls 10 \
  --max-tweets-per-query 500 \
  --max-replies-per-tweet 100 \
  --headless \
  --log-level INFO
```

Con queries externas:

```bash
python3 Scripts/Extracting_Procesing/twitter_extractor.py \
  --since 2026-03-03 \
  --until 2026-03-09 \
  --queries-file /ruta/queries_twitter_tampico.txt \
  --session-state-file /home/emilio/Documentos/RAdAR/Scripts/state/x_state.json
```

## Integración con preprocessing

Este extractor deja datasets fuente y metadata suficiente para que otro paso:

- lea el CSV principal;
- use `queries_summary.csv` para control operativo;
- use `manifest.json` para localizar artefactos;
- continúe con limpieza y normalización sin tocar el extractor.

Para integrarlo desde Python:

```python
from automation.extractors.twitter_extractor_core import run_extraction
```

## Limitaciones conocidas

- Depende de la disponibilidad de la interfaz web de X/Twitter y de una sesión válida.
- La extracción de métricas visibles puede variar según cambios del DOM.
- `view_count` y `conversation_id` son best effort; pueden quedar vacíos en algunos casos.
- Replies y expansión de texto dependen del DOM efectivo cargado por X/Twitter.
