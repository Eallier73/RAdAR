from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from config import CLASS_LABELS_3, CLASS_LABELS_5, CURRENT_TARGET_COLUMN, DATE_COLUMN, FEATURE_MODE_ALL
from classification_targets import ID_TO_CLASS_5, collapse_class_5_to_3
from evaluation import resolve_feature_mode


CLASSIFICATION_COMPONENT_WEIGHTS = {
    "recall_baja_fuerte": 0.35,
    "confusion_sube_fuerte_estabilidad": 0.20,
    "balanced_accuracy_5clases": 0.25,
    "macro_f1_3clases": 0.20,
}


def safe_binary_metric(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    positives: set[str],
    metric_name: str,
) -> float:
    y_true_bin = np.array([1 if label in positives else 0 for label in y_true], dtype=int)
    y_pred_bin = np.array([1 if label in positives else 0 for label in y_pred], dtype=int)
    if metric_name == "recall":
        return float(recall_score(y_true_bin, y_pred_bin, zero_division=0))
    if metric_name == "precision":
        return float(precision_score(y_true_bin, y_pred_bin, zero_division=0))
    raise ValueError(f"Metrica binaria no soportada: {metric_name}")


def compute_classification_metrics(predictions: pd.DataFrame) -> dict[str, Any]:
    if predictions.empty:
        raise ValueError("No hay predicciones para calcular metricas de clasificacion.")

    y_true_ids = predictions["y_true"].to_numpy(dtype=int)
    y_pred_ids = predictions["y_pred"].to_numpy(dtype=int)
    y_true = predictions["y_true_label"].astype(str).to_numpy()
    y_pred = predictions["y_pred_label"].astype(str).to_numpy()

    confusion_5 = confusion_matrix(y_true, y_pred, labels=list(CLASS_LABELS_5))
    soporte_5 = {label: int((y_true == label).sum()) for label in CLASS_LABELS_5}
    accuracy_5 = float(accuracy_score(y_true, y_pred))
    balanced_accuracy_5 = float(balanced_accuracy_score(y_true, y_pred))
    macro_f1_5 = float(f1_score(y_true, y_pred, labels=list(CLASS_LABELS_5), average="macro", zero_division=0))
    weighted_f1_5 = float(
        f1_score(y_true, y_pred, labels=list(CLASS_LABELS_5), average="weighted", zero_division=0)
    )
    recall_baja_fuerte = float(
        recall_score(
            y_true,
            y_pred,
            labels=["baja_fuerte"],
            average="macro",
            zero_division=0,
        )
    )
    precision_baja_fuerte = float(
        precision_score(
            y_true,
            y_pred,
            labels=["baja_fuerte"],
            average="macro",
            zero_division=0,
        )
    )
    recall_sube_fuerte = float(
        recall_score(
            y_true,
            y_pred,
            labels=["sube_fuerte"],
            average="macro",
            zero_division=0,
        )
    )
    recall_baja_total = safe_binary_metric(
        y_true,
        y_pred,
        positives={"baja_fuerte", "baja_moderada"},
        metric_name="recall",
    )
    recall_sube_total = safe_binary_metric(
        y_true,
        y_pred,
        positives={"sube_fuerte", "sube_moderada"},
        metric_name="recall",
    )

    y_true_3 = np.array([collapse_class_5_to_3(label) for label in y_true], dtype=object)
    y_pred_3 = np.array([collapse_class_5_to_3(label) for label in y_pred], dtype=object)
    accuracy_3 = float(accuracy_score(y_true_3, y_pred_3))
    balanced_accuracy_3 = float(balanced_accuracy_score(y_true_3, y_pred_3))
    macro_f1_3 = float(f1_score(y_true_3, y_pred_3, labels=list(CLASS_LABELS_3), average="macro", zero_division=0))

    true_sube_fuerte = y_true == "sube_fuerte"
    if true_sube_fuerte.any():
        confusion_sube_fuerte_estabilidad = float(np.mean(y_pred[true_sube_fuerte] == "se_mantiene"))
    else:
        confusion_sube_fuerte_estabilidad = 0.0

    l_recall_baja_fuerte = 1.0 - recall_baja_fuerte
    l_confusion_sube_fuerte_estabilidad = confusion_sube_fuerte_estabilidad
    l_balance_general = 1.0 - balanced_accuracy_5
    l_macro_f1_3 = 1.0 - macro_f1_3
    loss_clasificacion_bruta = (
        CLASSIFICATION_COMPONENT_WEIGHTS["recall_baja_fuerte"] * l_recall_baja_fuerte
        + CLASSIFICATION_COMPONENT_WEIGHTS["confusion_sube_fuerte_estabilidad"]
        * l_confusion_sube_fuerte_estabilidad
        + CLASSIFICATION_COMPONENT_WEIGHTS["balanced_accuracy_5clases"] * l_balance_general
        + CLASSIFICATION_COMPONENT_WEIGHTS["macro_f1_3clases"] * l_macro_f1_3
    )

    return {
        "accuracy_5clases": accuracy_5,
        "balanced_accuracy_5clases": balanced_accuracy_5,
        "macro_f1_5clases": macro_f1_5,
        "weighted_f1_5clases": weighted_f1_5,
        "recall_baja_fuerte": recall_baja_fuerte,
        "recall_baja_total": recall_baja_total,
        "precision_baja_fuerte": precision_baja_fuerte,
        "recall_sube_fuerte": recall_sube_fuerte,
        "recall_sube_total": recall_sube_total,
        "accuracy_3clases": accuracy_3,
        "macro_f1_3clases": macro_f1_3,
        "balanced_accuracy_3clases": balanced_accuracy_3,
        "l_clf_baja_fuerte": l_recall_baja_fuerte,
        "l_clf_sube_fuerte_vs_estabilidad": l_confusion_sube_fuerte_estabilidad,
        "l_clf_balance_general": l_balance_general,
        "l_clf_macro_f1_3clases": l_macro_f1_3,
        "loss_clasificacion_bruta": float(loss_clasificacion_bruta),
        "matriz_confusion_5clases": confusion_5.tolist(),
        "soporte_por_clase": soporte_5,
        "class_labels_5": list(CLASS_LABELS_5),
        "class_labels_3": list(CLASS_LABELS_3),
    }


def compute_classification_loss_h(
    *,
    metrics: dict[str, Any],
    horizon: int,
    reference_values: dict[str, Any],
) -> float:
    w_h = float(reference_values["horizon_weights"][int(horizon)])
    return float(w_h * float(metrics["loss_clasificacion_bruta"]))


def compute_total_classification_loss(
    *,
    horizon_results: list[dict[str, Any]],
) -> dict[str, float | None]:
    per_horizon = [float(item["loss_h"]) for item in horizon_results if item.get("loss_h") is not None]
    total = float(sum(per_horizon)) if per_horizon else None
    return {
        "sum_weighted_loss_h": total,
        "l_total_clasificacion": total,
        "avg_accuracy_5clases": _safe_average(horizon_results, "accuracy_5clases"),
        "avg_balanced_accuracy_5clases": _safe_average(horizon_results, "balanced_accuracy_5clases"),
        "avg_macro_f1_5clases": _safe_average(horizon_results, "macro_f1_5clases"),
        "avg_weighted_f1_5clases": _safe_average(horizon_results, "weighted_f1_5clases"),
        "avg_recall_baja_fuerte": _safe_average(horizon_results, "recall_baja_fuerte"),
        "avg_recall_baja_total": _safe_average(horizon_results, "recall_baja_total"),
        "avg_precision_baja_fuerte": _safe_average(horizon_results, "precision_baja_fuerte"),
        "avg_recall_sube_fuerte": _safe_average(horizon_results, "recall_sube_fuerte"),
        "avg_recall_sube_total": _safe_average(horizon_results, "recall_sube_total"),
        "avg_accuracy_3clases": _safe_average(horizon_results, "accuracy_3clases"),
        "avg_macro_f1_3clases": _safe_average(horizon_results, "macro_f1_3clases"),
        "avg_balanced_accuracy_3clases": _safe_average(horizon_results, "balanced_accuracy_3clases"),
    }


def _safe_average(horizon_results: list[dict[str, Any]], metric_name: str) -> float | None:
    values = [float(item[metric_name]) for item in horizon_results if item.get(metric_name) is not None]
    if not values:
        return None
    return float(sum(values) / len(values))


def walk_forward_predict_classifier(
    estimator,
    *,
    data: pd.DataFrame,
    feature_columns: list[str],
    class_label_column: str,
    class_id_column: str,
    class_3_label_column: str,
    delta_column: str,
    initial_train_size: int,
    feature_mode: str = FEATURE_MODE_ALL,
    always_include_columns: list[str] | None = None,
) -> pd.DataFrame:
    if len(data) <= initial_train_size:
        raise ValueError(
            f"No hay suficientes filas para walk-forward. Filas={len(data)}, "
            f"initial_train_size={initial_train_size}."
        )

    include_columns = always_include_columns or []
    predictions: list[dict[str, Any]] = []

    for test_idx in range(initial_train_size, len(data)):
        train = data.iloc[:test_idx]
        test = data.iloc[[test_idx]]
        selected_features = resolve_feature_mode(
            train_data=train,
            feature_columns=feature_columns,
            target_column=delta_column,
            feature_mode=feature_mode,
        )
        input_columns = [*include_columns, *selected_features]
        fitted = clone(estimator)
        fitted.fit(train[input_columns], train[class_id_column])

        predicted_id = int(np.asarray(fitted.predict(test[input_columns]), dtype=int)[0])
        if hasattr(fitted, "predict_proba"):
            probas = np.asarray(fitted.predict_proba(test[input_columns]), dtype=float)[0]
        else:
            probas = np.full(len(CLASS_LABELS_5), np.nan, dtype=float)

        row: dict[str, Any] = {
            DATE_COLUMN: test[DATE_COLUMN].iloc[0],
            "y_current": float(test[CURRENT_TARGET_COLUMN].iloc[0]),
            "y_true_level": float(test[CURRENT_TARGET_COLUMN].iloc[0] + test[delta_column].iloc[0]),
            "y_true_delta": float(test[delta_column].iloc[0]),
            "y_true": int(test[class_id_column].iloc[0]),
            "y_pred": predicted_id,
            "y_true_label": str(test[class_label_column].iloc[0]),
            "y_pred_label": ID_TO_CLASS_5[predicted_id],
            "y_true_label_3clases": str(test[class_3_label_column].iloc[0]),
            "y_pred_label_3clases": collapse_class_5_to_3(ID_TO_CLASS_5[predicted_id]),
            "selected_feature_count": len(selected_features),
            "selected_features": ",".join(selected_features),
        }
        for class_index, class_label in enumerate(CLASS_LABELS_5):
            probability = float(probas[class_index]) if class_index < len(probas) and not np.isnan(probas[class_index]) else None
            row[f"proba_{class_label}"] = probability
        predictions.append(row)

    return pd.DataFrame(predictions)
