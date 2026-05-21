#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline

from config import (
    CURRENT_TARGET_COLUMN,
    DATE_COLUMN,
    DEFAULT_RANDOM_STATE,
    FEATURE_MODE_ALL,
    FEATURE_MODE_CHOICES,
    TARGET_COLUMNS,
    TARGET_MODE_LEVEL,
    TRANSFORM_MODE_STANDARD,
)
from custom_estimators import ProphetExogenousRegressor
from data_master import get_base_feature_columns, load_master_dataset
from evaluation import (
    compute_loss_h,
    compute_radar_metrics,
    compute_total_radar_loss,
    resolve_feature_mode,
    select_best_alpha_time_series,
)
from experiment_logger import RadarExperimentTracker
from feature_engineering import build_model_frame
from pipeline_common import (
    add_common_experiment_args,
    add_reference_comparison_args,
    build_notas_config,
    build_run_parameters,
    finalize_common_args,
    normalize_reference_run_ids,
    parse_string_sequence,
    save_reference_comparisons,
)
from preprocessing import build_feature_transformer, describe_transform_mode

MODEL_RIDGE = "ridge_tscv"
MODEL_CATBOOST = "catboost_regressor"
MODEL_PROPHET = "prophet_exogenous_regressor"


@dataclass
class ModelSpec:
    model_name: str
    feature_mode: str
    params: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E8 | Familia híbrida residual con dos etapas y residuales temporales válidos.",
    )
    add_common_experiment_args(parser, default_run_id="E8_v1_clean")
    parser.set_defaults(
        target_mode=TARGET_MODE_LEVEL,
        feature_mode="corr",
        lags="1,2,3,4,5,6",
        initial_train_size=40,
        horizons="1,2,3,4",
    )
    add_reference_comparison_args(parser, default_reference_run_id="E1_v5_clean")

    parser.add_argument(
        "--base-model",
        choices=(MODEL_RIDGE, MODEL_CATBOOST),
        default=MODEL_RIDGE,
    )
    parser.add_argument(
        "--residual-model",
        choices=(MODEL_RIDGE, MODEL_CATBOOST, MODEL_PROPHET),
        default=MODEL_CATBOOST,
    )
    parser.add_argument(
        "--residual-feature-mode",
        choices=FEATURE_MODE_CHOICES,
        default="",
        help="Modo de seleccion del learner residual. Si se omite, usa --feature-mode.",
    )
    parser.add_argument(
        "--residual-inner-splits",
        type=int,
        default=3,
        help="Splits temporales internos para construir residuales OOF.",
    )
    parser.add_argument(
        "--residual-min-oof-rows",
        type=int,
        default=12,
        help="Minimo de filas OOF para entrenar el learner residual.",
    )

    parser.add_argument("--ridge-transform-mode", default=TRANSFORM_MODE_STANDARD)
    parser.add_argument("--ridge-winsor-lower-quantile", type=float, default=0.05)
    parser.add_argument("--ridge-winsor-upper-quantile", type=float, default=0.95)
    parser.add_argument("--ridge-alpha-grid-min-exp", type=float, default=-4.0)
    parser.add_argument("--ridge-alpha-grid-max-exp", type=float, default=4.0)
    parser.add_argument("--ridge-alpha-grid-points", type=int, default=40)
    parser.add_argument("--ridge-inner-splits", type=int, default=3)
    parser.add_argument("--ridge-selection-metric", choices=("mae", "rmse"), default="mae")

    parser.add_argument("--catboost-iterations", type=int, default=300)
    parser.add_argument("--catboost-depth", type=int, default=5)
    parser.add_argument("--catboost-learning-rate", type=float, default=0.05)
    parser.add_argument("--catboost-l2-leaf-reg", type=float, default=3.0)
    parser.add_argument("--catboost-subsample", type=float, default=0.8)
    parser.add_argument("--catboost-random-seed", type=int, default=DEFAULT_RANDOM_STATE)

    parser.add_argument("--prophet-changepoint-prior-scale", type=float, default=0.20)
    parser.add_argument("--prophet-seasonality-mode", default="additive")
    parser.add_argument("--prophet-weekly-seasonality", action="store_true")
    parser.add_argument("--prophet-yearly-seasonality", action="store_true")
    parser.add_argument("--prophet-daily-seasonality", action="store_true")

    args = finalize_common_args(parser.parse_args())
    args.extra_reference_run_ids = parse_string_sequence(args.extra_reference_run_ids)
    if not 0.0 <= args.ridge_winsor_lower_quantile < args.ridge_winsor_upper_quantile <= 1.0:
        raise ValueError("Los cuantiles de winsor deben cumplir 0 <= lower < upper <= 1.")
    if args.residual_inner_splits < 2:
        raise ValueError("--residual-inner-splits debe ser al menos 2.")
    if not args.residual_feature_mode:
        args.residual_feature_mode = args.feature_mode
    return args


def build_ridge_alpha_grid(args: argparse.Namespace) -> list[float]:
    return list(
        np.logspace(
            args.ridge_alpha_grid_min_exp,
            args.ridge_alpha_grid_max_exp,
            args.ridge_alpha_grid_points,
        )
    )


def build_ridge_estimator(alpha: float, args: argparse.Namespace) -> Pipeline:
    return Pipeline(
        steps=[
            (
                "transform",
                build_feature_transformer(
                    transform_mode=args.ridge_transform_mode,
                    winsor_lower_quantile=args.ridge_winsor_lower_quantile,
                    winsor_upper_quantile=args.ridge_winsor_upper_quantile,
                ),
            ),
            ("model", Ridge(alpha=float(alpha))),
        ]
    )


def build_catboost_estimator(args: argparse.Namespace):
    from catboost import CatBoostRegressor

    return CatBoostRegressor(
        iterations=args.catboost_iterations,
        depth=args.catboost_depth,
        learning_rate=args.catboost_learning_rate,
        l2_leaf_reg=args.catboost_l2_leaf_reg,
        bootstrap_type="Bernoulli",
        subsample=args.catboost_subsample,
        loss_function="RMSE",
        random_seed=args.catboost_random_seed,
        verbose=False,
        allow_writing_files=False,
        thread_count=4,
    )


def build_prophet_estimator(args: argparse.Namespace) -> ProphetExogenousRegressor:
    return ProphetExogenousRegressor(
        date_column=DATE_COLUMN,
        changepoint_prior_scale=args.prophet_changepoint_prior_scale,
        seasonality_mode=args.prophet_seasonality_mode,
        weekly_seasonality=args.prophet_weekly_seasonality,
        yearly_seasonality=args.prophet_yearly_seasonality,
        daily_seasonality=args.prophet_daily_seasonality,
    )


def build_model_spec(args: argparse.Namespace, role: str) -> ModelSpec:
    if role == "base":
        model_name = args.base_model
        feature_mode = args.feature_mode
    else:
        model_name = args.residual_model
        feature_mode = args.residual_feature_mode

    if model_name == MODEL_RIDGE:
        params = {
            "transform_mode": args.ridge_transform_mode,
            "winsor_lower_quantile": args.ridge_winsor_lower_quantile,
            "winsor_upper_quantile": args.ridge_winsor_upper_quantile,
            "alpha_grid": build_ridge_alpha_grid(args),
            "inner_splits": args.ridge_inner_splits,
            "selection_metric": args.ridge_selection_metric,
        }
    elif model_name == MODEL_CATBOOST:
        params = {
            "iterations": args.catboost_iterations,
            "depth": args.catboost_depth,
            "learning_rate": args.catboost_learning_rate,
            "l2_leaf_reg": args.catboost_l2_leaf_reg,
            "subsample": args.catboost_subsample,
            "random_seed": args.catboost_random_seed,
        }
    elif model_name == MODEL_PROPHET:
        params = {
            "changepoint_prior_scale": args.prophet_changepoint_prior_scale,
            "seasonality_mode": args.prophet_seasonality_mode,
            "weekly_seasonality": args.prophet_weekly_seasonality,
            "yearly_seasonality": args.prophet_yearly_seasonality,
            "daily_seasonality": args.prophet_daily_seasonality,
        }
    else:
        raise ValueError(f"Modelo no soportado: {model_name}")

    return ModelSpec(model_name=model_name, feature_mode=feature_mode, params=params)


def build_hybrid_model_name(base_spec: ModelSpec, residual_spec: ModelSpec) -> str:
    return f"hybrid_residual_{base_spec.model_name}_{residual_spec.model_name}"


def build_hybrid_model_params(args: argparse.Namespace, base_spec: ModelSpec, residual_spec: ModelSpec) -> dict[str, Any]:
    return {
        "base_model": base_spec.model_name,
        "base_feature_mode": base_spec.feature_mode,
        "base_params": base_spec.params,
        "residual_model": residual_spec.model_name,
        "residual_feature_mode": residual_spec.feature_mode,
        "residual_params": residual_spec.params,
        "residual_inner_splits": args.residual_inner_splits,
        "residual_min_oof_rows": args.residual_min_oof_rows,
        "uses_scaling": "mixed" if MODEL_RIDGE in {base_spec.model_name, residual_spec.model_name} else False,
        "uses_categorical_features": False,
        "hybrid_formula": "y_pred_final = y_pred_base + y_pred_residual",
        "residual_target_generation": "OOF temporal via TimeSeriesSplit dentro de cada fold externo",
    }


def build_feature_summary_from_column(predictions: pd.DataFrame, column_name: str) -> pd.DataFrame:
    values = predictions[column_name].fillna("").astype(str).map(str.strip)
    summary = (
        values.value_counts(dropna=False)
        .rename_axis(column_name)
        .reset_index(name="fold_count")
    )
    summary["feature_count"] = summary[column_name].map(
        lambda value: 0 if not value else len([token for token in value.split(",") if token])
    )
    summary["share_folds"] = summary["fold_count"] / max(len(predictions), 1)
    return summary


def fit_model_spec(
    spec: ModelSpec,
    *,
    train_data: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    args: argparse.Namespace,
):
    selected_features = resolve_feature_mode(
        train_data=train_data,
        feature_columns=feature_columns,
        target_column=target_column,
        feature_mode=spec.feature_mode,
    )

    if spec.model_name == MODEL_RIDGE:
        alpha_trace = select_best_alpha_time_series(
            train_data=train_data,
            feature_columns=selected_features,
            target_column=target_column,
            estimator_builder=lambda alpha: build_ridge_estimator(alpha, args),
            alpha_grid=spec.params["alpha_grid"],
            feature_mode=FEATURE_MODE_ALL,
            target_mode=TARGET_MODE_LEVEL,
            inner_splits=spec.params["inner_splits"],
            tuning_metric=spec.params["selection_metric"],
        )
        estimator = build_ridge_estimator(alpha_trace["best_alpha"], args)
        input_columns = list(selected_features)
        estimator.fit(train_data[input_columns], train_data[target_column])
        diagnostics = {
            "best_alpha": float(alpha_trace["best_alpha"]),
            "best_score": float(alpha_trace["best_score"]),
            "selection_metric": spec.params["selection_metric"],
            "inner_splits": int(spec.params["inner_splits"]),
            "transform_mode": spec.params["transform_mode"],
        }
        return estimator, input_columns, diagnostics

    if spec.model_name == MODEL_CATBOOST:
        estimator = build_catboost_estimator(args)
        input_columns = list(selected_features)
        estimator.fit(train_data[input_columns], train_data[target_column])
        diagnostics = dict(spec.params)
        return estimator, input_columns, diagnostics

    if spec.model_name == MODEL_PROPHET:
        estimator = build_prophet_estimator(args)
        input_columns = [DATE_COLUMN, *selected_features]
        estimator.fit(train_data[input_columns], train_data[target_column])
        diagnostics = dict(spec.params)
        return estimator, input_columns, diagnostics

    raise ValueError(f"Modelo no soportado: {spec.model_name}")


def predict_model_spec(estimator, test_data: pd.DataFrame, input_columns: list[str]) -> np.ndarray:
    return np.asarray(estimator.predict(test_data[input_columns]), dtype=float)


def build_temporal_oof_residual_dataset(
    *,
    train_data: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    base_spec: ModelSpec,
    args: argparse.Namespace,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    split_count = min(args.residual_inner_splits, len(train_data) - 1)
    min_train_size = max(args.residual_min_oof_rows, len(args.lags) + 4)
    if split_count < 2 or len(train_data) <= min_train_size:
        return pd.DataFrame(), {
            "split_count": split_count,
            "oof_rows": 0,
            "coverage_ratio": 0.0,
            "fallback_reason": "train_insuficiente_para_oof",
        }

    splitter = TimeSeriesSplit(n_splits=split_count)
    oof_frames: list[pd.DataFrame] = []

    for fold_number, (inner_train_idx, inner_valid_idx) in enumerate(splitter.split(train_data), start=1):
        if len(inner_train_idx) < min_train_size:
            continue
        inner_train = train_data.iloc[inner_train_idx].copy()
        inner_valid = train_data.iloc[inner_valid_idx].copy()
        fitted_base, input_columns, _ = fit_model_spec(
            base_spec,
            train_data=inner_train,
            feature_columns=feature_columns,
            target_column=target_column,
            args=args,
        )
        base_oof_pred = predict_model_spec(fitted_base, inner_valid, input_columns)
        fold_frame = inner_valid.copy()
        fold_frame["base_oof_pred"] = base_oof_pred
        fold_frame["residual_target"] = fold_frame[target_column].to_numpy(dtype=float) - base_oof_pred
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
    }


def build_zero_residual_predictions(test_data: pd.DataFrame, *, reason: str) -> tuple[np.ndarray, dict[str, Any], str]:
    estimator = DummyRegressor(strategy="constant", constant=0.0)
    estimator.fit(np.zeros((1, 1)), np.zeros(1))
    zero_pred = np.zeros(len(test_data), dtype=float)
    diagnostics = {"fallback_reason": reason}
    return zero_pred, diagnostics, ""


def walk_forward_predict_hybrid(
    *,
    args: argparse.Namespace,
    data: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    base_spec: ModelSpec,
    residual_spec: ModelSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if len(data) <= args.initial_train_size:
        raise ValueError(
            f"No hay suficientes filas para walk-forward. Filas={len(data)}, "
            f"initial_train_size={args.initial_train_size}."
        )

    predictions: list[dict[str, Any]] = []
    residual_audit_rows: list[pd.DataFrame] = []

    for test_idx in range(args.initial_train_size, len(data)):
        train_data = data.iloc[:test_idx].copy()
        test_data = data.iloc[[test_idx]].copy()

        fitted_base, base_input_columns, base_diagnostics = fit_model_spec(
            base_spec,
            train_data=train_data,
            feature_columns=feature_columns,
            target_column=target_column,
            args=args,
        )
        base_pred = predict_model_spec(fitted_base, test_data, base_input_columns)

        residual_train, residual_diagnostics = build_temporal_oof_residual_dataset(
            train_data=train_data,
            feature_columns=feature_columns,
            target_column=target_column,
            base_spec=base_spec,
            args=args,
        )

        if len(residual_train) < args.residual_min_oof_rows:
            residual_pred, residual_model_diagnostics, residual_selected_str = build_zero_residual_predictions(
                test_data,
                reason=(
                    residual_diagnostics["fallback_reason"]
                    or f"oof_rows<{args.residual_min_oof_rows}"
                ),
            )
            residual_selected_features = []
        else:
            fitted_residual, residual_input_columns, residual_model_diagnostics = fit_model_spec(
                residual_spec,
                train_data=residual_train,
                feature_columns=feature_columns,
                target_column="residual_target",
                args=args,
            )
            residual_pred = predict_model_spec(fitted_residual, test_data, residual_input_columns)
            residual_selected_features = [
                column for column in residual_input_columns if column != DATE_COLUMN
            ]
            residual_selected_str = ",".join(residual_selected_features)

        if not residual_train.empty:
            audit_frame = residual_train[[DATE_COLUMN, target_column, "base_oof_pred", "residual_target", "oof_fold"]].copy()
            audit_frame["outer_test_date"] = test_data[DATE_COLUMN].iloc[0]
            audit_frame["base_model"] = base_spec.model_name
            audit_frame["residual_model"] = residual_spec.model_name
            residual_audit_rows.append(audit_frame)

        base_selected_features = [column for column in base_input_columns if column != DATE_COLUMN]
        base_selected_str = ",".join(base_selected_features)
        union_selected = sorted(set(base_selected_features) | set(residual_selected_features))
        final_pred = base_pred + residual_pred
        y_true = float(test_data[target_column].iloc[0])
        y_current = float(test_data[CURRENT_TARGET_COLUMN].iloc[0])

        predictions.append(
            {
                DATE_COLUMN: test_data[DATE_COLUMN].iloc[0],
                "y_current": y_current,
                "y_true": y_true,
                "y_pred": float(final_pred[0]),
                "y_true_model": y_true,
                "y_pred_model": float(final_pred[0]),
                "y_pred_base": float(base_pred[0]),
                "y_pred_residual": float(residual_pred[0]),
                "error": float(final_pred[0] - y_true),
                "residual_component_abs_share": float(
                    abs(residual_pred[0]) / max(abs(final_pred[0]), 1e-8)
                ),
                "selected_feature_count": len(union_selected),
                "selected_features": ",".join(union_selected),
                "base_selected_feature_count": len(base_selected_features),
                "base_selected_features": base_selected_str,
                "residual_selected_feature_count": len(residual_selected_features),
                "residual_selected_features": residual_selected_str,
                "residual_train_rows": int(len(residual_train)),
                "residual_oof_coverage": float(residual_diagnostics["coverage_ratio"]),
                "base_diagnostics": json.dumps(base_diagnostics, ensure_ascii=False, sort_keys=True),
                "residual_diagnostics": json.dumps(
                    {**residual_diagnostics, **residual_model_diagnostics},
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            }
        )

    residual_audit = (
        pd.concat(residual_audit_rows, axis=0, ignore_index=True)
        if residual_audit_rows
        else pd.DataFrame(
            columns=[
                DATE_COLUMN,
                target_column,
                "base_oof_pred",
                "residual_target",
                "oof_fold",
                "outer_test_date",
                "base_model",
                "residual_model",
            ]
        )
    )
    return pd.DataFrame(predictions), residual_audit


def save_hybrid_outputs(
    *,
    run,
    horizon: int,
    predictions: pd.DataFrame,
    residual_audit: pd.DataFrame,
) -> None:
    run.save_dataframe(
        predictions,
        f"predicciones_h{horizon}.csv",
        artifact_type="predicciones",
        notes="Predicciones finales del híbrido con descomposición base + residual.",
    )
    run.save_dataframe(
        predictions[[DATE_COLUMN, "y_true", "y_pred_base"]],
        f"predicciones_base_h{horizon}.csv",
        artifact_type="predicciones_base",
        notes="Componente de predicción del modelo base.",
    )
    run.save_dataframe(
        predictions[[DATE_COLUMN, "y_true", "y_pred_residual"]],
        f"predicciones_residual_h{horizon}.csv",
        artifact_type="predicciones_residual",
        notes="Componente de predicción del learner residual.",
    )
    run.save_dataframe(
        residual_audit,
        f"residuales_entrenamiento_h{horizon}.csv",
        artifact_type="residuales_train",
        notes="Residuales OOF usados para entrenar el learner residual en cada fold externo.",
    )
    run.save_dataframe(
        build_feature_summary_from_column(predictions, "base_selected_features"),
        f"features_base_h{horizon}.csv",
        artifact_type="seleccion_features_base",
        notes="Resumen de features del modelo base por fold externo.",
    )
    run.save_dataframe(
        build_feature_summary_from_column(predictions, "residual_selected_features"),
        f"features_residual_h{horizon}.csv",
        artifact_type="seleccion_features_residual",
        notes="Resumen de features del learner residual por fold externo.",
    )


def summarize_rows_summary(predictions: pd.DataFrame) -> dict[str, Any]:
    return {
        "selected_feature_count_avg": float(predictions["selected_feature_count"].mean()),
        "selected_feature_count_min": int(predictions["selected_feature_count"].min()),
        "selected_feature_count_max": int(predictions["selected_feature_count"].max()),
        "base_selected_feature_count_avg": float(predictions["base_selected_feature_count"].mean()),
        "residual_selected_feature_count_avg": float(predictions["residual_selected_feature_count"].mean()),
        "residual_train_rows_avg": float(predictions["residual_train_rows"].mean()),
        "residual_oof_coverage_avg": float(predictions["residual_oof_coverage"].mean()),
        "residual_component_abs_share_avg": float(predictions["residual_component_abs_share"].mean()),
    }


def main() -> None:
    args = parse_args()
    base_spec = build_model_spec(args, role="base")
    residual_spec = build_model_spec(args, role="residual")
    model_name = build_hybrid_model_name(base_spec, residual_spec)
    reference_run_ids = normalize_reference_run_ids(args.reference_run_id, args.extra_reference_run_ids)

    tracker = RadarExperimentTracker(workbook_path=args.workbook, runs_dir=args.runs_dir)
    reference_values = tracker.get_reference_values()
    df = load_master_dataset(dataset_path=args.dataset_path, sheet_name=args.sheet_name)
    base_feature_columns = get_base_feature_columns(df)

    run = tracker.start_run(
        run_id=args.run_id,
        experiment_id="E8",
        family="hibrido_residual",
        model=model_name,
        script_path=__file__,
        parametros=build_run_parameters(
            args=args,
            model_name=model_name,
            feature_columns=base_feature_columns,
            model_params=build_hybrid_model_params(args, base_spec, residual_spec),
        ),
    )

    predictions_by_horizon: dict[int, pd.DataFrame] = {}
    horizon_results: list[dict[str, Any]] = []
    rows_summary: list[dict[str, Any]] = []
    dataset_periodo = f"{df[DATE_COLUMN].min().date()} a {df[DATE_COLUMN].max().date()}"
    comentarios = (
        f"Híbrido residual temporal limpio | hipotesis={args.hypothesis_note or 'sin_notas'} | "
        f"base={base_spec.model_name}({base_spec.feature_mode}) | "
        f"residual={residual_spec.model_name}({residual_spec.feature_mode}) | "
        "y_pred_final = y_pred_base + y_pred_residual | "
        "residuales entrenados con OOF temporal via TimeSeriesSplit dentro de cada fold externo"
    )

    for horizon in args.horizons:
        modeling_df, modeling_features, target_column = build_model_frame(
            df=df,
            horizon=horizon,
            feature_columns=base_feature_columns,
            lags=args.lags,
            target_mode=args.target_mode,
        )
        predictions, residual_audit = walk_forward_predict_hybrid(
            args=args,
            data=modeling_df,
            feature_columns=modeling_features,
            target_column=target_column,
            base_spec=base_spec,
            residual_spec=residual_spec,
        )
        predictions["horizonte_sem"] = horizon
        predictions["target_mode"] = args.target_mode
        predictions["feature_mode"] = args.feature_mode
        predictions["residual_feature_mode"] = args.residual_feature_mode
        predictions["run_id"] = args.run_id
        predictions["model_name"] = model_name
        predictions_by_horizon[horizon] = predictions
        save_hybrid_outputs(run=run, horizon=horizon, predictions=predictions, residual_audit=residual_audit)

        summary_row = {
            "horizonte_sem": horizon,
            "rows_modeling": len(modeling_df),
            "rows_eval": len(predictions),
            "feature_candidates": len(modeling_features),
            "feature_mode": args.feature_mode,
            "residual_feature_mode": args.residual_feature_mode,
            "target_mode": args.target_mode,
            **summarize_rows_summary(predictions),
        }
        rows_summary.append(summary_row)

        metrics = compute_radar_metrics(predictions)
        loss_h = compute_loss_h(metrics=metrics, horizon=horizon, reference_values=reference_values)
        horizon_results.append(
            {
                "horizonte_sem": horizon,
                "target": args.target_mode,
                "variables_temporales": f"y_t + lags {list(args.lags)}",
                "variables_tematicas": ", ".join(base_feature_columns),
                "transformacion": "hibrido_residual",
                "seleccion_variables": f"base={base_spec.feature_mode};residual={residual_spec.feature_mode}",
                "validacion": "walk-forward_expanding",
                "dataset_periodo": dataset_periodo,
                "notas_config": build_notas_config(
                    args=args,
                    model_name=model_name,
                    model_params=build_hybrid_model_params(args, base_spec, residual_spec),
                    horizon=horizon,
                    summary_row=summary_row,
                ),
                "estado": "corrido",
                "comentarios": comentarios,
                "loss_h": loss_h,
                **metrics,
            }
        )

    run.save_json(
        rows_summary,
        "resumen_modeling_horizontes.json",
        artifact_type="resumen",
        notes="Resumen de complejidad, cobertura OOF y descomposición base/residual por horizonte.",
    )

    total_radar = compute_total_radar_loss(
        horizon_results=horizon_results,
        reference_values=reference_values,
        l_coh=None,
    )
    if reference_run_ids:
        save_reference_comparisons(
            run=run,
            workbook_path=tracker.workbook_path,
            clean_run_id=args.run_id,
            reference_run_ids=reference_run_ids,
            horizon_results=horizon_results,
            l_total_radar=float(total_radar["l_total_radar"]),
        )

    run.finalize(
        horizon_results=horizon_results,
        target=args.target_mode,
        variables_temporales=f"y_t + lags {list(args.lags)}",
        variables_tematicas=", ".join(base_feature_columns),
        transformacion="hibrido_residual",
        seleccion_variables=f"base={base_spec.feature_mode};residual={residual_spec.feature_mode}",
        validacion="walk-forward_expanding",
        dataset_periodo=dataset_periodo,
        notas_config=json.dumps(rows_summary, ensure_ascii=False),
        estado="corrido",
        comentarios=f"{comentarios} | L_total_Radar={total_radar['l_total_radar']:.6f}",
    )

    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {total_radar['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
