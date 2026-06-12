"""
Selector v3 (RISK-AWARE) - BENCHMARK CONGELADO.

Este archivo contiene la versión limpia de v3 para uso como benchmark.
NO modificar - representar el estado dorado de riesgo separado sin mezcla v4/v5.

DESCRIPCIÓN

Consolida predicciones de E1 y E9 en una sola predicción ponderada por
desempeño reciente (MAE rolling), con corrección de sesgo por modelo.
Deriva dirección, riesgo de caída y confianza directamente del valor
numérico consolidado.

Características v3:
- Sin leakage temporal: MAE rolling y bias rolling usan shift(horizon)
- MAE rolling con shift(horizon) para evitar ver errores futuros
- Predicción consolidada honesta: usa error_consolidado real para MAE
- Separación clara entre:
  - direccion_predicha: baja/incierto/sube
  - caida_predicha: booleano (direccion_predicha == "baja")
  - alerta_caida: booleano (riesgo_caida in ["alto", "medio"])
  - riesgo_caida: alto/medio/bajo
- Sin mae_consolidado = min(MAE_E1, MAE_E9)
- Con ponderación por MAE inverso (no selector duro)

No modifica runners, función de pérdida ni empaquetado dual existente.
Consume predicciones ya generadas y produce una tabla de decisión
independiente.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SelectorConfig:
    rolling_window: int = 4
    confidence_k: float = 1.0
    min_observations_for_weight: int = 2


DIRECTION_LABELS = ("baja", "incierto", "sube")


def load_model_predictions(
    run_dir: Path,
    horizon: int,
) -> pd.DataFrame:
    path = run_dir / f"predicciones_h{horizon}.csv"
    df = pd.read_csv(path)
    date_col = "fecha" if "fecha" in df.columns else "fecha_inicio_semana"
    df["fecha"] = pd.to_datetime(df[date_col])
    return df


def _rolling_mae(errors: pd.Series, window: int, min_periods: int) -> pd.Series:
    return errors.abs().rolling(window=window, min_periods=min_periods).mean()


def _rolling_bias(errors: pd.Series, window: int, min_periods: int) -> pd.Series:
    return errors.rolling(window=window, min_periods=min_periods).mean()


def build_consolidated_table(
    e1_run_dir: Path,
    e9_run_dir: Path,
    horizon: int,
    config: SelectorConfig | None = None,
) -> pd.DataFrame:
    cfg = config or SelectorConfig()

    e1 = load_model_predictions(e1_run_dir, horizon)
    e9 = load_model_predictions(e9_run_dir, horizon)

    base = e1[["fecha", "y_current", "y_true"]].copy()
    base["E1_pred"] = e1["y_pred"]
    base["E1_error"] = e1["error"]

    e9_merged = e9[["fecha", "y_pred", "error"]].rename(
        columns={"y_pred": "E9_pred", "error": "E9_error"}
    )
    base = base.merge(e9_merged, on="fecha", how="left")
    base = base.sort_values("fecha").reset_index(drop=True)

    # --- MAE rolling por modelo, shift(horizon) para evitar leakage ---
    base["E1_mae_rolling"] = _rolling_mae(
        base["E1_error"], cfg.rolling_window, cfg.min_observations_for_weight
    ).shift(horizon)

    base["E9_mae_rolling"] = (
        base["E9_error"]
        .abs()
        .rolling(window=cfg.rolling_window, min_periods=cfg.min_observations_for_weight)
        .mean()
        .shift(horizon)
    )

    # --- Sesgo rolling por modelo, shift(horizon) ---
    base["E1_bias_rolling"] = _rolling_bias(
        base["E1_error"], cfg.rolling_window, cfg.min_observations_for_weight
    ).shift(horizon)

    base["E9_bias_rolling"] = (
        base["E9_error"]
        .rolling(window=cfg.rolling_window, min_periods=cfg.min_observations_for_weight)
        .mean()
        .shift(horizon)
    )

    # --- Pesos por inverso de MAE ---
    base["E1_inv_mae"] = 1.0 / base["E1_mae_rolling"].clip(lower=1e-8)
    base["E9_inv_mae"] = np.where(
        base["E9_mae_rolling"].notna(),
        1.0 / base["E9_mae_rolling"].clip(lower=1e-8),
        0.0,
    )

    total_inv = base["E1_inv_mae"] + base["E9_inv_mae"]
    base["peso_E1"] = base["E1_inv_mae"] / total_inv
    base["peso_E9"] = base["E9_inv_mae"] / total_inv

    # Sin historial suficiente (NaN por shift o min_periods), defaultear a solo E1
    no_hist = base["E1_mae_rolling"].isna()
    base.loc[no_hist, "peso_E1"] = 1.0
    base.loc[no_hist, "peso_E9"] = 0.0

    # Cuando E9 no tiene datos, peso_E1=1.0
    no_e9 = base["E9_pred"].isna()
    base.loc[no_e9, "peso_E1"] = 1.0
    base.loc[no_e9, "peso_E9"] = 0.0

    # --- Predicciones ajustadas por sesgo por modelo ---
    base["E1_pred_adj"] = base["E1_pred"] - base["E1_bias_rolling"].fillna(0.0)
    base["E9_pred_adj"] = base["E9_pred"] - base["E9_bias_rolling"].fillna(0.0)

    base["y_pred_consolidado"] = (
        base["peso_E1"] * base["E1_pred_adj"]
        + base["peso_E9"] * base["E9_pred_adj"].fillna(0.0)
    )

    base["error_consolidado"] = base["y_pred_consolidado"] - base["y_true"]
    base["mae_esperado"] = (
        base["peso_E1"] * base["E1_mae_rolling"].fillna(0.0)
        + base["peso_E9"] * base["E9_mae_rolling"].fillna(0.0)
    )

    # --- Dirección y riesgo ---
    base["delta_predicho"] = base["y_pred_consolidado"] - base["y_current"]
    base["delta_real"] = base["y_true"] - base["y_current"]

    base["ratio_delta_mae"] = base["delta_predicho"].abs() / base["mae_esperado"].clip(lower=1e-8)

    base["direccion_predicha"] = np.where(
        base["delta_predicho"] < 0,
        "baja",
        np.where(
            base["delta_predicho"] < cfg.confidence_k * base["mae_esperado"],
            "incierto",
            "sube",
        ),
    )

    base["direccion_real"] = np.where(
        base["delta_real"] > 0, "sube", "baja"
    )

    # --- Riesgo de caída (separado de dirección) ---
    base["riesgo_caida"] = np.where(
        base["delta_predicho"] < 0,
        "alto",
        np.where(
            base["delta_predicho"] < cfg.confidence_k * base["mae_esperado"],
            "medio",
            "bajo",
        ),
    )

    base["alerta_caida"] = base["riesgo_caida"].isin(["alto", "medio"])
    base["caida_predicha"] = base["direccion_predicha"] == "baja"
    base["caida_real"] = base["delta_real"] <= 0

    # --- Confianza (sin ambigüedad con "baja" dirección) ---
    base["confianza"] = np.where(
        base["direccion_predicha"] == "incierto",
        "sin_senal_firme",
        np.where(base["ratio_delta_mae"] > 2.0, "alta", "media"),
    )

    # Direccion correcta: SOLO baja/sube (sin incierto)
    base["direccion_correcta"] = (
        base["direccion_predicha"] == base["direccion_real"]
    )

    # Coverage: el selector se compromete con dirección (no es incierto)
    base["compromiso_direccion"] = base["direccion_predicha"] != "incierto"

    base["modelo_dominante"] = np.where(
        base["peso_E1"] >= base["peso_E9"], "E1", "E9"
    )

    base["horizonte"] = horizon

    return base


def compute_period_metrics(
    table: pd.DataFrame,
    label: str = "",
) -> dict[str, Any]:
    n = len(table)
    if n == 0:
        return {"label": label, "n": 0}

    # v3: MAE consolidado HONESTO - error real de la predicción consolidada
    mae_consolidado = table["error_consolidado"].abs().mean()
    mae_e1 = table["E1_error"].abs().mean()
    e9_valid = table.dropna(subset=["E9_error"])
    mae_e9 = e9_valid["E9_error"].abs().mean() if len(e9_valid) > 0 else float("nan")

    evaluable = table[table["direccion_predicha"] != "incierto"]
    if len(evaluable) > 0:
        dir_acc = (evaluable["direccion_real"] == evaluable["direccion_predicha"]).mean()
    else:
        dir_acc = float("nan")

    n_inciertos = (table["direccion_predicha"] == "incierto").sum()

    caidas_reales = table["caida_real"].sum()
    if caidas_reales > 0:
        caidas_predichas_en_reales = table.loc[table["caida_real"], "caida_predicha"].sum()
        deteccion_baja_explicita = caidas_predichas_en_reales / caidas_reales
    else:
        deteccion_baja_explicita = 1.0

    if caidas_reales > 0:
        alertas_en_caidas_reales = table.loc[table["caida_real"], "alerta_caida"].sum()
        deteccion_riesgo_caida = alertas_en_caidas_reales / caidas_reales
    else:
        deteccion_riesgo_caida = 1.0

    return {
        "label": label,
        "n": n,
        "mae_consolidado": float(mae_consolidado),
        "mae_e1_puro": float(mae_e1),
        "mae_e9_puro": float(mae_e9),
        "direccion_accuracy": float(dir_acc),
        "n_inciertos": int(n_inciertos),
        "caidas_reales": int(caidas_reales),
        "deteccion_baja_explicita": float(deteccion_baja_explicita),
        "deteccion_riesgo_caida": float(deteccion_riesgo_caida),
    }


def run_selector_analysis(
    e1_run_dir: Path,
    e9_run_dir: Path,
    cutoff_date: pd.Timestamp,
    horizons: tuple[int, ...] = (1, 2, 3, 4),
    config: SelectorConfig | None = None,
) -> dict[str, Any]:
    cfg = config or SelectorConfig()
    results: dict[str, Any] = {
        "config": {
            "rolling_window": cfg.rolling_window,
            "confidence_k": cfg.confidence_k,
            "min_observations_for_weight": cfg.min_observations_for_weight,
        },
        "cutoff_date": str(cutoff_date.date()),
        "horizons": {},
    }

    for h in horizons:
        table = build_consolidated_table(e1_run_dir, e9_run_dir, h, cfg)

        train = table[table["fecha"] <= cutoff_date]
        oos = table[table["fecha"] > cutoff_date]

        train_metrics = compute_period_metrics(train, label="train")
        oos_metrics = compute_period_metrics(oos, label="oos")

        results["horizons"][h] = {
            "train": train_metrics,
            "oos": oos_metrics,
            "table_oos": oos[[
                "fecha", "y_current", "y_true",
                "E1_pred", "E9_pred", "E1_pred_adj", "E9_pred_adj",
                "peso_E1", "peso_E9",
                "y_pred_consolidado", "error_consolidado",
                "delta_predicho", "delta_real", "mae_esperado",
                "direccion_predicha", "direccion_real", "direccion_correcta",
                "riesgo_caida", "alerta_caida",
                "caida_predicha", "caida_real",
                "confianza", "modelo_dominante", "horizonte",
            ]].copy(),
        }

    return results


def format_results(results: dict[str, Any]) -> str:
    lines = []
    lines.append("SELECTOR NUMERICO ADAPTATIVO v3 (RISK-AWARE) — RESULTADOS")
    lines.append(f"Cutoff: {results['cutoff_date']}")
    cfg = results["config"]
    lines.append(f"Config: rolling_window={cfg['rolling_window']}  k={cfg['confidence_k']}  min_obs={cfg['min_observations_for_weight']}")
    lines.append("")

    for h, data in results["horizons"].items():
        tr = data["train"]
        oo = data["oos"]

        lines.append(f"{'='*95}")
        lines.append(f"  HORIZONTE h{h}")
        lines.append(f"{'='*95}")
        lines.append(
            f"  {'':>18} {'MAE_cons':>9} {'MAE_E1':>9} {'MAE_E9':>9}"
            f" | {'Dir_acc':>8} {'Inciert':>8} {'Det_baja':>8} {'Det_riesgo':>10}"
        )
        lines.append(
            f"  {'TRAIN (n='+str(tr['n'])+')':>18}"
            f" {tr['mae_consolidado']:>9.4f}"
            f" {tr['mae_e1_puro']:>9.4f}"
            f" {tr['mae_e9_puro']:>9.4f}"
            f" | {tr['direccion_accuracy']:>8.1%}"
            f" {tr['n_inciertos']:>8}"
            f" {tr['deteccion_baja_explicita']:>8.1%}"
            f" {tr['deteccion_riesgo_caida']:>10.1%}"
        )
        lines.append(
            f"  {'OOS (n='+str(oo['n'])+')':>18}"
            f" {oo['mae_consolidado']:>9.4f}"
            f" {oo['mae_e1_puro']:>9.4f}"
            f" {oo['mae_e9_puro']:>9.4f}"
            f" | {oo['direccion_accuracy']:>8.1%}"
            f" {oo['n_inciertos']:>8}"
            f" {oo['deteccion_baja_explicita']:>8.1%}"
            f" {oo['deteccion_riesgo_caida']:>10.1%}"
        )

        table = data["table_oos"]
        lines.append("")
        lines.append(
            f"  {'fecha':>12} {'y_curr':>7} {'y_true':>7}"
            f" | {'y_cons':>7} {'err':>7} {'mae_esp':>7}"
            f" | {'dir_pred':>8} {'dir_real':>8} {'ok':>5}"
            f" | {'riesgo':>6} {'conf':>14} {'dom':>3}"
        )
        lines.append(f"  {'-'*95}")
        for _, r in table.iterrows():
            fecha = r["fecha"].strftime("%Y-%m-%d")
            ok = "OK" if r["direccion_correcta"] else "FALLO"
            lines.append(
                f"  {fecha:>12} {r['y_current']:>7.4f} {r['y_true']:>7.4f}"
                f" | {r['y_pred_consolidado']:>7.4f} {r['error_consolidado']:>+7.4f} {r['mae_esperado']:>7.4f}"
                f" | {r['direccion_predicha']:>8} {r['direccion_real']:>8} {ok:>5}"
                f" | {r['riesgo_caida']:>6} {r['confianza']:>14} {r['modelo_dominante']:>3}"
            )
        lines.append("")

    return "\n".join(lines)