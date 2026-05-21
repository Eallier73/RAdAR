from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

from config import (
    BASE_FEATURE_COLUMNS,
    CURRENT_TARGET_COLUMN,
    DATASET_PATH,
    DATE_COLUMN,
    DEFAULT_SHEET_NAME,
    TARGET_COLUMNS,
    WEEK_COLUMN,
)

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from common_runtime_logging import log_event


def load_master_dataset(
    dataset_path: Path = DATASET_PATH,
    sheet_name: str = DEFAULT_SHEET_NAME,
) -> pd.DataFrame:
    df = pd.read_excel(dataset_path, sheet_name=sheet_name)
    rows_loaded, cols_loaded = df.shape
    df = df.dropna(axis=1, how="all").copy()
    rows_after_dropna, cols_after_dropna = df.shape
    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])
    df = df.sort_values(DATE_COLUMN, kind="stable").reset_index(drop=True)

    required_columns = {
        DATE_COLUMN,
        WEEK_COLUMN,
        CURRENT_TARGET_COLUMN,
        *TARGET_COLUMNS.values(),
        *BASE_FEATURE_COLUMNS,
    }
    missing = sorted(required_columns.difference(df.columns))
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el dataset maestro: {missing}")

    log_event(
        "data_master",
        "INFO",
        "Dataset maestro cargado y validado",
        dataset_path=dataset_path,
        sheet_name=sheet_name,
        rows_loaded=rows_loaded,
        cols_loaded=cols_loaded,
        cols_after_dropna=cols_after_dropna,
        cols_removed_all_nan=cols_loaded - cols_after_dropna,
        rows_final=len(df),
    )

    return df


def get_base_feature_columns(df: pd.DataFrame) -> list[str]:
    return [column for column in BASE_FEATURE_COLUMNS if column in df.columns]
