from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT_DIR / "data" / "processed" / "modeling" / "datos_ML_master_indice_aceptación_digital.xlsx"
DEFAULT_SHEET_NAME = "Sheet1"

DATE_COLUMN = "fecha_inicio_semana"
WEEK_COLUMN = "semana_iso"
CURRENT_TARGET_COLUMN = "y_t_aceptacion_digital"
TARGET_COLUMNS = {
    1: "target_1w_aceptacion_digital",
    2: "target_2w_aceptacion_digital",
    3: "target_3w_aceptacion_digital",
    4: "target_4w_aceptacion_digital",
}

BASE_FEATURE_COLUMNS = [
    "sentimiento_medios",
    "v5_agua_neto",
    "v5_alumbrado_neto",
    "v5_americo_neto",
    "v5_basura_neto",
    "v5_corrupcion_neto",
    "v5_delitos_neto",
    "v5_morena_neto",
    "v5_obras_neto",
    "v5_prevencion_neto",
    "v5_vialidad_neto",
]

DEFAULT_LAGS = (1, 2, 3, 4)
DEFAULT_HORIZONS = (1, 2, 3, 4)
DEFAULT_INITIAL_TRAIN_SIZE = 40
ABS_ERROR_TOLERANCE = 0.05
FALL_THRESHOLD = 0.0
DEFAULT_RANDOM_STATE = 42

TARGET_MODE_LEVEL = "nivel"
TARGET_MODE_DELTA = "delta"
TARGET_MODE_CHOICES = (
    TARGET_MODE_LEVEL,
    TARGET_MODE_DELTA,
)

TARGET_MODE_CLF_BANDAS_5CLASES = "bandas_5clases"
TARGET_MODE_CLF_CHOICES = (TARGET_MODE_CLF_BANDAS_5CLASES,)

CLASS_LABELS_5 = (
    "baja_fuerte",
    "baja_moderada",
    "se_mantiene",
    "sube_moderada",
    "sube_fuerte",
)

CLASS_LABELS_3 = (
    "baja",
    "se_mantiene",
    "sube",
)

CLASS_CHANGE_THRESHOLDS = {
    "baja_fuerte_max": -3.0,
    "baja_moderada_max": -1.5,
    "sube_moderada_min": 1.5,
    "sube_fuerte_min": 3.0,
}

FEATURE_MODE_ALL = "all"
FEATURE_MODE_CORR = "corr"
FEATURE_MODE_LASSO = "lasso"
FEATURE_MODE_CHOICES = (
    FEATURE_MODE_ALL,
    FEATURE_MODE_CORR,
    FEATURE_MODE_LASSO,
)

TRANSFORM_MODE_NONE = "none"
TRANSFORM_MODE_STANDARD = "standard"
TRANSFORM_MODE_ROBUST = "robust"
TRANSFORM_MODE_WINSOR = "winsor"
TRANSFORM_MODE_CHOICES = (
    TRANSFORM_MODE_NONE,
    TRANSFORM_MODE_STANDARD,
    TRANSFORM_MODE_ROBUST,
    TRANSFORM_MODE_WINSOR,
)
