# Extractor Institucional de Facebook

## Objetivo

Materializar datos fuente de Facebook institucional de Tampico bajo un
estándar reproducible, trazable y compatible con el resto del sistema Radar.

La base canónica histórica fue `03_facebook_extractor_apify_Tampico.py`; la
implementación profesional ahora vive en:

- `automation/extractors/facebook_institutional_extractor.py`
- `automation/extractors/facebook_institutional_extractor_core.py`

Se deja compatibilidad temporal con:

- `Scripts/Extracting_Procesing/03_facebook_extractor_apify_Tampico.py`
- `Scripts/Extracting_Procesing/facebook_institutional_extractor.py`

## Alcance

Este componente es solo para Facebook institucional de Tampico.

Páginas canónicas activas:

- `964877296876825` -> `MonicaVillarreal`
- `474462132406835` -> `GobiernoTampico`

No está diseñado para medios ni para ampliar universo por defecto.

## Responsabilidades

- Recibir parámetros de extracción por CLI o `config-file`.
- Cargar páginas institucionales objetivo.
- Descubrir posts candidatos dentro del rango temporal.
- Aplicar sampling de posts antes de descargar comentarios.
- Descargar comentarios solo para los posts seleccionados.
- Cortar la extracción cuando una página alcanza su cap semanal.
- Preservar la relación post-comentario.
- Persistir salidas estructuradas y auditables.
- Generar `summary.json`, `metadata_run.json`, `parametros_run.json` y `manifest.json`.

No hace:

- homologación analítica
- NLP
- clasificación temática
- modelado
- reporting

## Sampling integrado a extracción

Este extractor no baja masivamente para recortar después.

Contrato metodológico implementado:

- unidad principal de interés: comentarios
- semilla reproducible: `42`
- cap semanal por página: `100` comentarios
- páginas institucionales canónicas: `MonicaVillarreal` y `GobiernoTampico`

Estrategia operativa:

1. descubrir posts candidatos por página y rango;
2. seleccionar posts con cobertura temporal mediante espaciado temporal;
3. ordenar los posts seleccionados por potencial de comentarios para eficiencia;
4. pedir comentarios por post con `max_comments_per_post`;
5. detener ampliación cuando la página alcanza su cap semanal.

## Lógica absorbida desde el script de comments

Se absorbió de `Facebook_Extractor_Comments_Apify_Tampico.py`:

- recuperación multi-campo del texto del post padre desde items del actor;
- priorización del texto de post más informativo;
- relleno de metadata faltante del post padre usando el mismo lote de comentarios ya descargado.

Se descartó deliberadamente:

- dependencia de CSV manual intermedio;
- scraping adicional de la URL del post para enriquecer texto;
- cualquier enriquecimiento que aumente costo de forma desproporcionada.

## Inputs

CLI mínima recomendada:

- `--since`
- `--until`
- `--pages-file`
- `--page-id`
- `--output-dir`
- `--run-id`
- `--log-level`
- `--overwrite`
- `--publish-canonical`
- `--week-name-mode`
- `--seed`
- `--weekly-comment-cap-per-page`
- `--max-posts-per-page-per-week`
- `--max-comments-per-post`
- `--apify-token-env`
- `--actor-name-posts`
- `--actor-name-comments`
- `--memory-mb`
- `--timeout-seconds`
- `--dry-run`

## Variable de entorno requerida

```bash
export APIFY_TOKEN="tu_token_real"
```

Si quieres usar otro nombre:

```bash
python3 Scripts/Extracting_Procesing/facebook_institutional_extractor.py \
  --apify-token-env RADAR_APIFY_TOKEN
```

## Política temporal y naming semanal

Opciones soportadas:

- `exact_range`
- `canonical_w_tue`

`canonical_w_tue` alinea el naming a semanas con cierre martes, compatible con
la lógica histórica de homologación. Además, cada registro guarda `week_label`
derivado del `created_time` con esa misma política W-TUE.

## Outputs

Cada corrida genera:

- `facebook_institutional_raw_<week_name>.csv`
- `posts_selected.csv`
- `comments_selected.csv`
- `selection_audit.csv`
- `summary.json`
- `metadata_run.json`
- `parametros_run.json`
- `manifest.json`
- `errores_detectados.json` si aplica
- `run.log`

## Estructura de carpetas

```text
<output_dir>/<week_name>/runs/<run_id>_<timestamp>/
├── facebook_institutional_raw_<week_name>.csv
├── posts_selected.csv
├── comments_selected.csv
├── selection_audit.csv
├── summary.json
├── metadata_run.json
├── parametros_run.json
├── manifest.json
├── errores_detectados.json
└── run.log
```

Opcionalmente, si se usa `--publish-canonical`, publica copias canónicas en
`<output_dir>/<week_name>/`.

## Política de errores

Estados finales:

- `success`
- `partial_success`
- `failed`

Exit codes:

- `0`: success
- `1`: partial_success
- `2`: failed por configuración
- `3`: failed por API/plataforma/dependencias
- `4`: failed por persistencia

Errores recuperables típicos:

- falla un actor para una página
- falla la descarga de comentarios de un post
- faltan campos en ciertos items

Errores fatales típicos:

- token ausente
- dependencia `apify-client` ausente en corrida real
- imposibilidad total de persistencia

## Ejemplo de ejecución

```bash
python3 Scripts/Extracting_Procesing/facebook_institutional_extractor.py \
  --since 2026-03-04 \
  --until 2026-03-10 \
  --output-dir /home/emilio/Documentos/RAdAR/Datos_RAdAR/Facebook \
  --run-id fb_inst_20260310 \
  --week-name-mode canonical_w_tue \
  --seed 42 \
  --weekly-comment-cap-per-page 100 \
  --max-posts-per-page-per-week 8 \
  --max-comments-per-post 25 \
  --publish-canonical \
  --overwrite \
  --log-level INFO
```

## Limitaciones conocidas

- Requiere `apify-client` para corridas reales.
- Depende de la disponibilidad y estabilidad de los actores de Apify.
- El control de costo es fuerte, pero la API/actor puede devolver menos datos de los solicitados.
- `total_comments_skipped_by_cap` usa metadata del post cuando existe; si el actor no la entrega, el valor es conservador.

## Integración posterior

La salida está pensada para conectarse después con una capa separada de:

- preprocessing
- homologación temporal
- integración multi-fuente
- modelado

No se requiere editar la lógica del extractor para orquestarlo desde otro
script Python o desde un runner principal.
