from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .frozen_inference import PredictOnlyNotReadyError, generate_pending_forecasts_for_e9, generate_pending_forecasts_for_profile
from .frozen_inference_assets import predict_only_asset_status
from .frozen_profiles import (
    DEFAULT_OPERATION_DATASET,
    NUMERIC_PRIMARY_RUN_ID,
    RISK_PRIMARY_RUN_ID,
    load_all_operation_profiles,
    resolve_latest_canonical_run_dir,
    week_slug,
)
from .run_context import build_repo_context_snapshot, now_text, resolve_week_window
from ..modeling.core.config import DATE_COLUMN
from ..modeling.core.data_master import load_master_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construye el registro formal de emisiones post-W10 usando perfiles congelados."
    )
    parser.add_argument("--operation-id", required=True)
    parser.add_argument("--operation-root", type=Path, required=True)
    parser.add_argument("--from-week", required=True)
    parser.add_argument("--to-week", required=True)
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_OPERATION_DATASET)
    parser.add_argument("--comment", default="")
    parser.add_argument("--e1-run-dir", type=Path)
    parser.add_argument("--e9-run-dir", type=Path)
    return parser.parse_args()


def _load_predictions_by_horizon(run_dir: Path) -> dict[int, pd.DataFrame]:
    frames: dict[int, pd.DataFrame] = {}
    for path in sorted(run_dir.glob("predicciones_h*.csv")):
        horizon = int(path.stem.split("h")[-1])
        frame = pd.read_csv(path)
        if DATE_COLUMN in frame.columns:
            frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN])
        elif "fecha" in frame.columns:
            frame[DATE_COLUMN] = pd.to_datetime(frame["fecha"])
        frames[horizon] = frame.sort_values(DATE_COLUMN, kind="stable").reset_index(drop=True)
    return frames


def _filter_since(frames: dict[int, pd.DataFrame], start_date: pd.Timestamp) -> dict[int, pd.DataFrame]:
    filtered: dict[int, pd.DataFrame] = {}
    for horizon, frame in frames.items():
        filtered[horizon] = frame.loc[frame[DATE_COLUMN] >= start_date].copy().reset_index(drop=True)
    return filtered


def _write_prediction_snapshots(
    *,
    bundle_run_id: str,
    horizon_frames: dict[int, pd.DataFrame],
    target_dir: Path,
) -> list[str]:
    artifact_paths: list[str] = []
    for horizon, frame in horizon_frames.items():
        if frame is None or frame.empty:
            continue
        path = target_dir / f"{bundle_run_id}_pending_h{horizon}.csv"
        frame.to_csv(path, index=False)
        artifact_paths.append(str(path))
    return artifact_paths


def _build_registry_rows(
    *,
    operation_id: str,
    role: str,
    model_profile_id: str,
    evaluated: dict[int, pd.DataFrame],
    pending: dict[int, pd.DataFrame],
    repo_context: dict[str, Any],
    dataset_path: Path,
    operation_start: pd.Timestamp,
    operation_end: pd.Timestamp,
    evaluated_run_dir: str | None,
    comments: str,
) -> list[dict[str, Any]]:
    dates: set[pd.Timestamp] = set()
    for frames in (evaluated, pending):
        for frame in frames.values():
            if frame is None or frame.empty:
                continue
            dates.update(pd.to_datetime(frame[DATE_COLUMN]).tolist())

    rows: list[dict[str, Any]] = []
    for base_date in sorted(date for date in dates if date >= operation_start):
        row: dict[str, Any] = {
            "emission_id": f"{operation_id}:{model_profile_id}:{base_date.date().isoformat()}",
            "operation_id": operation_id,
            "model_profile_id": model_profile_id,
            "role": role,
            "fecha_inicio_semana": base_date.date().isoformat(),
            "semana_iso": week_slug(base_date.date()),
            "tramo_cubierto_desde": operation_start.date().isoformat(),
            "tramo_cubierto_hasta": operation_end.date().isoformat(),
            "repo_commit": repo_context.get("commit", ""),
            "repo_branch": repo_context.get("branch", ""),
            "dataset_reference": str(dataset_path),
            "historical_run_dir": evaluated_run_dir or "",
            "estado_emision": "emitido",
            "comentarios_operativos": comments,
        }
        actuals_present = 0
        predictions_present = 0
        for horizon in (1, 2, 3, 4):
            pred = None
            actual = None
            source = ""
            eval_frame = evaluated.get(horizon)
            if eval_frame is not None and not eval_frame.empty:
                hit = eval_frame.loc[eval_frame[DATE_COLUMN] == base_date]
                if not hit.empty:
                    pred = float(hit.iloc[0]["y_pred"])
                    actual_raw = hit.iloc[0].get("y_true")
                    actual = None if pd.isna(actual_raw) else float(actual_raw)
                    source = "walk_forward_eval"
            if source == "":
                pending_frame = pending.get(horizon)
                if pending_frame is not None and not pending_frame.empty:
                    hit = pending_frame.loc[pending_frame[DATE_COLUMN] == base_date]
                    if not hit.empty:
                        pred = float(hit.iloc[0]["y_pred"])
                        source = str(hit.iloc[0].get("prediction_source", "forecast_pending"))
            row[f"prediccion_h{horizon}"] = pred
            row[f"actual_h{horizon}"] = actual
            row[f"prediction_source_h{horizon}"] = source
            if pred is not None:
                predictions_present += 1
            if actual is not None:
                actuals_present += 1
        if predictions_present == 0:
            continue
        if actuals_present == 4:
            row["estado_evaluacion"] = "evaluado"
        elif actuals_present == 0:
            row["estado_evaluacion"] = "pendiente_de_evaluacion"
        else:
            row["estado_evaluacion"] = "parcialmente_evaluable"
        rows.append(row)
    return rows


def _save_registry(
    *,
    rows: list[dict[str, Any]],
    target_dir: Path,
    operation_id: str,
    payload: dict[str, Any],
) -> dict[str, str]:
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.sort_values(["role", "fecha_inicio_semana"], kind="stable").reset_index(drop=True)
    csv_path = target_dir / "registro_emisiones.csv"
    json_path = target_dir / "registro_emisiones.json"
    latest_path = target_dir / "manifest_ultima_actualizacion.json"
    frame.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    stamped = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshots_dir = target_dir.parent / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    (snapshots_dir / f"registro_emisiones_{stamped}.csv").write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
    (snapshots_dir / f"registro_emisiones_{stamped}.json").write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    return {
        "csv": str(csv_path),
        "json": str(json_path),
        "latest_manifest": str(latest_path),
    }


def main() -> int:
    args = parse_args()
    args.operation_root = args.operation_root.expanduser().resolve()
    args.dataset_path = args.dataset_path.expanduser().resolve()

    operation_start = pd.Timestamp(resolve_week_window(args.from_week).start_date)
    operation_end = pd.Timestamp(resolve_week_window(args.to_week).start_date)
    repo_context = build_repo_context_snapshot()
    profiles = load_all_operation_profiles()
    args.e1_run_dir = (args.e1_run_dir or resolve_latest_canonical_run_dir(NUMERIC_PRIMARY_RUN_ID)).expanduser().resolve()
    args.e9_run_dir = (args.e9_run_dir or resolve_latest_canonical_run_dir(RISK_PRIMARY_RUN_ID)).expanduser().resolve()

    master_df = load_master_dataset(dataset_path=args.dataset_path)

    snapshots_dir = args.operation_root / "snapshots"
    emisiones_dir = args.operation_root / "emisiones"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    emisiones_dir.mkdir(parents=True, exist_ok=True)

    snapshot_artifacts: list[str] = []
    profile_statuses: dict[str, Any] = {
        NUMERIC_PRIMARY_RUN_ID: predict_only_asset_status(NUMERIC_PRIMARY_RUN_ID),
        RISK_PRIMARY_RUN_ID: predict_only_asset_status(RISK_PRIMARY_RUN_ID),
    }

    pending_e1_bundle = generate_pending_forecasts_for_profile(
        profiles[NUMERIC_PRIMARY_RUN_ID],
        dataset_path=args.dataset_path,
        df_master=master_df,
    )
    profile_statuses[NUMERIC_PRIMARY_RUN_ID] = {
        **profile_statuses[NUMERIC_PRIMARY_RUN_ID],
        "runtime_status": "ready",
        "asset_manifest_path": pending_e1_bundle.asset_manifest_path,
        "package_root": pending_e1_bundle.package_root,
    }
    snapshot_artifacts.extend(
        _write_prediction_snapshots(
            bundle_run_id=NUMERIC_PRIMARY_RUN_ID,
            horizon_frames=pending_e1_bundle.horizon_frames,
            target_dir=snapshots_dir,
        )
    )

    pending_e9_bundle = None
    e9_blocker = None
    try:
        pending_e9_bundle = generate_pending_forecasts_for_e9(
            profiles[RISK_PRIMARY_RUN_ID],
            dataset_path=args.dataset_path,
            df_master=master_df,
        )
        snapshot_artifacts.extend(
            _write_prediction_snapshots(
                bundle_run_id=RISK_PRIMARY_RUN_ID,
                horizon_frames=pending_e9_bundle.horizon_frames,
                target_dir=snapshots_dir,
            )
        )
        profile_statuses[RISK_PRIMARY_RUN_ID] = {
            **profile_statuses[RISK_PRIMARY_RUN_ID],
            "runtime_status": "ready",
            "asset_manifest_path": pending_e9_bundle.asset_manifest_path,
            "package_root": pending_e9_bundle.package_root,
        }
    except PredictOnlyNotReadyError as exc:
        e9_blocker = str(exc)
        profile_statuses[RISK_PRIMARY_RUN_ID] = {
            **profile_statuses[RISK_PRIMARY_RUN_ID],
            "runtime_status": "blocked",
            "reason": e9_blocker,
        }

    evaluated_e1 = _filter_since(_load_predictions_by_horizon(args.e1_run_dir), operation_start)
    evaluated_e9 = _filter_since(_load_predictions_by_horizon(args.e9_run_dir), operation_start)

    rows: list[dict[str, Any]] = []
    rows.extend(
        _build_registry_rows(
            operation_id=args.operation_id,
            role="campeon_numerico_vigente",
            model_profile_id=NUMERIC_PRIMARY_RUN_ID,
            evaluated=evaluated_e1,
            pending=pending_e1_bundle.horizon_frames,
            repo_context=repo_context,
            dataset_path=args.dataset_path,
            operation_start=operation_start,
            operation_end=operation_end,
            evaluated_run_dir=str(args.e1_run_dir),
            comments=args.comment,
        )
    )
    if pending_e9_bundle is not None:
        rows.extend(
            _build_registry_rows(
                operation_id=args.operation_id,
                role="referente_riesgo_direccion_caidas",
                model_profile_id=RISK_PRIMARY_RUN_ID,
                evaluated=evaluated_e9,
                pending=pending_e9_bundle.horizon_frames,
                repo_context=repo_context,
                dataset_path=args.dataset_path,
                operation_start=operation_start,
                operation_end=operation_end,
                evaluated_run_dir=str(args.e9_run_dir),
                comments=args.comment,
            )
        )

    payload = {
        "operation_id": args.operation_id,
        "updated_at": now_text(),
        "rows": len(rows),
        "dataset_path": str(args.dataset_path),
        "from_week": args.from_week,
        "to_week": args.to_week,
        "e1_run_dir": str(args.e1_run_dir),
        "e9_run_dir": str(args.e9_run_dir),
        "snapshot_artifacts": snapshot_artifacts,
        "profile_statuses": profile_statuses,
        "blocked_profiles": (
            []
            if e9_blocker is None
            else [{"run_id": RISK_PRIMARY_RUN_ID, "reason": e9_blocker}]
        ),
        "repo_context": repo_context,
        "comment": args.comment,
    }
    registry_paths = _save_registry(
        rows=rows,
        target_dir=emisiones_dir,
        operation_id=args.operation_id,
        payload=payload,
    )
    summary_path = args.operation_root / "emission_registry_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "registry_paths": registry_paths,
                "rows": len(rows),
                "profile_statuses": profile_statuses,
                "snapshot_artifacts": snapshot_artifacts,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(f"registry_csv={registry_paths['csv']}")
    print(f"registry_json={registry_paths['json']}")
    print(f"summary={summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
