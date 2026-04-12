# Extractor de YouTube para Radar

## Objetivo

Convertir `01_youtube_extractor_Tampico.py` en un componente profesional de ingesta para Radar: reusable, parametrizable, trazable y orquestable, manteniendo su alcance como extractor puro de YouTube.

## Renombre y compatibilidad

- Nombre histórico: `01_youtube_extractor_Tampico.py`
- Wrapper canónico para CLI: `Scripts/Extracting_Procesing/youtube_extractor.py`
- Módulo real de automatización: `Scripts/Extracting_Procesing/automation/extractors/youtube_extractor.py`
- Núcleo reusable: `Scripts/Extracting_Procesing/automation/extractors/youtube_extractor_core.py`
- Archivo de queries canónicas: `Scripts/Extracting_Procesing/automation/extractors/youtube_queries_canonical.txt`

`01_youtube_extractor_Tampico.py` se conserva como wrapper histórico para compatibilidad. La automatización real vive en `automation/extractors/` y el nombre recomendado para CLI queda como `youtube_extractor.py`.

## Responsabilidades

- Recibir parametros de extraccion por CLI o config JSON.
- Conectarse a la API de YouTube usando una API key tomada desde entorno.
- Buscar videos por query y rango temporal.
- Extraer comentarios `top_level` de esos videos.
- Persistir datasets y artefactos de corrida.
- Generar metadata, parametros efectivos, manifest y summary.
- Devolver un estado final reutilizable por un orquestador.

## Alcance explicito

- Esta version extrae comentarios `top_level`.
- No extrae replies por defecto.
- No hace NLP, limpieza avanzada, deduplicacion de negocio, clasificacion ni modelado.
- No consolida multi-fuente ni actualiza tableros.
- Depende de la disponibilidad, cuota y resultados expuestos por la API de YouTube.

## Inputs

- `--start-date YYYY-MM-DD`
- `--end-date YYYY-MM-DD`
- `--queries-file <txt|json|csv>` o `--queries "..." "..."`
- `--output-dir`
- `--youtube-api-key-env`
- `--week-name-mode exact_range|canonical_monday_sunday`
- `--max-results-search`
- `--max-comments-per-video`
- `--run-id`
- `--log-level`
- `--overwrite`
- `--publish-canonical`
- Opcionales: `--config-file`, `--country`, `--language`, `--include-replies`, `--dry-run`

## Politica de queries

Las queries pueden venir de:

1. `--queries-file`
2. `--queries`
3. el archivo canónico `youtube_queries_canonical.txt`

Contrato de edición del archivo canónico:

- una query por línea
- líneas que empiezan con `#` se ignoran

Las queries canónicas por default preservan el universo del extractor base `01_youtube_extractor_Tampico.py`:

- `presidenta municipal de Tampico`
- `Presidenta municipal de Tampico`
- `Gobierno de Tampico`
- `gobierno de Tampico`

La profesionalización aquí no cambia la lógica base de extracción: mantiene búsqueda por query y rango temporal, detalle de video y comentarios `top_level`; solo externaliza configuración, trazabilidad y artefactos. Si quieres otro universo de búsqueda, cámbialo con `--queries-file` o `--queries` sin tocar la lógica interna.

## Variables de entorno requeridas

Por default:

```bash
export YOUTUBE_API_KEY="tu_api_key_real"
```

Tambien puedes apuntar a otra variable:

```bash
python3 Scripts/Extracting_Procesing/youtube_extractor.py \
  --youtube-api-key-env RADAR_YOUTUBE_KEY \
  ...
```

## Ejemplo de uso CLI

```bash
export YOUTUBE_API_KEY="tu_api_key_real"

python3 Scripts/Extracting_Procesing/youtube_extractor.py \
  --start-date 2026-02-24 \
  --end-date 2026-03-02 \
  --output-dir /home/emilio/Documentos/RAdAR/Datos_RAdAR \
  --week-name-mode exact_range \
  --max-results-search 50 \
  --max-comments-per-video 200 \
  --run-id yt_tampico_semana_20260224 \
  --publish-canonical \
  --overwrite \
  --log-level INFO
```

Con queries externas:

```bash
python3 Scripts/Extracting_Procesing/youtube_extractor.py \
  --start-date 2026-02-24 \
  --end-date 2026-03-02 \
  --queries-file /ruta/youtube_queries_canonical.txt \
  --output-dir /home/emilio/Documentos/RAdAR/Datos_RAdAR
```

Si quieres aislar la fuente en una raíz propia, pásala explícitamente, por
ejemplo `--output-dir /home/emilio/Documentos/RAdAR/Datos_RAdAR/YouTube`.

## Estructura de salida

El extractor siempre crea una carpeta semanal y una carpeta de corrida:

```text
<output_dir>/
└── <week_name>/
    ├── runs/
    │   └── <run_id>_<timestamp>/
    │       ├── youtube_comentarios_<week_name>.csv
    │       ├── videos_encontrados.csv
    │       ├── queries_summary.csv
    │       ├── metadata_run.json
    │       ├── parametros_run.json
    │       ├── summary.json
    │       ├── manifest.json
    │       ├── errores_detectados.json
    │       └── run.log
    ├── youtube_comentarios_<week_name>.csv
    ├── videos_encontrados.csv
    ├── queries_summary.csv
    ├── metadata_run.json
    ├── parametros_run.json
    ├── summary.json
    ├── manifest.json
    └── errores_detectados.json
```

Los artefactos canonicos al nivel de la semana solo se publican si se usa `--publish-canonical`. Si ya existen, `--overwrite` define si se reemplazan o no.

## Politica semanal

- `exact_range`
  - El nombre semanal usa exactamente `start_date` y `end_date`.
  - La busqueda usa exactamente `start_date` y `end_date`.

- `canonical_monday_sunday`
  - El nombre semanal se alinea a lunes-domingo.
  - La busqueda sigue usando exactamente `start_date` y `end_date`.
  - Esto evita ambiguedad entre naming y ventana real de extraccion.

## Politica de errores y exit codes

- `0`: success
- `1`: partial_success
- `2`: failed por configuracion
- `3`: failed por API/autenticacion/fallo fatal de extraccion
- `4`: failed por escritura/publicacion de artefactos

Una query puede fallar sin colapsar toda la corrida cuando el error es recuperable. Esos detalles quedan en `errores_detectados.json` y `queries_summary.csv`.

## Integracion con procesamiento

El extractor deja datasets crudos/semi-estructurados y metadata suficiente para que otro script:

- lea el CSV principal;
- use `parametros_run.json` y `summary.json` para orquestacion;
- inspeccione `manifest.json` para localizar artefactos;
- continúe con limpieza, NLP o consolidacion sin modificar este extractor.

Para integrarlo desde Python, importa el nucleo reusable:

```python
from automation.extractors.youtube_extractor_core import (
    parse_args,
    resolve_config,
    run_extraction,
    setup_logging,
)
```

## Limitaciones conocidas

- No extrae replies aun si se pasa `--include-replies`; la bandera queda registrada y documentada.
- Los resultados dependen del ranking de la API de YouTube para cada query.
- Videos con comentarios deshabilitados o videos privados pueden generar errores recuperables por video.
- El extractor no deduplica semanticamente entre queries; una misma conversacion puede aparecer varias veces si el video entra por multiples queries.
