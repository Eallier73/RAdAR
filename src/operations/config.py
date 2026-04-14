from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]

RAW_WEEKLY_ROOT = ROOT_DIR / "data" / "raw" / "radar_weekly_flat"
TEXT_WEEKLY_ROOT = ROOT_DIR / "data" / "text" / "radar_weekly_flat"
PROCESSED_MODELING_ROOT = ROOT_DIR / "data" / "processed" / "modeling"
OPERATIONS_ARTIFACTS_ROOT = ROOT_DIR / "artifacts" / "operations"
PREPROCESSING_REPORT_PATH = ROOT_DIR / "artifacts" / "logs" / "preprocessing" / "reporte_semanas_incompletas.txt"
FACEBOOK_EXTRACTION_ARTIFACTS_ROOT = ROOT_DIR / "artifacts" / "runs" / "extraction" / "facebook"
EXPERIMENTS_RUNS_DIR = ROOT_DIR / "experiments" / "runs"
EXPERIMENTS_WORKBOOK = ROOT_DIR / "experiments" / "audit" / "grid_experimentos_radar.xlsx"

STAGE_NAMES = (
    "extraction",
    "preprocessing",
    "nlp",
    "modeling",
    "export",
    "report",
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

PUBLISHED_DIRNAME = "published"
PUBLISHED_POWERBI_DIRNAME = "powerbi"
PUBLISHED_REPORT_INPUTS_DIRNAME = "report_inputs"
PUBLISHED_EXPERIMENTAL_DIRNAME = "experimental"

DEFAULT_MODEL_RUNNER = "src.modeling.runners.run_e10_meta_selector"
DEFAULT_MODEL_DATASET = PROCESSED_MODELING_ROOT / "datos_ml_master_indice_aceptacion_digital.xlsx"

DEFAULT_EXPORT_FILES = {
    "sentimiento_semanal": PROCESSED_MODELING_ROOT / "aceptacion_digital_redes_medios_sentimiento_semanal.xlsx",
    "encuestas_sentimiento_mensual": PROCESSED_MODELING_ROOT / "encuestas_y_sentimiento_mensual_unificado.xlsx",
    "datos_ml_0": PROCESSED_MODELING_ROOT / "datos_ml_0.xlsx",
    "datos_ml_master_indice_aceptacion_digital": DEFAULT_MODEL_DATASET,
}
