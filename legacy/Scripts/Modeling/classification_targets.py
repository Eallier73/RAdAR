from __future__ import annotations

from typing import Any

import pandas as pd

from config import (
    CLASS_CHANGE_THRESHOLDS,
    CLASS_LABELS_5,
    CURRENT_TARGET_COLUMN,
    DATE_COLUMN,
    DEFAULT_LAGS,
    TARGET_COLUMNS,
    TARGET_MODE_CLF_BANDAS_5CLASES,
)
from feature_engineering import build_lagged_dataset


CLASS_TO_ID_5 = {label: index for index, label in enumerate(CLASS_LABELS_5)}
ID_TO_CLASS_5 = {index: label for label, index in CLASS_TO_ID_5.items()}
CLASS_TO_ID_3 = {"baja": 0, "se_mantiene": 1, "sube": 2}
ID_TO_CLASS_3 = {index: label for label, index in CLASS_TO_ID_3.items()}


def classify_future_delta(delta_value: float) -> str:
    if delta_value <= CLASS_CHANGE_THRESHOLDS["baja_fuerte_max"]:
        return "baja_fuerte"
    if delta_value <= CLASS_CHANGE_THRESHOLDS["baja_moderada_max"]:
        return "baja_moderada"
    if delta_value < CLASS_CHANGE_THRESHOLDS["sube_moderada_min"]:
        return "se_mantiene"
    if delta_value < CLASS_CHANGE_THRESHOLDS["sube_fuerte_min"]:
        return "sube_moderada"
    return "sube_fuerte"


def collapse_class_5_to_3(class_label: str) -> str:
    if class_label in {"baja_fuerte", "baja_moderada"}:
        return "baja"
    if class_label == "se_mantiene":
        return "se_mantiene"
    return "sube"


def build_classification_target_columns(
    df: pd.DataFrame,
    *,
    horizon: int,
    target_mode_clf: str = TARGET_MODE_CLF_BANDAS_5CLASES,
) -> tuple[pd.DataFrame, dict[str, str]]:
    if target_mode_clf != TARGET_MODE_CLF_BANDAS_5CLASES:
        raise ValueError(f"target_mode_clf no soportado: {target_mode_clf}")

    target_level_column = TARGET_COLUMNS[horizon]
    delta_column = f"delta_objetivo_h{horizon}"
    class_label_column = f"target_clase_h{horizon}"
    class_id_column = f"{class_label_column}_id"
    class_3_label_column = f"{class_label_column}_3clases"
    class_3_id_column = f"{class_3_label_column}_id"

    out = df.copy()
    out[delta_column] = out[target_level_column] - out[CURRENT_TARGET_COLUMN]
    out[class_label_column] = out[delta_column].map(classify_future_delta)
    out[class_id_column] = out[class_label_column].map(CLASS_TO_ID_5)
    out[class_3_label_column] = out[class_label_column].map(collapse_class_5_to_3)
    out[class_3_id_column] = out[class_3_label_column].map(CLASS_TO_ID_3)

    columns = {
        "target_level_column": target_level_column,
        "delta_column": delta_column,
        "class_label_column": class_label_column,
        "class_id_column": class_id_column,
        "class_3_label_column": class_3_label_column,
        "class_3_id_column": class_3_id_column,
    }
    return out, columns


def build_classification_model_frame(
    df: pd.DataFrame,
    *,
    horizon: int,
    feature_columns: list[str],
    lags: tuple[int, ...] = DEFAULT_LAGS,
    target_mode_clf: str = TARGET_MODE_CLF_BANDAS_5CLASES,
) -> tuple[pd.DataFrame, list[str], dict[str, str]]:
    with_targets, target_columns = build_classification_target_columns(
        df=df,
        horizon=horizon,
        target_mode_clf=target_mode_clf,
    )
    lagged = build_lagged_dataset(df=with_targets, feature_columns=feature_columns, lags=lags)

    lagged_feature_columns = []
    for column in [CURRENT_TARGET_COLUMN, *feature_columns]:
        for lag in lags:
            lagged_feature_columns.append(f"{column}_lag{lag}")

    modeling_columns = [
        DATE_COLUMN,
        CURRENT_TARGET_COLUMN,
        target_columns["target_level_column"],
        target_columns["delta_column"],
        target_columns["class_label_column"],
        target_columns["class_id_column"],
        target_columns["class_3_label_column"],
        target_columns["class_3_id_column"],
        *feature_columns,
        *lagged_feature_columns,
    ]

    modeling_df = lagged[modeling_columns].dropna().reset_index(drop=True)
    modeling_df[target_columns["class_id_column"]] = modeling_df[target_columns["class_id_column"]].astype(int)
    modeling_df[target_columns["class_3_id_column"]] = modeling_df[target_columns["class_3_id_column"]].astype(int)
    return modeling_df, [*feature_columns, *lagged_feature_columns], target_columns


def serialize_classification_target_metadata(
    *,
    horizon: int,
    target_mode_clf: str,
) -> dict[str, Any]:
    return {
        "target_mode_clf": target_mode_clf,
        "horizonte": horizon,
        "delta_definition": "delta_objetivo_h = y_{t+h} - y_t",
        "taxonomy_5_classes": {
            "baja_fuerte": "cambio <= -3.0",
            "baja_moderada": "-3.0 < cambio <= -1.5",
            "se_mantiene": "-1.5 < cambio < 1.5",
            "sube_moderada": "1.5 <= cambio < 3.0",
            "sube_fuerte": "cambio >= 3.0",
        },
        "class_to_id_5": CLASS_TO_ID_5,
        "class_to_id_3": CLASS_TO_ID_3,
    }
