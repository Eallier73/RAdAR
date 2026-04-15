# Secrets, credenciales y runtime state — RAdAR

## Donde pongo las keys una sola vez

Crea `.env` en la raiz del repo (copia de `.env.example`):

```bash
cp .env.example .env
# Edita .env con los valores reales
```

El archivo `.env` se carga automaticamente al importar cualquier modulo de `src.shared`.
Los extractores y el orquestador lo leen sin configuracion adicional.

**Prioridad:** variables ya definidas en el entorno del sistema tienen prioridad sobre `.env`.

---

## Variables requeridas por fuente

| Fuente    | Variable         | Descripcion                          | Obligatoria   |
|-----------|-----------------|--------------------------------------|---------------|
| facebook  | `SERPER_API_KEY` | Busqueda de URLs via Serper.dev       | Si (fase 1)   |
| facebook  | `APIFY_TOKEN`    | Descarga de comentarios via Apify     | Si (fase 2)   |
| youtube   | `YOUTUBE_API_KEY`| YouTube Data API v3                  | Si            |
| twitter   | *(ninguna)*      | Usa x_state.json (ver abajo)         | —             |
| medios    | *(ninguna)*      | Google News RSS gratuito             | —             |

---

## Por que ya no pedira las keys todo el tiempo

Antes de esta intervencion:
- `SERPER_API_KEY` estaba hardcodeada en el codigo del extractor de Facebook.
- `YOUTUBE_API_KEY` estaba hardcodeada en el extractor de YouTube.
- `APIFY_TOKEN` se pedia interactivamente via `getpass` si no estaba en el entorno.

Despues de esta intervencion:
- Todas las keys se leen del entorno (via `.env` o variables de sistema).
- El `.env` se carga una sola vez al importar `src.shared.secrets`.
- Los extractores ya no tienen ninguna key embebida en el codigo.
- El orquestador valida via preflight que todas esten disponibles antes de correr.

---

## Twitter/X: state persistente (x_state.json)

### Que es

`x_state.json` es un archivo de sesion de Playwright: contiene las cookies de autenticacion
de una sesion activa de Twitter/X. El extractor lo usa para navegar como usuario autenticado
sin necesidad de hacer login en cada corrida.

### Donde vive

```
artifacts/state/x_state.json
```

Este path esta centralizado en `src/shared/runtime_paths.py` como `TWITTER_STATE_PATH`.
El archivo esta **gitignoreado** via `artifacts/state/*.json` y nunca debe versionarse.

### Como se inicializa (primera vez)

El state NO se genera automaticamente. Debes generarlo manualmente una vez:

**Opcion A — Script de Playwright interactivo** (recomendado):

```python
# Ejecuta esto una sola vez para capturar la sesion activa
from playwright.sync_api import sync_playwright
import json

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

**Opcion B — Desde sesion existente:**

Si ya tienes `x_state.json` en otro proyecto de Tampico, copialo:

```bash
cp /ruta/al/proyecto/anterior/state/x_state.json artifacts/state/x_state.json
```

### Como se reutiliza

Automaticamente. El extractor de Twitter lee `artifacts/state/x_state.json` al iniciar.
No se vuelve a pedir login mientras el state sea valido.

### Cuando se necesita refrescar

El state expira cuando:
- Las cookies de Twitter caducan (normalmente meses).
- La sesion es cerrada desde otra parte.
- Twitter invalida la sesion (IP diferente, cambio de contrasena, etc.).

Para refrescar, repite el proceso de inicializacion (Opcion A) y sobreescribe el archivo.

### Si el state esta roto

El extractor fallara con un mensaje claro. El preflight del orquestador tambien lo detectara:

```
✗ TWITTER
     ✗ x_state.json [NO EXISTE]
     ✗ Falta x_state.json en artifacts/state/x_state.json.
```

---

## Verificacion de configuracion

Antes de correr el pipeline, verifica que todo este listo:

```bash
# Verificar todas las fuentes
conda run -n RadaR_3_11 python -m src.shared.check_config

# Verificar solo algunas fuentes
conda run -n RadaR_3_11 python -m src.shared.check_config --sources facebook twitter

# Ejemplo de salida exitosa:
# ✓  .env: /repo/.env [encontrado]
#
#   ✓  FACEBOOK
#        ✓  SERPER_API_KEY [disponible]
#        ✓  APIFY_TOKEN [disponible]
#
#   ✓  TWITTER
#        ✓  x_state.json (artifacts/state/x_state.json) [2048 bytes]
#
#   ✓  YOUTUBE
#        ✓  YOUTUBE_API_KEY [disponible]
#
#   ✓  MEDIOS
#        (sin requisitos de credenciales)
#
# ✓  Todo listo para correr el pipeline.
```

---

## Que pasa si falta una key

**Al correr el pipeline:**

El preflight se ejecuta automaticamente como primera etapa y reporta:

```
✗  YOUTUBE
     ✗  YOUTUBE_API_KEY [FALTANTE]
     ✗  Variable de entorno faltante: YOUTUBE_API_KEY. Agrega 'YOUTUBE_API_KEY=tu_valor' en .env.
```

Con `--fail-fast` (default): el pipeline se detiene antes de intentar extraer.
Con `--allow-partial`: las fuentes sin credenciales se excluyen y el pipeline continua con las demas.

**Al correr un extractor individualmente:**

```
ValueError: Variable de entorno requerida no encontrada: YOUTUBE_API_KEY
(requerido por youtube_extractor). Configura 'YOUTUBE_API_KEY=tu_valor' en .env ...
```

---

## Como correr el pipeline

```bash
# Pipeline completo para la semana 15 de 2026
conda run -n RadaR_3_11 python -m src.operations.run_radar_pipeline \
  --week 2026-W15 \
  --mode controlled

# Solo extraccion + preprocessing
conda run -n RadaR_3_11 python -m src.operations.run_radar_pipeline \
  --week 2026-W15 \
  --mode controlled \
  --from-stage preflight \
  --to-stage preprocessing

# Dry-run (planifica sin ejecutar)
conda run -n RadaR_3_11 python -m src.operations.run_radar_pipeline \
  --week 2026-W15 \
  --mode controlled \
  --dry-run

# Con partial: continua aunque falte una fuente
conda run -n RadaR_3_11 python -m src.operations.run_radar_pipeline \
  --week 2026-W15 \
  --mode controlled \
  --allow-partial

# Reanudar una corrida previa
conda run -n RadaR_3_11 python -m src.operations.run_radar_pipeline \
  --resume-run-id radar_2026W15_001
```

---

## Estructura de archivos relevantes

```
.env                                        <- Tus credenciales reales (gitignoreado)
.env.example                                <- Plantilla para crear .env
artifacts/state/x_state.json               <- State de Twitter/X (gitignoreado)
artifacts/state/x_state.example.json       <- Ejemplo de estructura (versionado)
src/shared/secrets.py                       <- Loader de .env + validacion de secretos
src/shared/runtime_paths.py                 <- Rutas canonicas de runtime
src/shared/check_config.py                  <- Checker standalone
src/operations/stages/preflight_stage.py    <- Etapa de preflight en el pipeline
```
