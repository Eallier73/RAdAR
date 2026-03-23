from __future__ import annotations

import math
from itertools import product
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LassoCV
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

from config import (
    ABS_ERROR_TOLERANCE,
    CURRENT_TARGET_COLUMN,
    DATE_COLUMN,
    FALL_THRESHOLD,
    FEATURE_MODE_ALL,
    FEATURE_MODE_CORR,
    FEATURE_MODE_LASSO,
    TARGET_MODE_DELTA,
    TARGET_MODE_LEVEL,
)


def resolve_feature_mode(
    train_data: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    feature_mode: str = FEATURE_MODE_ALL,
) -> list[str]:
    available_columns = [column for column in feature_columns if column in train_data.columns]
    if feature_mode == FEATURE_MODE_ALL or len(available_columns) <= 1:
        return available_columns

    if feature_mode == FEATURE_MODE_CORR:
        return select_features_by_correlation(
            train_data=train_data,
            feature_columns=available_columns,
            target_column=target_column,
        )

    if feature_mode == FEATURE_MODE_LASSO:
        return select_features_by_lasso(
            train_data=train_data,
            feature_columns=available_columns,
            target_column=target_column,
        )

    raise ValueError(f"Feature mode no soportado: {feature_mode}")


def select_features_by_correlation(
    train_data: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
) -> list[str]:
    if not feature_columns:
        return []

    correlations = (
        train_data[feature_columns]
        .corrwith(train_data[target_column])
        .abs()
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
    )
    top_k = max(4, min(len(feature_columns), int(math.ceil(len(feature_columns) * 0.35))))
    selected = correlations.sort_values(ascending=False).head(top_k).index.tolist()
    return selected or feature_columns


def select_features_by_lasso(
    train_data: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
) -> list[str]:
    if not feature_columns:
        return []

    scaler = StandardScaler()
    x_train = scaler.fit_transform(train_data[feature_columns])
    y_train = train_data[target_column].to_numpy()
    cv_folds = max(2, min(5, len(train_data) // 8))

    selector = LassoCV(
        cv=cv_folds,
        max_iter=20000,
        random_state=42,
    )
    selector.fit(x_train, y_train)

    selected = [
        column
        for column, coef in zip(feature_columns, selector.coef_, strict=False)
        if abs(float(coef)) > 1e-8
    ]
    if selected:
        return selected

    return select_features_by_correlation(
        train_data=train_data,
        feature_columns=feature_columns,
        target_column=target_column,
    )


def walk_forward_predict(
    estimator,
    data: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    initial_train_size: int,
    *,
    feature_mode: str = FEATURE_MODE_ALL,
    target_mode: str = TARGET_MODE_LEVEL,
    actual_target_column: str | None = None,
    always_include_columns: list[str] | None = None,
) -> pd.DataFrame:
    if len(data) <= initial_train_size:
        raise ValueError(
            f"No hay suficientes filas para walk-forward. Filas={len(data)}, "
            f"initial_train_size={initial_train_size}."
        )

    include_columns = always_include_columns or []
    predictions: list[dict[str, float | int | str]] = []

    for test_idx in range(initial_train_size, len(data)):
        train = data.iloc[:test_idx]
        test = data.iloc[[test_idx]]
        selected_features = resolve_feature_mode(
            train_data=train,
            feature_columns=feature_columns,
            target_column=target_column,
            feature_mode=feature_mode,
        )
        input_columns = [*include_columns, *selected_features]
        fitted = clone(estimator)
        fitted.fit(train[input_columns], train[target_column])
        model_prediction = float(fitted.predict(test[input_columns])[0])
        y_current = float(test[CURRENT_TARGET_COLUMN].iloc[0])

        if target_mode == TARGET_MODE_DELTA:
            if actual_target_column is None:
                raise ValueError("actual_target_column es requerido cuando target_mode='delta'.")
            y_true = float(test[actual_target_column].iloc[0])
            y_true_model = float(test[target_column].iloc[0])
            y_pred = y_current + model_prediction
        else:
            y_true = float(test[target_column].iloc[0])
            y_true_model = y_true
            y_pred = model_prediction

        predictions.append(
            {
                DATE_COLUMN: test[DATE_COLUMN].iloc[0],
                "y_current": y_current,
                "y_true": y_true,
                "y_pred": y_pred,
                "y_true_model": y_true_model,
                "y_pred_model": model_prediction,
                "error": y_pred - y_true,
                "selected_feature_count": len(selected_features),
                "selected_features": ",".join(selected_features),
            }
        )

    return pd.DataFrame(predictions)


def select_best_alpha_time_series(
    *,
    train_data: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    estimator_builder,
    alpha_grid: list[float],
    feature_mode: str = FEATURE_MODE_ALL,
    target_mode: str = TARGET_MODE_LEVEL,
    actual_target_column: str | None = None,
    always_include_columns: list[str] | None = None,
    inner_splits: int = 3,
    tuning_metric: str = "mae",
) -> dict[str, Any]:
    include_columns = always_include_columns or []
    split_count = min(inner_splits, len(train_data) - 1)
    if split_count < 2:
        raise ValueError(
            f"No hay suficientes observaciones para TimeSeriesSplit interno. "
            f"Filas_train={len(train_data)}, inner_splits={inner_splits}."
        )

    if tuning_metric not in {"mae", "rmse"}:
        raise ValueError(f"Metrica de tuning no soportada: {tuning_metric}")

    splitter = TimeSeriesSplit(n_splits=split_count)
    alpha_results: list[dict[str, Any]] = []

    for alpha in alpha_grid:
        fold_scores: list[float] = []

        for inner_train_idx, inner_valid_idx in splitter.split(train_data):
            inner_train = train_data.iloc[inner_train_idx]
            inner_valid = train_data.iloc[inner_valid_idx]

            selected_features = resolve_feature_mode(
                train_data=inner_train,
                feature_columns=feature_columns,
                target_column=target_column,
                feature_mode=feature_mode,
            )
            input_columns = [*include_columns, *selected_features]
            estimator = clone(estimator_builder(float(alpha)))
            estimator.fit(inner_train[input_columns], inner_train[target_column])

            predicted_model = np.asarray(estimator.predict(inner_valid[input_columns]), dtype=float)
            if target_mode == TARGET_MODE_DELTA:
                if actual_target_column is None:
                    raise ValueError("actual_target_column es requerido cuando target_mode='delta'.")
                y_true = inner_valid[actual_target_column].to_numpy(dtype=float)
                y_pred = inner_valid[CURRENT_TARGET_COLUMN].to_numpy(dtype=float) + predicted_model
            else:
                y_true = inner_valid[target_column].to_numpy(dtype=float)
                y_pred = predicted_model

            if tuning_metric == "mae":
                score = float(mean_absolute_error(y_true, y_pred))
            else:
                score = float(math.sqrt(mean_squared_error(y_true, y_pred)))
            fold_scores.append(score)

        alpha_results.append(
            {
                "alpha": float(alpha),
                "mean_score": float(np.mean(fold_scores)),
                "std_score": float(np.std(fold_scores)),
                "fold_scores": fold_scores,
            }
        )

    best_result = min(alpha_results, key=lambda item: (item["mean_score"], item["alpha"]))
    return {
        "best_alpha": float(best_result["alpha"]),
        "best_score": float(best_result["mean_score"]),
        "tuning_metric": tuning_metric,
        "inner_split_count": split_count,
        "alpha_results": alpha_results,
    }


def expand_parameter_grid(param_grid: dict[str, list[Any] | tuple[Any, ...]]) -> list[dict[str, Any]]:
    if not param_grid:
        raise ValueError("param_grid no puede estar vacio.")

    keys = list(param_grid)
    values_product = product(*(param_grid[key] for key in keys))
    candidates = []
    for values in values_product:
        candidates.append({key: value for key, value in zip(keys, values, strict=True)})
    return candidates


def select_best_params_time_series(
    *,
    train_data: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    estimator_builder,
    param_grid: dict[str, list[Any] | tuple[Any, ...]],
    feature_mode: str = FEATURE_MODE_ALL,
    target_mode: str = TARGET_MODE_LEVEL,
    actual_target_column: str | None = None,
    always_include_columns: list[str] | None = None,
    inner_splits: int = 3,
    tuning_metric: str = "mae",
) -> dict[str, Any]:
    include_columns = always_include_columns or []
    split_count = min(inner_splits, len(train_data) - 1)
    if split_count < 2:
        raise ValueError(
            f"No hay suficientes observaciones para TimeSeriesSplit interno. "
            f"Filas_train={len(train_data)}, inner_splits={inner_splits}."
        )

    if tuning_metric not in {"mae", "rmse"}:
        raise ValueError(f"Metrica de tuning no soportada: {tuning_metric}")

    splitter = TimeSeriesSplit(n_splits=split_count)
    param_candidates = expand_parameter_grid(param_grid)
    param_results: list[dict[str, Any]] = []

    for params in param_candidates:
        fold_scores: list[float] = []

        for inner_train_idx, inner_valid_idx in splitter.split(train_data):
            inner_train = train_data.iloc[inner_train_idx]
            inner_valid = train_data.iloc[inner_valid_idx]

            selected_features = resolve_feature_mode(
                train_data=inner_train,
                feature_columns=feature_columns,
                target_column=target_column,
                feature_mode=feature_mode,
            )
            input_columns = [*include_columns, *selected_features]
            estimator = clone(estimator_builder(params))
            estimator.fit(inner_train[input_columns], inner_train[target_column])

            predicted_model = np.asarray(estimator.predict(inner_valid[input_columns]), dtype=float)
            if target_mode == TARGET_MODE_DELTA:
                if actual_target_column is None:
                    raise ValueError("actual_target_column es requerido cuando target_mode='delta'.")
                y_true = inner_valid[actual_target_column].to_numpy(dtype=float)
                y_pred = inner_valid[CURRENT_TARGET_COLUMN].to_numpy(dtype=float) + predicted_model
            else:
                y_true = inner_valid[target_column].to_numpy(dtype=float)
                y_pred = predicted_model

            if tuning_metric == "mae":
                score = float(mean_absolute_error(y_true, y_pred))
            else:
                score = float(math.sqrt(mean_squared_error(y_true, y_pred)))
            fold_scores.append(score)

        param_results.append(
            {
                "params": dict(params),
                "mean_score": float(np.mean(fold_scores)),
                "std_score": float(np.std(fold_scores)),
                "fold_scores": fold_scores,
            }
        )

    best_result = min(param_results, key=lambda item: (item["mean_score"], repr(sorted(item["params"].items()))))
    return {
        "best_params": dict(best_result["params"]),
        "best_score": float(best_result["mean_score"]),
        "tuning_metric": tuning_metric,
        "inner_split_count": split_count,
        "param_results": param_results,
    }


def walk_forward_predict_with_tscv_alpha_tuning(
    *,
    estimator_builder,
    alpha_grid: list[float],
    data: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    initial_train_size: int,
    feature_mode: str = FEATURE_MODE_ALL,
    target_mode: str = TARGET_MODE_LEVEL,
    actual_target_column: str | None = None,
    always_include_columns: list[str] | None = None,
    inner_splits: int = 3,
    tuning_metric: str = "mae",
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    if len(data) <= initial_train_size:
        raise ValueError(
            f"No hay suficientes filas para walk-forward. Filas={len(data)}, "
            f"initial_train_size={initial_train_size}."
        )

    include_columns = always_include_columns or []
    predictions: list[dict[str, float | int | str]] = []
    alpha_trace: list[dict[str, Any]] = []

    for test_idx in range(initial_train_size, len(data)):
        train = data.iloc[:test_idx]
        test = data.iloc[[test_idx]]

        tuning = select_best_alpha_time_series(
            train_data=train,
            feature_columns=feature_columns,
            target_column=target_column,
            estimator_builder=estimator_builder,
            alpha_grid=alpha_grid,
            feature_mode=feature_mode,
            target_mode=target_mode,
            actual_target_column=actual_target_column,
            always_include_columns=include_columns,
            inner_splits=inner_splits,
            tuning_metric=tuning_metric,
        )

        selected_features = resolve_feature_mode(
            train_data=train,
            feature_columns=feature_columns,
            target_column=target_column,
            feature_mode=feature_mode,
        )
        input_columns = [*include_columns, *selected_features]
        fitted = clone(estimator_builder(tuning["best_alpha"]))
        fitted.fit(train[input_columns], train[target_column])
        model_prediction = float(fitted.predict(test[input_columns])[0])
        y_current = float(test[CURRENT_TARGET_COLUMN].iloc[0])

        if target_mode == TARGET_MODE_DELTA:
            if actual_target_column is None:
                raise ValueError("actual_target_column es requerido cuando target_mode='delta'.")
            y_true = float(test[actual_target_column].iloc[0])
            y_true_model = float(test[target_column].iloc[0])
            y_pred = y_current + model_prediction
        else:
            y_true = float(test[target_column].iloc[0])
            y_true_model = y_true
            y_pred = model_prediction

        predictions.append(
            {
                DATE_COLUMN: test[DATE_COLUMN].iloc[0],
                "y_current": y_current,
                "y_true": y_true,
                "y_pred": y_pred,
                "y_true_model": y_true_model,
                "y_pred_model": model_prediction,
                "error": y_pred - y_true,
                "selected_feature_count": len(selected_features),
                "selected_features": ",".join(selected_features),
                "best_alpha": float(tuning["best_alpha"]),
                "inner_tuning_metric": tuning["tuning_metric"],
                "inner_best_score": float(tuning["best_score"]),
                "inner_split_count": int(tuning["inner_split_count"]),
            }
        )
        alpha_trace.append(
            {
                "fecha_test": str(test[DATE_COLUMN].iloc[0]),
                "best_alpha": float(tuning["best_alpha"]),
                "best_score": float(tuning["best_score"]),
                "tuning_metric": tuning["tuning_metric"],
                "inner_split_count": int(tuning["inner_split_count"]),
                "alpha_results": tuning["alpha_results"],
            }
        )

    return pd.DataFrame(predictions), alpha_trace


def walk_forward_predict_with_tscv_param_tuning(
    *,
    estimator_builder,
    param_grid: dict[str, list[Any] | tuple[Any, ...]],
    data: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    initial_train_size: int,
    feature_mode: str = FEATURE_MODE_ALL,
    target_mode: str = TARGET_MODE_LEVEL,
    actual_target_column: str | None = None,
    always_include_columns: list[str] | None = None,
    inner_splits: int = 3,
    tuning_metric: str = "mae",
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    if len(data) <= initial_train_size:
        raise ValueError(
            f"No hay suficientes filas para walk-forward. Filas={len(data)}, "
            f"initial_train_size={initial_train_size}."
        )

    include_columns = always_include_columns or []
    predictions: list[dict[str, float | int | str]] = []
    param_trace: list[dict[str, Any]] = []

    for test_idx in range(initial_train_size, len(data)):
        train = data.iloc[:test_idx]
        test = data.iloc[[test_idx]]

        tuning = select_best_params_time_series(
            train_data=train,
            feature_columns=feature_columns,
            target_column=target_column,
            estimator_builder=estimator_builder,
            param_grid=param_grid,
            feature_mode=feature_mode,
            target_mode=target_mode,
            actual_target_column=actual_target_column,
            always_include_columns=include_columns,
            inner_splits=inner_splits,
            tuning_metric=tuning_metric,
        )

        selected_features = resolve_feature_mode(
            train_data=train,
            feature_columns=feature_columns,
            target_column=target_column,
            feature_mode=feature_mode,
        )
        input_columns = [*include_columns, *selected_features]
        fitted = clone(estimator_builder(tuning["best_params"]))
        fitted.fit(train[input_columns], train[target_column])
        model_prediction = float(fitted.predict(test[input_columns])[0])
        y_current = float(test[CURRENT_TARGET_COLUMN].iloc[0])
        best_params = dict(tuning["best_params"])

        if target_mode == TARGET_MODE_DELTA:
            if actual_target_column is None:
                raise ValueError("actual_target_column es requerido cuando target_mode='delta'.")
            y_true = float(test[actual_target_column].iloc[0])
            y_true_model = float(test[target_column].iloc[0])
            y_pred = y_current + model_prediction
        else:
            y_true = float(test[target_column].iloc[0])
            y_true_model = y_true
            y_pred = model_prediction

        prediction_row = {
            DATE_COLUMN: test[DATE_COLUMN].iloc[0],
            "y_current": y_current,
            "y_true": y_true,
            "y_pred": y_pred,
            "y_true_model": y_true_model,
            "y_pred_model": model_prediction,
            "error": y_pred - y_true,
            "selected_feature_count": len(selected_features),
            "selected_features": ",".join(selected_features),
            "inner_tuning_metric": tuning["tuning_metric"],
            "inner_best_score": float(tuning["best_score"]),
            "inner_split_count": int(tuning["inner_split_count"]),
        }
        for key, value in best_params.items():
            prediction_row[f"best_{key}"] = value
        predictions.append(prediction_row)
        param_trace.append(
            {
                "fecha_test": str(test[DATE_COLUMN].iloc[0]),
                **tuning,
            }
        )

    return pd.DataFrame(predictions), param_trace


def compute_radar_metrics(
    predictions: pd.DataFrame,
    tolerance: float = ABS_ERROR_TOLERANCE,
    fall_threshold: float = FALL_THRESHOLD,
) -> dict[str, float]:
    y_true = predictions["y_true"].to_numpy()
    y_pred = predictions["y_pred"].to_numpy()
    y_current = predictions["y_current"].to_numpy()

    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(math.sqrt(mean_squared_error(y_true, y_pred)))

    actual_delta = y_true - y_current
    predicted_delta = y_pred - y_current

    actual_direction = np.sign(actual_delta)
    predicted_direction = np.sign(predicted_delta)
    direction_accuracy = float(np.mean(actual_direction == predicted_direction))

    actual_fall = actual_delta <= fall_threshold
    predicted_fall = predicted_delta <= fall_threshold
    if actual_fall.any():
        deteccion_caidas = float(np.mean(predicted_fall[actual_fall]))
    else:
        deteccion_caidas = 1.0

    target_range = float(np.max(y_true) - np.min(y_true))
    if target_range == 0:
        target_range = 1.0

    l_num = min(mae / target_range, 1.0)
    l_trend = 1.0 - direction_accuracy
    l_risk = 1.0 - deteccion_caidas
    l_tol = float(np.mean(np.abs(y_pred - y_true) > tolerance))

    return {
        "l_num": l_num,
        "l_trend": l_trend,
        "l_risk": l_risk,
        "l_tol": l_tol,
        "mae": mae,
        "rmse": rmse,
        "direccion_accuracy": direction_accuracy,
        "deteccion_caidas": deteccion_caidas,
    }


def compute_loss_h(
    metrics: dict[str, Any],
    horizon: int,
    reference_values: dict[str, Any],
) -> float:
    alpha = float(reference_values["alpha"])
    beta = float(reference_values["beta"])
    gamma = float(reference_values["gamma"])
    delta = float(reference_values["delta"])
    w_h = float(reference_values["horizon_weights"][int(horizon)])

    return float(
        w_h
        * (
            alpha * float(metrics["l_num"])
            + beta * float(metrics["l_trend"])
            + gamma * float(metrics["l_risk"])
            + delta * float(metrics["l_tol"])
        )
    )


def compute_total_radar_loss(
    horizon_results: list[dict[str, Any]],
    reference_values: dict[str, Any],
    l_coh: float | None = None,
) -> dict[str, float | None]:
    sum_weighted_loss_h = 0.0
    for result in horizon_results:
        sum_weighted_loss_h += compute_loss_h(
            metrics=result,
            horizon=int(result["horizonte_sem"]),
            reference_values=reference_values,
        )

    l_coh_value = float(l_coh) if l_coh is not None else None
    eta = float(reference_values["eta"])
    l_total_radar = sum_weighted_loss_h + ((l_coh_value or 0.0) * eta)

    return {
        "sum_weighted_loss_h": sum_weighted_loss_h,
        "l_coh": l_coh_value,
        "eta": eta,
        "l_total_radar": l_total_radar,
    }
