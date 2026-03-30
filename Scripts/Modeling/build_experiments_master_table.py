#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook

from config import DATE_COLUMN


RUN_DIR_PATTERN = re.compile(
    r"^(?P<run_id>.+?)_(?P<timestamp>\d{8}_\d{6})(?P<aborted>_aborted)?$"
)
RUN_ID_PATTERN = re.compile(r"\bE\d+_v\d+(?:_clean)?\b")

CORE_FILES = (
    "metadata_run.json",
    "parametros_run.json",
    "metricas_horizonte.json",
    "resumen_modeling_horizontes.json",
)

HORIZON_METRIC_SPECS = (
    {"metric": "mae", "column_suffix": "mae", "sense": "menor_es_mejor", "ascending": True},
    {"metric": "rmse", "column_suffix": "rmse", "sense": "menor_es_mejor", "ascending": True},
    {
        "metric": "direction_accuracy",
        "column_suffix": "direction_accuracy",
        "sense": "mayor_es_mejor",
        "ascending": False,
    },
    {
        "metric": "deteccion_caidas",
        "column_suffix": "deteccion_caidas",
        "sense": "mayor_es_mejor",
        "ascending": False,
    },
    {"metric": "loss_h", "column_suffix": "loss", "sense": "menor_es_mejor", "ascending": True},
)
RANKING_TIEBREAKER_TEXT = "L_total_Radar asc, run_id asc"
PREDICTION_DATE_CANDIDATES = (DATE_COLUMN, "fecha", "fecha_semana", "week_start")
PREDICTION_Y_TRUE_CANDIDATES = ("y_true", "y_true_model", "actual", "y_actual")
PREDICTION_Y_PRED_CANDIDATES = ("y_pred", "y_pred_model", "pred", "prediction")


@dataclass
class PredictionAuditResult:
    coverage_row: dict[str, Any]
    standardized_df: pd.DataFrame | None


@dataclass
class RunDirectoryRecord:
    path: Path
    inferred_run_id: str
    timestamp: str | None
    is_aborted: bool
    metadata: dict[str, Any] | None
    parametros: dict[str, Any] | None
    metricas: dict[str, Any] | None
    resumen: list[dict[str, Any]] | None
    comparison_files: list[Path]
    prediction_files: list[Path]
    selected_feature_files: list[Path]
    issues: list[str]

    @property
    def effective_run_id(self) -> str:
        if self.metadata and self.metadata.get("run_id"):
            return str(self.metadata["run_id"])
        return self.inferred_run_id

    @property
    def model(self) -> str | None:
        if self.metadata and self.metadata.get("model"):
            return str(self.metadata["model"])
        if self.parametros and self.parametros.get("model"):
            return str(self.parametros["model"])
        return None

    @property
    def experiment_id(self) -> str | None:
        if self.metadata and self.metadata.get("experiment_id"):
            return str(self.metadata["experiment_id"])
        run_id = self.effective_run_id
        if "_" in run_id:
            return run_id.split("_", 1)[0]
        return None

    @property
    def artifact_status(self) -> str:
        core_present = sum(int((self.path / name).exists()) for name in CORE_FILES)
        if core_present == len(CORE_FILES) and len(self.prediction_files) >= 4:
            return "completo"
        if core_present >= 2 or self.prediction_files or self.selected_feature_files:
            return "parcial"
        return "inconsistente"

    @property
    def completeness_score(self) -> tuple[int, int, int, int, int, int]:
        return (
            sum(int((self.path / name).exists()) for name in CORE_FILES),
            len(self.prediction_files),
            len(self.comparison_files),
            len(self.selected_feature_files),
            int(self.metadata is not None),
            0 if self.is_aborted else 1,
        )


@dataclass
class MasterAuditBuildResult:
    csv_path: Path
    xlsx_path: Path
    json_path: Path
    markdown_path: Path
    master_runs_total: int
    inventory_directories_total: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audita runs reales de Radar y construye una tabla maestra comparativa por horizonte.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("/home/emilio/Documentos/RAdAR/Experimentos/runs"),
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        default=Path("/home/emilio/Documentos/RAdAR/Experimentos/grid_experimentos_radar.xlsx"),
    )
    parser.add_argument(
        "--prompts-dir",
        type=Path,
        default=Path("/home/emilio/Documentos/RAdAR/Experimentos/Prompts_Agente"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/home/emilio/Documentos/RAdAR/Experimentos"),
    )
    return parser.parse_args()


def load_json_if_exists(path: Path) -> dict[str, Any] | list[dict[str, Any]] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def parse_run_directory_name(name: str) -> tuple[str, str | None, bool]:
    match = RUN_DIR_PATTERN.match(name)
    if not match:
        return name, None, False
    return match.group("run_id"), match.group("timestamp"), bool(match.group("aborted"))


def scan_run_directories(runs_dir: Path) -> list[RunDirectoryRecord]:
    records: list[RunDirectoryRecord] = []
    for path in sorted(runs_dir.iterdir()):
        if not path.is_dir():
            continue
        inferred_run_id, timestamp, is_aborted = parse_run_directory_name(path.name)
        comparison_files = sorted(path.glob("comparacion_vs_*.json"))
        prediction_files = sorted(path.glob("predicciones_h*.csv"))
        selected_feature_files = sorted(path.glob("features_seleccionadas_h*.csv"))
        metadata = load_json_if_exists(path / "metadata_run.json")
        parametros = load_json_if_exists(path / "parametros_run.json")
        metricas = load_json_if_exists(path / "metricas_horizonte.json")
        resumen = load_json_if_exists(path / "resumen_modeling_horizontes.json")
        issues: list[str] = []
        if metadata is None:
            issues.append("faltante_metadata")
        if parametros is None:
            issues.append("faltante_parametros")
        if metricas is None:
            issues.append("faltante_metricas")
        if resumen is None:
            issues.append("faltante_resumen")
        if len(prediction_files) < 4:
            issues.append("predicciones_incompletas")
        records.append(
            RunDirectoryRecord(
                path=path,
                inferred_run_id=inferred_run_id,
                timestamp=timestamp,
                is_aborted=is_aborted,
                metadata=metadata if isinstance(metadata, dict) else None,
                parametros=parametros if isinstance(parametros, dict) else None,
                metricas=metricas if isinstance(metricas, dict) else None,
                resumen=resumen if isinstance(resumen, list) else None,
                comparison_files=comparison_files,
                prediction_files=prediction_files,
                selected_feature_files=selected_feature_files,
                issues=issues,
            )
        )
    return records


def select_canonical_records(
    records: list[RunDirectoryRecord],
) -> tuple[dict[str, RunDirectoryRecord], dict[str, list[RunDirectoryRecord]]]:
    grouped: dict[str, list[RunDirectoryRecord]] = {}
    for record in records:
        grouped.setdefault(record.effective_run_id, []).append(record)

    canonical: dict[str, RunDirectoryRecord] = {}
    for run_id, candidates in grouped.items():
        canonical[run_id] = sorted(
            candidates,
            key=lambda item: (
                item.completeness_score,
                item.timestamp or "",
                item.path.name,
            ),
            reverse=True,
        )[0]
    return canonical, grouped


def normalize_feature_mode(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().lower()
    mapping = {
        "todas": "all",
        "todas_las_variables": "all",
        "all": "all",
        "corr": "corr",
        "lasso": "lasso",
    }
    return mapping.get(raw, raw or None)


def normalize_transform_mode(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().lower()
    mapping = {
        "estandarizada": "standard",
        "standard": "standard",
        "standard_scaler": "standard",
        "robust": "robust",
        "robust_scaler": "robust",
        "winsor": "winsor",
        "sin_escalar": "none",
        "": "none",
        "none": "none",
    }
    return mapping.get(raw, raw or None)


def normalize_family(run_id: str, family: Any, model: Any) -> str | None:
    raw_family = str(family).strip().lower() if family is not None else None
    model_name = str(model).strip().lower() if model is not None else ""
    if run_id.startswith("E1_"):
        return "lineal_regularizado"
    if run_id.startswith("E2_"):
        return "robusto"
    if run_id.startswith("E3_"):
        return "arboles_boosting"
    if raw_family:
        if "lineal" in raw_family and "ridge" in model_name:
            return "lineal_regularizado"
        return raw_family
    return raw_family


def parse_feature_count_prom(
    resumen: list[dict[str, Any]] | None,
    metricas: dict[str, Any] | None,
) -> float | None:
    if resumen:
        values = [
            float(item["selected_feature_count_avg"])
            for item in resumen
            if item.get("selected_feature_count_avg") is not None
        ]
        if values:
            return float(sum(values) / len(values))
    if metricas:
        horizons = metricas.get("horizon_results", [])
        counts = []
        for item in horizons:
            notas = str(item.get("notas_config", ""))
            match = re.search(r"(\d+(?:\.\d+)?)\s+features", notas)
            if match:
                counts.append(float(match.group(1)))
        if counts:
            return float(sum(counts) / len(counts))
    return None


def build_workbook_lookup(workbook_path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[int, dict[str, Any]]]]:
    workbook = load_workbook(workbook_path, data_only=True)
    summary_lookup: dict[str, dict[str, Any]] = {}
    ws = workbook["RUN_SUMMARY"]
    headers = {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1)}
    for row in range(2, ws.max_row + 1):
        run_id = ws.cell(row, headers["Run_ID"]).value
        if not run_id:
            continue
        summary_lookup[str(run_id)] = {
            "L_total_Radar": ws.cell(row, headers["L_total_Radar"]).value,
            "Avg_MAE": ws.cell(row, headers["Avg_MAE"]).value,
            "Avg_RMSE": ws.cell(row, headers["Avg_RMSE"]).value,
            "Dir_acc_prom": ws.cell(row, headers["Dir_acc_prom"]).value,
            "Det_caidas_prom": ws.cell(row, headers["Det_caidas_prom"]).value,
            "Comentarios": ws.cell(row, headers["Comentarios"]).value,
        }

    results_lookup: dict[str, dict[int, dict[str, Any]]] = {}
    ws = workbook["RESULTADOS_GRID"]
    headers = {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1)}
    for row in range(2, ws.max_row + 1):
        run_id = ws.cell(row, headers["Run_ID"]).value
        if not run_id:
            continue
        horizon = ws.cell(row, headers["Horizonte_sem"]).value
        if horizon is None:
            continue
        results_lookup.setdefault(str(run_id), {})[int(horizon)] = {
            "Loss_h": ws.cell(row, headers["Loss_h"]).value,
            "MAE": ws.cell(row, headers["MAE"]).value,
            "RMSE": ws.cell(row, headers["RMSE"]).value,
            "Direccion_accuracy": ws.cell(row, headers["Direccion_accuracy"]).value,
            "Deteccion_caidas": ws.cell(row, headers["Deteccion_caidas"]).value,
        }
    return summary_lookup, results_lookup


def horizon_metrics_map(record: RunDirectoryRecord) -> dict[int, dict[str, Any]]:
    if not record.metricas:
        return {}
    result: dict[int, dict[str, Any]] = {}
    for item in record.metricas.get("horizon_results", []):
        horizon = int(item["horizonte_sem"])
        result[horizon] = item
    return result


def extract_target_mode(record: RunDirectoryRecord, horizon_map: dict[int, dict[str, Any]]) -> str | None:
    if record.parametros and record.parametros.get("target_mode"):
        return str(record.parametros["target_mode"])
    for item in horizon_map.values():
        if item.get("target"):
            return str(item["target"])
    return None


def extract_feature_mode(record: RunDirectoryRecord, horizon_map: dict[int, dict[str, Any]]) -> str | None:
    if record.parametros and record.parametros.get("feature_mode") is not None:
        return normalize_feature_mode(record.parametros["feature_mode"])
    for item in horizon_map.values():
        if item.get("seleccion_variables") is not None:
            return normalize_feature_mode(item["seleccion_variables"])
    return None


def extract_transform_mode(record: RunDirectoryRecord, horizon_map: dict[int, dict[str, Any]]) -> str | None:
    if record.parametros and "transform_mode" in record.parametros:
        return normalize_transform_mode(record.parametros.get("transform_mode"))
    for item in horizon_map.values():
        if item.get("transformacion") is not None:
            return normalize_transform_mode(item["transformacion"])
    return None


def extract_lags(record: RunDirectoryRecord, horizon_map: dict[int, dict[str, Any]]) -> str | None:
    if record.parametros and record.parametros.get("lags"):
        return ",".join(str(value) for value in record.parametros["lags"])
    for item in horizon_map.values():
        text = str(item.get("variables_temporales", ""))
        match = re.search(r"lags\s*\[([0-9,\s]+)\]", text)
        if match:
            return ",".join(token.strip() for token in match.group(1).split(","))
        if "1..4" in text:
            return "1,2,3,4"
    return None


def extract_horizons(record: RunDirectoryRecord, horizon_map: dict[int, dict[str, Any]]) -> str | None:
    if record.parametros and record.parametros.get("horizons"):
        return ",".join(str(value) for value in record.parametros["horizons"])
    if horizon_map:
        return ",".join(str(value) for value in sorted(horizon_map))
    return None


def parse_notes_config_payload(raw_value: Any) -> dict[str, Any]:
    if raw_value is None:
        return {}
    if isinstance(raw_value, dict):
        return raw_value
    if isinstance(raw_value, str):
        token = raw_value.strip()
        if not token:
            return {}
        try:
            payload = json.loads(token)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}
    return {}


def extract_first_notes_config(record: RunDirectoryRecord, horizon_map: dict[int, dict[str, Any]]) -> dict[str, Any]:
    for horizon in sorted(horizon_map):
        payload = parse_notes_config_payload(horizon_map[horizon].get("notas_config"))
        if payload:
            return payload
    return {}


def extract_initial_train_size(record: RunDirectoryRecord, horizon_map: dict[int, dict[str, Any]]) -> int | None:
    if record.parametros and record.parametros.get("initial_train_size") is not None:
        return int(record.parametros["initial_train_size"])
    notes_payload = extract_first_notes_config(record, horizon_map)
    if notes_payload.get("initial_train_size") is not None:
        return int(notes_payload["initial_train_size"])
    return None


def infer_tuning_interno(record: RunDirectoryRecord, horizon_map: dict[int, dict[str, Any]]) -> bool | None:
    model_params = {}
    if record.parametros and isinstance(record.parametros.get("model_params"), dict):
        model_params = record.parametros["model_params"]
    tuning_strategy = str(model_params.get("tuning_strategy", "")).strip().lower()
    if tuning_strategy:
        if "sin_tuning" in tuning_strategy or "baseline_fijo" in tuning_strategy:
            return False
        if any(token in tuning_strategy for token in ("tscv", "temporal", "interno", "grid")):
            return True

    model_name = (record.model or "").strip().lower()
    if "tscv" in model_name:
        return True
    if any(token in model_name for token in ("random_forest", "extra_trees", "xgboost")):
        return False

    notes_payload = extract_first_notes_config(record, horizon_map)
    model_params_notes = notes_payload.get("model_params", {})
    if isinstance(model_params_notes, dict):
        tuning_strategy_notes = str(model_params_notes.get("tuning_strategy", "")).strip().lower()
        if tuning_strategy_notes:
            if "sin_tuning" in tuning_strategy_notes or "baseline_fijo" in tuning_strategy_notes:
                return False
            if any(token in tuning_strategy_notes for token in ("tscv", "temporal", "interno", "grid")):
                return True
    return None


def normalize_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    raw = str(value).strip().lower()
    if raw in {"true", "1", "si", "sí", "yes"}:
        return True
    if raw in {"false", "0", "no"}:
        return False
    return None


def normalize_created_at(record: RunDirectoryRecord) -> str | None:
    if record.metadata and record.metadata.get("created_at"):
        return str(record.metadata["created_at"])
    if record.timestamp:
        token = record.timestamp
        return f"{token[0:4]}-{token[4:6]}-{token[6:8]} {token[9:11]}:{token[11:13]}:{token[13:15]}"
    return None


def extract_notes_config_text(record: RunDirectoryRecord, horizon_map: dict[int, dict[str, Any]]) -> str:
    for horizon in sorted(horizon_map):
        raw = horizon_map[horizon].get("notas_config")
        if raw not in (None, ""):
            return str(raw)
    if record.parametros:
        return json.dumps(record.parametros, ensure_ascii=False, sort_keys=True)
    return ""


def resolve_script_family(record: RunDirectoryRecord) -> str | None:
    if record.metadata and record.metadata.get("script_path"):
        return Path(str(record.metadata["script_path"])).name
    return None


def resolve_path_if_exists(path: Path) -> str:
    return str(path.resolve()) if path.exists() else ""


def get_prediction_file(record: RunDirectoryRecord, horizon: int) -> Path:
    return record.path / f"predicciones_h{horizon}.csv"


def build_master_rows(
    canonical: dict[str, RunDirectoryRecord],
    summary_lookup: dict[str, dict[str, Any]],
    results_lookup: dict[str, dict[int, dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run_id in sorted(canonical):
        record = canonical[run_id]
        horizon_map = horizon_metrics_map(record)
        summary = summary_lookup.get(run_id, {})
        workbook_horizons = results_lookup.get(run_id, {})
        feature_count_prom = parse_feature_count_prom(record.resumen, record.metricas)
        row: dict[str, Any] = {
            "run_id": run_id,
            "family": normalize_family(run_id, (record.metadata or {}).get("family"), record.model),
            "model": record.model,
            "target_mode": extract_target_mode(record, horizon_map),
            "feature_mode": extract_feature_mode(record, horizon_map),
            "transform_mode": extract_transform_mode(record, horizon_map),
            "lags": extract_lags(record, horizon_map),
            "feature_count_prom": feature_count_prom,
            "L_total_Radar": summary.get("L_total_Radar"),
            "observacion_breve": summary.get("Comentarios") or (
                "Run consolidado desde artefactos en disco."
                if record.artifact_status == "completo"
                else "Run con artefactos incompletos."
            ),
            "status_run": record.artifact_status,
        }
        for horizon in (1, 2, 3, 4):
            horizon_row = horizon_map.get(horizon, {})
            workbook_row = workbook_horizons.get(horizon, {})
            row[f"H{horizon}_mae"] = horizon_row.get("mae", workbook_row.get("MAE"))
            row[f"H{horizon}_rmse"] = horizon_row.get("rmse", workbook_row.get("RMSE"))
            row[f"H{horizon}_direction_accuracy"] = horizon_row.get(
                "direccion_accuracy", workbook_row.get("Direccion_accuracy")
            )
            row[f"H{horizon}_deteccion_caidas"] = horizon_row.get(
                "deteccion_caidas", workbook_row.get("Deteccion_caidas")
            )
            row[f"H{horizon}_loss"] = horizon_row.get("loss_h", workbook_row.get("Loss_h"))

        row["mae_promedio"] = summary.get("Avg_MAE")
        if row["mae_promedio"] is None:
            mae_values = [row[f"H{h}_mae"] for h in (1, 2, 3, 4) if row[f"H{h}_mae"] is not None]
            row["mae_promedio"] = float(sum(mae_values) / len(mae_values)) if mae_values else None

        row["rmse_promedio"] = summary.get("Avg_RMSE")
        if row["rmse_promedio"] is None:
            rmse_values = [row[f"H{h}_rmse"] for h in (1, 2, 3, 4) if row[f"H{h}_rmse"] is not None]
            row["rmse_promedio"] = float(sum(rmse_values) / len(rmse_values)) if rmse_values else None

        row["direction_accuracy_promedio"] = summary.get("Dir_acc_prom")
        if row["direction_accuracy_promedio"] is None:
            dir_values = [
                row[f"H{h}_direction_accuracy"]
                for h in (1, 2, 3, 4)
                if row[f"H{h}_direction_accuracy"] is not None
            ]
            row["direction_accuracy_promedio"] = (
                float(sum(dir_values) / len(dir_values)) if dir_values else None
            )

        row["deteccion_caidas_promedio"] = summary.get("Det_caidas_prom")
        if row["deteccion_caidas_promedio"] is None:
            risk_values = [
                row[f"H{h}_deteccion_caidas"]
                for h in (1, 2, 3, 4)
                if row[f"H{h}_deteccion_caidas"] is not None
            ]
            row["deteccion_caidas_promedio"] = (
                float(sum(risk_values) / len(risk_values)) if risk_values else None
            )

        required_columns = [
            "L_total_Radar",
            "H1_mae",
            "H1_rmse",
            "H1_direction_accuracy",
            "H1_deteccion_caidas",
            "H1_loss",
            "H2_mae",
            "H2_rmse",
            "H2_direction_accuracy",
            "H2_deteccion_caidas",
            "H2_loss",
            "H3_mae",
            "H3_rmse",
            "H3_direction_accuracy",
            "H3_deteccion_caidas",
            "H3_loss",
            "H4_mae",
            "H4_rmse",
            "H4_direction_accuracy",
            "H4_deteccion_caidas",
            "H4_loss",
        ]
        missing_required = [column for column in required_columns if row.get(column) is None]
        if missing_required:
            row["status_run"] = "parcial" if record.artifact_status == "completo" else record.artifact_status
            if row["observacion_breve"]:
                row["observacion_breve"] = (
                    f"{row['observacion_breve']} | faltantes_metricos={','.join(missing_required)}"
                )
        rows.append(row)
    return rows


def build_inventory_rows(
    records: list[RunDirectoryRecord],
    canonical: dict[str, RunDirectoryRecord],
    grouped: dict[str, list[RunDirectoryRecord]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda item: item.path.name):
        run_id = record.effective_run_id
        is_canonical = canonical.get(run_id) == record
        duplicate_count = len(grouped.get(run_id, []))
        comment_parts = []
        if duplicate_count > 1:
            comment_parts.append(f"duplicado_detectado={duplicate_count}")
            if is_canonical:
                comment_parts.append("directorio_valido_resuelto")
            else:
                comment_parts.append("intento_descartado_por_menor_completitud")
        if record.is_aborted:
            comment_parts.append("directorio_abortado")
        if record.issues:
            comment_parts.append(",".join(record.issues))
        rows.append(
            {
                "run_id": run_id,
                "family": normalize_family(run_id, (record.metadata or {}).get("family"), record.model),
                "model": record.model,
                "path_run": str(record.path.resolve()),
                "metadata_run": str((record.path / "metadata_run.json").resolve())
                if (record.path / "metadata_run.json").exists()
                else "",
                "metricas_horizonte": str((record.path / "metricas_horizonte.json").resolve())
                if (record.path / "metricas_horizonte.json").exists()
                else "",
                "parametros_run": str((record.path / "parametros_run.json").resolve())
                if (record.path / "parametros_run.json").exists()
                else "",
                "predicciones": len(record.prediction_files),
                "comparaciones": len(record.comparison_files),
                "features_seleccionadas": len(record.selected_feature_files),
                "resumen_horizontes": int((record.path / "resumen_modeling_horizontes.json").exists()),
                "status_artifactos": record.artifact_status,
                "comentario": "; ".join(comment_parts),
                "es_directorio_canonico": is_canonical,
            }
        )
    return rows


def build_runs_catalog_rows(
    canonical: dict[str, RunDirectoryRecord],
    summary_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run_id in sorted(canonical):
        record = canonical[run_id]
        horizon_map = horizon_metrics_map(record)
        summary = summary_lookup.get(run_id, {})
        metadata_path = record.path / "metadata_run.json"
        parametros_path = record.path / "parametros_run.json"
        metricas_path = record.path / "metricas_horizonte.json"
        resumen_path = record.path / "resumen_modeling_horizontes.json"
        row: dict[str, Any] = {
            "run_id": run_id,
            "family": normalize_family(run_id, (record.metadata or {}).get("family"), record.model),
            "model": record.model,
            "script_family": resolve_script_family(record),
            "target_mode": extract_target_mode(record, horizon_map),
            "feature_mode": extract_feature_mode(record, horizon_map),
            "transform_mode": extract_transform_mode(record, horizon_map),
            "lags": extract_lags(record, horizon_map),
            "horizons": extract_horizons(record, horizon_map),
            "initial_train_size": extract_initial_train_size(record, horizon_map),
            "tuning_interno": infer_tuning_interno(record, horizon_map),
            "fecha_run": normalize_created_at(record),
            "status_run": record.artifact_status,
            "L_total_Radar": summary.get("L_total_Radar"),
            "path_run": str(record.path.resolve()),
            "metadata_run_path": resolve_path_if_exists(metadata_path),
            "parametros_run_path": resolve_path_if_exists(parametros_path),
            "metricas_horizonte_path": resolve_path_if_exists(metricas_path),
            "resumen_horizontes_path": resolve_path_if_exists(resumen_path),
            "notas_config": extract_notes_config_text(record, horizon_map),
            "es_candidato_meta_modelo": False,
            "motivo_exclusion_meta_modelo": "",
        }
        for horizon in (1, 2, 3, 4):
            pred_path = get_prediction_file(record, horizon)
            row[f"predicciones_h{horizon}_path"] = resolve_path_if_exists(pred_path)
            row[f"predicciones_h{horizon}_existe"] = pred_path.exists()
        rows.append(row)
    return rows


def build_metricas_por_horizonte_long(
    canonical: dict[str, RunDirectoryRecord],
    master_df: pd.DataFrame,
    results_lookup: dict[str, dict[int, dict[str, Any]]],
) -> pd.DataFrame:
    master_lookup = {
        row["run_id"]: row
        for row in master_df.to_dict(orient="records")
    }
    rows: list[dict[str, Any]] = []
    for run_id in sorted(canonical):
        record = canonical[run_id]
        horizon_map = horizon_metrics_map(record)
        workbook_horizons = results_lookup.get(run_id, {})
        master_row = master_lookup.get(run_id, {})
        for horizon in (1, 2, 3, 4):
            horizon_row = horizon_map.get(horizon, {})
            workbook_row = workbook_horizons.get(horizon, {})
            rows.append(
                {
                    "run_id": run_id,
                    "horizonte": horizon,
                    "horizonte_label": f"H{horizon}",
                    "family": master_row.get("family"),
                    "model": master_row.get("model"),
                    "target_mode": master_row.get("target_mode"),
                    "feature_mode": master_row.get("feature_mode"),
                    "lags": master_row.get("lags"),
                    "mae": horizon_row.get("mae", workbook_row.get("MAE")),
                    "rmse": horizon_row.get("rmse", workbook_row.get("RMSE")),
                    "direction_accuracy": horizon_row.get(
                        "direccion_accuracy", workbook_row.get("Direccion_accuracy")
                    ),
                    "deteccion_caidas": horizon_row.get(
                        "deteccion_caidas", workbook_row.get("Deteccion_caidas")
                    ),
                    "l_num": horizon_row.get("l_num"),
                    "l_trend": horizon_row.get("l_trend"),
                    "l_risk": horizon_row.get("l_risk"),
                    "l_tol": horizon_row.get("l_tol"),
                    "loss_h": horizon_row.get("loss_h", workbook_row.get("Loss_h")),
                    "status_run": master_row.get("status_run"),
                    "L_total_Radar": master_row.get("L_total_Radar"),
                }
            )

    long_df = pd.DataFrame(rows)
    rank_specs = (
        ("mae", True, "rank_mae_por_horizonte"),
        ("rmse", True, "rank_rmse_por_horizonte"),
        ("direction_accuracy", False, "rank_direction_accuracy_por_horizonte"),
        ("deteccion_caidas", False, "rank_deteccion_caidas_por_horizonte"),
        ("loss_h", True, "rank_loss_h_por_horizonte"),
    )
    for _, _, rank_col in rank_specs:
        long_df[rank_col] = pd.NA

    for horizon in (1, 2, 3, 4):
        horizon_mask = long_df["horizonte"] == horizon
        horizon_subset = long_df[horizon_mask]
        for metric_col, ascending, rank_col in rank_specs:
            metric_subset = horizon_subset.dropna(subset=[metric_col]).copy()
            if metric_subset.empty:
                continue
            metric_subset = sort_metric_subset(
                metric_subset,
                metric_col=metric_col,
                ascending=ascending,
            )
            rank_map = {
                row["run_id"]: rank
                for rank, (_, row) in enumerate(metric_subset.iterrows(), start=1)
            }
            long_df.loc[horizon_mask, rank_col] = long_df.loc[horizon_mask, "run_id"].map(rank_map)

    return long_df.sort_values(["horizonte", "rank_loss_h_por_horizonte", "run_id"], kind="mergesort").reset_index(drop=True)


def pick_column(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    lower_map = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


def audit_prediction_file(run_id: str, horizon: int, pred_path: Path) -> PredictionAuditResult:
    base_row = {
        "run_id": run_id,
        "horizonte": horizon,
        "horizonte_label": f"H{horizon}",
        "pred_path": str(pred_path.resolve()),
        "existe_archivo": pred_path.exists(),
        "fecha_min_pred": None,
        "fecha_max_pred": None,
        "n_predicciones": 0,
        "n_fechas_unicas": 0,
        "sin_duplicados_fecha": False,
        "columnas_detectadas": "",
        "date_column": "",
        "y_true_column": "",
        "y_pred_column": "",
        "tiene_fecha": False,
        "tiene_y_true": False,
        "tiene_y_pred": False,
        "columnas_minimas_ok": False,
        "orden_temporal_ok": False,
        "compatible_para_merge": False,
        "comentario": "",
    }
    if not pred_path.exists():
        base_row["comentario"] = "archivo_no_encontrado"
        return PredictionAuditResult(base_row, None)

    try:
        raw_df = pd.read_csv(pred_path)
    except Exception as exc:  # pragma: no cover - defensive path
        base_row["comentario"] = f"error_lectura={exc}"
        return PredictionAuditResult(base_row, None)

    columns = list(raw_df.columns)
    base_row["columnas_detectadas"] = ",".join(columns)
    base_row["n_predicciones"] = int(len(raw_df))

    date_col = pick_column(columns, PREDICTION_DATE_CANDIDATES)
    y_true_col = pick_column(columns, PREDICTION_Y_TRUE_CANDIDATES)
    y_pred_col = pick_column(columns, PREDICTION_Y_PRED_CANDIDATES)
    base_row["date_column"] = date_col or ""
    base_row["y_true_column"] = y_true_col or ""
    base_row["y_pred_column"] = y_pred_col or ""
    base_row["tiene_fecha"] = bool(date_col)
    base_row["tiene_y_true"] = bool(y_true_col)
    base_row["tiene_y_pred"] = bool(y_pred_col)
    base_row["columnas_minimas_ok"] = bool(date_col and y_true_col and y_pred_col)

    if not base_row["columnas_minimas_ok"]:
        missing = []
        if not date_col:
            missing.append("fecha")
        if not y_true_col:
            missing.append("y_true")
        if not y_pred_col:
            missing.append("y_pred")
        base_row["comentario"] = f"columnas_faltantes={','.join(missing)}"
        return PredictionAuditResult(base_row, None)

    parsed_dates = pd.to_datetime(raw_df[date_col], errors="coerce")
    standardized_df = pd.DataFrame(
        {
            "fecha": parsed_dates,
            "y_true": pd.to_numeric(raw_df[y_true_col], errors="coerce"),
            "y_pred": pd.to_numeric(raw_df[y_pred_col], errors="coerce"),
        }
    )
    standardized_df = standardized_df.dropna(subset=["fecha", "y_true", "y_pred"]).copy()

    if standardized_df.empty:
        base_row["comentario"] = "sin_filas_validas_para_merge"
        return PredictionAuditResult(base_row, None)

    standardized_df["fecha"] = pd.to_datetime(standardized_df["fecha"])
    base_row["n_predicciones"] = int(len(standardized_df))
    base_row["n_fechas_unicas"] = int(standardized_df["fecha"].nunique())
    base_row["sin_duplicados_fecha"] = bool(base_row["n_predicciones"] == base_row["n_fechas_unicas"])
    base_row["orden_temporal_ok"] = bool(standardized_df["fecha"].is_monotonic_increasing)
    base_row["fecha_min_pred"] = standardized_df["fecha"].min().date().isoformat()
    base_row["fecha_max_pred"] = standardized_df["fecha"].max().date().isoformat()
    base_row["compatible_para_merge"] = bool(
        base_row["columnas_minimas_ok"]
        and base_row["n_predicciones"] > 0
        and base_row["sin_duplicados_fecha"]
    )
    base_row["comentario"] = (
        "ok"
        if base_row["compatible_para_merge"]
        else "inconsistencia_merge"
    )

    standardized_df = standardized_df.sort_values("fecha", kind="mergesort").reset_index(drop=True)
    standardized_df["fecha"] = standardized_df["fecha"].dt.date.astype(str)
    return PredictionAuditResult(base_row, standardized_df)


def build_prediction_coverage(
    canonical: dict[str, RunDirectoryRecord],
) -> tuple[pd.DataFrame, dict[tuple[str, int], pd.DataFrame]]:
    rows: list[dict[str, Any]] = []
    standardized_lookup: dict[tuple[str, int], pd.DataFrame] = {}
    for run_id in sorted(canonical):
        record = canonical[run_id]
        for horizon in (1, 2, 3, 4):
            pred_path = get_prediction_file(record, horizon)
            audit_result = audit_prediction_file(run_id, horizon, pred_path)
            rows.append(audit_result.coverage_row)
            if audit_result.standardized_df is not None:
                standardized_lookup[(run_id, horizon)] = audit_result.standardized_df
    coverage_df = pd.DataFrame(rows).sort_values(["run_id", "horizonte"]).reset_index(drop=True)
    return coverage_df, standardized_lookup


def build_stacking_readiness(
    runs_catalog_df: pd.DataFrame,
    coverage_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    coverage_lookup = coverage_df.groupby("run_id", sort=True)

    for _, catalog_row in runs_catalog_df.iterrows():
        run_id = catalog_row["run_id"]
        subset = coverage_lookup.get_group(run_id) if run_id in coverage_lookup.groups else pd.DataFrame()
        compatible_horizons = subset[subset["compatible_para_merge"]]["horizonte"].tolist()
        available_horizons = subset[subset["existe_archivo"]]["horizonte"].tolist()
        predicciones_completas = set(available_horizons) == {1, 2, 3, 4}
        columnas_minimas_ok = bool(not subset.empty and subset["columnas_minimas_ok"].all())
        tiene_fecha = bool(not subset.empty and subset["tiene_fecha"].all())
        tiene_y_true = bool(not subset.empty and subset["tiene_y_true"].all())
        tiene_y_pred = bool(not subset.empty and subset["tiene_y_pred"].all())
        orden_temporal_ok = bool(not subset.empty and subset["orden_temporal_ok"].all())
        sin_duplicados = bool(not subset.empty and subset["sin_duplicados_fecha"].all())
        compatible_para_stacking = bool(
            catalog_row["status_run"] == "completo"
            and predicciones_completas
            and set(compatible_horizons) == {1, 2, 3, 4}
        )

        motivos: list[str] = []
        if catalog_row["status_run"] != "completo":
            motivos.append(f"status_run={catalog_row['status_run']}")
        if not predicciones_completas:
            motivos.append("predicciones_incompletas_1a4")
        if not columnas_minimas_ok:
            motivos.append("columnas_minimas_no_validas")
        if not tiene_fecha:
            motivos.append("falta_fecha")
        if not tiene_y_true:
            motivos.append("falta_y_true")
        if not tiene_y_pred:
            motivos.append("falta_y_pred")
        if not sin_duplicados:
            motivos.append("duplicados_fecha")
        if set(compatible_horizons) != {1, 2, 3, 4}:
            faltantes = [str(h) for h in (1, 2, 3, 4) if h not in set(compatible_horizons)]
            if faltantes:
                motivos.append(f"horizontes_no_mergeables={','.join(faltantes)}")

        compatible_count = len(compatible_horizons)
        if compatible_para_stacking:
            prioridad = "alta"
        elif compatible_count >= 2:
            prioridad = "media"
        elif compatible_count >= 1:
            prioridad = "baja"
        else:
            prioridad = "excluido"

        row = {
            "run_id": run_id,
            "family": catalog_row["family"],
            "model": catalog_row["model"],
            "horizontes_disponibles": ",".join(str(h) for h in available_horizons),
            "predicciones_completas_1a4": predicciones_completas,
            "columnas_minimas_ok": columnas_minimas_ok,
            "tiene_fecha": tiene_fecha,
            "tiene_y_true": tiene_y_true,
            "tiene_y_pred": tiene_y_pred,
            "orden_temporal_ok": orden_temporal_ok,
            "sin_duplicados_fecha": sin_duplicados,
            "cantidad_obs_h1": int(subset.loc[subset["horizonte"] == 1, "n_predicciones"].max()) if 1 in set(subset["horizonte"]) else 0,
            "cantidad_obs_h2": int(subset.loc[subset["horizonte"] == 2, "n_predicciones"].max()) if 2 in set(subset["horizonte"]) else 0,
            "cantidad_obs_h3": int(subset.loc[subset["horizonte"] == 3, "n_predicciones"].max()) if 3 in set(subset["horizonte"]) else 0,
            "cantidad_obs_h4": int(subset.loc[subset["horizonte"] == 4, "n_predicciones"].max()) if 4 in set(subset["horizonte"]) else 0,
            "cobertura_total_predicciones": int(subset["n_predicciones"].sum()) if not subset.empty else 0,
            "compatible_para_stacking": compatible_para_stacking,
            "prioridad_para_meta_modelo": prioridad,
            "motivo_no_compatible": ";".join(motivos),
        }
        rows.append(row)

    return pd.DataFrame(rows).sort_values(["compatible_para_stacking", "run_id"], ascending=[False, True]).reset_index(drop=True)


def build_stacking_base_sheet(
    *,
    horizon: int,
    coverage_df: pd.DataFrame,
    runs_catalog_df: pd.DataFrame,
    standardized_lookup: dict[tuple[str, int], pd.DataFrame],
) -> pd.DataFrame:
    run_status_lookup = dict(zip(runs_catalog_df["run_id"], runs_catalog_df["status_run"]))
    eligible = coverage_df[
        (coverage_df["horizonte"] == horizon)
        & (coverage_df["compatible_para_merge"] == True)
    ].copy()
    eligible = eligible[eligible["run_id"].map(run_status_lookup).fillna("") == "completo"]
    eligible = eligible.sort_values("run_id").reset_index(drop=True)

    if eligible.empty:
        return pd.DataFrame(columns=["fecha", "y_true", "n_modelos_disponibles_fila"])

    merged_df: pd.DataFrame | None = None
    y_true_columns: list[str] = []
    pred_columns: list[str] = []

    for _, row in eligible.iterrows():
        run_id = row["run_id"]
        standardized_df = standardized_lookup.get((run_id, horizon))
        if standardized_df is None or standardized_df.empty:
            continue
        model_df = standardized_df.rename(
            columns={
                "y_true": f"__y_true_{run_id}",
                "y_pred": run_id,
            }
        )
        y_true_columns.append(f"__y_true_{run_id}")
        pred_columns.append(run_id)
        if merged_df is None:
            merged_df = model_df
        else:
            merged_df = merged_df.merge(model_df, on="fecha", how="outer", sort=True)

    if merged_df is None or merged_df.empty:
        return pd.DataFrame(columns=["fecha", "y_true", "n_modelos_disponibles_fila"])

    merged_df = merged_df.sort_values("fecha", kind="mergesort").reset_index(drop=True)
    if y_true_columns:
        merged_df["y_true"] = merged_df[y_true_columns].bfill(axis=1).iloc[:, 0]
        merged_df = merged_df.drop(columns=y_true_columns)
    else:
        merged_df["y_true"] = pd.NA
    ordered_columns = ["fecha", "y_true", *pred_columns]
    merged_df = merged_df[ordered_columns]
    merged_df["n_modelos_disponibles_fila"] = merged_df[pred_columns].notna().sum(axis=1) if pred_columns else 0
    return merged_df


def build_rankings(master_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    ranking_specs = [
        ("global", "L_total_Radar"),
        ("H1", "H1_loss"),
        ("H2", "H2_loss"),
        ("H3", "H3_loss"),
        ("H4", "H4_loss"),
    ]
    for criterio, column in ranking_specs:
        subset = master_df.dropna(subset=[column]).sort_values(column, ascending=True).reset_index(drop=True)
        for index, (_, row) in enumerate(subset.iterrows(), start=1):
            rows.append(
                {
                    "criterio": criterio,
                    "ranking": index,
                    "run_id": row["run_id"],
                    "family": row["family"],
                    "model": row["model"],
                    "score": row[column],
                    "feature_mode": row["feature_mode"],
                    "lags": row["lags"],
                    "status_run": row["status_run"],
                }
            )
    return pd.DataFrame(rows)


def sort_metric_subset(subset: pd.DataFrame, *, metric_col: str, ascending: bool) -> pd.DataFrame:
    sortable = subset.copy()
    sortable["__l_total_sort"] = sortable["L_total_Radar"].fillna(float("inf"))
    sorted_subset = sortable.sort_values(
        by=[metric_col, "__l_total_sort", "run_id"],
        ascending=[ascending, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    return sorted_subset.drop(columns="__l_total_sort")


def build_metric_rankings_long(master_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for horizon in (1, 2, 3, 4):
        for spec in HORIZON_METRIC_SPECS:
            metric_col = f"H{horizon}_{spec['column_suffix']}"
            subset = master_df.dropna(subset=[metric_col]).copy()
            if subset.empty:
                continue
            subset = sort_metric_subset(
                subset,
                metric_col=metric_col,
                ascending=bool(spec["ascending"]),
            )
            previous_value = None
            for rank, (_, row) in enumerate(subset.iterrows(), start=1):
                value = row[metric_col]
                rows.append(
                    {
                        "horizonte": f"H{horizon}",
                        "metrica": spec["metric"],
                        "sentido_optimizacion": spec["sense"],
                        "criterio_desempate": RANKING_TIEBREAKER_TEXT,
                        "rank": rank,
                        "run_id": row["run_id"],
                        "family": row["family"],
                        "model": row["model"],
                        "valor_metrica": value,
                        "status_run": row["status_run"],
                        "L_total_Radar": row["L_total_Radar"],
                        "observacion_breve": row["observacion_breve"],
                        "empate_exacto_con_anterior": bool(previous_value is not None and value == previous_value),
                    }
                )
                previous_value = value
    return pd.DataFrame(rows)


def build_metric_winners_compact(metric_rankings_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if metric_rankings_df.empty:
        return pd.DataFrame(rows)

    grouped = metric_rankings_df.groupby(["horizonte", "metrica"], sort=True)
    for (horizonte, metrica), subset in grouped:
        subset = subset.sort_values("rank", kind="mergesort").reset_index(drop=True)
        first = subset.iloc[0] if len(subset) >= 1 else None
        second = subset.iloc[1] if len(subset) >= 2 else None
        third = subset.iloc[2] if len(subset) >= 3 else None
        rows.append(
            {
                "horizonte": horizonte,
                "metrica": metrica,
                "sentido_optimizacion": first["sentido_optimizacion"] if first is not None else "",
                "criterio_desempate": RANKING_TIEBREAKER_TEXT,
                "mejor_run_id": first["run_id"] if first is not None else "",
                "mejor_family": first["family"] if first is not None else "",
                "mejor_model": first["model"] if first is not None else "",
                "mejor_status_run": first["status_run"] if first is not None else "",
                "mejor_valor": first["valor_metrica"] if first is not None else None,
                "mejor_L_total_Radar": first["L_total_Radar"] if first is not None else None,
                "segundo_run_id": second["run_id"] if second is not None else "",
                "segundo_family": second["family"] if second is not None else "",
                "segundo_model": second["model"] if second is not None else "",
                "segundo_valor": second["valor_metrica"] if second is not None else None,
                "tercer_run_id": third["run_id"] if third is not None else "",
                "tercer_family": third["family"] if third is not None else "",
                "tercer_model": third["model"] if third is not None else "",
                "tercer_valor": third["valor_metrica"] if third is not None else None,
                "empate_exacto_top1_top2": bool(
                    first is not None
                    and second is not None
                    and first["valor_metrica"] == second["valor_metrica"]
                ),
            }
        )
    return pd.DataFrame(rows)


def build_dimension_rankings(master_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for horizon in (1, 2, 3, 4):
        mae_col = f"H{horizon}_mae"
        rmse_col = f"H{horizon}_rmse"
        dir_col = f"H{horizon}_direction_accuracy"
        risk_col = f"H{horizon}_deteccion_caidas"
        loss_col = f"H{horizon}_loss"

        best_mae = sort_metric_subset(
            master_df.dropna(subset=[mae_col]),
            metric_col=mae_col,
            ascending=True,
        ).iloc[0]
        best_rmse = sort_metric_subset(
            master_df.dropna(subset=[rmse_col]),
            metric_col=rmse_col,
            ascending=True,
        ).iloc[0]
        best_direction = sort_metric_subset(
            master_df.dropna(subset=[dir_col]),
            metric_col=dir_col,
            ascending=False,
        ).iloc[0]
        best_risk = sort_metric_subset(
            master_df.dropna(subset=[risk_col]),
            metric_col=risk_col,
            ascending=False,
        ).iloc[0]
        best_loss = sort_metric_subset(
            master_df.dropna(subset=[loss_col]),
            metric_col=loss_col,
            ascending=True,
        ).iloc[0]

        rows.append(
            {
                "horizonte": f"H{horizon}",
                "mejor_mae_run_id": best_mae["run_id"],
                "mejor_mae_family": best_mae["family"],
                "mejor_mae_model": best_mae["model"],
                "mejor_mae": best_mae[mae_col],
                "mejor_rmse_run_id": best_rmse["run_id"],
                "mejor_rmse_family": best_rmse["family"],
                "mejor_rmse_model": best_rmse["model"],
                "mejor_rmse": best_rmse[rmse_col],
                "mejor_direction_accuracy_run_id": best_direction["run_id"],
                "mejor_direction_accuracy_family": best_direction["family"],
                "mejor_direction_accuracy_model": best_direction["model"],
                "mejor_direction_accuracy": best_direction[dir_col],
                "mejor_deteccion_caidas_run_id": best_risk["run_id"],
                "mejor_deteccion_caidas_family": best_risk["family"],
                "mejor_deteccion_caidas_model": best_risk["model"],
                "mejor_deteccion_caidas": best_risk[risk_col],
                "mejor_loss_run_id": best_loss["run_id"],
                "mejor_loss_family": best_loss["family"],
                "mejor_loss_model": best_loss["model"],
                "mejor_loss_h": best_loss[loss_col],
            }
        )
    return pd.DataFrame(rows)


def discover_planned_run_ids(prompts_dir: Path) -> list[str]:
    planned: set[str] = set()
    for path in prompts_dir.rglob("*.md"):
        text = path.read_text()
        for match in RUN_ID_PATTERN.findall(text):
            planned.add(match)
    return sorted(planned)


def format_metric_value(value: Any) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"{float(value):.6f}"


def build_horizon_metric_sections(compact_df: pd.DataFrame) -> str:
    sections: list[str] = []
    metric_order = ("mae", "rmse", "direction_accuracy", "deteccion_caidas", "loss_h")

    for horizonte in ("H1", "H2", "H3", "H4"):
        horizon_rows = compact_df[compact_df["horizonte"] == horizonte].copy()
        if horizon_rows.empty:
            continue
        sections.append(f"### {horizonte}")

        winners_in_horizon: list[str] = []
        for metric in metric_order:
            metric_row = horizon_rows[horizon_rows["metrica"] == metric]
            if metric_row.empty:
                sections.append(f"- mejor en {metric}: no disponible")
                continue
            row = metric_row.iloc[0]
            winners_in_horizon.append(str(row["mejor_run_id"]))
            tie_note = ""
            if bool(row.get("empate_exacto_top1_top2")) and row.get("segundo_run_id"):
                tie_note = f" | empate exacto con `{row['segundo_run_id']}`"
            sections.append(
                f"- mejor en {metric}: `{row['mejor_run_id']}` con `{format_metric_value(row['mejor_valor'])}`{tie_note}"
            )

        winner_counts = pd.Series(winners_in_horizon).value_counts()
        if not winner_counts.empty and int(winner_counts.iloc[0]) > 1:
            dominant_run = winner_counts.index[0]
            sections.append(
                f"- dominio_multiple: `{dominant_run}` gana {int(winner_counts.iloc[0])} de 5 metricas en {horizonte}."
            )
        else:
            sections.append(f"- lectura: no hay un dominador unico en {horizonte}; el horizonte reparte ventajas.")

    return "\n".join(sections)


def build_markdown_summary(
    *,
    master_df: pd.DataFrame,
    runs_catalog_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    stacking_readiness_df: pd.DataFrame,
    coverage_df: pd.DataFrame,
    stacking_base_sheets: dict[str, pd.DataFrame],
    planned_run_ids: list[str],
) -> str:
    metric_rankings_df = build_metric_rankings_long(master_df)
    winners_compact_df = build_metric_winners_compact(metric_rankings_df)
    complete_master = master_df[master_df["status_run"] == "completo"].copy()
    best_global = complete_master.nsmallest(1, "L_total_Radar").iloc[0]
    best_h1 = complete_master.nsmallest(1, "H1_loss").iloc[0]
    best_h2 = complete_master.nsmallest(1, "H2_loss").iloc[0]
    best_h3 = complete_master.nsmallest(1, "H3_loss").iloc[0]
    best_h4 = complete_master.nsmallest(1, "H4_loss").iloc[0]
    best_dir_global = complete_master.nlargest(1, "direction_accuracy_promedio").iloc[0]
    best_risk_global = complete_master.nlargest(1, "deteccion_caidas_promedio").iloc[0]
    best_dir_h1 = complete_master.nlargest(1, "H1_direction_accuracy").iloc[0]
    best_dir_h2 = complete_master.nlargest(1, "H2_direction_accuracy").iloc[0]
    best_dir_h3 = complete_master.nlargest(1, "H3_direction_accuracy").iloc[0]
    best_dir_h4 = complete_master.nlargest(1, "H4_direction_accuracy").iloc[0]
    best_risk_h1 = complete_master.nlargest(1, "H1_deteccion_caidas").iloc[0]
    best_risk_h2 = complete_master.nlargest(1, "H2_deteccion_caidas").iloc[0]
    best_risk_h3 = complete_master.nlargest(1, "H3_deteccion_caidas").iloc[0]
    best_risk_h4 = complete_master.nlargest(1, "H4_deteccion_caidas").iloc[0]

    family_counts = complete_master["family"].fillna("desconocida").value_counts().to_dict()
    canonical_run_ids = set(master_df["run_id"])
    planned_without_artifacts = [run_id for run_id in planned_run_ids if run_id not in canonical_run_ids]
    partial_dirs = inventory_df[inventory_df["status_artifactos"] != "completo"]
    if partial_dirs.empty:
        partial_dirs_text = "- No se detectaron directorios parciales."
    else:
        partial_lines = []
        for _, row in partial_dirs.iterrows():
            partial_lines.append(
                f"- `{row['run_id']}` | `{row['status_artifactos']}` | `{row['path_run']}` | {row['comentario']}"
            )
        partial_dirs_text = "\n".join(partial_lines)

    selected_features_count = int((inventory_df["features_seleccionadas"] > 0).sum())
    resumen_count = int((inventory_df["resumen_horizontes"] > 0).sum())
    stacking_compatible = stacking_readiness_df[stacking_readiness_df["compatible_para_stacking"] == True]
    stacking_partial = stacking_readiness_df[
        (stacking_readiness_df["compatible_para_stacking"] != True)
        & (stacking_readiness_df["prioridad_para_meta_modelo"].isin(["media", "baja"]))
    ]
    per_horizon_mergeable = (
        coverage_df.groupby("horizonte_label")["compatible_para_merge"].sum().to_dict()
        if not coverage_df.empty
        else {}
    )
    stacking_base_lines = []
    for sheet_name, sheet_df in stacking_base_sheets.items():
        pred_columns = [column for column in sheet_df.columns if column not in {"fecha", "y_true", "n_modelos_disponibles_fila"}]
        stacking_base_lines.append(
            f"- `{sheet_name}`: filas={len(sheet_df)}, modelos_integrados={len(pred_columns)}"
        )
    stacking_base_text = "\n".join(stacking_base_lines) if stacking_base_lines else "- No se construyeron bases parciales."

    return f"""# Resumen Auditoria Experimentos Radar

## Hallazgos principales

- Runs maestros consolidados: {len(master_df)}
- Runs en catalogo integral: {len(runs_catalog_df)}
- Directorios auditados en inventario: {len(inventory_df)}
- Directorios con artefactos parciales o inconsistentes: {len(partial_dirs)}
- Familias con runs maestros: {json.dumps(family_counts, ensure_ascii=False)}

## Mejor desempeño encontrado

- Mejor global por `L_total_Radar`: `{best_global['run_id']}` con `{best_global['L_total_Radar']:.6f}`
- Mejor `H1`: `{best_h1['run_id']}` con `loss_h={best_h1['H1_loss']:.6f}`
- Mejor `H2`: `{best_h2['run_id']}` con `loss_h={best_h2['H2_loss']:.6f}`
- Mejor `H3`: `{best_h3['run_id']}` con `loss_h={best_h3['H3_loss']:.6f}`
- Mejor `H4`: `{best_h4['run_id']}` con `loss_h={best_h4['H4_loss']:.6f}`
- Mejor `direction_accuracy` promedio: `{best_dir_global['run_id']}` con `{best_dir_global['direction_accuracy_promedio']:.6f}`
- Mejor `deteccion_caidas` promedio: `{best_risk_global['run_id']}` con `{best_risk_global['deteccion_caidas_promedio']:.6f}`

## Fortalezas operativas por horizonte

- Mejor `direction_accuracy` en `H1`: `{best_dir_h1['run_id']}` con `{best_dir_h1['H1_direction_accuracy']:.6f}`
- Mejor `direction_accuracy` en `H2`: `{best_dir_h2['run_id']}` con `{best_dir_h2['H2_direction_accuracy']:.6f}`
- Mejor `direction_accuracy` en `H3`: `{best_dir_h3['run_id']}` con `{best_dir_h3['H3_direction_accuracy']:.6f}`
- Mejor `direction_accuracy` en `H4`: `{best_dir_h4['run_id']}` con `{best_dir_h4['H4_direction_accuracy']:.6f}`
- Mejor `deteccion_caidas` en `H1`: `{best_risk_h1['run_id']}` con `{best_risk_h1['H1_deteccion_caidas']:.6f}`
- Mejor `deteccion_caidas` en `H2`: `{best_risk_h2['run_id']}` con `{best_risk_h2['H2_deteccion_caidas']:.6f}`
- Mejor `deteccion_caidas` en `H3`: `{best_risk_h3['run_id']}` con `{best_risk_h3['H3_deteccion_caidas']:.6f}`
- Mejor `deteccion_caidas` en `H4`: `{best_risk_h4['run_id']}` con `{best_risk_h4['H4_deteccion_caidas']:.6f}`

## Ganadores por metrica y horizonte

{build_horizon_metric_sections(winners_compact_df)}

## Inventario real por familia

- `E1`: {sum(run_id.startswith('E1_') for run_id in master_df['run_id'])} runs maestros
- `E2`: {sum(run_id.startswith('E2_') for run_id in master_df['run_id'])} runs maestros
- `E3`: {sum(run_id.startswith('E3_') for run_id in master_df['run_id'])} runs maestros
- `E4`: {sum(run_id.startswith('E4_') for run_id in master_df['run_id'])} runs maestros

## Runs parciales / inconsistentes

{partial_dirs_text}

## Runs planeados detectados sin artefactos consolidados

{', '.join(planned_without_artifacts) if planned_without_artifacts else 'No se detectaron run_ids planeados sin artefactos mediante el barrido de prompts.'}

Nota: esta lista sale de menciones en prompts/documentos `.md`; no distingue automaticamente entre runs cancelados, diferidos o nunca ejecutados.

## Inconsistencias detectadas

- `E2_v1_clean` tiene tres directorios: dos intentos abortados y un directorio canónico completo. Se consolidó el directorio `E2_v1_clean_20260323_050029`.
- Los runs históricos `E1_v1` y `E1_v2` usan una estructura de artefactos más antigua, pero contienen métricas y predicciones suficientes para tratarlos como completos.
- No se encontraron artefactos experimentales fuera de `Experimentos/runs/` para `metadata_run.json`, `parametros_run.json`, `metricas_horizonte.json` o `resumen_modeling_horizontes.json`.

## Artefactos útiles para explicación por horizonte

- Directorios con `features_seleccionadas_h*.csv`: {selected_features_count}
- Directorios con `resumen_modeling_horizontes.json`: {resumen_count}
- No se encontraron artefactos homogéneos y reutilizables de importancias de variables o coeficientes comparables entre familias. Esa capa explicativa sigue pendiente.

## Readiness para stacking / hipermodelo

- Runs compatibles para stacking 1..4: {len(stacking_compatible)}
- Runs con utilidad parcial para merge por horizonte: {len(stacking_partial)}
- Cobertura mergeable por horizonte: {json.dumps(per_horizon_mergeable, ensure_ascii=False)}

### Bases parciales reconstruidas

{stacking_base_text}

### Lectura retrospectiva

- Se pudo reconstruir retrospectivamente catalogo, metricas por horizonte, cobertura de predicciones y compatibilidad estructural para stacking a partir de artefactos reales en disco.
- Se pudieron construir hojas `stacking_base_h1` a `stacking_base_h4` con los runs que tienen predicciones mergeables por horizonte.
- Lo que todavia no se pudo homogeneizar retrospectivamente es la capa explicativa transversal entre familias: coeficientes, importancias e interpretabilidad comparable.

## Lectura preliminar

- La evidencia sí sugiere especialización por horizonte: `{best_h1['run_id']}` domina `H1`, `{best_h2['run_id']}` domina `H2`, `{best_h3['run_id']}` domina `H3` y `{best_h4['run_id']}` domina `H4`.
- También hay especialización operativa: dirección y detección de caídas no siempre coinciden con el mejor `loss_h`.
- En `E3`, la señal más útil quedó en `E3_v2_clean`; `E3_v3_clean` no mejora esa línea y `E4` no desplazó a bagging.
- Ya existe base suficiente para pensar en un ensamblado por horizonte como hipótesis metodológica futura, con cobertura real de `E1-E4` y auditoría explícita de compatibilidad de predicciones.
- Conviene automatizar a partir de ahora la reconstrucción de esta tabla maestra en cada corrida nueva para evitar que el análisis dependa del workbook manual.
"""


def build_experiments_master_table(
    *,
    runs_dir: Path,
    workbook: Path,
    prompts_dir: Path,
    output_dir: Path,
) -> MasterAuditBuildResult:
    runs_dir = runs_dir.expanduser().resolve()
    workbook = workbook.expanduser().resolve()
    prompts_dir = prompts_dir.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    records = scan_run_directories(runs_dir)
    canonical, grouped = select_canonical_records(records)
    summary_lookup, results_lookup = build_workbook_lookup(workbook)

    master_rows = build_master_rows(canonical, summary_lookup, results_lookup)
    master_df = pd.DataFrame(master_rows).sort_values("run_id").reset_index(drop=True)
    runs_catalog_rows = build_runs_catalog_rows(canonical, summary_lookup)
    runs_catalog_df = pd.DataFrame(runs_catalog_rows).sort_values("run_id").reset_index(drop=True)
    metricas_long_df = build_metricas_por_horizonte_long(canonical, master_df, results_lookup)
    coverage_df, standardized_lookup = build_prediction_coverage(canonical)
    stacking_readiness_df = build_stacking_readiness(runs_catalog_df, coverage_df)

    inventory_rows = build_inventory_rows(records, canonical, grouped)
    inventory_df = pd.DataFrame(inventory_rows).sort_values(["run_id", "path_run"]).reset_index(drop=True)

    ranking_df = build_rankings(master_df)
    ranking_dim_df = build_dimension_rankings(master_df)
    metric_rankings_df = build_metric_rankings_long(master_df)
    winners_compact_df = build_metric_winners_compact(metric_rankings_df)
    planned_run_ids = discover_planned_run_ids(prompts_dir)
    stacking_readiness_lookup = stacking_readiness_df.set_index("run_id").to_dict(orient="index")
    runs_catalog_df["es_candidato_meta_modelo"] = runs_catalog_df["run_id"].map(
        lambda run_id: stacking_readiness_lookup.get(run_id, {}).get("compatible_para_stacking", False)
    )
    runs_catalog_df["motivo_exclusion_meta_modelo"] = runs_catalog_df["run_id"].map(
        lambda run_id: stacking_readiness_lookup.get(run_id, {}).get("motivo_no_compatible", "")
    )

    stacking_base_sheets = {
        f"stacking_base_h{horizon}": build_stacking_base_sheet(
            horizon=horizon,
            coverage_df=coverage_df,
            runs_catalog_df=runs_catalog_df,
            standardized_lookup=standardized_lookup,
        )
        for horizon in (1, 2, 3, 4)
    }

    inventory_json = {
        "summary": {
            "master_runs_total": int(len(master_df)),
            "runs_catalog_total": int(len(runs_catalog_df)),
            "inventory_directories_total": int(len(inventory_df)),
            "e1_master_runs": int(sum(master_df["run_id"].str.startswith("E1_"))),
            "e2_master_runs": int(sum(master_df["run_id"].str.startswith("E2_"))),
            "e3_master_runs": int(sum(master_df["run_id"].str.startswith("E3_"))),
            "e4_master_runs": int(sum(master_df["run_id"].str.startswith("E4_"))),
            "stacking_compatible_runs": int(stacking_readiness_df["compatible_para_stacking"].sum()),
        },
        "canonical_runs": master_rows,
        "runs_catalogo": runs_catalog_df.to_dict(orient="records"),
        "metricas_por_horizonte_long": metricas_long_df.to_dict(orient="records"),
        "inventory_directories": inventory_rows,
        "stacking_readiness": stacking_readiness_df.to_dict(orient="records"),
        "cobertura_predicciones": coverage_df.to_dict(orient="records"),
        "stacking_base_summary": {
            sheet_name: {
                "filas": int(len(sheet_df)),
                "columnas_modelo": int(
                    len([c for c in sheet_df.columns if c not in {"fecha", "y_true", "n_modelos_disponibles_fila"}])
                ),
            }
            for sheet_name, sheet_df in stacking_base_sheets.items()
        },
        "planned_run_ids_detected": planned_run_ids,
        "planned_without_artifacts": [
            run_id for run_id in planned_run_ids if run_id not in set(master_df["run_id"])
        ],
    }

    csv_path = output_dir / "tabla_maestra_experimentos_radar.csv"
    xlsx_path = output_dir / "tabla_maestra_experimentos_radar.xlsx"
    json_path = output_dir / "inventario_experimentos_radar.json"
    md_path = output_dir / "resumen_auditoria_experimentos.md"

    master_df.to_csv(csv_path, index=False)
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        runs_catalog_df.to_excel(writer, sheet_name="runs_catalogo", index=False)
        master_df.to_excel(writer, sheet_name="runs_consolidados", index=False)
        metricas_long_df.to_excel(writer, sheet_name="metricas_por_horizonte_long", index=False)
        ranking_df.to_excel(writer, sheet_name="ranking_por_horizonte", index=False)
        ranking_dim_df.to_excel(writer, sheet_name="ranking_dimensiones", index=False)
        metric_rankings_df.to_excel(writer, sheet_name="ranking_metricas_por_horizonte", index=False)
        winners_compact_df.to_excel(writer, sheet_name="ganadores_por_metrica_horizonte", index=False)
        stacking_readiness_df.to_excel(writer, sheet_name="stacking_readiness", index=False)
        coverage_df.to_excel(writer, sheet_name="cobertura_predicciones", index=False)
        inventory_df.to_excel(writer, sheet_name="inventario_runs", index=False)
        for sheet_name, sheet_df in stacking_base_sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    json_path.write_text(json.dumps(inventory_json, ensure_ascii=False, indent=2))
    md_path.write_text(
        build_markdown_summary(
            master_df=master_df,
            runs_catalog_df=runs_catalog_df,
            inventory_df=inventory_df,
            stacking_readiness_df=stacking_readiness_df,
            coverage_df=coverage_df,
            stacking_base_sheets=stacking_base_sheets,
            planned_run_ids=planned_run_ids,
        )
    )

    return MasterAuditBuildResult(
        csv_path=csv_path,
        xlsx_path=xlsx_path,
        json_path=json_path,
        markdown_path=md_path,
        master_runs_total=len(master_df),
        inventory_directories_total=len(inventory_df),
    )


def main() -> None:
    args = parse_args()
    result = build_experiments_master_table(
        runs_dir=args.runs_dir,
        workbook=args.workbook,
        prompts_dir=args.prompts_dir,
        output_dir=args.output_dir,
    )

    print(f"CSV: {result.csv_path}")
    print(f"XLSX: {result.xlsx_path}")
    print(f"JSON: {result.json_path}")
    print(f"MD: {result.markdown_path}")
    print(f"Runs maestros: {result.master_runs_total}")
    print(f"Directorios inventariados: {result.inventory_directories_total}")


if __name__ == "__main__":
    main()
