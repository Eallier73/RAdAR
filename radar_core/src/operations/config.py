from __future__ import annotations

import os
import sys
from pathlib import Path

# Carga .env antes de resolver rutas de entornos Python
from src.shared.secrets import load_env as _load_env  # noqa: E402
_load_env()

ROOT_DIR = Path(__file__).resolve().parents[2]

RAW_WEEKLY_ROOT = ROOT_DIR / "data" / "raw" / "radar_weekly_flat"
TEXT_WEEKLY_ROOT = ROOT_DIR / "data" / "text" / "radar_weekly_flat"
PROCESSED_MODELING_ROOT = ROOT_DIR / "data" / "processed" / "modeling"
OPERATIONS_ARTIFACTS_ROOT = ROOT_DIR / "artifacts" / "operations"
PREPROCESSING_REPORT_PATH = ROOT_DIR / "artifacts" / "logs" / "preprocessing" / "reporte_semanas_incompletas.txt"
FACEBOOK_EXTRACTION_ARTIFACTS_ROOT = ROOT_DIR / "artifacts" / "runs" / "extraction" / "facebook"

STAGE_NAMES = (
    "preflight",
    "extraction",
    "preprocessing",
    "nlp",
    "modeling",
)

SOURCE_NAMES = ("facebook", "twitter", "youtube", "medios")
DEFAULT_SOURCES = SOURCE_NAMES
ALLOWED_MODES = ("controlled", "experimental")

PIPELINE_LOG_FILENAME = "pipeline.log"
DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_FAIL_FAST = True
DEFAULT_ALLOW_PARTIAL = False

STAGE_STATUS_VALUES = (
    "planned",
    "running",
    "success",
    "partial_success",
    "failed",
    "skipped",
    "stubbed",
)
TERMINAL_STAGE_STATUSES = frozenset({"success", "partial_success", "failed", "skipped", "stubbed"})
SUCCESS_LIKE_STAGE_STATUSES = frozenset({"success", "partial_success", "skipped", "stubbed"})

DEFAULT_MODEL_DATASET = PROCESSED_MODELING_ROOT / "datos_ml_master_indice_aceptacion_digital.xlsx"

# ── Python ejecutable por etapa ───────────────────────────────────────────────
#
# Se resuelve así (en orden):
#   1. Variable de entorno RADAR_OPS_PYTHON
#   2. sys.executable (entorno activo al lanzar el orquestador)
#
_OPS_PYTHON: str = os.environ.get("RADAR_OPS_PYTHON") or sys.executable

OPS_PYTHON: str = _OPS_PYTHON

STAGE_PYTHON: dict[str, str] = {
    "preflight":     _OPS_PYTHON,
    "extraction":    _OPS_PYTHON,
    "preprocessing": _OPS_PYTHON,
    "nlp":           _OPS_PYTHON,
    "modeling":      _OPS_PYTHON,
}
