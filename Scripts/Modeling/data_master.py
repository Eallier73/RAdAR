from __future__ import annotations

from pathlib import Path

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


def load_master_dataset(
    dataset_path: Path = DATASET_PATH,
    sheet_name: str = DEFAULT_SHEET_NAME,
) -> pd.DataFrame:
    df = pd.read_excel(dataset_path, sheet_name=sheet_name)
    df = df.dropna(axis=1, how="all").copy()
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

    return df


def get_base_feature_columns(df: pd.DataFrame) -> list[str]:
    return [column for column in BASE_FEATURE_COLUMNS if column in df.columns]
