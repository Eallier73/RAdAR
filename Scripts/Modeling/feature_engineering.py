from __future__ import annotations

import pandas as pd
import sys
from pathlib import Path

from config import (
    CURRENT_TARGET_COLUMN,
    DATE_COLUMN,
    DEFAULT_LAGS,
    TARGET_COLUMNS,
    TARGET_MODE_DELTA,
    TARGET_MODE_LEVEL,
)

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from common_runtime_logging import log_event


def build_lagged_dataset(
    df: pd.DataFrame,
    feature_columns: list[str],
    lags: tuple[int, ...] = DEFAULT_LAGS,
) -> pd.DataFrame:
    out = df.copy()
    lag_source_columns = [CURRENT_TARGET_COLUMN, *feature_columns]

    for column in lag_source_columns:
        for lag in lags:
            out[f"{column}_lag{lag}"] = out[column].shift(lag)

    return out


def build_model_frame(
    df: pd.DataFrame,
    horizon: int,
    feature_columns: list[str],
    lags: tuple[int, ...] = DEFAULT_LAGS,
    target_mode: str = TARGET_MODE_LEVEL,
) -> tuple[pd.DataFrame, list[str], str]:
    target_level_column = TARGET_COLUMNS[horizon]
    lagged = build_lagged_dataset(df=df, feature_columns=feature_columns, lags=lags)

    if target_mode == TARGET_MODE_DELTA:
        target_column = f"{target_level_column}_delta"
        lagged[target_column] = lagged[target_level_column] - lagged[CURRENT_TARGET_COLUMN]
    else:
        target_column = target_level_column

    lagged_feature_columns = []
    for column in [CURRENT_TARGET_COLUMN, *feature_columns]:
        for lag in lags:
            lagged_feature_columns.append(f"{column}_lag{lag}")

    modeling_columns = [
        DATE_COLUMN,
        CURRENT_TARGET_COLUMN,
        target_level_column,
        *feature_columns,
        *lagged_feature_columns,
    ]
    if target_column not in modeling_columns:
        modeling_columns.append(target_column)

    rows_before_dropna = len(lagged)
    modeling_df = lagged[modeling_columns].dropna().reset_index(drop=True)
    log_event(
        "feature_engineering",
        "INFO",
        "Model frame construido",
        horizon=horizon,
        target_mode=target_mode,
        feature_count=len(feature_columns),
        lag_count=len(lags),
        rows_before_dropna=rows_before_dropna,
        rows_after_dropna=len(modeling_df),
        rows_removed=rows_before_dropna - len(modeling_df),
    )
    return modeling_df, [*feature_columns, *lagged_feature_columns], target_column
