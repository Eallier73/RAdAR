#!/usr/bin/env python3
from __future__ import annotations

import argparse

from classification_pipeline_common import (
    add_common_classification_args,
    add_reference_comparison_args,
    finalize_common_classification_args,
    prepare_classification_references,
    run_classification_experiment,
)
from config import CLASS_LABELS_5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="C2 | Familia XGBoostClassifier multiclase bajo walk-forward temporal.",
    )
    add_common_classification_args(parser, default_run_id="C2_v1_clean")
    parser.set_defaults(
        feature_mode="all",
        target_mode_clf="bandas_5clases",
        lags="1,2,3,4,5,6",
        initial_train_size=40,
        horizons="1,2,3,4",
    )
    add_reference_comparison_args(parser, default_reference_run_id="")
    parser.add_argument("--n-estimators", type=int, default=200)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--subsample", type=float, default=0.8)
    parser.add_argument("--colsample-bytree", type=float, default=0.8)
    parser.add_argument("--min-child-weight", type=float, default=4.0)
    parser.add_argument("--reg-alpha", type=float, default=0.5)
    parser.add_argument("--reg-lambda", type=float, default=2.0)
    parser.add_argument("--objective", default="multi:softprob")
    parser.add_argument("--eval-metric", default="mlogloss")
    return finalize_common_classification_args(parser.parse_args())


def build_estimator(args: argparse.Namespace):
    from xgboost import XGBClassifier

    return XGBClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
        subsample=args.subsample,
        colsample_bytree=args.colsample_bytree,
        min_child_weight=args.min_child_weight,
        reg_alpha=args.reg_alpha,
        reg_lambda=args.reg_lambda,
        objective=args.objective,
        eval_metric=args.eval_metric,
        num_class=len(CLASS_LABELS_5),
        random_state=args.random_seed,
        n_jobs=4,
    )


def build_model_params(args: argparse.Namespace) -> dict[str, object]:
    return {
        "n_estimators": args.n_estimators,
        "max_depth": args.max_depth,
        "learning_rate": args.learning_rate,
        "subsample": args.subsample,
        "colsample_bytree": args.colsample_bytree,
        "min_child_weight": args.min_child_weight,
        "reg_alpha": args.reg_alpha,
        "reg_lambda": args.reg_lambda,
        "objective": args.objective,
        "eval_metric": args.eval_metric,
        "random_seed": args.random_seed,
        "uses_scaling": False,
        "tuning_strategy": "baseline_fijo_sin_tuning_interno",
    }


def main() -> None:
    args = parse_args()
    reference_run_ids = prepare_classification_references(args.reference_run_id, args.extra_reference_run_ids)
    result = run_classification_experiment(
        args=args,
        script_path=__file__,
        experiment_id="C2",
        family="clasificacion_xgboost",
        model_name="xgboost_classifier",
        estimator=build_estimator(args),
        model_params=build_model_params(args),
        comentarios=(
            "XGBoostClassifier limpio con walk-forward temporal | "
            f"hipotesis={args.hypothesis_note or 'xgboost_clasificacion_baseline'} | "
            "baseline fijo sin tuning interno"
        ),
        reference_run_ids=reference_run_ids,
    )
    print(f"Run registrado: {args.run_id}")
    print(f"Horizontes procesados: {', '.join(str(h) for h in args.horizons)}")
    print(f"L_total_Clasificacion: {result['l_total_clasificacion']:.6f}")


if __name__ == "__main__":
    main()
