#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

import numpy as np
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import (
    CURRENT_TARGET_COLUMN,
    DATASET_PATH,
    DEFAULT_INITIAL_TRAIN_SIZE,
    DEFAULT_LAGS,
)
from data_master import get_base_feature_columns, load_master_dataset
from evaluation import compute_radar_metrics, walk_forward_predict
from experiment_logger import RadarExperimentTracker
from feature_engineering import build_model_frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Corre el baseline E1 Ridge para 1..4 semanas.")
    parser.add_argument("--run-id", default="E1_v2", help="Run_ID a registrar en el grid.")
    parser.add_argument(
        "--initial-train-size",
        type=int,
        default=DEFAULT_INITIAL_TRAIN_SIZE,
        help=f"Tamano inicial de entrenamiento para walk-forward. Default: {DEFAULT_INITIAL_TRAIN_SIZE}",
    )
    return parser.parse_args()


def build_estimator() -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", RidgeCV(alphas=np.logspace(-4, 4, 41))),
        ]
    )


def main() -> None:
    args = parse_args()
    df = load_master_dataset(dataset_path=DATASET_PATH)
    feature_columns = get_base_feature_columns(df)

    tracker = RadarExperimentTracker()
    run = tracker.start_run(
        run_id=args.run_id,
        experiment_id="E1",
        family="lineal",
        model="RidgeCV",
        script_path=__file__,
        parametros={
            "dataset_path": str(DATASET_PATH),
            "feature_columns": feature_columns,
            "lags": list(DEFAULT_LAGS),
            "initial_train_size": args.initial_train_size,
            "model": "RidgeCV",
            "alphas": list(np.logspace(-4, 4, 41)),
        },
    )

    horizon_results: list[dict[str, float | int | str]] = []
    rows_summary: list[dict[str, int | str]] = []

    for horizon in (1, 2, 3, 4):
        modeling_df, modeling_features, target_column = build_model_frame(
            df=df,
            horizon=horizon,
            feature_columns=feature_columns,
            lags=DEFAULT_LAGS,
        )
        estimator = build_estimator()
        predictions = walk_forward_predict(
            estimator=estimator,
            data=modeling_df,
            feature_columns=modeling_features,
            target_column=target_column,
            initial_train_size=args.initial_train_size,
        )
        metrics = compute_radar_metrics(predictions)

        run.save_dataframe(
            predictions,
            f"predicciones_h{horizon}.csv",
            artifact_type="predicciones",
            notes=f"Walk-forward Ridge para horizonte {horizon}.",
        )

        rows_summary.append(
            {
                "horizonte_sem": horizon,
                "rows_modeling": len(modeling_df),
                "rows_eval": len(predictions),
                "feature_count": len(modeling_features),
            }
        )

        horizon_results.append(
            {
                "horizonte_sem": horizon,
                "target": "nivel",
                "variables_temporales": "y_t + lags 1..4",
                "variables_tematicas": ", ".join(feature_columns),
                "transformacion": "estandarizada",
                "seleccion_variables": "todas",
                "validacion": "walk-forward_expanding",
                "dataset_periodo": (
                    f"{df['fecha_inicio_semana'].min().date()} a "
                    f"{df['fecha_inicio_semana'].max().date()}"
                ),
                "notas_config": (
                    f"RidgeCV con {len(modeling_features)} features, "
                    f"lags={list(DEFAULT_LAGS)}, initial_train_size={args.initial_train_size}"
                ),
                **metrics,
            }
        )

    run.save_json(
        rows_summary,
        "resumen_modeling_horizontes.json",
        artifact_type="resumen",
        notes="Resumen de tamanos por horizonte.",
    )

    run.finalize(
        horizon_results=horizon_results,
        target="nivel",
        variables_temporales="y_t + lags",
        variables_tematicas=", ".join(feature_columns),
        transformacion="estandarizada",
        seleccion_variables="todas",
        validacion="walk-forward_expanding",
        dataset_periodo=f"{df['fecha_inicio_semana'].min().date()} a {df['fecha_inicio_semana'].max().date()}",
        notas_config=json.dumps(rows_summary, ensure_ascii=False),
        estado="corrido",
        comentarios="Baseline E1 RidgeCV sobre dataset maestro de aceptación digital.",
    )

    print(f"Run registrado: {args.run_id}")
    print("Horizontes procesados: 1, 2, 3, 4")


if __name__ == "__main__":
    main()
