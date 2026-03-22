from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from config import (
    DATASET_PATH,
    DATE_COLUMN,
    DEFAULT_HORIZONS,
    DEFAULT_INITIAL_TRAIN_SIZE,
    DEFAULT_LAGS,
    DEFAULT_SHEET_NAME,
    FEATURE_MODE_ALL,
    FEATURE_MODE_CHOICES,
    TARGET_COLUMNS,
    TARGET_MODE_CHOICES,
    TARGET_MODE_LEVEL,
)
from data_master import get_base_feature_columns, load_master_dataset
from evaluation import compute_loss_h, compute_radar_metrics, compute_total_radar_loss, walk_forward_predict
from experiment_logger import DEFAULT_RUNS_DIR, DEFAULT_WORKBOOK, RadarExperimentTracker
from feature_engineering import build_model_frame


def parse_int_sequence(raw_value: str, label: str) -> tuple[int, ...]:
    values = []
    for token in raw_value.split(","):
        token = token.strip()
        if not token:
            continue
        values.append(int(token))
    if not values:
        raise ValueError(f"{label} no puede quedar vacio.")
    return tuple(values)


def parse_lags(raw_value: str) -> tuple[int, ...]:
    return parse_int_sequence(raw_value, label="lags")


def parse_horizons(raw_value: str) -> tuple[int, ...]:
    horizons = parse_int_sequence(raw_value, label="horizons")
    invalid = [horizon for horizon in horizons if horizon not in TARGET_COLUMNS]
    if invalid:
        raise ValueError(f"Horizontes no soportados: {invalid}. Usa {sorted(TARGET_COLUMNS)}.")
    return horizons


def parse_order(raw_value: str) -> tuple[int, int, int]:
    values = parse_int_sequence(raw_value, label="order")
    if len(values) != 3:
        raise ValueError("order debe tener exactamente tres enteros, por ejemplo 1,0,0.")
    return values[0], values[1], values[2]


def add_common_experiment_args(parser: argparse.ArgumentParser, *, default_run_id: str) -> None:
    parser.add_argument("--run-id", default=default_run_id, help="Run_ID a registrar en el grid.")
    parser.add_argument(
        "--target-mode",
        choices=TARGET_MODE_CHOICES,
        default=TARGET_MODE_LEVEL,
        help="Modo de target del modelo: nivel o delta.",
    )
    parser.add_argument(
        "--lags",
        default=",".join(str(lag) for lag in DEFAULT_LAGS),
        help="Lags separados por coma. Ejemplo: 1,2,3,4",
    )
    parser.add_argument(
        "--feature-mode",
        choices=FEATURE_MODE_CHOICES,
        default=FEATURE_MODE_ALL,
        help="Modo de seleccion de features.",
    )
    parser.add_argument(
        "--initial-train-size",
        type=int,
        default=DEFAULT_INITIAL_TRAIN_SIZE,
        help=f"Tamano inicial de entrenamiento. Default: {DEFAULT_INITIAL_TRAIN_SIZE}",
    )
    parser.add_argument(
        "--horizons",
        default=",".join(str(horizon) for horizon in DEFAULT_HORIZONS),
        help="Horizontes a correr, separados por coma.",
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=DATASET_PATH,
        help=f"Ruta del dataset maestro. Default: {DATASET_PATH}",
    )
    parser.add_argument(
        "--sheet-name",
        default=DEFAULT_SHEET_NAME,
        help=f"Hoja del dataset maestro. Default: {DEFAULT_SHEET_NAME}",
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_WORKBOOK,
        help=f"Workbook del grid de experimentos. Default: {DEFAULT_WORKBOOK}",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=DEFAULT_RUNS_DIR,
        help=f"Directorio donde se guardan runs y artefactos. Default: {DEFAULT_RUNS_DIR}",
    )


def finalize_common_args(args: argparse.Namespace) -> argparse.Namespace:
    args.lags = parse_lags(args.lags)
    args.horizons = parse_horizons(args.horizons)
    args.dataset_path = args.dataset_path.expanduser().resolve()
    args.workbook = args.workbook.expanduser().resolve()
    args.runs_dir = args.runs_dir.expanduser().resolve()
    return args


def serialize_model_params(model_params: dict[str, Any] | None) -> dict[str, Any]:
    if not model_params:
        return {}
    serialized: dict[str, Any] = {}
    for key, value in model_params.items():
        if isinstance(value, Path):
            serialized[key] = str(value)
        elif isinstance(value, tuple):
            serialized[key] = list(value)
        else:
            serialized[key] = value
    return serialized


def build_run_parameters(
    args: argparse.Namespace,
    model_name: str,
    feature_columns: list[str],
    model_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "dataset_path": str(args.dataset_path),
        "sheet_name": args.sheet_name,
        "model": model_name,
        "target_mode": args.target_mode,
        "feature_mode": args.feature_mode,
        "transform_mode": getattr(args, "transform_mode", ""),
        "feature_columns": feature_columns,
        "lags": list(args.lags),
        "horizons": list(args.horizons),
        "initial_train_size": args.initial_train_size,
        "model_params": serialize_model_params(model_params),
    }


def build_notas_config(
    args: argparse.Namespace,
    model_name: str,
    model_params: dict[str, Any] | None,
    horizon: int,
    summary_row: dict[str, Any],
) -> str:
    payload = {
        "model": model_name,
        "target_mode": args.target_mode,
        "feature_mode": args.feature_mode,
        "transform_mode": getattr(args, "transform_mode", ""),
        "lags": list(args.lags),
        "initial_train_size": args.initial_train_size,
        "horizon": horizon,
        "rows_modeling": summary_row["rows_modeling"],
        "rows_eval": summary_row["rows_eval"],
        "feature_candidates": summary_row["feature_candidates"],
        "selected_feature_count_avg": summary_row["selected_feature_count_avg"],
        "model_params": serialize_model_params(model_params),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def save_run_outputs(
    run,
    predictions_by_horizon: dict[int, Any],
    rows_summary: list[dict[str, Any]],
) -> None:
    for horizon, predictions in predictions_by_horizon.items():
        run.save_dataframe(
            predictions,
            f"predicciones_h{horizon}.csv",
            artifact_type="predicciones",
            notes=f"Predicciones walk-forward para horizonte {horizon}.",
        )

    run.save_json(
        rows_summary,
        "resumen_modeling_horizontes.json",
        artifact_type="resumen",
        notes="Resumen de tamanos y seleccion de features por horizonte.",
    )


def run_tabular_experiment(
    *,
    args: argparse.Namespace,
    script_path: str | Path,
    experiment_id: str,
    family: str,
    model_name: str,
    estimator,
    model_params: dict[str, Any] | None = None,
    transformacion: str = "",
    comentarios: str = "",
    always_include_columns: list[str] | None = None,
    l_coh: float | None = None,
) -> dict[str, Any]:
    tracker = RadarExperimentTracker(workbook_path=args.workbook, runs_dir=args.runs_dir)
    reference_values = tracker.get_reference_values()
    df = load_master_dataset(dataset_path=args.dataset_path, sheet_name=args.sheet_name)
    base_feature_columns = get_base_feature_columns(df)

    run = tracker.start_run(
        run_id=args.run_id,
        experiment_id=experiment_id,
        family=family,
        model=model_name,
        script_path=script_path,
        parametros=build_run_parameters(
            args=args,
            model_name=model_name,
            feature_columns=base_feature_columns,
            model_params=model_params,
        ),
    )

    predictions_by_horizon: dict[int, Any] = {}
    horizon_results: list[dict[str, Any]] = []
    rows_summary: list[dict[str, Any]] = []
    dataset_periodo = f"{df[DATE_COLUMN].min().date()} a {df[DATE_COLUMN].max().date()}"

    for horizon in args.horizons:
        modeling_df, modeling_features, target_column = build_model_frame(
            df=df,
            horizon=horizon,
            feature_columns=base_feature_columns,
            lags=args.lags,
            target_mode=args.target_mode,
        )
        predictions = walk_forward_predict(
            estimator=estimator,
            data=modeling_df,
            feature_columns=modeling_features,
            target_column=target_column,
            actual_target_column=TARGET_COLUMNS[horizon],
            initial_train_size=args.initial_train_size,
            feature_mode=args.feature_mode,
            target_mode=args.target_mode,
            always_include_columns=always_include_columns,
        )
        predictions["horizonte_sem"] = horizon
        predictions["target_mode"] = args.target_mode
        predictions["feature_mode"] = args.feature_mode
        predictions["transform_mode"] = getattr(args, "transform_mode", "")
        predictions["run_id"] = args.run_id
        predictions["model_name"] = model_name
        predictions_by_horizon[horizon] = predictions

        summary_row = {
            "horizonte_sem": horizon,
            "rows_modeling": len(modeling_df),
            "rows_eval": len(predictions),
            "feature_candidates": len(modeling_features),
            "selected_feature_count_avg": float(predictions["selected_feature_count"].mean()),
            "selected_feature_count_min": int(predictions["selected_feature_count"].min()),
            "selected_feature_count_max": int(predictions["selected_feature_count"].max()),
            "feature_mode": args.feature_mode,
            "target_mode": args.target_mode,
            "transform_mode": getattr(args, "transform_mode", ""),
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
                "transformacion": transformacion,
                "seleccion_variables": args.feature_mode,
                "validacion": "walk-forward_expanding",
                "dataset_periodo": dataset_periodo,
                "notas_config": build_notas_config(
                    args=args,
                    model_name=model_name,
                    model_params=model_params,
                    horizon=horizon,
                    summary_row=summary_row,
                ),
                "estado": "corrido",
                "comentarios": comentarios,
                "loss_h": loss_h,
                **metrics,
            }
        )

    save_run_outputs(run=run, predictions_by_horizon=predictions_by_horizon, rows_summary=rows_summary)
    total_radar = compute_total_radar_loss(
        horizon_results=horizon_results,
        reference_values=reference_values,
        l_coh=l_coh,
    )

    run.finalize(
        horizon_results=horizon_results,
        target=args.target_mode,
        variables_temporales=f"y_t + lags {list(args.lags)}",
        variables_tematicas=", ".join(base_feature_columns),
        transformacion=transformacion,
        seleccion_variables=args.feature_mode,
        validacion="walk-forward_expanding",
        dataset_periodo=dataset_periodo,
        notas_config=json.dumps(rows_summary, ensure_ascii=False),
        estado="corrido",
        comentarios=(
            f"{comentarios} | L_total_Radar={total_radar['l_total_radar']:.6f}"
            if comentarios
            else f"L_total_Radar={total_radar['l_total_radar']:.6f}"
        ),
        l_coh=l_coh,
    )

    return {
        "workbook_path": tracker.workbook_path,
        "run_dir": run.run_dir,
        "horizon_results": horizon_results,
        "rows_summary": rows_summary,
        "l_total_radar": total_radar["l_total_radar"],
    }


def run_time_series_experiment(**kwargs) -> dict[str, Any]:
    return run_tabular_experiment(**kwargs)
