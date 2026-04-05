#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline

from config import (
    CURRENT_TARGET_COLUMN,
    DATASET_PATH,
    DATE_COLUMN,
    DEFAULT_SHEET_NAME,
    FEATURE_MODE_ALL,
    FEATURE_MODE_CHOICES,
    TARGET_COLUMNS,
    TARGET_MODE_CHOICES,
    TARGET_MODE_DELTA,
    TARGET_MODE_LEVEL,
    TRANSFORM_MODE_CHOICES,
    TRANSFORM_MODE_STANDARD,
)
from data_master import get_base_feature_columns, load_master_dataset
from evaluation import (
    compute_loss_h,
    compute_radar_metrics,
    compute_total_radar_loss,
    resolve_feature_mode,
    select_best_alpha_time_series,
)
from experiment_logger import DEFAULT_RUNS_DIR, DEFAULT_WORKBOOK, RadarExperimentTracker
from feature_engineering import build_lagged_dataset
from pipeline_common import (
    add_reference_comparison_args,
    build_comparison_payload,
    finalize_common_args,
    normalize_reference_run_ids,
    parse_string_sequence,
    save_reference_comparisons,
)
from preprocessing import build_feature_transformer, describe_transform_mode

DUAL_MODE_PARALLEL = "parallel"
DUAL_MODE_FALL_DETECTOR = "fall_detector"
DUAL_MODE_RESIDUAL = "residual_dual"
DUAL_MODE_CHOICES = (DUAL_MODE_PARALLEL, DUAL_MODE_FALL_DETECTOR, DUAL_MODE_RESIDUAL)

TARGET_MODE_CLS_DIRECTION = "direction_3clases"
TARGET_MODE_CLS_FALL = "fall_binary"
TARGET_MODE_CLS_CHOICES = (TARGET_MODE_CLS_DIRECTION, TARGET_MODE_CLS_FALL)

DIRECTION_LABELS = ("baja", "se_mantiene", "sube")
FALL_LABELS = ("cae", "no_cae")
DIRECTION_CLASS_TO_ID = {label: idx for idx, label in enumerate(DIRECTION_LABELS)}
FALL_CLASS_TO_ID = {label: idx for idx, label in enumerate(FALL_LABELS)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E11 | Arquitectura dual controlada: forecast numerico + lectura categórica.",
    )
    parser.add_argument("--run-id", default="E11_v1_clean", help="Run_ID a registrar en el grid.")
    add_reference_comparison_args(parser, default_reference_run_id="E1_v5_clean")
    parser.add_argument(
        "--dual-mode",
        choices=DUAL_MODE_CHOICES,
        required=True,
        help="Modo dual: parallel, fall_detector o residual_dual.",
    )
    parser.add_argument(
        "--target-mode-reg",
        choices=TARGET_MODE_CHOICES,
        default=TARGET_MODE_LEVEL,
        help="Modo de target del componente de regresion.",
    )
    parser.add_argument(
        "--target-mode-cls",
        choices=TARGET_MODE_CLS_CHOICES,
        default=TARGET_MODE_CLS_DIRECTION,
        help="Modo de target del componente categórico.",
    )
    parser.add_argument(
        "--lags",
        default="1,2,3,4,5,6",
        help="Lags separados por coma. Ejemplo: 1,2,3,4,5,6",
    )
    parser.add_argument(
        "--feature-mode",
        choices=FEATURE_MODE_CHOICES,
        default="corr",
        help="Modo de seleccion de features para componentes regresivo y categórico.",
    )
    parser.add_argument("--initial-train-size", type=int, default=40)
    parser.add_argument("--horizons", default="1,2,3,4")
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=DATASET_PATH,
    )
    parser.add_argument("--sheet-name", default=DEFAULT_SHEET_NAME)
    parser.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_WORKBOOK,
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=DEFAULT_RUNS_DIR,
    )

    parser.add_argument(
        "--transform-mode",
        choices=TRANSFORM_MODE_CHOICES,
        default=TRANSFORM_MODE_STANDARD,
    )
    parser.add_argument("--winsor-lower-quantile", type=float, default=0.05)
    parser.add_argument("--winsor-upper-quantile", type=float, default=0.95)
    parser.add_argument("--alpha-grid-min-exp", type=float, default=-4.0)
    parser.add_argument("--alpha-grid-max-exp", type=float, default=4.0)
    parser.add_argument("--alpha-grid-points", type=int, default=40)
    parser.add_argument("--inner-splits", type=int, default=3)
    parser.add_argument("--alpha-selection-metric", choices=("mae", "rmse"), default="mae")

    parser.add_argument("--classifier-c", type=float, default=1.0)
    parser.add_argument("--classifier-max-iter", type=int, default=5000)
    parser.add_argument("--classifier-class-weight", default="balanced")

    parser.add_argument(
        "--movement-threshold",
        type=float,
        default=0.5,
        help="Umbral absoluto ex ante para direction_3clases. |delta| < threshold => se_mantiene.",
    )
    parser.add_argument(
        "--fall-threshold-cls",
        type=float,
        default=0.0,
        help="Umbral absoluto ex ante para cae/no_cae. cae si delta <= -threshold.",
    )

    parser.add_argument("--residual-inner-splits", type=int, default=3)
    parser.add_argument("--residual-min-oof-rows", type=int, default=12)

    args = finalize_common_args(parser.parse_args())
    args.extra_reference_run_ids = parse_string_sequence(args.extra_reference_run_ids)
    if not 0.0 <= args.winsor_lower_quantile < args.winsor_upper_quantile <= 1.0:
        raise ValueError("Los cuantiles de winsor deben cumplir 0 <= lower < upper <= 1.")
    if args.inner_splits < 2:
        raise ValueError("--inner-splits debe ser al menos 2.")
    if args.residual_inner_splits < 2:
        raise ValueError("--residual-inner-splits debe ser al menos 2.")

    if args.dual_mode == DUAL_MODE_PARALLEL and args.target_mode_cls != TARGET_MODE_CLS_DIRECTION:
        raise ValueError("dual_mode=parallel requiere --target-mode-cls direction_3clases.")
    if args.dual_mode in {DUAL_MODE_FALL_DETECTOR, DUAL_MODE_RESIDUAL} and args.target_mode_cls != TARGET_MODE_CLS_FALL:
        raise ValueError("dual_mode fall_detector o residual_dual requiere --target-mode-cls fall_binary.")

    return args


def build_alpha_grid(args: argparse.Namespace) -> list[float]:
    return list(np.logspace(args.alpha_grid_min_exp, args.alpha_grid_max_exp, args.alpha_grid_points))


def build_ridge_estimator(alpha: float, args: argparse.Namespace) -> Pipeline:
    return Pipeline(
        steps=[
            (
                "transform",
                build_feature_transformer(
                    transform_mode=args.transform_mode,
                    winsor_lower_quantile=args.winsor_lower_quantile,
                    winsor_upper_quantile=args.winsor_upper_quantile,
                ),
            ),
            ("model", Ridge(alpha=float(alpha))),
        ]
    )


def build_classifier_estimator(args: argparse.Namespace) -> Pipeline:
    return Pipeline(
        steps=[
            (
                "transform",
                build_feature_transformer(
                    transform_mode=args.transform_mode,
                    winsor_lower_quantile=args.winsor_lower_quantile,
                    winsor_upper_quantile=args.winsor_upper_quantile,
                ),
            ),
            (
                "model",
                LogisticRegression(
                    C=float(args.classifier_c),
                    max_iter=int(args.classifier_max_iter),
                    class_weight=args.classifier_class_weight or None,
                    solver="lbfgs",
                ),
            ),
        ]
    )


def classify_direction(delta_value: float, threshold: float) -> str:
    if delta_value <= -abs(threshold):
        return "baja"
    if delta_value >= abs(threshold):
        return "sube"
    return "se_mantiene"


def classify_fall(delta_value: float, threshold: float) -> str:
    fall_cut = -abs(threshold)
    return "cae" if delta_value <= fall_cut else "no_cae"


def resolve_class_maps(target_mode_cls: str) -> tuple[tuple[str, ...], dict[str, int], dict[int, str]]:
    if target_mode_cls == TARGET_MODE_CLS_DIRECTION:
        labels = DIRECTION_LABELS
        class_to_id = DIRECTION_CLASS_TO_ID
    elif target_mode_cls == TARGET_MODE_CLS_FALL:
        labels = FALL_LABELS
        class_to_id = FALL_CLASS_TO_ID
    else:
        raise ValueError(f"target_mode_cls no soportado: {target_mode_cls}")
    id_to_class = {idx: label for label, idx in class_to_id.items()}
    return labels, class_to_id, id_to_class


def build_dual_model_frame(
    *,
    df: pd.DataFrame,
    horizon: int,
    feature_columns: list[str],
    lags: tuple[int, ...],
    target_mode_reg: str,
    target_mode_cls: str,
    movement_threshold: float,
    fall_threshold_cls: float,
) -> tuple[pd.DataFrame, list[str], dict[str, Any]]:
    target_level_column = TARGET_COLUMNS[horizon]
    lagged = build_lagged_dataset(df=df, feature_columns=feature_columns, lags=lags)

    delta_column = f"delta_objetivo_h{horizon}"
    lagged[delta_column] = lagged[target_level_column] - lagged[CURRENT_TARGET_COLUMN]

    if target_mode_reg == TARGET_MODE_DELTA:
        reg_target_column = f"{target_level_column}_delta_reg"
        lagged[reg_target_column] = lagged[delta_column]
    else:
        reg_target_column = target_level_column

    labels, class_to_id, _ = resolve_class_maps(target_mode_cls)
    class_label_column = f"target_cls_h{horizon}_{target_mode_cls}"
    class_id_column = f"{class_label_column}_id"

    if target_mode_cls == TARGET_MODE_CLS_DIRECTION:
        lagged[class_label_column] = lagged[delta_column].map(lambda value: classify_direction(float(value), movement_threshold))
    else:
        lagged[class_label_column] = lagged[delta_column].map(lambda value: classify_fall(float(value), fall_threshold_cls))
    lagged[class_id_column] = lagged[class_label_column].map(class_to_id)

    lagged_feature_columns = []
    for column in [CURRENT_TARGET_COLUMN, *feature_columns]:
        for lag in lags:
            lagged_feature_columns.append(f"{column}_lag{lag}")

    modeling_columns = [
        DATE_COLUMN,
        CURRENT_TARGET_COLUMN,
        target_level_column,
        delta_column,
        class_label_column,
        class_id_column,
        *feature_columns,
        *lagged_feature_columns,
    ]
    if reg_target_column not in modeling_columns:
        modeling_columns.append(reg_target_column)

    modeling_df = lagged[modeling_columns].dropna().reset_index(drop=True)
    modeling_df[class_id_column] = modeling_df[class_id_column].astype(int)
    metadata = {
        "target_level_column": target_level_column,
        "delta_column": delta_column,
        "reg_target_column": reg_target_column,
        "class_label_column": class_label_column,
        "class_id_column": class_id_column,
        "target_mode_reg": target_mode_reg,
        "target_mode_cls": target_mode_cls,
        "movement_threshold": float(movement_threshold),
        "fall_threshold_cls": float(fall_threshold_cls),
        "labels": list(labels),
        "class_to_id": class_to_id,
    }
    return modeling_df, [*feature_columns, *lagged_feature_columns], metadata


def summarize_alpha_trace(alpha_trace: list[dict[str, Any]]) -> dict[str, Any]:
    best_alphas = [float(item["best_alpha"]) for item in alpha_trace]
    return {
        "best_alpha_mean": float(np.mean(best_alphas)),
        "best_alpha_median": float(np.median(best_alphas)),
        "best_alpha_min": float(np.min(best_alphas)),
        "best_alpha_max": float(np.max(best_alphas)),
        "best_alphas_by_fold": alpha_trace,
    }


def fit_ridge_fold(
    *,
    train_data: pd.DataFrame,
    test_data: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    target_level_column: str,
    args: argparse.Namespace,
    alpha_grid: list[float],
    feature_mode: str,
) -> dict[str, Any]:
    tuning = select_best_alpha_time_series(
        train_data=train_data,
        feature_columns=feature_columns,
        target_column=target_column,
        estimator_builder=lambda alpha: build_ridge_estimator(alpha, args),
        alpha_grid=alpha_grid,
        feature_mode=feature_mode,
        target_mode=TARGET_MODE_LEVEL if target_column == target_level_column else TARGET_MODE_DELTA,
        actual_target_column=target_level_column,
        inner_splits=args.inner_splits,
        tuning_metric=args.alpha_selection_metric,
    )
    selected_features = resolve_feature_mode(
        train_data=train_data,
        feature_columns=feature_columns,
        target_column=target_column,
        feature_mode=feature_mode,
    )
    estimator = build_ridge_estimator(tuning["best_alpha"], args)
    estimator.fit(train_data[selected_features], train_data[target_column])
    model_prediction = float(estimator.predict(test_data[selected_features])[0])
    y_current = float(test_data[CURRENT_TARGET_COLUMN].iloc[0])
    if target_column == target_level_column:
        y_pred = model_prediction
    else:
        y_pred = y_current + model_prediction
    return {
        "model_prediction": model_prediction,
        "y_pred": float(y_pred),
        "selected_features": selected_features,
        "tuning": tuning,
        "estimator": estimator,
    }


def fit_classifier_fold(
    *,
    train_data: pd.DataFrame,
    test_data: pd.DataFrame,
    feature_columns: list[str],
    delta_column: str,
    class_label_column: str,
    class_id_column: str,
    labels: tuple[str, ...],
    args: argparse.Namespace,
    feature_mode: str,
) -> dict[str, Any]:
    selected_features = resolve_feature_mode(
        train_data=train_data,
        feature_columns=feature_columns,
        target_column=delta_column,
        feature_mode=feature_mode,
    )
    observed_class_ids = sorted(int(value) for value in train_data[class_id_column].unique())
    probabilities = {label: 0.0 for label in labels}

    if len(observed_class_ids) == 1:
        predicted_id = observed_class_ids[0]
        probabilities[labels[predicted_id]] = 1.0
    else:
        global_to_local = {global_id: local_id for local_id, global_id in enumerate(observed_class_ids)}
        local_to_global = {local_id: global_id for global_id, local_id in global_to_local.items()}
        y_train_local = train_data[class_id_column].map(global_to_local).astype(int)
        estimator = clone(build_classifier_estimator(args))
        estimator.fit(train_data[selected_features], y_train_local)
        predicted_local = int(np.asarray(estimator.predict(test_data[selected_features]), dtype=int)[0])
        predicted_id = int(local_to_global[predicted_local])
        if hasattr(estimator, "predict_proba"):
            local_probas = np.asarray(estimator.predict_proba(test_data[selected_features]), dtype=float)[0]
            for local_id, probability in enumerate(local_probas):
                global_id = int(local_to_global[int(local_id)])
                probabilities[labels[global_id]] = float(probability)

    return {
        "predicted_id": predicted_id,
        "predicted_label": labels[predicted_id],
        "true_id": int(test_data[class_id_column].iloc[0]),
        "true_label": str(test_data[class_label_column].iloc[0]),
        "selected_features": selected_features,
        "probabilities": probabilities,
        "train_class_ids": observed_class_ids,
        "train_class_labels": [labels[class_id] for class_id in observed_class_ids],
    }


def build_temporal_oof_residual_train(
    *,
    train_data: pd.DataFrame,
    feature_columns: list[str],
    reg_target_column: str,
    target_level_column: str,
    args: argparse.Namespace,
    alpha_grid: list[float],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    split_count = min(args.residual_inner_splits, len(train_data) - 1)
    min_train_size = max(args.residual_min_oof_rows, len(args.lags) + 4)
    if split_count < 2 or len(train_data) <= min_train_size:
        return pd.DataFrame(), {
            "split_count": split_count,
            "oof_rows": 0,
            "coverage_ratio": 0.0,
            "fallback_reason": "train_insuficiente_para_residual_oof",
        }

    splitter = []
    step = len(train_data)
    try:
        from sklearn.model_selection import TimeSeriesSplit

        splitter = list(TimeSeriesSplit(n_splits=split_count).split(train_data))
    except Exception:
        splitter = []
    oof_frames: list[pd.DataFrame] = []

    for fold_number, (inner_train_idx, inner_valid_idx) in enumerate(splitter, start=1):
        if len(inner_train_idx) < min_train_size:
            continue
        inner_train = train_data.iloc[inner_train_idx].copy()
        inner_valid = train_data.iloc[inner_valid_idx].copy()
        tuning = select_best_alpha_time_series(
            train_data=inner_train,
            feature_columns=feature_columns,
            target_column=reg_target_column,
            estimator_builder=lambda alpha: build_ridge_estimator(alpha, args),
            alpha_grid=alpha_grid,
            feature_mode=args.feature_mode,
            target_mode=TARGET_MODE_LEVEL if reg_target_column == target_level_column else TARGET_MODE_DELTA,
            actual_target_column=target_level_column,
            inner_splits=args.inner_splits,
            tuning_metric=args.alpha_selection_metric,
        )
        selected_features = resolve_feature_mode(
            train_data=inner_train,
            feature_columns=feature_columns,
            target_column=reg_target_column,
            feature_mode=args.feature_mode,
        )
        estimator = build_ridge_estimator(tuning["best_alpha"], args)
        estimator.fit(inner_train[selected_features], inner_train[reg_target_column])
        valid_predictions = np.asarray(estimator.predict(inner_valid[selected_features]), dtype=float)
        if reg_target_column == target_level_column:
            base_level_pred = valid_predictions
        else:
            base_level_pred = inner_valid[CURRENT_TARGET_COLUMN].to_numpy(dtype=float) + valid_predictions

        fold_frame = inner_valid.copy()
        fold_frame["base_pred_feature"] = base_level_pred
        fold_frame["residual_target"] = fold_frame[target_level_column].to_numpy(dtype=float) - base_level_pred
        fold_frame["oof_fold"] = fold_number
        oof_frames.append(fold_frame)

    if not oof_frames:
        return pd.DataFrame(), {
            "split_count": split_count,
            "oof_rows": 0,
            "coverage_ratio": 0.0,
            "fallback_reason": "sin_folds_oof_validos",
        }

    residual_train = pd.concat(oof_frames, axis=0, ignore_index=True).sort_values(DATE_COLUMN).reset_index(drop=True)
    return residual_train, {
        "split_count": split_count,
        "oof_rows": int(len(residual_train)),
        "coverage_ratio": float(len(residual_train) / max(len(train_data), 1)),
        "fallback_reason": "",
        "rows_train_total": int(step),
    }


def fit_residual_fold(
    *,
    residual_train: pd.DataFrame,
    test_data: pd.DataFrame,
    feature_columns: list[str],
    base_level_prediction: float,
    args: argparse.Namespace,
    alpha_grid: list[float],
    oof_diagnostics: dict[str, Any],
) -> dict[str, Any]:
    if residual_train.empty:
        return {
            "residual_pred": 0.0,
            "selected_features": [],
            "tuning": None,
            "oof_diagnostics": oof_diagnostics,
            "fallback_reason": oof_diagnostics.get("fallback_reason") or "sin_residual_train",
        }

    residual_test = test_data.copy()
    residual_test["base_pred_feature"] = float(base_level_prediction)
    tuning = select_best_alpha_time_series(
        train_data=residual_train,
        feature_columns=feature_columns,
        target_column="residual_target",
        estimator_builder=lambda alpha: build_ridge_estimator(alpha, args),
        alpha_grid=alpha_grid,
        feature_mode=args.feature_mode,
        target_mode=TARGET_MODE_LEVEL,
        inner_splits=args.inner_splits,
        tuning_metric=args.alpha_selection_metric,
        always_include_columns=["base_pred_feature"],
    )
    selected_features = resolve_feature_mode(
        train_data=residual_train,
        feature_columns=feature_columns,
        target_column="residual_target",
        feature_mode=args.feature_mode,
    )
    estimator = build_ridge_estimator(tuning["best_alpha"], args)
    estimator.fit(
        residual_train[["base_pred_feature", *selected_features]],
        residual_train["residual_target"],
    )
    residual_pred = float(estimator.predict(residual_test[["base_pred_feature", *selected_features]])[0])
    return {
        "residual_pred": residual_pred,
        "selected_features": selected_features,
        "tuning": tuning,
        "oof_diagnostics": oof_diagnostics,
        "fallback_reason": "",
    }


def compute_dual_metrics(predictions: pd.DataFrame, *, target_mode_cls: str, labels: tuple[str, ...]) -> dict[str, Any]:
    y_true = predictions["y_true_cls_label"].astype(str).to_numpy()
    y_pred = predictions["y_pred_cls_label"].astype(str).to_numpy()
    support = {label: int((y_true == label).sum()) for label in labels}
    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=list(labels), average="macro", zero_division=0)),
        "matriz_confusion": confusion_matrix(y_true, y_pred, labels=list(labels)).tolist(),
        "labels": list(labels),
        "soporte_por_clase": support,
        "classes_observed": [label for label in labels if support[label] > 0],
    }
    if target_mode_cls == TARGET_MODE_CLS_DIRECTION:
        metrics.update(
            {
                "recall_baja": float(
                    recall_score(y_true, y_pred, labels=["baja"], average="macro", zero_division=0)
                ),
                "precision_baja": float(
                    precision_score(y_true, y_pred, labels=["baja"], average="macro", zero_division=0)
                ),
                "recall_sube": float(
                    recall_score(y_true, y_pred, labels=["sube"], average="macro", zero_division=0)
                ),
            }
        )
    else:
        metrics.update(
            {
                "recall_cae": float(
                    recall_score(y_true, y_pred, labels=["cae"], average="macro", zero_division=0)
                ),
                "precision_cae": float(
                    precision_score(y_true, y_pred, labels=["cae"], average="macro", zero_division=0)
                ),
                "f1_cae": float(
                    f1_score(y_true, y_pred, labels=["cae"], average="macro", zero_division=0)
                ),
            }
        )
    return metrics


def compute_dual_consistency(predictions: pd.DataFrame, *, target_mode_cls: str, movement_threshold: float, fall_threshold_cls: float) -> dict[str, Any]:
    numeric_delta = predictions["y_pred"].to_numpy(dtype=float) - predictions["y_current"].to_numpy(dtype=float)
    if target_mode_cls == TARGET_MODE_CLS_DIRECTION:
        numeric_labels = np.array([classify_direction(delta, movement_threshold) for delta in numeric_delta], dtype=object)
    else:
        numeric_labels = np.array([classify_fall(delta, fall_threshold_cls) for delta in numeric_delta], dtype=object)
    classifier_labels = predictions["y_pred_cls_label"].astype(str).to_numpy()
    return {
        "consistencia_prediccion_dual": float(np.mean(numeric_labels == classifier_labels)),
        "numeric_implied_labels": pd.Series(numeric_labels).value_counts(dropna=False).to_dict(),
    }


def build_feature_summary(predictions: pd.DataFrame, column_name: str, component: str) -> pd.DataFrame:
    values = predictions[column_name].fillna("").astype(str).map(str.strip)
    summary = values.value_counts(dropna=False).rename_axis("selected_features").reset_index(name="fold_count")
    summary["feature_count"] = summary["selected_features"].map(
        lambda value: 0 if not value else len([token for token in value.split(",") if token])
    )
    summary["share_folds"] = summary["fold_count"] / max(len(predictions), 1)
    summary["component"] = component
    return summary[["component", "selected_features", "feature_count", "fold_count", "share_folds"]]


def build_run_parameters(args: argparse.Namespace, base_feature_columns: list[str], alpha_grid: list[float]) -> dict[str, Any]:
    return {
        "dataset_path": str(args.dataset_path),
        "sheet_name": args.sheet_name,
        "model": "dual_architecture",
        "dual_mode": args.dual_mode,
        "target_mode_reg": args.target_mode_reg,
        "target_mode_cls": args.target_mode_cls,
        "feature_mode": args.feature_mode,
        "transform_mode": args.transform_mode,
        "feature_columns": base_feature_columns,
        "lags": list(args.lags),
        "horizons": list(args.horizons),
        "initial_train_size": args.initial_train_size,
        "model_params": {
            "regression_model": "ridge_tscv",
            "classification_model": "logistic_regression",
            "alpha_grid": alpha_grid,
            "inner_splits": args.inner_splits,
            "alpha_selection_metric": args.alpha_selection_metric,
            "classifier_c": args.classifier_c,
            "classifier_class_weight": args.classifier_class_weight,
            "classifier_max_iter": args.classifier_max_iter,
            "movement_threshold": args.movement_threshold,
            "fall_threshold_cls": args.fall_threshold_cls,
            "residual_inner_splits": args.residual_inner_splits,
            "residual_min_oof_rows": args.residual_min_oof_rows,
        },
    }


def build_notas_config(args: argparse.Namespace, *, horizon: int, rows_modeling: int, rows_eval: int, feature_candidates: int) -> str:
    payload = {
        "dual_mode": args.dual_mode,
        "target_mode_reg": args.target_mode_reg,
        "target_mode_cls": args.target_mode_cls,
        "feature_mode": args.feature_mode,
        "transform_mode": args.transform_mode,
        "lags": list(args.lags),
        "initial_train_size": args.initial_train_size,
        "inner_splits": args.inner_splits,
        "alpha_selection_metric": args.alpha_selection_metric,
        "movement_threshold": args.movement_threshold,
        "fall_threshold_cls": args.fall_threshold_cls,
        "rows_modeling": rows_modeling,
        "rows_eval": rows_eval,
        "feature_candidates": feature_candidates,
        "horizon": horizon,
        "threshold_strategy": "fijados_ex_ante",
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def build_comments(args: argparse.Namespace) -> str:
    if args.dual_mode == DUAL_MODE_PARALLEL:
        return (
            "Arquitectura dual paralela: Ridge numerico + clasificador ternario de direccion. "
            "La salida numerica se preserva y la salida categórica se audita por separado."
        )
    if args.dual_mode == DUAL_MODE_FALL_DETECTOR:
        return (
            "Arquitectura dual con detector de caidas: Ridge numerico + clasificador binario cae/no_cae. "
            "La salida numerica se preserva y la capa de riesgo se audita por separado."
        )
    return (
        "Arquitectura dual residual: Ridge numerico base + correccion residual OOF + detector binario de caidas. "
        "La salida numerica final incluye ajuste residual temporalmente valido."
    )


def run_dual_experiment(args: argparse.Namespace) -> dict[str, Any]:
    tracker = RadarExperimentTracker(workbook_path=args.workbook, runs_dir=args.runs_dir)
    reference_values = tracker.get_reference_values()
    df = load_master_dataset(dataset_path=args.dataset_path, sheet_name=args.sheet_name)
    base_feature_columns = get_base_feature_columns(df)
    alpha_grid = build_alpha_grid(args)
    reference_run_ids = normalize_reference_run_ids(args.reference_run_id, args.extra_reference_run_ids)

    run = tracker.start_run(
        run_id=args.run_id,
        experiment_id="E11",
        family="arquitectura_dual_controlada",
        model=f"dual_{args.dual_mode}",
        script_path=__file__,
        parametros=build_run_parameters(args, base_feature_columns, alpha_grid),
    )
    run.copy_file(
        args.dataset_path,
        artifact_type="dataset_snapshot",
        notes="Dataset maestro usado por E11.",
        subdir="copias_dataset",
    )

    predictions_by_horizon: dict[int, pd.DataFrame] = {}
    cls_predictions_by_horizon: dict[int, pd.DataFrame] = {}
    cls_probabilities_by_horizon: dict[int, pd.DataFrame] = {}
    residuals_by_horizon: dict[int, pd.DataFrame] = {}
    horizon_results: list[dict[str, Any]] = []
    dual_horizon_results: list[dict[str, Any]] = []
    rows_summary: list[dict[str, Any]] = []
    reg_alpha_payload: list[dict[str, Any]] = []
    dual_thresholds = {
        "target_mode_cls": args.target_mode_cls,
        "movement_threshold": float(args.movement_threshold),
        "fall_threshold_cls": float(args.fall_threshold_cls),
        "fall_cut_rule": -abs(float(args.fall_threshold_cls)),
        "threshold_definition": "fijados_ex_ante",
    }

    for horizon in args.horizons:
        modeling_df, modeling_features, target_meta = build_dual_model_frame(
            df=df,
            horizon=horizon,
            feature_columns=base_feature_columns,
            lags=args.lags,
            target_mode_reg=args.target_mode_reg,
            target_mode_cls=args.target_mode_cls,
            movement_threshold=args.movement_threshold,
            fall_threshold_cls=args.fall_threshold_cls,
        )
        labels, _, _ = resolve_class_maps(args.target_mode_cls)
        predictions_rows: list[dict[str, Any]] = []
        cls_rows: list[dict[str, Any]] = []
        residual_rows: list[dict[str, Any]] = []
        reg_alpha_trace: list[dict[str, Any]] = []
        residual_alpha_trace: list[dict[str, Any]] = []

        for test_idx in range(args.initial_train_size, len(modeling_df)):
            train_data = modeling_df.iloc[:test_idx].copy()
            test_data = modeling_df.iloc[[test_idx]].copy()

            reg_fold = fit_ridge_fold(
                train_data=train_data,
                test_data=test_data,
                feature_columns=modeling_features,
                target_column=target_meta["reg_target_column"],
                target_level_column=target_meta["target_level_column"],
                args=args,
                alpha_grid=alpha_grid,
                feature_mode=args.feature_mode,
            )
            reg_alpha_trace.append(
                {
                    "fecha_test": str(test_data[DATE_COLUMN].iloc[0]),
                    "component": "regression",
                    "best_alpha": float(reg_fold["tuning"]["best_alpha"]),
                    "best_score": float(reg_fold["tuning"]["best_score"]),
                    "tuning_metric": reg_fold["tuning"]["tuning_metric"],
                    "inner_split_count": int(reg_fold["tuning"]["inner_split_count"]),
                    "alpha_results": reg_fold["tuning"]["alpha_results"],
                }
            )

            final_prediction = float(reg_fold["y_pred"])
            residual_pred = 0.0
            residual_feature_string = ""
            residual_fallback_reason = ""
            residual_oof_rows = None
            if args.dual_mode == DUAL_MODE_RESIDUAL:
                residual_train, oof_diag = build_temporal_oof_residual_train(
                    train_data=train_data,
                    feature_columns=modeling_features,
                    reg_target_column=target_meta["reg_target_column"],
                    target_level_column=target_meta["target_level_column"],
                    args=args,
                    alpha_grid=alpha_grid,
                )
                residual_fold = fit_residual_fold(
                    residual_train=residual_train,
                    test_data=test_data,
                    feature_columns=modeling_features,
                    base_level_prediction=float(reg_fold["y_pred"]),
                    args=args,
                    alpha_grid=alpha_grid,
                    oof_diagnostics=oof_diag,
                )
                residual_pred = float(residual_fold["residual_pred"])
                final_prediction = float(reg_fold["y_pred"] + residual_pred)
                residual_feature_string = ",".join(residual_fold["selected_features"])
                residual_fallback_reason = residual_fold["fallback_reason"]
                residual_oof_rows = residual_fold["oof_diagnostics"].get("oof_rows")
                if residual_fold["tuning"] is not None:
                    residual_alpha_trace.append(
                        {
                            "fecha_test": str(test_data[DATE_COLUMN].iloc[0]),
                            "component": "residual",
                            "best_alpha": float(residual_fold["tuning"]["best_alpha"]),
                            "best_score": float(residual_fold["tuning"]["best_score"]),
                            "tuning_metric": residual_fold["tuning"]["tuning_metric"],
                            "inner_split_count": int(residual_fold["tuning"]["inner_split_count"]),
                            "alpha_results": residual_fold["tuning"]["alpha_results"],
                        }
                    )

            cls_fold = fit_classifier_fold(
                train_data=train_data,
                test_data=test_data,
                feature_columns=modeling_features,
                delta_column=target_meta["delta_column"],
                class_label_column=target_meta["class_label_column"],
                class_id_column=target_meta["class_id_column"],
                labels=labels,
                args=args,
                feature_mode=args.feature_mode,
            )

            y_current = float(test_data[CURRENT_TARGET_COLUMN].iloc[0])
            y_true = float(test_data[target_meta["target_level_column"]].iloc[0])
            prediction_row = {
                DATE_COLUMN: test_data[DATE_COLUMN].iloc[0],
                "y_current": y_current,
                "y_true": y_true,
                "y_pred": final_prediction,
                "y_true_model": float(test_data[target_meta["reg_target_column"]].iloc[0]),
                "y_pred_model": float(reg_fold["model_prediction"]),
                "y_pred_base": float(reg_fold["y_pred"]),
                "y_pred_residual": residual_pred,
                "error": float(final_prediction - y_true),
                "selected_feature_count": int(len(reg_fold["selected_features"])),
                "selected_features": ",".join(reg_fold["selected_features"]),
                "selected_features_reg": ",".join(reg_fold["selected_features"]),
                "selected_features_clf": ",".join(cls_fold["selected_features"]),
                "selected_features_residual": residual_feature_string,
                "best_alpha": float(reg_fold["tuning"]["best_alpha"]),
                "inner_tuning_metric": reg_fold["tuning"]["tuning_metric"],
                "inner_best_score": float(reg_fold["tuning"]["best_score"]),
                "inner_split_count": int(reg_fold["tuning"]["inner_split_count"]),
                "dual_mode": args.dual_mode,
                "target_mode_reg": args.target_mode_reg,
                "target_mode_cls": args.target_mode_cls,
                "y_true_cls_label": cls_fold["true_label"],
                "y_pred_cls_label": cls_fold["predicted_label"],
                "y_true_cls_id": int(cls_fold["true_id"]),
                "y_pred_cls_id": int(cls_fold["predicted_id"]),
                "residual_fallback_reason": residual_fallback_reason,
                "residual_oof_rows": residual_oof_rows,
            }
            predictions_rows.append(prediction_row)

            cls_row = {
                DATE_COLUMN: test_data[DATE_COLUMN].iloc[0],
                "y_current": y_current,
                "y_true_level": y_true,
                "y_true_delta": float(test_data[target_meta["delta_column"]].iloc[0]),
                "y_true_cls_id": int(cls_fold["true_id"]),
                "y_pred_cls_id": int(cls_fold["predicted_id"]),
                "y_true_cls_label": cls_fold["true_label"],
                "y_pred_cls_label": cls_fold["predicted_label"],
                "selected_feature_count_cls": int(len(cls_fold["selected_features"])),
                "selected_features_clf": ",".join(cls_fold["selected_features"]),
                "train_class_ids": ",".join(str(value) for value in cls_fold["train_class_ids"]),
                "train_class_labels": ",".join(cls_fold["train_class_labels"]),
            }
            for label in labels:
                cls_row[f"proba_{label}"] = float(cls_fold["probabilities"][label])
            cls_rows.append(cls_row)

            if args.dual_mode == DUAL_MODE_RESIDUAL:
                residual_rows.append(
                    {
                        DATE_COLUMN: test_data[DATE_COLUMN].iloc[0],
                        "y_current": y_current,
                        "y_true": y_true,
                        "y_pred_base": float(reg_fold["y_pred"]),
                        "y_pred_residual": residual_pred,
                        "y_pred_final": final_prediction,
                        "error_base": float(reg_fold["y_pred"] - y_true),
                        "error_final": float(final_prediction - y_true),
                        "selected_features_residual": residual_feature_string,
                        "residual_fallback_reason": residual_fallback_reason,
                        "residual_oof_rows": residual_oof_rows,
                    }
                )

        predictions_df = pd.DataFrame(predictions_rows)
        cls_predictions_df = pd.DataFrame(cls_rows)
        predictions_by_horizon[horizon] = predictions_df
        cls_predictions_by_horizon[horizon] = cls_predictions_df
        cls_probabilities_by_horizon[horizon] = cls_predictions_df[
            [DATE_COLUMN, *[f"proba_{label}" for label in labels]]
        ].copy()
        if residual_rows:
            residuals_by_horizon[horizon] = pd.DataFrame(residual_rows)

        dual_metrics = compute_dual_metrics(cls_predictions_df, target_mode_cls=args.target_mode_cls, labels=labels)
        dual_consistency = compute_dual_consistency(
            predictions_df,
            target_mode_cls=args.target_mode_cls,
            movement_threshold=args.movement_threshold,
            fall_threshold_cls=args.fall_threshold_cls,
        )
        radar_metrics = compute_radar_metrics(predictions_df)
        loss_h = compute_loss_h(metrics=radar_metrics, horizon=horizon, reference_values=reference_values)

        summary_row = {
            "horizonte_sem": horizon,
            "rows_modeling": int(len(modeling_df)),
            "rows_eval": int(len(predictions_df)),
            "feature_candidates": int(len(modeling_features)),
            "selected_feature_count_avg": float(predictions_df["selected_feature_count"].mean()),
            "selected_feature_count_cls_avg": float(cls_predictions_df["selected_feature_count_cls"].mean()),
            "feature_mode": args.feature_mode,
            "target_mode_reg": args.target_mode_reg,
            "target_mode_cls": args.target_mode_cls,
            "dual_mode": args.dual_mode,
        }
        rows_summary.append(summary_row)

        horizon_results.append(
            {
                "horizonte_sem": horizon,
                "target": args.target_mode_reg,
                "variables_temporales": f"y_t + lags {list(args.lags)}",
                "variables_tematicas": ", ".join(base_feature_columns),
                "transformacion": describe_transform_mode(args.transform_mode),
                "seleccion_variables": args.feature_mode,
                "validacion": "walk-forward_expanding",
                "dataset_periodo": f"{predictions_df[DATE_COLUMN].min().date()} a {predictions_df[DATE_COLUMN].max().date()}",
                "notas_config": build_notas_config(
                    args,
                    horizon=horizon,
                    rows_modeling=len(modeling_df),
                    rows_eval=len(predictions_df),
                    feature_candidates=len(modeling_features),
                ),
                "estado": "corrido",
                "comentarios": build_comments(args),
                "loss_h": loss_h,
                **radar_metrics,
            }
        )
        dual_horizon_results.append(
            {
                "horizonte_sem": horizon,
                "dual_mode": args.dual_mode,
                "target_mode_cls": args.target_mode_cls,
                "rows_eval": int(len(cls_predictions_df)),
                "movement_threshold": float(args.movement_threshold),
                "fall_threshold_cls": float(args.fall_threshold_cls),
                **dual_metrics,
                **dual_consistency,
            }
        )
        reg_alpha_payload.append(
            {
                "horizonte_sem": horizon,
                "component": "regression",
                **summarize_alpha_trace(reg_alpha_trace),
            }
        )
        if residual_alpha_trace:
            reg_alpha_payload.append(
                {
                    "horizonte_sem": horizon,
                    "component": "residual",
                    **summarize_alpha_trace(residual_alpha_trace),
                }
            )

        feature_summaries = [
            build_feature_summary(predictions_df, "selected_features_reg", "regresion"),
            build_feature_summary(cls_predictions_df, "selected_features_clf", "clasificacion"),
        ]
        if residual_rows:
            feature_summaries.append(
                build_feature_summary(pd.DataFrame(residual_rows), "selected_features_residual", "residual")
            )
        features_summary_df = pd.concat(feature_summaries, axis=0, ignore_index=True)
        run.save_dataframe(
            features_summary_df,
            f"features_seleccionadas_h{horizon}.csv",
            artifact_type="seleccion_features",
            notes="Resumen dual de combinaciones de features seleccionadas por fold externo.",
        )

    for horizon, predictions_df in predictions_by_horizon.items():
        run.save_dataframe(
            predictions_df,
            f"predicciones_h{horizon}.csv",
            artifact_type="predicciones",
            notes=f"Predicciones numericas finales walk-forward para horizonte {horizon}.",
        )
        run.save_dataframe(
            cls_predictions_by_horizon[horizon],
            f"predicciones_clasificacion_h{horizon}.csv",
            artifact_type="predicciones_clasificacion",
            notes=f"Salida categórica dual para horizonte {horizon}.",
        )
        run.save_dataframe(
            cls_probabilities_by_horizon[horizon],
            f"probabilidades_clasificacion_h{horizon}.csv",
            artifact_type="probabilidades_clasificacion",
            notes=f"Probabilidades categóricas duales para horizonte {horizon}.",
        )
        if horizon in residuals_by_horizon:
            run.save_dataframe(
                residuals_by_horizon[horizon],
                f"residuales_h{horizon}.csv",
                artifact_type="residuales",
                notes=f"Descomposicion base/residual/final para horizonte {horizon}.",
            )

    run.save_json(
        rows_summary,
        "resumen_modeling_horizontes.json",
        artifact_type="resumen",
        notes="Resumen dual de tamanos y seleccion de features por horizonte.",
    )
    run.save_json(
        dual_horizon_results,
        "resumen_dual_horizontes.json",
        artifact_type="resumen_dual",
        notes="Resumen de metricas categóricas y consistencia dual por horizonte.",
    )
    run.save_json(
        dual_thresholds,
        "thresholds_clases.json",
        artifact_type="config_dual",
        notes="Umbrales categóricos fijados ex ante para la familia E11.",
    )
    run.save_json(
        reg_alpha_payload,
        "alpha_tuning_horizontes.json",
        artifact_type="tuning",
        notes="Resumen de tuning temporal de alpha para componentes Ridge.",
    )

    total_radar = compute_total_radar_loss(
        horizon_results=horizon_results,
        reference_values=reference_values,
        l_coh=None,
    )
    dual_global = {
        "avg_accuracy": float(np.mean([item["accuracy"] for item in dual_horizon_results])),
        "avg_balanced_accuracy": float(np.mean([item["balanced_accuracy"] for item in dual_horizon_results])),
        "avg_macro_f1": float(np.mean([item["macro_f1"] for item in dual_horizon_results])),
        "avg_consistencia_prediccion_dual": float(
            np.mean([item["consistencia_prediccion_dual"] for item in dual_horizon_results])
        ),
    }
    if args.target_mode_cls == TARGET_MODE_CLS_DIRECTION:
        dual_global["avg_recall_baja"] = float(np.mean([item["recall_baja"] for item in dual_horizon_results]))
    else:
        dual_global["avg_recall_cae"] = float(np.mean([item["recall_cae"] for item in dual_horizon_results]))
        dual_global["avg_precision_cae"] = float(np.mean([item["precision_cae"] for item in dual_horizon_results]))

    save_reference_comparisons(
        run=run,
        workbook_path=args.workbook,
        clean_run_id=args.run_id,
        reference_run_ids=reference_run_ids,
        horizon_results=horizon_results,
        l_total_radar=float(total_radar["l_total_radar"]),
    )

    comparison_payload = {
        "run_id": args.run_id,
        "dual_mode": args.dual_mode,
        "reference_run_ids": list(reference_run_ids),
        "l_total_radar": float(total_radar["l_total_radar"]),
        "dual_global": dual_global,
        "comparacion_global_vs_benchmarks": [],
    }
    for reference_run_id in reference_run_ids:
        payload = build_comparison_payload(
            workbook_path=args.workbook,
            reference_run_id=reference_run_id,
            clean_run_id=args.run_id,
            horizon_results=horizon_results,
            l_total_radar=float(total_radar["l_total_radar"]),
        )
        comparison_payload["comparacion_global_vs_benchmarks"].append(payload)
    run.save_json(
        comparison_payload,
        "comparacion_dual_vs_benchmarks.json",
        artifact_type="comparacion",
        notes="Comparacion global de E11 contra benchmarks vigentes y resumen dual.",
    )

    run.finalize(
        horizon_results=horizon_results,
        target=args.target_mode_reg,
        variables_temporales=f"y_t + lags {list(args.lags)}",
        variables_tematicas=", ".join(base_feature_columns),
        transformacion=describe_transform_mode(args.transform_mode),
        seleccion_variables=args.feature_mode,
        validacion="walk-forward_expanding",
        dataset_periodo=f"{df[DATE_COLUMN].min().date()} a {df[DATE_COLUMN].max().date()}",
        notas_config=json.dumps(
            {
                "dual_mode": args.dual_mode,
                "target_mode_reg": args.target_mode_reg,
                "target_mode_cls": args.target_mode_cls,
                "movement_threshold": args.movement_threshold,
                "fall_threshold_cls": args.fall_threshold_cls,
                "threshold_strategy": "fijados_ex_ante",
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        estado="corrido",
        comentarios=build_comments(args),
        l_coh=None,
        summary_metrics={**total_radar, **dual_global},
        task_type="regresion",
    )

    return {
        "l_total_radar": float(total_radar["l_total_radar"]),
        "dual_global": dual_global,
        "horizon_results": horizon_results,
        "dual_horizon_results": dual_horizon_results,
    }


def main() -> None:
    args = parse_args()
    result = run_dual_experiment(args)
    print(f"Run registrado: {args.run_id}")
    print(f"Dual mode: {args.dual_mode}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")
    print(f"Dual avg accuracy: {result['dual_global']['avg_accuracy']:.6f}")


if __name__ == "__main__":
    main()
