#!/usr/bin/env python3
from __future__ import annotations

import argparse

import numpy as np
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline

from config import TRANSFORM_MODE_CHOICES, TRANSFORM_MODE_STANDARD
from pipeline_common import add_common_experiment_args, finalize_common_args, run_tabular_experiment
from preprocessing import build_feature_transformer, describe_transform_mode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E1 | Familia lineal regularizada con RidgeCV.",
    )
    add_common_experiment_args(parser, default_run_id="E1_v2")
    parser.add_argument(
        "--transform-mode",
        choices=TRANSFORM_MODE_CHOICES,
        default=TRANSFORM_MODE_STANDARD,
        help="Transformacion aplicada dentro del pipeline de Ridge.",
    )
    parser.add_argument(
        "--winsor-lower-quantile",
        type=float,
        default=0.05,
        help="Cuantil inferior para winsorizacion cuando transform_mode='winsor'.",
    )
    parser.add_argument(
        "--winsor-upper-quantile",
        type=float,
        default=0.95,
        help="Cuantil superior para winsorizacion cuando transform_mode='winsor'.",
    )
    parser.add_argument("--alpha-grid-min-exp", type=float, default=-4.0)
    parser.add_argument("--alpha-grid-max-exp", type=float, default=4.0)
    parser.add_argument("--alpha-grid-points", type=int, default=41)
    return finalize_common_args(parser.parse_args())


def build_estimator(args: argparse.Namespace) -> Pipeline:
    alphas = np.logspace(
        args.alpha_grid_min_exp,
        args.alpha_grid_max_exp,
        args.alpha_grid_points,
    )
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
            ("model", RidgeCV(alphas=alphas)),
        ]
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "alphas": list(
            np.logspace(
                args.alpha_grid_min_exp,
                args.alpha_grid_max_exp,
                args.alpha_grid_points,
            )
        ),
        "transform_mode": args.transform_mode,
        "winsor_lower_quantile": args.winsor_lower_quantile,
        "winsor_upper_quantile": args.winsor_upper_quantile,
    }


def main() -> None:
    args = parse_args()
    result = run_tabular_experiment(
        args=args,
        script_path=__file__,
        experiment_id="E1",
        family="lineal_regularizado",
        model_name="RidgeCV",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        transformacion=describe_transform_mode(args.transform_mode),
        comentarios=(
            f"Familia lineal regularizada con RidgeCV | "
            f"transform_mode={args.transform_mode}."
        ),
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Radar: {result['l_total_radar']:.6f}")


if __name__ == "__main__":
    main()
