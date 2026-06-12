"""
Selector v3b: riesgo separado + baja operativa preventiva, sin leakage.

Consolida predicciones de E1 y E9 en una sola predicción ponderada por
desempeño reciente (MAE rolling), con corrección de sesgo por modelo.
Deriva dirección, riesgo de caída y confianza directamente del valor
numérico consolidado.

DEFINICIONES DE MÉTRICAS

Det_baja_estricta = baja explícita (direccion_predicha == "baja")

Det_baja_operativa = baja + baja_preventiva
(direccion_predicha.isin(["baja", "baja_preventiva"]))

Det_riesgo = baja + baja_preventiva + incierto con riesgo
(baja + baja_preventiva + riesgo_caida.isin(["alto", "medio"]))

SEMÁNTICA DE BAJA_PREVENTIVA

baja_preventiva NO es una predicción categórica dura de caída;
es una ALERTA OPERATIVA DE VULNERABILIDAD.

Clasificación de dirección:
- "sube": delta >= confidence_k * mae (señal clara de subida)
- "baja": delta < 0 (caída explícita)
- "baja_preventiva": 0 <= delta < preventive_k * mae (zona vulnerable)
- "incierto": preventive_k * mae <= delta < confidence_k * mae

La salida pública debe usar etiquetas amigables:
- "baja" → "baja" o "caída"
- "baja_preventiva" → "riesgo de baja" o "alerta de deterioro" o "señal vulnerable"
- "incierto" → "incierto" o "sin señal firme"

CARACTERÍSTICAS v3b (extiende v3)

- Añade categoría "baja_preventiva" para detección operativa de bajas
- Clasificación: sube, baja, baja_preventiva, incierto
- Det_baja_operativa = baja + baja_preventiva
- Métricas expandidas para evaluación operativa
- Sin leakage: todo usa shift(horizon)

v3b NO es v4 ni v5:
- Mantiene ponderación por MAE inverso (no selección dura)
- No reporta MAE = min(MAE_E1, MAE_E9)
- MAE consolidado honesto (predicción real del selector)

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
class SelectorConfigV3B:
    rolling_window: int = 4
    confidence_k: float = 1.0
    min_observations_for_weight: int = 2
    # Umbral para baja preventiva: fraction del MAE esperado
    preventive_k: float = 0.5
    # Umbral para sube claro
    sube_k: float = 1.0


DIRECTION_LABELS_V3B = ("sube", "baja", "baja_preventiva", "incierto")


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


def build_consolidated_table_v3b(
    e1_run_dir: Path,
    e9_run_dir: Path,
    horizon: int,
    config: SelectorConfigV3B | None = None,
) -> pd.DataFrame:
    cfg = config or SelectorConfigV3B()

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

    # --- Delta y dirección v3b ---
    base["delta_predicho"] = base["y_pred_consolidado"] - base["y_current"]
    base["delta_real"] = base["y_true"] - base["y_current"]

    base["ratio_delta_mae"] = base["delta_predicho"].abs() / base["mae_esperado"].clip(lower=1e-8)

    # v3b: Clasificación de dirección con baja_preventiva
    # baja: delta < 0 (caída explícita)
    # baja_preventiva: 0 <= delta < preventive_k * mae (zona vulnerable)
    # incierto: preventive_k * mae <= delta < confidence_k * mae
    # sube: delta >= confidence_k * mae
    base["direccion_predicha"] = np.where(
        base["delta_predicho"] < 0,
        "baja",
        np.where(
            base["delta_predicho"] < cfg.preventive_k * base["mae_esperado"],
            "baja_preventiva",
            np.where(
                base["delta_predicho"] < cfg.confidence_k * base["mae_esperado"],
                "incierto",
                "sube",
            ),
        ),
    )

    base["direccion_real"] = np.where(
        base["delta_real"] > 0, "sube", "baja"
    )

    # --- Riesgo de caída (separado de dirección, igual que v3) ---
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

    # --- Confianza (sin ambigüedad) ---
    base["confianza"] = np.where(
        base["direccion_predicha"] == "incierto",
        "sin_senal_firme",
        np.where(base["ratio_delta_mae"] > 2.0, "alta", "media"),
    )

    # Direccion correcta: SOLO baja/sube (sin incierto, sin baja_preventiva)
    base["direccion_correcta"] = (
        base["direccion_predicha"] == base["direccion_real"]
    )

    # Coverage: el selector se compromete con dirección (no es incierto)
    base["compromiso_direccion"] = base["direccion_predicha"].isin(["baja", "sube"])

    base["modelo_dominante"] = np.where(
        base["peso_E1"] >= base["peso_E9"], "E1", "E9"
    )

    base["horizonte"] = horizon

    return base


def compute_period_metrics_v3b(
    table: pd.DataFrame,
    label: str = "",
) -> dict[str, Any]:
    n = len(table)
    if n == 0:
        return {"label": label, "n": 0}

    # MAE honesto del selector (período real)
    mae_selector_real = table["error_consolidado"].abs().mean()
    mae_e1 = table["E1_error"].abs().mean()
    e9_valid = table.dropna(subset=["E9_error"])
    mae_e9 = e9_valid["E9_error"].abs().mean() if len(e9_valid) > 0 else float("nan")

    # MAE rolling maduros (usados para cálculos - con shift(horizon))
    mae_e1_rolling = table["E1_mae_rolling"].mean()
    mae_e9_rolling = table["E9_mae_rolling"].mean()
    mae_esperado = table["mae_esperado"].mean()

    # Dir_acc: solo baja/sube (sin incierto, sin baja_preventiva)
    evaluable = table[table["direccion_predicha"].isin(["baja", "sube"])]
    if len(evaluable) > 0:
        dir_acc = (evaluable["direccion_real"] == evaluable["direccion_predicha"]).mean()
    else:
        dir_acc = float("nan")

    # Conteos por categoría
    n_bajas_estrictas = (table["direccion_predicha"] == "baja").sum()
    n_bajas_preventivas = (table["direccion_predicha"] == "baja_preventiva").sum()
    n_inciertos = (table["direccion_predicha"] == "incierto").sum()
    n_subes = (table["direccion_predicha"] == "sube").sum()

    # Caídas reales
    caidas_reales = table["caida_real"].sum()

    # Det_baja_estricta: solo baja explícita
    if caidas_reales > 0:
        deteccion_baja_estricta = table["caida_predicha"].loc[table["caida_real"]].sum() / caidas_reales
    else:
        deteccion_baja_estricta = 1.0

    # Det_baja_operativa: baja + baja_preventiva
    baja_operativa_predicha = table["direccion_predicha"].isin(["baja", "baja_preventiva"])
    if caidas_reales > 0:
        deteccion_baja_operativa = baja_operativa_predicha.loc[table["caida_real"]].sum() / caidas_reales
    else:
        deteccion_baja_operativa = 1.0

    # Det_riesgo: baja + baja_preventiva + incierto con riesgo (medio/alto)
    riesgo_alto_o_medio = table["riesgo_caida"].isin(["alto", "medio"])
    if caidas_reales > 0:
        deteccion_riesgo = riesgo_alto_o_medio.loc[table["caida_real"]].sum() / caidas_reales
    else:
        deteccion_riesgo = 1.0

    # Precision de riesgo: de las alertas, cuántas fueron reales
    n_alertas_riesgo = riesgo_alto_o_medio.sum()
    if n_alertas_riesgo > 0:
        precision_riesgo = (
            table.loc[riesgo_alto_o_medio, "caida_real"].sum() / n_alertas_riesgo
        )
    else:
        precision_riesgo = float("nan")

    # Falsas alertas de riesgo
    falsas_alertas_riesgo = (
        riesgo_alto_o_medio & ~table["caida_real"]
    ).sum()

    # Precision baja operativa
    n_baja_operativa = baja_operativa_predicha.sum()
    if n_baja_operativa > 0:
        precision_baja_operativa = (
            table.loc[baja_operativa_predicha, "caida_real"].sum() / n_baja_operativa
        )
    else:
        precision_baja_operativa = float("nan")

    # Recall de riesgo (igual a Det_riesgo)
    recall_riesgo = deteccion_riesgo

    # Coverage
    coverage_direccion = (table["direccion_predicha"] != "incierto").mean()

    return {
        "label": label,
        "n": n,
        # MAE reales del período
        "mae_selector_real": float(mae_selector_real),
        "mae_e1": float(mae_e1),
        "mae_e9": float(mae_e9),
        # MAE rolling maduros (usados para cálculos)
        "mae_e1_rolling": float(mae_e1_rolling) if not pd.isna(mae_e1_rolling) else float("nan"),
        "mae_e9_rolling": float(mae_e9_rolling) if not pd.isna(mae_e9_rolling) else float("nan"),
        "mae_esperado": float(mae_esperado) if not pd.isna(mae_esperado) else float("nan"),
        # Métricas de dirección
        "direccion_accuracy": float(dir_acc),
        "n_bajas_estrictas": int(n_bajas_estrictas),
        "n_bajas_preventivas": int(n_bajas_preventivas),
        "n_inciertos": int(n_inciertos),
        "n_subes": int(n_subes),
        "caidas_reales": int(caidas_reales),
        "deteccion_baja_estricta": float(deteccion_baja_estricta),
        "deteccion_baja_operativa": float(deteccion_baja_operativa),
        "deteccion_riesgo": float(deteccion_riesgo),
        "precision_baja_operativa": float(precision_baja_operativa),
        "precision_riesgo": float(precision_riesgo),
        "recall_riesgo": float(recall_riesgo),
        "falsas_alertas_riesgo": int(falsas_alertas_riesgo),
        "n_alertas_riesgo": int(n_alertas_riesgo),
        "coverage_direccion": float(coverage_direccion),
    }


def run_selector_analysis_v3b(
    e1_run_dir: Path,
    e9_run_dir: Path,
    cutoff_date: pd.Timestamp,
    horizons: tuple[int, ...] = (1, 2, 3, 4),
    config: SelectorConfigV3B | None = None,
) -> dict[str, Any]:
    cfg = config or SelectorConfigV3B()
    results: dict[str, Any] = {
        "config": {
            "rolling_window": cfg.rolling_window,
            "confidence_k": cfg.confidence_k,
            "min_observations_for_weight": cfg.min_observations_for_weight,
            "preventive_k": cfg.preventive_k,
            "sube_k": cfg.sube_k,
        },
        "cutoff_date": str(cutoff_date.date()),
        "horizons": {},
    }

    for h in horizons:
        table = build_consolidated_table_v3b(e1_run_dir, e9_run_dir, h, cfg)

        train = table[table["fecha"] <= cutoff_date]
        oos = table[table["fecha"] > cutoff_date]

        train_metrics = compute_period_metrics_v3b(train, label="train")
        oos_metrics = compute_period_metrics_v3b(oos, label="oos")

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


def format_results_v3b(results: dict[str, Any]) -> str:
    lines = []
    lines.append("SELECTOR v3b (BAJA OPERATIVA PREVENTIVA) — RESULTADOS")
    lines.append(f"Cutoff: {results['cutoff_date']}")
    cfg = results["config"]
    lines.append(f"Config: rolling_window={cfg['rolling_window']}  k={cfg['confidence_k']}  preventive_k={cfg['preventive_k']}")
    lines.append("")

    for h, data in results["horizons"].items():
        tr = data["train"]
        oo = data["oos"]

        lines.append(f"{'='*100}")
        lines.append(f"  HORIZONTE h{h}")
        lines.append(f"{'='*100}")
        lines.append(
            f"  {'':>18} {'MAE_sel':>9} {'MAE_E1':>9} {'MAE_E9':>9} {'MAE_E1_r':>9} {'MAE_E9_r':>9}"
            f" | {'Dir_acc':>8} {'Cov':>6}"
            f" | {'Det_baja':>9} {'Det_baja_op':>12} {'Det_riesgo':>9}"
            f" | {'Prec_baja_op':>12} {'Prec_riesgo':>10}"
        )
        lines.append(
            f"  {'TRAIN (n='+str(tr['n'])+')':>18}"
            f" {tr['mae_selector_real']:>9.4f}"
            f" {tr['mae_e1']:>9.4f}"
            f" {tr['mae_e9']:>9.4f}"
            f" {tr['mae_e1_rolling']:>9.4f}"
            f" {tr['mae_e9_rolling']:>9.4f}"
            f" | {tr['direccion_accuracy']:>8.1%}"
            f" {tr['coverage_direccion']:>6.1%}"
            f" | {tr['deteccion_baja_estricta']:>9.1%}"
            f" {tr['deteccion_baja_operativa']:>12.1%}"
            f" {tr['deteccion_riesgo']:>9.1%}"
            f" | {tr['precision_baja_operativa']:>12.1%}"
            f" {tr['precision_riesgo']:>10.1%}"
        )
        lines.append(
            f"  {'OOS (n='+str(oo['n'])+')':>18}"
            f" {oo['mae_selector_real']:>9.4f}"
            f" {oo['mae_e1']:>9.4f}"
            f" {oo['mae_e9']:>9.4f}"
            f" {oo['mae_e1_rolling']:>9.4f}"
            f" {oo['mae_e9_rolling']:>9.4f}"
            f" | {oo['direccion_accuracy']:>8.1%}"
            f" {oo['coverage_direccion']:>6.1%}"
            f" | {oo['deteccion_baja_estricta']:>9.1%}"
            f" {oo['deteccion_baja_operativa']:>12.1%}"
            f" {oo['deteccion_riesgo']:>9.1%}"
            f" | {oo['precision_baja_operativa']:>12.1%}"
            f" {oo['precision_riesgo']:>10.1%}"
        )

        # Detalle de categorías
        lines.append("")
        lines.append(
            f"  Categorías OOS: baja={oo['n_bajas_estrictas']}, baja_prev={oo['n_bajas_preventivas']}, "
            f"incierto={oo['n_inciertos']}, sube={oo['n_subes']}"
        )
        lines.append(
            f"  Caídas reales: {oo['caidas_reales']}, Alertas riesgo: {oo['n_alertas_riesgo']}, "
            f"Falsas alertas: {oo['falsas_alertas_riesgo']}"
        )

        table = data["table_oos"]
        lines.append("")
        lines.append(
            f"  {'fecha':>12} {'y_curr':>7} {'y_true':>7}"
            f" | {'y_cons':>7} {'err':>7} {'mae_esp':>7}"
            f" | {'dir_pred':>16} {'dir_real':>8} {'ok':>5}"
            f" | {'riesgo':>6} {'conf':>14}"
        )
        lines.append(f"  {'-'*100}")
        for _, r in table.iterrows():
            fecha = r["fecha"].strftime("%Y-%m-%d")
            ok = "OK" if r["direccion_correcta"] else "FALLO"
            lines.append(
                f"  {fecha:>12} {r['y_current']:>7.4f} {r['y_true']:>7.4f}"
                f" | {r['y_pred_consolidado']:>7.4f} {r['error_consolidado']:>+7.4f} {r['mae_esperado']:>7.4f}"
                f" | {r['direccion_predicha']:>16} {r['direccion_real']:>8} {ok:>5}"
                f" | {r['riesgo_caida']:>6} {r['confianza']:>14}"
            )
        lines.append("")

    return "\n".join(lines)