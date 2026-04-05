#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT_DIR / "Scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from common_runtime_logging import log_event
from Modeling.config import FALL_THRESHOLD
from Operational_Controlada.run_benchmarks_operativos_vigentes import (
    GRID_WORKBOOK_PATH,
    INVENTORY_PATH,
    MASTER_WORKBOOK_PATH,
    REGISTRY_PATH,
    build_validation_report,
    load_inventory,
    load_registry,
)


DEFAULT_OUTPUT_DIR = (
    ROOT_DIR / "Experimentos" / "operacion_dual_controlada" / "paquete_vigente"
)
NUMERIC_BENCHMARK_ID = "benchmark_numerico_puro_vigente"
FALL_BENCHMARK_ID = "benchmark_operativo_riesgo_vigente"
DIRECTION_POLICY_BY_HORIZON = {
    1: "E9_v2_clean",
    2: "E1_v5_clean",
    3: "E9_v2_clean",
    4: "E1_v5_clean",
}
DIRECTION_MODEL_BY_RUN = {
    "E1_v5_clean": "E1_v5_clean",
    "E9_v2_clean": "E9_v2_clean",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Empaqueta el sistema operativo dual vigente del Radar.",
    )
    parser.add_argument(
        "--registry-path",
        type=Path,
        default=REGISTRY_PATH,
        help="JSON canonico del registro operativo controlado.",
    )
    parser.add_argument(
        "--inventory-path",
        type=Path,
        default=INVENTORY_PATH,
        help="Inventario maestro canonico.",
    )
    parser.add_argument(
        "--grid-workbook-path",
        type=Path,
        default=GRID_WORKBOOK_PATH,
        help="Workbook del tracker operativo.",
    )
    parser.add_argument(
        "--master-workbook-path",
        type=Path,
        default=MASTER_WORKBOOK_PATH,
        help="Workbook maestro del proyecto.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directorio del paquete operativo dual canonico.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Falla si la auditoria operativa o el empaquetado detectan gaps.",
    )
    return parser.parse_args()


def _direction_label(delta: float) -> str:
    if delta > 0:
        return "sube"
    if delta < 0:
        return "baja"
    return "se_mantiene"


def _load_prediction_frame(run_dir: Path, run_id: str, horizon: int) -> pd.DataFrame:
    path = run_dir / f"predicciones_h{horizon}.csv"
    df = pd.read_csv(path)
    date_col = "fecha" if "fecha" in df.columns else "fecha_inicio_semana"
    normalized = pd.DataFrame(
        {
            "fecha_inicio_semana": df.get("fecha_inicio_semana", df[date_col]),
            "fecha_referencia": df[date_col],
            "horizonte_sem": horizon,
            "y_current": df["y_current"],
            "y_true": df["y_true"],
            "y_pred": df["y_pred"],
            "error": df.get("error"),
            "run_id_origen": run_id,
            "run_dir_origen": str(run_dir),
        }
    )
    normalized["delta_real"] = normalized["y_true"] - normalized["y_current"]
    normalized["delta_predicho"] = normalized["y_pred"] - normalized["y_current"]
    normalized["direction_real"] = normalized["delta_real"].map(_direction_label)
    normalized["direction_predicha"] = normalized["delta_predicho"].map(_direction_label)
    normalized["direction_correcta"] = (
        normalized["direction_real"] == normalized["direction_predicha"]
    )
    normalized["caida_real"] = normalized["delta_real"] <= FALL_THRESHOLD
    normalized["alerta_caida_predicha"] = normalized["delta_predicho"] <= FALL_THRESHOLD
    normalized["deteccion_caida_correcta"] = (
        normalized["caida_real"] == normalized["alerta_caida_predicha"]
    )
    return normalized


def _load_benchmark_predictions(registry_entry: dict[str, Any]) -> pd.DataFrame:
    run_id = str(registry_entry["run_id"])
    run_dir = Path(registry_entry["run_dir"])
    frames = [_load_prediction_frame(run_dir, run_id, horizon) for horizon in (1, 2, 3, 4)]
    return pd.concat(frames, ignore_index=True)


def _build_numeric_output(benchmark_entry: dict[str, Any]) -> pd.DataFrame:
    df = _load_benchmark_predictions(benchmark_entry).copy()
    df["modelo_oficial_numerico"] = benchmark_entry["run_id"]
    df["prediccion_numerica_oficial"] = df["y_pred"]
    return df[
        [
            "fecha_inicio_semana",
            "fecha_referencia",
            "horizonte_sem",
            "y_current",
            "y_true",
            "prediccion_numerica_oficial",
            "delta_real",
            "delta_predicho",
            "direction_real",
            "direction_predicha",
            "direction_correcta",
            "modelo_oficial_numerico",
            "run_id_origen",
            "run_dir_origen",
        ]
    ].sort_values(["horizonte_sem", "fecha_inicio_semana"])


def _build_direction_output(benchmark_entries_by_run: dict[str, dict[str, Any]]) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    for horizon, run_id in DIRECTION_POLICY_BY_HORIZON.items():
        source_entry = benchmark_entries_by_run[run_id]
        frame = _load_prediction_frame(Path(source_entry["run_dir"]), run_id, horizon).copy()
        frame["run_id_direction_oficial"] = run_id
        frame["politica_direccional"] = "9-1-9-1"
        pieces.append(
            frame[
                [
                    "fecha_inicio_semana",
                    "fecha_referencia",
                    "horizonte_sem",
                    "y_current",
                    "y_true",
                    "delta_real",
                    "delta_predicho",
                    "direction_real",
                    "direction_predicha",
                    "direction_correcta",
                    "run_id_direction_oficial",
                    "politica_direccional",
                    "run_dir_origen",
                ]
            ]
        )
    return pd.concat(pieces, ignore_index=True).sort_values(
        ["horizonte_sem", "fecha_inicio_semana"]
    )


def _build_fall_output(benchmark_entry: dict[str, Any]) -> pd.DataFrame:
    df = _load_benchmark_predictions(benchmark_entry).copy()
    df["run_id_alerta_caida_oficial"] = benchmark_entry["run_id"]
    return df[
        [
            "fecha_inicio_semana",
            "fecha_referencia",
            "horizonte_sem",
            "y_current",
            "y_true",
            "delta_real",
            "delta_predicho",
            "caida_real",
            "alerta_caida_predicha",
            "deteccion_caida_correcta",
            "run_id_alerta_caida_oficial",
            "run_dir_origen",
        ]
    ].sort_values(["horizonte_sem", "fecha_inicio_semana"])


def _build_consolidated_output(
    numeric_df: pd.DataFrame,
    direction_df: pd.DataFrame,
    fall_df: pd.DataFrame,
) -> pd.DataFrame:
    consolidated = numeric_df.merge(
        direction_df[
            [
                "fecha_inicio_semana",
                "horizonte_sem",
                "direction_real",
                "direction_predicha",
                "direction_correcta",
                "run_id_direction_oficial",
                "politica_direccional",
            ]
        ],
        on=["fecha_inicio_semana", "horizonte_sem"],
        how="outer",
        suffixes=("", "_direction"),
    )
    consolidated = consolidated.merge(
        fall_df[
            [
                "fecha_inicio_semana",
                "horizonte_sem",
                "caida_real",
                "alerta_caida_predicha",
                "deteccion_caida_correcta",
                "run_id_alerta_caida_oficial",
            ]
        ],
        on=["fecha_inicio_semana", "horizonte_sem"],
        how="outer",
        suffixes=("", "_fall"),
    )
    if "direction_real_direction" in consolidated.columns:
        consolidated["direction_real"] = consolidated["direction_real"].fillna(
            consolidated["direction_real_direction"]
        )
        consolidated = consolidated.drop(columns=["direction_real_direction"])
    if "caida_real_fall" in consolidated.columns:
        consolidated["caida_real"] = consolidated["caida_real"].fillna(
            consolidated["caida_real_fall"]
        )
        consolidated = consolidated.drop(columns=["caida_real_fall"])
    consolidated["disponible_prediccion_numerica"] = consolidated[
        "prediccion_numerica_oficial"
    ].notna()
    consolidated["disponible_direction_accuracy"] = consolidated[
        "run_id_direction_oficial"
    ].notna()
    consolidated["disponible_alerta_caida"] = consolidated[
        "run_id_alerta_caida_oficial"
    ].notna()
    return consolidated.sort_values(["horizonte_sem", "fecha_inicio_semana"])


def _build_manifest(
    *,
    registry: dict[str, Any],
    validation_report: dict[str, Any],
    numeric_entry: dict[str, Any],
    fall_entry: dict[str, Any],
    output_dir: Path,
    numeric_df: pd.DataFrame,
    direction_df: pd.DataFrame,
    fall_df: pd.DataFrame,
    consolidated_df: pd.DataFrame,
) -> dict[str, Any]:
    return {
        "fase_operativa": "produccion_controlada_dual",
        "estado_operativo": "vigente",
        "modelo_unico_final": False,
        "descripcion": (
            "Sistema operativo compuesto del Radar con salida numerica oficial desde E1_v5_clean, "
            "alerta de caida oficial desde E9_v2_clean y politica direccional fija por horizonte 9-1-9-1."
        ),
        "benchmarks_operativos_vigentes": registry.get("benchmarks_operativos_vigentes", []),
        "politica_direccional_por_horizonte": DIRECTION_POLICY_BY_HORIZON,
        "tabla_funcional_dual_vigente": registry.get("tabla_funcional_dual_vigente", []),
        "politica_funcional_dual_vigente": registry.get("politica_funcional_dual_vigente", []),
        "validacion_operativa": validation_report["summary"],
        "fuentes": {
            "prediccion_numerica_oficial": {
                "run_id": numeric_entry["run_id"],
                "run_dir": numeric_entry["run_dir"],
                "runner_script_canonico": numeric_entry["runner_script_canonico"],
            },
            "alertas_caida_oficiales": {
                "run_id": fall_entry["run_id"],
                "run_dir": fall_entry["run_dir"],
                "runner_script_canonico": fall_entry["runner_script_canonico"],
            },
            "direction_accuracy_oficial_por_horizonte": {
                f"H{horizon}": {
                    "run_id": run_id,
                    "runner_script_canonico": registry_entry["runner_script_canonico"],
                    "run_dir": registry_entry["run_dir"],
                }
                for horizon, run_id in DIRECTION_POLICY_BY_HORIZON.items()
                for registry_entry in registry.get("benchmarks_operativos_vigentes", [])
                if registry_entry["run_id"] == run_id
            },
        },
        "artefactos_generados": {
            "prediccion_numerica_oficial.csv": int(len(numeric_df)),
            "lectura_direccional_oficial.csv": int(len(direction_df)),
            "alertas_caida_oficiales.csv": int(len(fall_df)),
            "salida_dual_operativa_consolidada.csv": int(len(consolidated_df)),
            "tabla_funcional_canonica.csv": len(registry.get("tabla_funcional_dual_vigente", [])),
            "politica_funcional_dual.csv": len(registry.get("politica_funcional_dual_vigente", [])),
        },
        "output_dir": str(output_dir),
        "advertencia": (
            "La politica 9-1-9-1 es fija y funcional. No implica mezcla dinamica online ni seleccion ex post por fila."
        ),
    }


def _write_summary_markdown(
    *,
    output_dir: Path,
    manifest: dict[str, Any],
    numeric_df: pd.DataFrame,
    direction_df: pd.DataFrame,
    fall_df: pd.DataFrame,
    consolidated_df: pd.DataFrame,
) -> None:
    lines = [
        "# Resumen Operativo Dual Radar",
        "",
        f"- `fase_operativa`: `{manifest['fase_operativa']}`",
        f"- `estado_operativo`: `{manifest['estado_operativo']}`",
        "- `modelo_unico_final`: `False`",
        f"- `output_dir`: `{output_dir}`",
        "",
        "## Politica Funcional Congelada",
        "",
        "- Salida numerica principal: `E1_v5_clean`",
        "- Deteccion de caidas: `E9_v2_clean`",
        "- Direction H1: `E9_v2_clean`",
        "- Direction H2: `E1_v5_clean`",
        "- Direction H3: `E9_v2_clean`",
        "- Direction H4: `E1_v5_clean`",
        "",
        "## Artefactos Canonicos",
        "",
        f"- `prediccion_numerica_oficial.csv`: `{len(numeric_df)}` fila(s)",
        f"- `lectura_direccional_oficial.csv`: `{len(direction_df)}` fila(s)",
        f"- `alertas_caida_oficiales.csv`: `{len(fall_df)}` fila(s)",
        f"- `salida_dual_operativa_consolidada.csv`: `{len(consolidated_df)}` fila(s)",
        "- `tabla_funcional_canonica.csv`",
        "- `politica_funcional_dual.csv`",
        "- `manifiesto_operativo_dual.json`",
        "",
        "## Reglas de Lectura",
        "",
        "- `prediccion_numerica_oficial.csv` es la salida principal del sistema.",
        "- `lectura_direccional_oficial.csv` reporta la politica fija 9-1-9-1 por horizonte.",
        "- `alertas_caida_oficiales.csv` reporta la capa oficial de caidas desde `E9_v2_clean`.",
        "- `salida_dual_operativa_consolidada.csv` integra las tres capas sin fingir un modelo unico.",
    ]
    (output_dir / "resumen_operativo_dual.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    registry = load_registry(args.registry_path)
    inventory = load_inventory(args.inventory_path)
    validation_report = build_validation_report(
        registry=registry,
        registry_path=args.registry_path,
        inventory=inventory,
        inventory_path=args.inventory_path,
        grid_workbook_path=args.grid_workbook_path,
        master_workbook_path=args.master_workbook_path,
    )
    if validation_report["summary"]["gaps_total"] > 0 and args.strict:
        raise SystemExit(
            f"No se empaqueta el sistema dual: auditoria con gaps {validation_report['summary']}"
        )

    benchmark_entries = {
        item["benchmark_id"]: item for item in registry["benchmarks_operativos_vigentes"]
    }
    benchmark_entries_by_run = {
        item["run_id"]: item for item in registry["benchmarks_operativos_vigentes"]
    }
    numeric_entry = benchmark_entries[NUMERIC_BENCHMARK_ID]
    fall_entry = benchmark_entries[FALL_BENCHMARK_ID]

    numeric_df = _build_numeric_output(numeric_entry)
    direction_df = _build_direction_output(benchmark_entries_by_run)
    fall_df = _build_fall_output(fall_entry)
    consolidated_df = _build_consolidated_output(numeric_df, direction_df, fall_df)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(registry.get("tabla_funcional_dual_vigente", [])).to_csv(
        output_dir / "tabla_funcional_canonica.csv",
        index=False,
    )
    pd.DataFrame(registry.get("politica_funcional_dual_vigente", [])).to_csv(
        output_dir / "politica_funcional_dual.csv",
        index=False,
    )
    numeric_df.to_csv(output_dir / "prediccion_numerica_oficial.csv", index=False)
    direction_df.to_csv(output_dir / "lectura_direccional_oficial.csv", index=False)
    fall_df.to_csv(output_dir / "alertas_caida_oficiales.csv", index=False)
    consolidated_df.to_csv(
        output_dir / "salida_dual_operativa_consolidada.csv",
        index=False,
    )
    manifest = _build_manifest(
        registry=registry,
        validation_report=validation_report,
        numeric_entry=numeric_entry,
        fall_entry=fall_entry,
        output_dir=output_dir,
        numeric_df=numeric_df,
        direction_df=direction_df,
        fall_df=fall_df,
        consolidated_df=consolidated_df,
    )
    (output_dir / "manifiesto_operativo_dual.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_summary_markdown(
        output_dir=output_dir,
        manifest=manifest,
        numeric_df=numeric_df,
        direction_df=direction_df,
        fall_df=fall_df,
        consolidated_df=consolidated_df,
    )

    log_event(
        "operacion_dual",
        "INFO",
        "Paquete operativo dual actualizado",
        output_dir=output_dir,
        filas_numerico=len(numeric_df),
        filas_direction=len(direction_df),
        filas_caidas=len(fall_df),
        filas_consolidado=len(consolidated_df),
    )


if __name__ == "__main__":
    main()
