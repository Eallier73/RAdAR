"""
Rutas canonicas de runtime para el proyecto RAdAR.

Centraliza los paths de archivos persistentes y de estado.
No contiene logica, solo constantes derivadas de REPO_ROOT.

Reutilizable por extractores y orquestador para referenciar
archivos de state, cache y configuracion sin hardcodear rutas.
"""
from __future__ import annotations

from pathlib import Path

# ── Raiz del repositorio ────────────────────────────────────────────────────
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

# ── Configuracion ───────────────────────────────────────────────────────────
DOT_ENV_PATH: Path = REPO_ROOT / ".env"

# ── State persistente ───────────────────────────────────────────────────────
STATE_DIR: Path = REPO_ROOT / "artifacts" / "state"

# State de sesion Playwright para Twitter/X.
# Generado manualmente via login (ver docs/operations/secrets_and_runtime.md).
# NUNCA se versiona. Gitignoreado via artifacts/state/*.json.
TWITTER_STATE_PATH: Path = STATE_DIR / "x_state.json"

# ── Cache ───────────────────────────────────────────────────────────────────
CACHE_DIR: Path = REPO_ROOT / "artifacts" / "cache"
MEDIOS_RSS_CACHE_DIR: Path = CACHE_DIR / "extraction" / "medios_rss"

# ── Logs ────────────────────────────────────────────────────────────────────
LOGS_DIR: Path = REPO_ROOT / "artifacts" / "logs"
LOGS_PREPROCESSING_DIR: Path = LOGS_DIR / "preprocessing"

# ── Datos canonicos ─────────────────────────────────────────────────────────
RAW_WEEKLY_ROOT: Path = REPO_ROOT / "data" / "raw" / "radar_weekly_flat"
TEXT_WEEKLY_ROOT: Path = REPO_ROOT / "data" / "text" / "radar_weekly_flat"
