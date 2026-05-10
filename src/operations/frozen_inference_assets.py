from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pandas as pd
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .config import OPERATIONS_ARTIFACTS_ROOT
from .frozen_profiles import (
    E9_CURATED_TABLE_PATH,
    NUMERIC_PRIMARY_RUN_ID,
    RISK_PRIMARY_RUN_ID,
    RISK_SUPPORT_RUN_IDS,
    FrozenRunProfile,
    VALIDATED_HISTORY_LAST_START,
    load_frozen_profile,
)
from ..modeling.core.config import CURRENT_TARGET_COLUMN, DATE_COLUMN, TARGET_COLUMNS
from ..modeling.core.data_master import get_base_feature_columns, load_master_dataset
from ..modeling.core.feature_engineering import build_model_frame
from ..modeling.runners.run_e1_ridge_clean import build_estimator as build_e1_estimator
from ..modeling.runners.run_e2_huber_clean import build_estimator as build_e2_estimator
from ..modeling.runners.run_e3_random_forest import build_estimator as build_e3_estimator
from ..modeling.runners.run_e5_catboost import build_estimator as build_e5_estimator
from ..modeling.runners.run_e7_prophet import build_estimator as build_e7_estimator


FROZEN_INFERENCE_ROOT = OPERATIONS_ARTIFACTS_ROOT / "frozen_inference_profiles"
BASE_PREDICT_ONLY_RUN_IDS = (
    NUMERIC_PRIMARY_RUN_ID,
    *RISK_SUPPORT_RUN_IDS,
)
STACKING_PREDICT_ONLY_RUN_IDS = (RISK_PRIMARY_RUN_ID,)
SUPPORTED_PREDICT_ONLY_RUN_IDS = (
    *BASE_PREDICT_ONLY_RUN_IDS,
    *STACKING_PREDICT_ONLY_RUN_IDS,
)

PACKAGE_KIND_BASE_MODEL = "base_model"
PACKAGE_KIND_STACKING_META_MODEL = "stacking_meta_model"
PREDICT_ONLY_PACKAGE_FORMAT = "predict_only_v2"

E9_CANDIDATES_BY_HORIZON: dict[int, tuple[str, ...]] = {
    1: ("E1_v5_clean", "E5_v4_clean", "E3_v2_clean", "E2_v3_clean"),
    2: ("E1_v5_clean", "E5_v4_clean", "E2_v3_clean", "E7_v3_clean"),
    3: ("E1_v5_clean", "E5_v4_clean", "E3_v2_clean", "E7_v3_clean"),
    4: ("E1_v5_clean", "E5_v4_clean", "E3_v2_clean", "E2_v3_clean"),
}
E9_NON_FEATURE_COLUMNS = {
    "fecha",
    "y_true",
    "n_modelos_disponibles",
    "fila_completa",
    "cobertura_modelos_fila",
}
STACKING_DEPENDENCIES_BY_RUN_ID = {
    RISK_PRIMARY_RUN_ID: (NUMERIC_PRIMARY_RUN_ID, *RISK_SUPPORT_RUN_IDS),
}
ALWAYS_INCLUDE_COLUMNS_BY_RUN_ID = {
    "E7_v3_clean": (DATE_COLUMN,),
}


class FrozenInferenceAssetError(RuntimeError):
    """Base para errores de bootstrap/carga de inferencia congelada."""


class FrozenInferenceAssetMissingError(FrozenInferenceAssetError):
    """Señala que no existe todavía un paquete predict-only para el perfil pedido."""


class FrozenInferenceAssetContractError(FrozenInferenceAssetError):
    """Señala que el contrato congelado no se puede satisfacer con el dataset actual."""


@dataclass(frozen=True)
class FrozenHorizonAsset:
    horizon: int
    selected_features: tuple[str, ...]
    target_column: str
    training_rows: int
    training_start_date: str
    training_end_date: str
    terminal_fold_reference_date: str
    model_path: Path
    spec_path: Path
    estimator_kind: str
    model_params: dict[str, Any]
    always_include_columns: tuple[str, ...] = ()

    @property
    def input_columns(self) -> tuple[str, ...]:
        return (*self.always_include_columns, *self.selected_features)


@dataclass(frozen=True)
class FrozenInferenceAsset:
    run_id: str
    package_root: Path
    manifest_path: Path
    canonical_run_dir: Path
    dataset_cutoff_week: str
    dataset_cutoff_start: str
    target_mode: str
    feature_mode: str
    transform_mode: str
    lags: tuple[int, ...]
    horizons: tuple[int, ...]
    package_kind: str
    input_contract_columns: tuple[str, ...]
    dependencies: tuple[str, ...]
    horizon_assets: dict[int, FrozenHorizonAsset]

    @property
    def base_feature_columns(self) -> tuple[str, ...]:
        return self.input_contract_columns


def _package_root(run_id: str) -> Path:
    return FROZEN_INFERENCE_ROOT / run_id


def _manifest_path(run_id: str) -> Path:
    return _package_root(run_id) / "manifest.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _union_preserving_order(*values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for block in values:
        for item in block:
            if item in seen:
                continue
            seen.add(item)
            ordered.append(item)
    return tuple(ordered)


def _split_selected_features(raw_value: Any) -> tuple[str, ...]:
    return tuple(
        item.strip()
        for item in str(raw_value).split(",")
        if item and item.strip()
    )


def _resolve_target_cutoff_dataset(df: pd.DataFrame) -> pd.DataFrame:
    cutoff = pd.Timestamp(VALIDATED_HISTORY_LAST_START)
    working = df.copy()
    working[DATE_COLUMN] = pd.to_datetime(working[DATE_COLUMN])
    working = working.loc[working[DATE_COLUMN] <= cutoff].copy()
    for horizon, target_column in TARGET_COLUMNS.items():
        last_known_base_date = cutoff - pd.Timedelta(days=7 * horizon)
        working.loc[working[DATE_COLUMN] > last_known_base_date, target_column] = pd.NA
    return working.sort_values(DATE_COLUMN, kind="stable").reset_index(drop=True)


def _terminal_predictions_path(profile: FrozenRunProfile, horizon: int) -> Path:
    return profile.canonical_run_dir / f"predicciones_h{horizon}.csv"


def _load_terminal_row(profile: FrozenRunProfile, horizon: int) -> pd.Series:
    predictions_path = _terminal_predictions_path(profile, horizon)
    if not predictions_path.exists():
        raise FrozenInferenceAssetMissingError(
            f"Falta {predictions_path.name} en {profile.canonical_run_dir} para derivar el paquete predict-only."
        )
    predictions = pd.read_csv(predictions_path)
    if predictions.empty:
        raise FrozenInferenceAssetMissingError(
            f"{predictions_path.name} está vacío; no se puede congelar un perfil de inferencia."
        )
    return predictions.iloc[-1]


def _profile_args_e1(profile: FrozenRunProfile) -> SimpleNamespace:
    model_params = profile.parameters["model_params"]
    return SimpleNamespace(
        transform_mode=str(profile.parameters["transform_mode"]),
        winsor_lower_quantile=float(model_params["winsor_lower_quantile"]),
        winsor_upper_quantile=float(model_params["winsor_upper_quantile"]),
    )


def _profile_args_e2(profile: FrozenRunProfile) -> SimpleNamespace:
    model_params = profile.parameters["model_params"]
    return SimpleNamespace(
        transform_mode=str(model_params["transform_mode"]),
        winsor_lower_quantile=float(model_params["winsor_lower_quantile"]),
        winsor_upper_quantile=float(model_params["winsor_upper_quantile"]),
    )


def _profile_args_e3(profile: FrozenRunProfile) -> SimpleNamespace:
    model_params = profile.parameters["model_params"]
    return SimpleNamespace(
        tree_model=str(model_params["tree_model"]),
        n_estimators=int(model_params["n_estimators"]),
        max_depth=None if model_params["max_depth"] is None else int(model_params["max_depth"]),
        min_samples_leaf=int(model_params["min_samples_leaf"]),
        min_samples_split=int(model_params["min_samples_split"]),
        max_features=model_params["max_features"],
        bootstrap=bool(model_params["bootstrap"]),
        random_state=int(model_params["random_state"]),
    )


def _profile_args_e5(profile: FrozenRunProfile) -> SimpleNamespace:
    model_params = profile.parameters["model_params"]
    return SimpleNamespace(
        iterations=int(model_params["iterations"]),
        depth=int(model_params["depth"]),
        learning_rate=float(model_params["learning_rate"]),
        l2_leaf_reg=float(model_params["l2_leaf_reg"]),
        subsample=float(model_params["subsample"]),
        loss_function=str(model_params["loss_function"]),
        random_seed=int(model_params["random_seed"]),
    )


def _profile_args_e7(profile: FrozenRunProfile) -> SimpleNamespace:
    model_params = profile.parameters["model_params"]
    return SimpleNamespace(
        changepoint_prior_scale=float(model_params["changepoint_prior_scale"]),
        seasonality_mode=str(model_params["seasonality_mode"]),
        weekly_seasonality=bool(model_params["weekly_seasonality"]),
        yearly_seasonality=bool(model_params["yearly_seasonality"]),
        daily_seasonality=bool(model_params["daily_seasonality"]),
    )


def _build_base_terminal_specs(profile: FrozenRunProfile) -> dict[int, dict[str, Any]]:
    specs: dict[int, dict[str, Any]] = {}
    for horizon in profile.horizons:
        terminal = _load_terminal_row(profile, horizon)
        selected_features = _split_selected_features(terminal["selected_features"])
        if not selected_features:
            raise FrozenInferenceAssetContractError(
                f"No se pudieron resolver selected_features terminales para {profile.run_id} H{horizon}."
            )
        model_params: dict[str, Any]
        estimator_kind: str
        if profile.run_id == "E1_v5_clean":
            model_params = {"best_alpha": float(terminal["best_alpha"])}
            estimator_kind = "ridge_with_winsor_transform"
        elif profile.run_id == "E2_v3_clean":
            model_params = {
                "epsilon": float(terminal["best_epsilon"]),
                "alpha": float(terminal["best_alpha"]),
                "max_iter": int(terminal["best_max_iter"]),
                "tol": float(terminal["best_tol"]),
            }
            estimator_kind = "huber_with_winsor_transform"
        elif profile.run_id == "E3_v2_clean":
            model_params = {}
            estimator_kind = str(profile.parameters["model_params"]["tree_model"])
        elif profile.run_id == "E5_v4_clean":
            model_params = {
                "iterations": int(terminal["best_iterations"]),
                "depth": int(terminal["best_depth"]),
                "l2_leaf_reg": float(terminal["best_l2_leaf_reg"]),
            }
            estimator_kind = "catboost_regressor"
        elif profile.run_id == "E7_v3_clean":
            model_params = {}
            estimator_kind = "prophet_exogenous_regressor"
        else:
            raise FrozenInferenceAssetMissingError(
                f"No existe extractor de especificaciones terminales para {profile.run_id}."
            )
        specs[horizon] = {
            "selected_features": selected_features,
            "model_params": model_params,
            "estimator_kind": estimator_kind,
            "always_include_columns": ALWAYS_INCLUDE_COLUMNS_BY_RUN_ID.get(profile.run_id, ()),
            "terminal_fold_reference_date": str(terminal[DATE_COLUMN]),
        }
    return specs


def _build_e9_terminal_specs(profile: FrozenRunProfile) -> dict[int, dict[str, Any]]:
    specs: dict[int, dict[str, Any]] = {}
    for horizon in profile.horizons:
        terminal = _load_terminal_row(profile, horizon)
        meta_model = str(terminal["meta_model"]).strip().lower()
        if meta_model not in {"huber", "ridge"}:
            raise FrozenInferenceAssetContractError(
                f"E9 H{horizon} usa meta_model no soportado en predict-only: {meta_model}"
            )
        model_params: dict[str, Any] = {"meta_model": meta_model}
        if meta_model == "ridge":
            if "best_alpha" not in terminal.index or pd.isna(terminal["best_alpha"]):
                raise FrozenInferenceAssetContractError(
                    f"E9 H{horizon} requiere best_alpha congelado para meta-modelo ridge y no está disponible."
                )
            model_params["best_alpha"] = float(terminal["best_alpha"])
        specs[horizon] = {
            "selected_features": E9_CANDIDATES_BY_HORIZON[int(horizon)],
            "model_params": model_params,
            "estimator_kind": f"stacking_{meta_model}",
            "always_include_columns": (),
            "terminal_fold_reference_date": str(terminal[DATE_COLUMN]),
        }
    return specs


def _profile_args_for_run(profile: FrozenRunProfile) -> SimpleNamespace | None:
    if profile.run_id == "E1_v5_clean":
        return _profile_args_e1(profile)
    if profile.run_id == "E2_v3_clean":
        return _profile_args_e2(profile)
    if profile.run_id == "E3_v2_clean":
        return _profile_args_e3(profile)
    if profile.run_id == "E5_v4_clean":
        return _profile_args_e5(profile)
    if profile.run_id == "E7_v3_clean":
        return _profile_args_e7(profile)
    return None


def _build_base_estimator(
    *,
    profile: FrozenRunProfile,
    args: SimpleNamespace,
    terminal_spec: dict[str, Any],
) -> Any:
    model_params = terminal_spec["model_params"]
    if profile.run_id == "E1_v5_clean":
        return build_e1_estimator(float(model_params["best_alpha"]), args)
    if profile.run_id == "E2_v3_clean":
        return build_e2_estimator(
            {
                "epsilon": float(model_params["epsilon"]),
                "alpha": float(model_params["alpha"]),
                "max_iter": int(model_params["max_iter"]),
                "tol": float(model_params["tol"]),
            },
            args,
        )
    if profile.run_id == "E3_v2_clean":
        return build_e3_estimator(args)
    if profile.run_id == "E5_v4_clean":
        return build_e5_estimator(args, overrides=model_params)
    if profile.run_id == "E7_v3_clean":
        return build_e7_estimator(args)
    raise FrozenInferenceAssetMissingError(
        f"No existe constructor de estimador predict-only para {profile.run_id}."
    )


def _build_e9_estimator(terminal_spec: dict[str, Any]) -> Pipeline:
    meta_model = str(terminal_spec["model_params"]["meta_model"])
    if meta_model == "ridge":
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("model", Ridge(alpha=float(terminal_spec["model_params"]["best_alpha"]))),
            ]
        )
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", HuberRegressor()),
        ]
    )


def _load_e9_curated_training_frame(
    *,
    table_path: Path,
    master_df: pd.DataFrame,
    horizon: int,
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    sheet_name = f"E9_base_h{horizon}"
    sheet_df = pd.read_excel(table_path, sheet_name=sheet_name)
    required_columns = {"fecha", "y_true", "fila_completa", "n_modelos_disponibles", "cobertura_modelos_fila"}
    missing_required = sorted(required_columns.difference(sheet_df.columns))
    if missing_required:
        raise FrozenInferenceAssetContractError(
            f"Faltan columnas requeridas en {sheet_name}: {missing_required}"
        )

    feature_columns = E9_CANDIDATES_BY_HORIZON[int(horizon)]
    missing_features = [column for column in feature_columns if column not in sheet_df.columns]
    if missing_features:
        raise FrozenInferenceAssetContractError(
            f"Faltan columnas de candidatos aprobados en {sheet_name}: {missing_features}"
        )

    extra_model_columns = [
        column for column in sheet_df.columns if column not in E9_NON_FEATURE_COLUMNS and column not in feature_columns
    ]
    if extra_model_columns:
        raise FrozenInferenceAssetContractError(
            f"La hoja {sheet_name} contiene columnas extra no aprobadas: {extra_model_columns}"
        )

    working_df = sheet_df.copy()
    working_df["fecha"] = pd.to_datetime(working_df["fecha"])
    working_df = working_df.loc[working_df["fila_completa"].astype(bool)].copy()
    working_df = working_df.loc[working_df["fecha"] <= pd.Timestamp(VALIDATED_HISTORY_LAST_START)].copy()

    merge_columns = [DATE_COLUMN, CURRENT_TARGET_COLUMN, TARGET_COLUMNS[horizon]]
    merged = working_df.merge(
        master_df[merge_columns],
        left_on="fecha",
        right_on=DATE_COLUMN,
        how="left",
        validate="one_to_one",
    )
    if merged[CURRENT_TARGET_COLUMN].isna().any():
        missing_dates = merged.loc[merged[CURRENT_TARGET_COLUMN].isna(), "fecha"].dt.strftime("%Y-%m-%d").tolist()
        raise FrozenInferenceAssetContractError(
            f"No se pudo reconstruir y_current para {sheet_name}. Fechas faltantes: {missing_dates}"
        )

    max_target_diff = float((merged["y_true"] - merged[TARGET_COLUMNS[horizon]]).abs().max())
    if max_target_diff > 1e-9:
        raise FrozenInferenceAssetContractError(
            f"Inconsistencia técnica en {sheet_name}: y_true no coincide con {TARGET_COLUMNS[horizon]} "
            f"(max_diff={max_target_diff})."
        )

    merged["y_current"] = merged[CURRENT_TARGET_COLUMN].astype(float)
    merged["y_true"] = merged["y_true"].astype(float)
    for column in feature_columns:
        merged[column] = merged[column].astype(float)
    merged = merged.sort_values(DATE_COLUMN, kind="stable").reset_index(drop=True)
    if merged.empty:
        raise FrozenInferenceAssetContractError(
            f"No quedaron filas históricas completas en {sheet_name} al cortar en {VALIDATED_HISTORY_LAST_START}."
        )
    return merged, feature_columns


def _serialize_horizon_asset(
    *,
    horizons_dir: Path,
    horizon: int,
    estimator: Any,
    selected_features: tuple[str, ...],
    always_include_columns: tuple[str, ...],
    target_column: str,
    training_rows: int,
    training_start_date: str,
    training_end_date: str,
    terminal_fold_reference_date: str,
    estimator_kind: str,
    model_params: dict[str, Any],
) -> FrozenHorizonAsset:
    model_path = horizons_dir / f"model_h{horizon}.pkl"
    with model_path.open("wb") as handle:
        pickle.dump(estimator, handle)

    spec_path = horizons_dir / f"spec_h{horizon}.json"
    spec_payload = {
        "horizon": int(horizon),
        "selected_features": list(selected_features),
        "always_include_columns": list(always_include_columns),
        "target_column": target_column,
        "training_rows": int(training_rows),
        "training_start_date": training_start_date,
        "training_end_date": training_end_date,
        "terminal_fold_reference_date": terminal_fold_reference_date,
        "estimator_kind": estimator_kind,
        "model_params": model_params,
        "model_path": str(model_path),
    }
    _write_json(spec_path, spec_payload)

    return FrozenHorizonAsset(
        horizon=int(horizon),
        selected_features=selected_features,
        target_column=target_column,
        training_rows=int(training_rows),
        training_start_date=training_start_date,
        training_end_date=training_end_date,
        terminal_fold_reference_date=terminal_fold_reference_date,
        model_path=model_path,
        spec_path=spec_path,
        estimator_kind=estimator_kind,
        model_params=model_params,
        always_include_columns=always_include_columns,
    )


def _bootstrap_base_predict_only_asset(
    profile: FrozenRunProfile,
    *,
    dataset_path: Path | None = None,
) -> FrozenInferenceAsset:
    dataset = load_master_dataset(dataset_path=dataset_path) if dataset_path else load_master_dataset()
    historical_df = _resolve_target_cutoff_dataset(dataset)
    base_feature_columns = tuple(get_base_feature_columns(historical_df))
    missing_base = sorted(set(profile.parameters["feature_columns"]).difference(base_feature_columns))
    if missing_base:
        raise FrozenInferenceAssetContractError(
            f"Faltan columnas base requeridas para {profile.run_id}: {missing_base}"
        )

    terminal_specs = _build_base_terminal_specs(profile)
    args = _profile_args_for_run(profile)
    if args is None:
        raise FrozenInferenceAssetMissingError(
            f"{profile.run_id} no tiene bootstrap predict-only soportado."
        )

    package_root = _package_root(profile.run_id)
    package_root.mkdir(parents=True, exist_ok=True)
    horizons_dir = package_root / "horizons"
    horizons_dir.mkdir(parents=True, exist_ok=True)

    horizon_assets: dict[int, FrozenHorizonAsset] = {}
    for horizon in profile.horizons:
        modeling_df, _, target_column = build_model_frame(
            df=historical_df,
            horizon=horizon,
            feature_columns=list(base_feature_columns),
            lags=profile.lags,
            target_mode=profile.parameters["target_mode"],
        )
        terminal_spec = terminal_specs[horizon]
        selected_features = terminal_spec["selected_features"]
        required_columns = _union_preserving_order(
            terminal_spec["always_include_columns"],
            selected_features,
        )
        missing_selected = sorted(set(required_columns).difference(modeling_df.columns))
        if missing_selected:
            raise FrozenInferenceAssetContractError(
                f"El contrato congelado H{horizon} para {profile.run_id} pide columnas inexistentes: {missing_selected}"
            )

        estimator = _build_base_estimator(
            profile=profile,
            args=args,
            terminal_spec=terminal_spec,
        )
        estimator.fit(modeling_df[list(required_columns)], modeling_df[target_column])

        horizon_assets[horizon] = _serialize_horizon_asset(
            horizons_dir=horizons_dir,
            horizon=horizon,
            estimator=estimator,
            selected_features=selected_features,
            always_include_columns=terminal_spec["always_include_columns"],
            target_column=target_column,
            training_rows=len(modeling_df),
            training_start_date=pd.Timestamp(modeling_df[DATE_COLUMN].min()).date().isoformat(),
            training_end_date=pd.Timestamp(modeling_df[DATE_COLUMN].max()).date().isoformat(),
            terminal_fold_reference_date=terminal_spec["terminal_fold_reference_date"],
            estimator_kind=terminal_spec["estimator_kind"],
            model_params=terminal_spec["model_params"],
        )

    manifest_payload = {
        "run_id": profile.run_id,
        "package_format": PREDICT_ONLY_PACKAGE_FORMAT,
        "package_kind": PACKAGE_KIND_BASE_MODEL,
        "canonical_run_dir": str(profile.canonical_run_dir),
        "canonical_metadata_path": str(profile.metadata_path),
        "canonical_parameters_path": str(profile.parameters_path),
        "dataset_cutoff_week": "2026-W10",
        "dataset_cutoff_start": VALIDATED_HISTORY_LAST_START.isoformat(),
        "target_mode": str(profile.parameters["target_mode"]),
        "feature_mode": str(profile.parameters["feature_mode"]),
        "transform_mode": str(profile.parameters["transform_mode"]),
        "lags": list(profile.lags),
        "horizons": list(profile.horizons),
        "input_contract_columns": list(base_feature_columns),
        "base_feature_columns": list(base_feature_columns),
        "dependencies": [],
        "horizons_manifest": {
            str(horizon): {
                "spec_path": str(asset.spec_path),
                "model_path": str(asset.model_path),
            }
            for horizon, asset in horizon_assets.items()
        },
    }
    _write_json(_manifest_path(profile.run_id), manifest_payload)
    return load_predict_only_asset(profile.run_id)


def _bootstrap_e9_predict_only_asset(
    profile: FrozenRunProfile,
    *,
    dataset_path: Path | None = None,
) -> FrozenInferenceAsset:
    dataset = load_master_dataset(dataset_path=dataset_path) if dataset_path else load_master_dataset()
    historical_df = _resolve_target_cutoff_dataset(dataset)
    dependencies = STACKING_DEPENDENCIES_BY_RUN_ID.get(profile.run_id, ())
    for dependency_run_id in dependencies:
        manifest_path = _manifest_path(dependency_run_id)
        if not manifest_path.exists():
            bootstrap_predict_only_asset(dependency_run_id, dataset_path=dataset_path)

    terminal_specs = _build_e9_terminal_specs(profile)
    package_root = _package_root(profile.run_id)
    package_root.mkdir(parents=True, exist_ok=True)
    horizons_dir = package_root / "horizons"
    horizons_dir.mkdir(parents=True, exist_ok=True)

    horizon_assets: dict[int, FrozenHorizonAsset] = {}
    for horizon in profile.horizons:
        modeling_df, feature_columns = _load_e9_curated_training_frame(
            table_path=E9_CURATED_TABLE_PATH,
            master_df=historical_df,
            horizon=horizon,
        )
        terminal_spec = terminal_specs[horizon]
        selected_features = terminal_spec["selected_features"]
        if tuple(feature_columns) != selected_features:
            raise FrozenInferenceAssetContractError(
                f"El contrato E9 H{horizon} difiere entre tabla curada y especificación terminal."
            )

        estimator = _build_e9_estimator(terminal_spec)
        estimator.fit(modeling_df[list(selected_features)], modeling_df["y_true"])

        horizon_assets[horizon] = _serialize_horizon_asset(
            horizons_dir=horizons_dir,
            horizon=horizon,
            estimator=estimator,
            selected_features=selected_features,
            always_include_columns=(),
            target_column="y_true",
            training_rows=len(modeling_df),
            training_start_date=pd.Timestamp(modeling_df[DATE_COLUMN].min()).date().isoformat(),
            training_end_date=pd.Timestamp(modeling_df[DATE_COLUMN].max()).date().isoformat(),
            terminal_fold_reference_date=terminal_spec["terminal_fold_reference_date"],
            estimator_kind=terminal_spec["estimator_kind"],
            model_params=terminal_spec["model_params"],
        )

    manifest_payload = {
        "run_id": profile.run_id,
        "package_format": PREDICT_ONLY_PACKAGE_FORMAT,
        "package_kind": PACKAGE_KIND_STACKING_META_MODEL,
        "canonical_run_dir": str(profile.canonical_run_dir),
        "canonical_metadata_path": str(profile.metadata_path),
        "canonical_parameters_path": str(profile.parameters_path),
        "dataset_cutoff_week": "2026-W10",
        "dataset_cutoff_start": VALIDATED_HISTORY_LAST_START.isoformat(),
        "target_mode": str(profile.parameters.get("target_mode", "nivel")),
        "feature_mode": str(profile.parameters.get("feature_mode", "stacking_curado")),
        "transform_mode": str(profile.parameters.get("transform_mode", "")),
        "lags": list(profile.lags),
        "horizons": list(profile.horizons),
        "input_contract_columns": list(dependencies),
        "base_feature_columns": list(dependencies),
        "dependencies": list(dependencies),
        "curated_table_path": str(E9_CURATED_TABLE_PATH),
        "horizons_manifest": {
            str(horizon): {
                "spec_path": str(asset.spec_path),
                "model_path": str(asset.model_path),
            }
            for horizon, asset in horizon_assets.items()
        },
    }
    _write_json(_manifest_path(profile.run_id), manifest_payload)
    return load_predict_only_asset(profile.run_id)


def bootstrap_predict_only_asset(
    run_id: str,
    *,
    dataset_path: Path | None = None,
) -> FrozenInferenceAsset:
    if run_id not in SUPPORTED_PREDICT_ONLY_RUN_IDS:
        raise FrozenInferenceAssetMissingError(
            f"{run_id} todavía no tiene bootstrap predict-only soportado."
        )

    profile = load_frozen_profile(run_id)
    if run_id in BASE_PREDICT_ONLY_RUN_IDS:
        return _bootstrap_base_predict_only_asset(profile, dataset_path=dataset_path)
    if run_id in STACKING_PREDICT_ONLY_RUN_IDS:
        return _bootstrap_e9_predict_only_asset(profile, dataset_path=dataset_path)
    raise FrozenInferenceAssetMissingError(
        f"{run_id} todavía no tiene bootstrap predict-only soportado."
    )


def load_predict_only_asset(run_id: str) -> FrozenInferenceAsset:
    manifest_path = _manifest_path(run_id)
    if not manifest_path.exists():
        raise FrozenInferenceAssetMissingError(
            f"No existe paquete predict-only para {run_id} en {manifest_path.parent}."
        )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    horizon_assets: dict[int, FrozenHorizonAsset] = {}
    for horizon_text, pointers in payload["horizons_manifest"].items():
        spec_path = Path(pointers["spec_path"])
        spec_payload = json.loads(spec_path.read_text(encoding="utf-8"))
        horizon = int(horizon_text)
        horizon_assets[horizon] = FrozenHorizonAsset(
            horizon=horizon,
            selected_features=tuple(str(value) for value in spec_payload["selected_features"]),
            target_column=str(spec_payload["target_column"]),
            training_rows=int(spec_payload["training_rows"]),
            training_start_date=str(spec_payload["training_start_date"]),
            training_end_date=str(spec_payload["training_end_date"]),
            terminal_fold_reference_date=str(spec_payload["terminal_fold_reference_date"]),
            model_path=Path(spec_payload["model_path"]),
            spec_path=spec_path,
            estimator_kind=str(spec_payload.get("estimator_kind", "")),
            model_params=dict(spec_payload.get("model_params", {})),
            always_include_columns=tuple(str(value) for value in spec_payload.get("always_include_columns", [])),
        )

    input_contract_raw = payload.get("input_contract_columns", payload.get("base_feature_columns", []))
    return FrozenInferenceAsset(
        run_id=str(payload["run_id"]),
        package_root=manifest_path.parent,
        manifest_path=manifest_path,
        canonical_run_dir=Path(payload["canonical_run_dir"]),
        dataset_cutoff_week=str(payload["dataset_cutoff_week"]),
        dataset_cutoff_start=str(payload["dataset_cutoff_start"]),
        target_mode=str(payload["target_mode"]),
        feature_mode=str(payload["feature_mode"]),
        transform_mode=str(payload["transform_mode"]),
        lags=tuple(int(value) for value in payload["lags"]),
        horizons=tuple(int(value) for value in payload["horizons"]),
        package_kind=str(payload.get("package_kind", PACKAGE_KIND_BASE_MODEL)),
        input_contract_columns=tuple(str(value) for value in input_contract_raw),
        dependencies=tuple(str(value) for value in payload.get("dependencies", [])),
        horizon_assets=horizon_assets,
    )


def load_serialized_model(path: Path) -> Any:
    with path.open("rb") as handle:
        return pickle.load(handle)


def predict_only_asset_status(run_id: str) -> dict[str, str]:
    try:
        asset = load_predict_only_asset(run_id)
    except FrozenInferenceAssetMissingError as exc:
        return {"status": "missing", "reason": str(exc)}
    if run_id not in SUPPORTED_PREDICT_ONLY_RUN_IDS:
        return {
            "status": "unsupported",
            "reason": f"{run_id} no tiene soporte predict-only implementado en esta capa.",
        }
    return {
        "status": "ready",
        "manifest_path": str(asset.manifest_path),
        "package_root": str(asset.package_root),
        "package_kind": asset.package_kind,
    }
