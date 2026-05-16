# Secrets, credenciales y runtime operativo — RAdAR

Guía autoritativa para preparar y correr pruebas de extracción y preprocessing.
No describe la orquestación final (ver `src/operations/` cuando esté lista).

---

## Entorno operativo

El entorno de extracción y preprocessing es **`radar-ops-py311`**, definido en
`environment.ops.yml`. Es independiente del entorno de modelado (`environment.modeling.yml`).

### Crear o actualizar el entorno

```bash
bash setup_env_ops.sh
```

El script:
- Lee el nombre del entorno desde `environment.ops.yml`
- Crea o actualiza el entorno conda
- Instala los navegadores de Playwright (chromium) automáticamente
- Falla con mensajes claros si falta `conda.sh`

Si `conda.sh` no está en la ruta por defecto (`~/anaconda3/...`):

```bash
export CONDA_SH=$HOME/miniconda3/etc/profile.d/conda.sh
bash setup_env_ops.sh
```

Si la instalación de Playwright falla en el script, complétala manualmente:

```bash
conda activate radar-ops-py311
playwright install chromium
```

### Activar el entorno

```bash
conda activate radar-ops-py311
```

O sin activar (para comandos individuales):

```bash
conda run -n radar-ops-py311 python ...
```

---

## Donde pongo las keys una sola vez

Crea `.env` en la raíz del repo (copia de `.env.example`):

```bash
cp .env.example .env
# Edita .env con los valores reales
```

El archivo `.env` se carga automáticamente al importar cualquier módulo de `src.shared`.
Los extractores y el orquestador lo leen sin configuración adicional.

**Prioridad:** variables ya definidas en el entorno del sistema tienen prioridad sobre `.env`.

---

## Variables requeridas por fuente

| Fuente    | Variable          | Descripción                           | Obligatoria    |
|-----------|-------------------|---------------------------------------|----------------|
| facebook  | `SERPER_API_KEY`  | Búsqueda de URLs via Serper.dev        | Sí (fase 1)    |
| facebook  | `APIFY_TOKEN`     | Descarga de comentarios via Apify      | Sí (fase 2)    |
| youtube   | `YOUTUBE_API_KEY` | YouTube Data API v3                   | Sí             |
| twitter   | *(ninguna)*       | Usa `x_state.json` (ver abajo)        | —              |
| medios    | *(ninguna)*       | Google News RSS gratuito              | —              |

---

## Twitter/X: state persistente (x_state.json)

### Qué es

`x_state.json` es un archivo de sesión de Playwright: contiene las cookies de autenticación
de una sesión activa de Twitter/X. El extractor lo usa para navegar como usuario autenticado
sin necesidad de hacer login en cada corrida.

### Dónde vive

```
artifacts/state/x_state.json
```

Path centralizado en `src/shared/runtime_paths.py` como `TWITTER_STATE_PATH`.
El archivo está **gitignoreado** via `artifacts/state/*.json` y nunca debe versionarse.

### Cómo se inicializa (primera vez)

El state NO se genera automáticamente. Generarlo manualmente una vez:

**Opción A — Script de Playwright interactivo** (recomendado):

```python
# Ejecuta esto una sola vez para capturar la sesión activa
from playwright.sync_api import sync_playwright
import json
from pathlib import Path

Path("artifacts/state").mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # headless=False para ver el navegador
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://x.com/login")
    input("Inicia sesion en el navegador y presiona ENTER aqui cuando termines...")
    state = context.storage_state()
    with open("artifacts/state/x_state.json", "w") as f:
        json.dump(state, f, indent=2)
    browser.close()
    print("State guardado en artifacts/state/x_state.json")
```

**Opción B — Desde sesión existente:**

```bash
cp /ruta/al/proyecto/anterior/state/x_state.json artifacts/state/x_state.json
```

### Cuándo se necesita refrescar

El state expira cuando las cookies caducan o Twitter invalida la sesión.
Para refrescar: repite la Opción A y sobreescribe el archivo.

---

## Preparar directorios de runtime

Los directorios de runtime no se versionan. Crearlos antes de extraer:

```bash
conda run -n radar-ops-py311 python -m src.shared.check_config --ensure-dirs
```

Directorios que crea:
- `artifacts/state/`
- `artifacts/cache/`
- `artifacts/logs/preprocessing/`
- `data/raw/radar_weekly_flat/`
- `data/text/radar_weekly_flat/`

---

## Verificación de configuración (preflight)

Antes de correr extractores o preprocessing:

```bash
# Verificar todas las fuentes + directorios
conda run -n radar-ops-py311 python -m src.shared.check_config --ensure-dirs

# Solo algunas fuentes
conda run -n radar-ops-py311 python -m src.shared.check_config --sources facebook twitter

# Solo verificar (sin crear directorios)
conda run -n radar-ops-py311 python -m src.shared.check_config
```

Ejemplo de salida exitosa:

```
✓  .env: /repo/.env [encontrado]

  ✓  FACEBOOK
       ✓  SERPER_API_KEY [disponible]
       ✓  APIFY_TOKEN [disponible]

  ✓  TWITTER
       ✓  x_state.json (artifacts/state/x_state.json) [2048 bytes]

  ✓  YOUTUBE
       ✓  YOUTUBE_API_KEY [disponible]

  ✓  MEDIOS
       (sin requisitos de credenciales)

  Directorios de runtime:
       ✓  .../artifacts/state [ok]
       ✓  .../artifacts/cache [ok]
       ✓  .../artifacts/logs/preprocessing [ok]
       ✓  .../data/raw/radar_weekly_flat [ok]
       ✓  .../data/text/radar_weekly_flat [ok]

✓  Todo listo para correr el pipeline.
```

---

## Pruebas mínimas de extracción por fuente

Todos los extractores se ejecutan con `python -m src.extraction.runners.<nombre>` desde la raíz del repo.
Esta forma es obligatoria: los extractores importan `src.shared` internamente, y el flag `-m`
agrega el directorio actual a `sys.path`, haciendo que `src` sea importable sin configuración extra.
Ejecutar con `python src/extraction/runners/<nombre>.py` directamente falla con `ModuleNotFoundError`.

### Twitter/X

Requiere: `x_state.json` válido en `artifacts/state/`.
Salida: `data/raw/radar_weekly_flat/{nombre_semana}/{nombre_semana}_twitter.csv`

```bash
# Fechas como argumentos posicionales
conda run -n radar-ops-py311 python -m src.extraction.runners.twitter_extractor_tampico \
  2026-04-07 2026-04-13

# Con queries personalizadas
conda run -n radar-ops-py311 python -m src.extraction.runners.twitter_extractor_tampico \
  2026-04-07 2026-04-13 \
  --query "Monica Villarreal Tampico" \
  --query "gobierno de Tampico"

# Sin fechas: usa CONFIG_START_DATE_STR / CONFIG_END_DATE_STR del script
conda run -n radar-ops-py311 python src/extraction/runners/twitter_extractor_tampico.py
```

### YouTube

Requiere: `YOUTUBE_API_KEY` en `.env`.
Salida: `data/raw/radar_weekly_flat/{nombre_semana}/{nombre_semana}_youtube.csv`

```bash
conda run -n radar-ops-py311 python -m src.extraction.runners.youtube_extractor_tampico \
  --since 2026-04-07 --before 2026-04-13

# Sin fechas: usa CONFIG_START_DATE_STR / CONFIG_END_DATE_STR del script
conda run -n radar-ops-py311 python -m src.extraction.runners.youtube_extractor_tampico
```

### Facebook (Apify + Serper)

Requiere: `SERPER_API_KEY` y `APIFY_TOKEN` en `.env`.
Salida: `artifacts/runs/extraction/facebook/{nombre_semana}/` (artefactos intermedios).
Después de extraer, distribuir a la estructura canónica con el paso de preprocessing.

```bash
# Pipeline completo (URLs + comentarios)
conda run -n radar-ops-py311 python -m src.extraction.runners.facebook_extractor_apify_tampico \
  --since 2026-04-07 --before 2026-04-13

# Solo URLs (fase 1 — verificación rápida de SERPER_API_KEY)
conda run -n radar-ops-py311 python -m src.extraction.runners.facebook_extractor_apify_tampico \
  --since 2026-04-07 --before 2026-04-13 \
  --solo-urls

# Con páginas específicas
conda run -n radar-ops-py311 python -m src.extraction.runners.facebook_extractor_apify_tampico \
  --since 2026-04-07 --before 2026-04-13 \
  --pages TampicoGob monicavtampico
```

**Nota:** Facebook no escribe directamente a `data/raw/radar_weekly_flat/`.
Para mover a la estructura canónica, usar el paso `distribuir-facebook` del preprocessing.

### Medios (Google News RSS)

Sin credenciales requeridas.
Salida: `data/raw/radar_weekly_flat/{nombre_semana}/`
Caché RSS: `artifacts/cache/extraction/medios_rss/`

```bash
conda run -n radar-ops-py311 python -m src.extraction.runners.medios_extractor \
  --since 2026-04-07 --before 2026-04-13

# Sin fechas: usa FECHA_INICIO_EXACTA / FECHA_FIN_EXACTA del script
conda run -n radar-ops-py311 python -m src.extraction.runners.medios_extractor
```

---

## Preprocessing base

El módulo de preprocessing es invocable con `python -m src.preprocessing`.

### Ver comandos disponibles

```bash
conda run -n radar-ops-py311 python -m src.preprocessing --help
conda run -n radar-ops-py311 python -m src.preprocessing pipeline-base --help
```

### Dry-run del pipeline base (sin aplicar cambios)

```bash
conda run -n radar-ops-py311 python -m src.preprocessing pipeline-base
```

### Ejecutar el pipeline base (aplica cambios)

```bash
conda run -n radar-ops-py311 python -m src.preprocessing pipeline-base --apply
```

El pipeline-base ejecuta en secuencia:
1. `normalizar-semanas` — prefijado cronológico y normalización canónica de carpetas
2. `distribuir-facebook` — mueve artefactos de Facebook a estructura semanal
3. `distribuir-medios` — asigna archivos externos de medios
4. Completar semanas faltantes por fuente (facebook, twitter, youtube)

### Pasos individuales

```bash
# Normalizar nombres de carpetas semanales
conda run -n radar-ops-py311 python -m src.preprocessing normalizar-semanas --apply

# Distribuir Facebook desde artifacts/runs a raw/
conda run -n radar-ops-py311 python -m src.preprocessing distribuir-facebook --apply

# Completar una fuente específica
conda run -n radar-ops-py311 python -m src.preprocessing completar-facebook --apply
conda run -n radar-ops-py311 python -m src.preprocessing completar-twitter --apply
conda run -n radar-ops-py311 python -m src.preprocessing completar-youtube --apply
```

---

## Promover raw a texto

```bash
conda run -n radar-ops-py311 python -m src.preprocessing promover-texto
```

Lee de: `data/raw/radar_weekly_flat/`
Escribe a: `data/text/radar_weekly_flat/`
Auditoría: `data/text/radar_weekly_flat/_auditoria_preprocessing/`

**Nota:** La lógica de limpieza textual en este script es **[CONGELADA]**.
No modificar las funciones `normalize_*` sin revisión metodológica formal.

---

## Flujo mínimo operable (secuencia completa)

```bash
# 1. Verificar configuración y crear directorios
conda run -n radar-ops-py311 python -m src.shared.check_config --ensure-dirs

# 2. Extraer por fuente (reemplazar fechas según semana objetivo)
conda run -n radar-ops-py311 python -m src.extraction.runners.twitter_extractor_tampico \
  2026-04-07 2026-04-13
conda run -n radar-ops-py311 python -m src.extraction.runners.youtube_extractor_tampico \
  --since 2026-04-07 --before 2026-04-13
conda run -n radar-ops-py311 python -m src.extraction.runners.facebook_extractor_apify_tampico \
  --since 2026-04-07 --before 2026-04-13
conda run -n radar-ops-py311 python -m src.extraction.runners.medios_extractor \
  --since 2026-04-07 --before 2026-04-13

# 3. Preprocessing base (normaliza estructura + distribuye Facebook)
conda run -n radar-ops-py311 python -m src.preprocessing pipeline-base --apply

# 4. Promover raw a texto
conda run -n radar-ops-py311 python -m src.preprocessing promover-texto
```

---

## Qué pasa si falta una key

Al correr un extractor individualmente:

```
ValueError: Variable de entorno requerida no encontrada: YOUTUBE_API_KEY
(requerido por youtube_extractor). Configura 'YOUTUBE_API_KEY=tu_valor' en .env ...
```

Al correr el preflight:

```
✗  YOUTUBE
     ✗  YOUTUBE_API_KEY [FALTANTE]
     ✗  Variable de entorno faltante: YOUTUBE_API_KEY. Agrega 'YOUTUBE_API_KEY=tu_valor' en .env.
```

---

## Estructura de archivos relevantes

```
.env                                            ← Credenciales reales (gitignoreado)
.env.example                                    ← Plantilla para crear .env
environment.ops.yml                             ← Entorno operativo (extraccion/preprocessing)
setup_env_ops.sh                                ← Script para crear/actualizar entorno ops
artifacts/state/x_state.json                   ← State de Twitter/X (gitignoreado)
artifacts/state/                                ← State persistente de extractores
artifacts/cache/                                ← Cache de RSS y otros intermedios
artifacts/logs/preprocessing/                  ← Logs y reportes de preprocessing
data/raw/radar_weekly_flat/                     ← Datos extraídos por semana/fuente
data/text/radar_weekly_flat/                    ← Corpus textual procesado
src/shared/secrets.py                           ← Loader de .env + validación de secretos
src/shared/runtime_paths.py                    ← Rutas canónicas de runtime
src/shared/check_config.py                     ← Checker standalone de preflight
src/extraction/runners/                         ← Extractores por fuente
src/preprocessing/                              ← Preprocessing base y promoción
```
