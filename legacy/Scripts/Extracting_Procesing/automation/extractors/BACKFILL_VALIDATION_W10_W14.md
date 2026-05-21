# Backfill Validation W10-W14

## Alcance

Consolidación fina de `Scripts/Extracting_Procesing/automation/extractors`
usando únicamente backfill útil del tramo:

- `2026-W10`: `2026-03-02` a `2026-03-08`
- `2026-W11`: `2026-03-09` a `2026-03-15`
- `2026-W12`: `2026-03-16` a `2026-03-22`
- `2026-W13`: `2026-03-23` a `2026-03-29`
- `2026-W14`: `2026-03-30` a `2026-04-05`

Criterios aplicados en esta fase:

- no rehacer la arquitectura;
- no correr ventanas artificiales;
- no re-bajar todo cuando el material ya era útil;
- corregir solo gaps reales detectados en el tramo W10-W14.

## Correcciones consolidadas

### Documentación y contratos

- `README_facebook_institutional_extractor.md`
  - Se corrigió la nota desfasada que seguía atribuyendo el límite de
    discovery al actor viejo.
- `facebook_institutional_extractor_core.py`
  - Se corrigió el mensaje de validación de `discovery_results_per_page` para
    que describa la política canónica real y no el actor anterior.
- Se auditó la legibilidad de archivos canónicos:
  - `facebook_institutional_pages_canonical.csv`
  - `media_queries_canonical.csv`
  - `twitter_queries_canonical.txt`
  - `youtube_queries_canonical.txt`
  - Estado: ya estaban en formato legible y auditable; no requirieron rehacerse.

### Correcciones operativas ya absorbidas por los extractores

- `Medios`
  - Se eliminó el cap artificial semanal y por query.
  - Se re-hizo el tramo W10-W14 con cobertura real completa.
  - `summary.json` y `metadata_run.json` ya exponen uso agregado de fallback y
    Playwright.
- `Twitter`
  - Se mantuvo la sonda de selectores y el registro de `selector_warnings`.
  - La sesión persistida en `Scripts/state/x_state.json` quedó validada en
    corridas reales del tramo W10-W14.
- `YouTube`
  - Se confirmó el contrato documental y de artefactos con corridas reales del
    mismo tramo.
- `Facebook institucional`
  - La lógica buena quedó consolidada con `apify/facebook-posts-scraper`.
  - W11 y W12, que seguían canónicamente publicadas con el actor viejo y vacías,
    se re-corrieron de forma puntual el `2026-04-11` y quedaron corregidas.

## Estado real por fuente

### Medios

| Semana | Run ID | Estado | RSS detectados | URLs resueltas | Artículos OK | Fallback % | Playwright % |
|---|---|---|---:|---:|---:|---:|---:|
| W10 | `media_w10_full` | `success` | 208 | 200 | 200 | 50.00 | 0.00 |
| W11 | `media_w11_full` | `success` | 208 | 201 | 201 | 50.25 | 0.00 |
| W12 | `media_w12_full` | `success` | 213 | 201 | 201 | 49.75 | 0.00 |
| W13 | `media_w13_full` | `success` | 211 | 202 | 202 | 49.50 | 0.00 |
| W14 | `media_w14_full` | `success` | 208 | 177 | 177 | 44.07 | 0.00 |

Lectura operativa:

- El tramo marzo-primera semana de abril quedó re-materializado sin cap
  artificial.
- `--use-playwright` estuvo habilitado en los reruns full, pero no fue
  necesario usar Playwright en los artículos capturados de W10-W14.
- El fallback HTTP/HTML sí se usó de forma relevante y queda visible en el
  contrato de salida.

### Twitter

| Semana | Run ID | Estado | Tweets detectados | Tweets guardados | Selector warnings | Expansión texto |
|---|---|---|---:|---:|---:|---:|
| W10 | `twitter_w10_backfill` | `success` | 112 | 38 | 0 | 0/0 |
| W11 | `twitter_w11_rerun` | `success` | 221 | 38 | 0 | 0/0 |
| W12 | `twitter_w12_backfill` | `success` | 84 | 22 | 0 | 0/0 |
| W13 | `twitter_w13_backfill` | `partial_success` | 237 | 79 | 0 | 0/0 |
| W14 | `twitter_w14_backfill` | `success` | 273 | 99 | 0 | 0/0 |

Incidencia real del tramo:

- `W13` quedó `partial_success` por `3` eventos `tweet_parse_empty` en la query
  `tampico`.
- No hubo `selector_warnings` en el tramo W10-W14.
- La sesión persistida funcionó de manera estable.

### YouTube

| Semana | Run ID | Estado | Videos encontrados | Comentarios extraídos | Incidencias recuperables |
|---|---|---|---:|---:|---:|
| W10 | `yt_w10_backfill` | `partial_success` | 70 | 5568 | 4 |
| W11 | `yt_w11_rerun` | `success` | 68 | 2666 | 0 |
| W12 | `yt_w12_backfill` | `success` | 2 | 1 | 0 |
| W13 | `yt_w13_backfill` | `partial_success` | 60 | 1691 | 2 |
| W14 | `yt_w14_backfill` | `success` | 61 | 1283 | 0 |

Incidencia real del tramo:

- Los `partial_success` de W10 y W13 vienen de videos con
  `commentsDisabled` en la API, no de fallo estructural del extractor.
- El material útil sí quedó publicado en las semanas canónicas.

### Facebook institucional

| Semana | Run ID | Estado | Posts candidatos | Posts seleccionados | Comentarios guardados | Uso Apify USD |
|---|---|---|---:|---:|---:|---:|
| W10 | `fb_w10_backfill_fix` | `success` | 49 | 16 | 61 | 0.209 |
| W11 | `fb_w11_backfill_fix` | `success` | 69 | 16 | 65 | 0.339 |
| W12 | `fb_w12_backfill_fix` | `success` | 61 | 16 | 70 | 0.274 |
| W13 | `fb_w13_backfill` | `success` | 85 | 16 | 70 | 0.403 |
| W14 | `fb_w14_backfill` | `success` | 52 | 16 | 88 | 0.235 |

Detalle relevante:

- W11 y W12 ya no están vacías.
- Ambas semanas fueron republicadas canónicamente el `2026-04-11` con
  `--week-name-mode exact_range`, `--publish-canonical`, `--overwrite`,
  `seed=42`, `weekly_comment_cap_per_page=100`, `max_posts_per_page_per_week=8`
  y `discovery_results_per_page=100`.
- `GobiernoTampico` también materializó posts y comentarios útiles en las
  semanas re-corridas, por lo que el gap operativo real quedó cerrado.

## Artefactos canónicos por fuente

### Medios

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

### Twitter

- `twitter_data_<week_name>.csv`
- `tweets_raw.jsonl`
- `queries_summary.csv`
- `summary.json`
- `metadata_run.json`
- `parametros_run.json`
- `manifest.json`
- `errores_detectados.json` cuando aplica
- `run.log`

### YouTube

- `youtube_comentarios_<week_name>.csv`
- `videos_encontrados.csv`
- `queries_summary.csv`
- `summary.json`
- `metadata_run.json`
- `parametros_run.json`
- `manifest.json`
- `errores_detectados.json` cuando aplica
- `run.log`

### Facebook institucional

- `facebook_institutional_raw_<week_name>.csv`
- `posts_selected.csv`
- `comments_selected.csv`
- `selection_audit.csv`
- `summary.json`
- `metadata_run.json`
- `parametros_run.json`
- `manifest.json`
- `errores_detectados.json` cuando aplica
- `run.log`

## Incidencias relevantes del tramo

- `Medios`
  - No quedaron incidencias bloqueantes en el tramo final W10-W14.
  - La señal operativa importante es el uso alto de fallback HTTP/HTML, no de
    Playwright.
- `Twitter`
  - `W13`: `3` errores recuperables `tweet_parse_empty` en la query `tampico`.
- `YouTube`
  - `W10`: `4` videos con `commentsDisabled`.
  - `W13`: `2` videos con `commentsDisabled`.
- `Facebook`
  - El problema real del tramo no era metodológico sino de publicación canónica:
    W11 y W12 seguían vacías con el actor anterior. Eso ya quedó corregido.

## Dictamen operativo

Estado de la carpeta al cierre de esta fase: `congelable con monitoreo operativo`.

Lectura técnica:

- no hace falta otra reestructuración de arquitectura;
- el contrato de salida por fuente quedó suficientemente estable;
- W10-W14 ya está cubierto canónicamente en las cuatro fuentes;
- los residuos que quedan son de operación externa esperable:
  - DOM/UI de X/Twitter;
  - comentarios deshabilitados en YouTube;
  - variación de accesibilidad/fallback en Medios;
  - costo y comportamiento de actores de Apify en Facebook.

## Pendientes reales

No queda un gap estructural abierto dentro del tramo W10-W14.

Sí conviene mantener como vigilancia operativa:

- `Twitter`: seguir observando `tweet_parse_empty` si vuelve a aparecer.
- `YouTube`: seguir tratando `commentsDisabled` como residual esperado y no como
  fallo del extractor.
- `Medios`: monitorear si el porcentaje de fallback sube o si Playwright
  empieza a usarse de forma material.
- `Facebook`: conservar W11/W12 ya corregidas como referencia de que la ruta
  canónica vigente es `apify/facebook-posts-scraper`.
