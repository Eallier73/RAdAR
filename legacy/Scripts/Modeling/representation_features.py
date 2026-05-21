from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config import CURRENT_TARGET_COLUMN, DATE_COLUMN, TARGET_COLUMNS, TARGET_MODE_DELTA, TARGET_MODE_LEVEL
from feature_engineering import build_lagged_dataset


REPRESENTATION_MODE_MINIMAL = "minimal"
REPRESENTATION_MODE_EXPANDED = "expanded"
REPRESENTATION_MODE_DISAGREEMENT_ONLY = "disagreement_only"
REPRESENTATION_MODE_CHOICES = (
    REPRESENTATION_MODE_MINIMAL,
    REPRESENTATION_MODE_EXPANDED,
    REPRESENTATION_MODE_DISAGREEMENT_ONLY,
)

DEFAULT_SOURCE_RUN_IDS_MINIMAL = ("E1_v5_clean", "E5_v4_clean")
DEFAULT_SOURCE_RUN_IDS_EXPANDED = ("E1_v5_clean", "E5_v4_clean", "E3_v2_clean", "E7_v3_clean")


def sanitize_run_id(run_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", run_id.lower()).strip("_")


def parse_run_summary(workbook_path: Path) -> pd.DataFrame:
    return pd.read_excel(workbook_path, sheet_name="RUN_SUMMARY")


def resolve_run_dir(workbook_path: Path, run_id: str) -> Path:
    run_summary = parse_run_summary(workbook_path)
    matches = run_summary.loc[run_summary["Run_ID"] == run_id]
    if matches.empty:
        raise ValueError(f"No se encontro run_id={run_id} en RUN_SUMMARY.")
    run_dir_value = matches.iloc[-1]["Run_dir"]
    if not isinstance(run_dir_value, str) or not run_dir_value:
        raise ValueError(f"RUN_SUMMARY no tiene Run_dir valido para {run_id}.")
    root_dir = workbook_path.resolve().parents[1]
    run_dir = root_dir / run_dir_value
    if not run_dir.exists():
        raise FileNotFoundError(f"Run_dir no encontrado para {run_id}: {run_dir}")
    return run_dir


def load_prediction_feature_frame(
    *,
    workbook_path: Path,
    run_id: str,
    horizon: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    run_dir = resolve_run_dir(workbook_path, run_id)
    path = run_dir / f"predicciones_h{horizon}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Predicciones faltantes para {run_id} h{horizon}: {path}")
    df = pd.read_csv(path, usecols=[DATE_COLUMN, "y_pred"])
    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])
    pred_column = f"rep_pred_{sanitize_run_id(run_id)}"
    df = df.rename(columns={"y_pred": pred_column})
    return (
        df,
        {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "prediction_path": str(path),
            "pred_column": pred_column,
        },
    )


def resolve_representation_spec(
    mode: str,
    source_run_ids_override: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    if source_run_ids_override:
        source_run_ids = tuple(source_run_ids_override)
    elif mode == REPRESENTATION_MODE_MINIMAL:
        source_run_ids = DEFAULT_SOURCE_RUN_IDS_MINIMAL
    else:
        source_run_ids = DEFAULT_SOURCE_RUN_IDS_EXPANDED

    if mode == REPRESENTATION_MODE_MINIMAL:
        return {
            "mode": mode,
            "source_run_ids": source_run_ids,
            "include_regime_block": True,
            "include_raw_prediction_block": True,
            "include_raw_delta_block": True,
            "include_disagreement_only": False,
            "description": "bloque parsimonioso con predicciones archivadas minimas + desacuerdo simple + regimen observable",
        }
    if mode == REPRESENTATION_MODE_EXPANDED:
        return {
            "mode": mode,
            "source_run_ids": source_run_ids,
            "include_regime_block": True,
            "include_raw_prediction_block": True,
            "include_raw_delta_block": True,
            "include_disagreement_only": False,
            "description": "bloque ampliado con diversidad de bases heterogeneas + agregados de desacuerdo + regimen observable",
        }
    if mode == REPRESENTATION_MODE_DISAGREEMENT_ONLY:
        return {
            "mode": mode,
            "source_run_ids": source_run_ids,
            "include_regime_block": False,
            "include_raw_prediction_block": False,
            "include_raw_delta_block": False,
            "include_disagreement_only": True,
            "description": "stress test metodologico dejando solo desacuerdo/consenso entre bases y quitando señales de regimen",
        }
    raise ValueError(f"Modo de representacion no soportado: {mode}")


def _build_regime_features(lagged: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    out = lagged.copy()
    rows: list[dict[str, Any]] = []
    current = CURRENT_TARGET_COLUMN
    lag1 = f"{current}_lag1"
    lag2 = f"{current}_lag2"
    lag3 = f"{current}_lag3"

    out["reg_obs_delta_lag1"] = out[current] - out[lag1]
    out["reg_obs_delta_lag2"] = out[lag1] - out[lag2]
    out["reg_obs_delta_lag3"] = out[lag2] - out[lag3]

    delta_cols = ["reg_obs_delta_lag1", "reg_obs_delta_lag2", "reg_obs_delta_lag3"]
    out["reg_obs_delta_mean_w3"] = out[delta_cols].mean(axis=1)
    out["reg_obs_abs_delta_mean_w3"] = out[delta_cols].abs().mean(axis=1)
    out["reg_obs_delta_std_w3"] = out[delta_cols].std(axis=1)
    out["reg_obs_streak_signed_w3"] = np.sign(out[delta_cols]).sum(axis=1)

    rows.extend(
        [
            {
                "feature_name": "reg_obs_delta_lag1",
                "block": "regimen_observable",
                "definition": "Cambio observado mas reciente del target",
                "formula_or_procedure": "y_t - y_t_lag1",
                "source": "dataset maestro",
                "temporal_availability": "observable_en_t",
                "leakage_note": "Usa solo y_t y lags historicos del target",
                "substantive_intuition": "Captura arranque o desaceleracion inmediata",
            },
            {
                "feature_name": "reg_obs_delta_lag2",
                "block": "regimen_observable",
                "definition": "Cambio observado dos pasos atras",
                "formula_or_procedure": "y_t_lag1 - y_t_lag2",
                "source": "dataset maestro",
                "temporal_availability": "observable_en_t",
                "leakage_note": "Usa solo historial del target",
                "substantive_intuition": "Captura persistencia reciente del movimiento",
            },
            {
                "feature_name": "reg_obs_delta_lag3",
                "block": "regimen_observable",
                "definition": "Cambio observado tres pasos atras",
                "formula_or_procedure": "y_t_lag2 - y_t_lag3",
                "source": "dataset maestro",
                "temporal_availability": "observable_en_t",
                "leakage_note": "Usa solo historial del target",
                "substantive_intuition": "Captura continuidad o reversa de la trayectoria reciente",
            },
            {
                "feature_name": "reg_obs_delta_mean_w3",
                "block": "regimen_observable",
                "definition": "Promedio reciente de cambios observados",
                "formula_or_procedure": "mean(delta_lag1, delta_lag2, delta_lag3)",
                "source": "dataset maestro",
                "temporal_availability": "observable_en_t",
                "leakage_note": "Resume solo cambios ya observados",
                "substantive_intuition": "Resume momentum local",
            },
            {
                "feature_name": "reg_obs_abs_delta_mean_w3",
                "block": "regimen_observable",
                "definition": "Magnitud tipica reciente del cambio observado",
                "formula_or_procedure": "mean(abs(delta_lag1), abs(delta_lag2), abs(delta_lag3))",
                "source": "dataset maestro",
                "temporal_availability": "observable_en_t",
                "leakage_note": "Usa solo historia del target",
                "substantive_intuition": "Aproxima volatilidad local util para arranques de horizonte",
            },
            {
                "feature_name": "reg_obs_delta_std_w3",
                "block": "regimen_observable",
                "definition": "Dispersion reciente del cambio observado",
                "formula_or_procedure": "std(delta_lag1, delta_lag2, delta_lag3)",
                "source": "dataset maestro",
                "temporal_availability": "observable_en_t",
                "leakage_note": "No usa ningun valor futuro",
                "substantive_intuition": "Mide estabilidad o cambio de regimen",
            },
            {
                "feature_name": "reg_obs_streak_signed_w3",
                "block": "regimen_observable",
                "definition": "Suma de signos de los tres cambios observados mas recientes",
                "formula_or_procedure": "sign(delta_lag1)+sign(delta_lag2)+sign(delta_lag3)",
                "source": "dataset maestro",
                "temporal_availability": "observable_en_t",
                "leakage_note": "Se calcula solo con historial disponible",
                "substantive_intuition": "Resume racha reciente de subidas o bajas",
            },
        ]
    )
    return out, rows


def build_e12_model_frame(
    *,
    df: pd.DataFrame,
    horizon: int,
    feature_columns: list[str],
    lags: tuple[int, ...],
    target_mode: str,
    workbook_path: Path,
    representation_mode: str,
    source_run_ids_override: tuple[str, ...] | None = None,
) -> tuple[pd.DataFrame, list[str], list[str], str, pd.DataFrame, dict[str, Any]]:
    target_level_column = TARGET_COLUMNS[horizon]
    lagged = build_lagged_dataset(df=df, feature_columns=feature_columns, lags=lags)
    lagged[DATE_COLUMN] = pd.to_datetime(lagged[DATE_COLUMN])

    if target_mode == TARGET_MODE_DELTA:
        target_column = f"{target_level_column}_delta"
        lagged[target_column] = lagged[target_level_column] - lagged[CURRENT_TARGET_COLUMN]
    elif target_mode == TARGET_MODE_LEVEL:
        target_column = target_level_column
    else:
        raise ValueError(f"target_mode no soportado: {target_mode}")

    spec = resolve_representation_spec(representation_mode, source_run_ids_override)
    source_metadata: list[dict[str, Any]] = []
    inventory_rows: list[dict[str, Any]] = []
    pred_columns: list[str] = []
    delta_columns: list[str] = []

    for run_id in spec["source_run_ids"]:
        pred_frame, metadata = load_prediction_feature_frame(
            workbook_path=workbook_path,
            run_id=run_id,
            horizon=horizon,
        )
        lagged = lagged.merge(pred_frame, on=DATE_COLUMN, how="left")
        source_metadata.append(metadata)
        pred_column = metadata["pred_column"]
        delta_column = pred_column.replace("rep_pred_", "rep_delta_")
        lagged[delta_column] = lagged[pred_column] - lagged[CURRENT_TARGET_COLUMN]
        pred_columns.append(pred_column)
        delta_columns.append(delta_column)
        inventory_rows.extend(
            [
                {
                    "feature_name": pred_column,
                    "block": "prediccion_archivada",
                    "definition": f"Prediccion historica archivada del run {run_id} para el mismo horizonte",
                    "formula_or_procedure": f"y_pred de {run_id} alineado por fecha y horizonte",
                    "source": str(metadata["prediction_path"]),
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "Cada valor proviene de una prediccion historica fuera de muestra generada con pasado disponible en su fecha",
                    "substantive_intuition": "Resume una lectura funcional alternativa del problema",
                },
                {
                    "feature_name": delta_column,
                    "block": "prediccion_archivada",
                    "definition": f"Delta implicito de la prediccion archivada del run {run_id}",
                    "formula_or_procedure": f"{pred_column} - {CURRENT_TARGET_COLUMN}",
                    "source": str(metadata["prediction_path"]),
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "Se deriva solo de la prediccion archivada y del valor actual observable en t",
                    "substantive_intuition": "Captura direccion y magnitud del movimiento sugerido por la base",
                },
            ]
        )

    lagged_feature_columns = []
    for column in [CURRENT_TARGET_COLUMN, *feature_columns]:
        for lag in lags:
            lagged_feature_columns.append(f"{column}_lag{lag}")

    always_include_columns: list[str] = []

    if spec["include_raw_prediction_block"]:
        always_include_columns.extend(pred_columns)
    if spec["include_raw_delta_block"]:
        always_include_columns.extend(delta_columns)

    pred_slug_map = {run_id: f"rep_pred_{sanitize_run_id(run_id)}" for run_id in spec["source_run_ids"]}
    delta_slug_map = {run_id: f"rep_delta_{sanitize_run_id(run_id)}" for run_id in spec["source_run_ids"]}

    if representation_mode == REPRESENTATION_MODE_MINIMAL:
        e1_pred = pred_slug_map.get("E1_v5_clean")
        e5_pred = pred_slug_map.get("E5_v4_clean")
        e1_delta = delta_slug_map.get("E1_v5_clean")
        e5_delta = delta_slug_map.get("E5_v4_clean")
        lagged["rep_spread_e1_e5"] = (lagged[e1_pred] - lagged[e5_pred]).abs()
        lagged["rep_pred_mean_e1_e5"] = lagged[[e1_pred, e5_pred]].mean(axis=1)
        lagged["rep_delta_mean_e1_e5"] = lagged[[e1_delta, e5_delta]].mean(axis=1)
        lagged["rep_delta_std_e1_e5"] = lagged[[e1_delta, e5_delta]].std(axis=1)
        always_include_columns.extend(
            [
                "rep_spread_e1_e5",
                "rep_pred_mean_e1_e5",
                "rep_delta_mean_e1_e5",
                "rep_delta_std_e1_e5",
            ]
        )
        inventory_rows.extend(
            [
                {
                    "feature_name": "rep_spread_e1_e5",
                    "block": "desacuerdo_modelos",
                    "definition": "Diferencia absoluta entre las predicciones archivadas de E1 y E5",
                    "formula_or_procedure": f"abs({e1_pred} - {e5_pred})",
                    "source": "predicciones archivadas E1_v5_clean y E5_v4_clean",
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "Solo usa predicciones historicas fuera de muestra ya disponibles en la fecha",
                    "substantive_intuition": "Mide conflicto entre lectura lineal y no lineal tabular",
                },
                {
                    "feature_name": "rep_pred_mean_e1_e5",
                    "block": "consenso_modelos",
                    "definition": "Promedio de las predicciones archivadas de E1 y E5",
                    "formula_or_procedure": f"mean({e1_pred}, {e5_pred})",
                    "source": "predicciones archivadas E1_v5_clean y E5_v4_clean",
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "No usa y futuro",
                    "substantive_intuition": "Resumen parsimonioso del consenso entre base lineal y no lineal",
                },
                {
                    "feature_name": "rep_delta_mean_e1_e5",
                    "block": "consenso_modelos",
                    "definition": "Promedio del delta sugerido por E1 y E5",
                    "formula_or_procedure": f"mean({e1_delta}, {e5_delta})",
                    "source": "predicciones archivadas E1_v5_clean y E5_v4_clean",
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "Deriva solo de predicciones historicas y del valor actual observable",
                    "substantive_intuition": "Resume direccion y magnitud promedio sugerida por dos familias",
                },
                {
                    "feature_name": "rep_delta_std_e1_e5",
                    "block": "desacuerdo_modelos",
                    "definition": "Desviacion estandar del delta sugerido por E1 y E5",
                    "formula_or_procedure": f"std({e1_delta}, {e5_delta})",
                    "source": "predicciones archivadas E1_v5_clean y E5_v4_clean",
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "Solo usa informacion disponible en t",
                    "substantive_intuition": "Proxy minima de incertidumbre inter-familia",
                },
            ]
        )
    else:
        lagged["rep_pred_mean_all"] = lagged[pred_columns].mean(axis=1)
        lagged["rep_pred_std_all"] = lagged[pred_columns].std(axis=1)
        lagged["rep_pred_range_all"] = lagged[pred_columns].max(axis=1) - lagged[pred_columns].min(axis=1)
        lagged["rep_delta_mean_all"] = lagged[delta_columns].mean(axis=1)
        lagged["rep_delta_std_all"] = lagged[delta_columns].std(axis=1)
        lagged["rep_fall_share_all"] = (lagged[delta_columns] <= 0.0).mean(axis=1)
        lagged["rep_direction_consensus_mean"] = np.sign(lagged[delta_columns]).mean(axis=1)
        always_include_columns.extend(
            [
                "rep_pred_mean_all",
                "rep_pred_std_all",
                "rep_pred_range_all",
                "rep_delta_mean_all",
                "rep_delta_std_all",
                "rep_fall_share_all",
                "rep_direction_consensus_mean",
            ]
        )
        inventory_rows.extend(
            [
                {
                    "feature_name": "rep_pred_mean_all",
                    "block": "consenso_modelos",
                    "definition": "Promedio de todas las predicciones archivadas usadas en el horizonte",
                    "formula_or_procedure": "mean(predicciones_archivadas_fuente)",
                    "source": ",".join(spec["source_run_ids"]),
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "No usa informacion futura",
                    "substantive_intuition": "Resumen del consenso general entre bases heterogeneas",
                },
                {
                    "feature_name": "rep_pred_std_all",
                    "block": "desacuerdo_modelos",
                    "definition": "Dispersion de todas las predicciones archivadas",
                    "formula_or_procedure": "std(predicciones_archivadas_fuente)",
                    "source": ",".join(spec["source_run_ids"]),
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "Solo usa predicciones ya disponibles en la fecha",
                    "substantive_intuition": "Proxy de incertidumbre o conflicto entre familias",
                },
                {
                    "feature_name": "rep_pred_range_all",
                    "block": "desacuerdo_modelos",
                    "definition": "Rango entre maxima y minima prediccion archivada",
                    "formula_or_procedure": "max(preds)-min(preds)",
                    "source": ",".join(spec["source_run_ids"]),
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "Sin uso del target futuro",
                    "substantive_intuition": "Mide dispersion extrema entre familias",
                },
                {
                    "feature_name": "rep_delta_mean_all",
                    "block": "consenso_modelos",
                    "definition": "Promedio del delta sugerido por todas las bases",
                    "formula_or_procedure": "mean(pred_i - y_t)",
                    "source": ",".join(spec["source_run_ids"]),
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "Deriva solo de predicciones archivadas y del valor actual",
                    "substantive_intuition": "Sintetiza el movimiento promedio sugerido por las bases",
                },
                {
                    "feature_name": "rep_delta_std_all",
                    "block": "desacuerdo_modelos",
                    "definition": "Dispersion del delta sugerido por todas las bases",
                    "formula_or_procedure": "std(pred_i - y_t)",
                    "source": ",".join(spec["source_run_ids"]),
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "No usa y futuro",
                    "substantive_intuition": "Cuantifica conflicto direccional y de magnitud entre bases",
                },
                {
                    "feature_name": "rep_fall_share_all",
                    "block": "consenso_modelos",
                    "definition": "Proporcion de bases que sugieren caida",
                    "formula_or_procedure": "mean((pred_i - y_t) <= 0)",
                    "source": ",".join(spec["source_run_ids"]),
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "Usa solo predicciones historicas y el valor actual",
                    "substantive_intuition": "Proxy simple de consenso bajista entre familias",
                },
                {
                    "feature_name": "rep_direction_consensus_mean",
                    "block": "consenso_modelos",
                    "definition": "Promedio del signo del movimiento sugerido por las bases",
                    "formula_or_procedure": "mean(sign(pred_i - y_t))",
                    "source": ",".join(spec["source_run_ids"]),
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "Se construye solo con informacion observable en t",
                    "substantive_intuition": "Resume el consenso direccional agregado",
                },
            ]
        )
        if "E1_v5_clean" in pred_slug_map and {"E3_v2_clean", "E5_v4_clean"}.issubset(pred_slug_map):
            e1_pred = pred_slug_map["E1_v5_clean"]
            nonlinear_cols = [pred_slug_map["E3_v2_clean"], pred_slug_map["E5_v4_clean"]]
            lagged["rep_pred_mean_nonlinear_tabular"] = lagged[nonlinear_cols].mean(axis=1)
            lagged["rep_spread_linear_vs_nonlinear"] = lagged[e1_pred] - lagged["rep_pred_mean_nonlinear_tabular"]
            always_include_columns.extend(
                [
                    "rep_pred_mean_nonlinear_tabular",
                    "rep_spread_linear_vs_nonlinear",
                ]
            )
            inventory_rows.extend(
                [
                    {
                        "feature_name": "rep_pred_mean_nonlinear_tabular",
                        "block": "consenso_modelos",
                        "definition": "Promedio de las bases tabulares no lineales E3 y E5",
                        "formula_or_procedure": "mean(pred_E3, pred_E5)",
                        "source": "E3_v2_clean,E5_v4_clean",
                        "temporal_availability": "prediccion_archivada_temporalmente_valida",
                        "leakage_note": "Solo usa predicciones historicas del mismo horizonte",
                        "substantive_intuition": "Resumen del bloque no lineal tabular",
                    },
                    {
                        "feature_name": "rep_spread_linear_vs_nonlinear",
                        "block": "desacuerdo_modelos",
                        "definition": "Diferencia entre el ancla lineal y el promedio no lineal tabular",
                        "formula_or_procedure": f"{e1_pred} - rep_pred_mean_nonlinear_tabular",
                        "source": "E1_v5_clean,E3_v2_clean,E5_v4_clean",
                        "temporal_availability": "prediccion_archivada_temporalmente_valida",
                        "leakage_note": "Se construye solo con predicciones historicas ya disponibles",
                        "substantive_intuition": "Mide desacuerdo estructural entre lectura lineal y no lineal",
                    },
                ]
            )
        if "E7_v3_clean" in pred_slug_map and {"E3_v2_clean", "E5_v4_clean"}.issubset(pred_slug_map):
            temporal_pred = pred_slug_map["E7_v3_clean"]
            tabular_cols = [pred_slug_map["E3_v2_clean"], pred_slug_map["E5_v4_clean"]]
            lagged["rep_spread_temporal_vs_tabular"] = lagged[temporal_pred] - lagged[tabular_cols].mean(axis=1)
            always_include_columns.append("rep_spread_temporal_vs_tabular")
            inventory_rows.append(
                {
                    "feature_name": "rep_spread_temporal_vs_tabular",
                    "block": "desacuerdo_modelos",
                    "definition": "Diferencia entre la base temporal y el promedio tabular no lineal",
                    "formula_or_procedure": f"{temporal_pred} - mean(pred_E3, pred_E5)",
                    "source": "E7_v3_clean,E3_v2_clean,E5_v4_clean",
                    "temporal_availability": "prediccion_archivada_temporalmente_valida",
                    "leakage_note": "No usa ningun target futuro",
                    "substantive_intuition": "Captura conflicto entre estructura temporal y tabular",
                }
            )
        if representation_mode == REPRESENTATION_MODE_DISAGREEMENT_ONLY:
            always_include_columns = [
                column
                for column in always_include_columns
                if column.startswith("rep_")
            ]

    if spec["include_regime_block"]:
        lagged, regime_inventory = _build_regime_features(lagged)
        inventory_rows.extend(regime_inventory)
        always_include_columns.extend(
            [
                "reg_obs_delta_lag1",
                "reg_obs_delta_lag2",
                "reg_obs_delta_lag3",
                "reg_obs_delta_mean_w3",
                "reg_obs_abs_delta_mean_w3",
                "reg_obs_delta_std_w3",
                "reg_obs_streak_signed_w3",
            ]
        )

    always_include_columns = list(dict.fromkeys(always_include_columns))
    base_feature_candidates = [*feature_columns, *lagged_feature_columns]
    modeling_columns = [
        DATE_COLUMN,
        CURRENT_TARGET_COLUMN,
        target_level_column,
        *feature_columns,
        *lagged_feature_columns,
        *always_include_columns,
    ]
    if target_column not in modeling_columns:
        modeling_columns.append(target_column)

    rows_before_dropna = len(lagged)
    modeling_df = lagged[modeling_columns].dropna().reset_index(drop=True)

    inventory_df = pd.DataFrame(inventory_rows)
    if not inventory_df.empty:
        inventory_df["horizonte_sem"] = horizon
        inventory_df["representation_mode"] = representation_mode
        inventory_df["source_run_ids"] = ",".join(spec["source_run_ids"])
        inventory_df = inventory_df[
            [
                "horizonte_sem",
                "representation_mode",
                "feature_name",
                "block",
                "definition",
                "formula_or_procedure",
                "source",
                "temporal_availability",
                "leakage_note",
                "substantive_intuition",
                "source_run_ids",
            ]
        ].drop_duplicates(subset=["horizonte_sem", "feature_name"])

    diagnostics = {
        "representation_mode": representation_mode,
        "source_run_ids": list(spec["source_run_ids"]),
        "source_run_metadata": source_metadata,
        "rows_before_dropna": int(rows_before_dropna),
        "rows_after_dropna": int(len(modeling_df)),
        "rows_removed": int(rows_before_dropna - len(modeling_df)),
        "base_feature_candidates": int(len(base_feature_candidates)),
        "representation_feature_count": int(len(always_include_columns)),
        "representation_features": always_include_columns,
        "description": spec["description"],
    }
    return modeling_df, base_feature_candidates, always_include_columns, target_column, inventory_df, diagnostics
