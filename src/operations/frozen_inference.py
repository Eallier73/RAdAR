from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .frozen_inference_assets import (
    PACKAGE_KIND_BASE_MODEL,
    PACKAGE_KIND_STACKING_META_MODEL,
    FrozenInferenceAsset,
    FrozenInferenceAssetContractError,
    FrozenInferenceAssetMissingError,
    load_predict_only_asset,
    load_serialized_model,
)
from .frozen_profiles import DEFAULT_OPERATION_DATASET, FrozenRunProfile, load_frozen_profile
from ..modeling.core.config import CURRENT_TARGET_COLUMN, DATE_COLUMN, TARGET_COLUMNS, TARGET_MODE_DELTA
from ..modeling.core.data_master import load_master_dataset
from ..modeling.core.feature_engineering import build_lagged_dataset


PRIMARY_PENDING_SOURCE = "predict_only_frozen_model"
STACKING_PENDING_SOURCE = "predict_only_frozen_stacking_model"


class PredictOnlyNotReadyError(RuntimeError):
    """La capa predict-only no tiene todavía soporte operativo suficiente."""


@dataclass(frozen=True)
class PendingForecastBundle:
    run_id: str
    horizon_frames: dict[int, pd.DataFrame]
    asset_manifest_path: str
    package_root: str


def _build_candidate_frame(
    *,
    df: pd.DataFrame,
    horizon: int,
    feature_columns: list[str],
    lags: tuple[int, ...],
    target_mode: str,
) -> tuple[pd.DataFrame, str]:
    target_level_column = TARGET_COLUMNS[horizon]
    lagged = build_lagged_dataset(df=df, feature_columns=feature_columns, lags=lags)

    if target_mode == TARGET_MODE_DELTA:
        target_column = f"{target_level_column}_delta"
        lagged[target_column] = lagged[target_level_column] - lagged[CURRENT_TARGET_COLUMN]
    else:
        target_column = target_level_column

    lagged_feature_columns = []
    for column in [CURRENT_TARGET_COLUMN, *feature_columns]:
        for lag in lags:
            lagged_feature_columns.append(f"{column}_lag{lag}")

    modeling_columns = [
        DATE_COLUMN,
        CURRENT_TARGET_COLUMN,
        target_level_column,
        *feature_columns,
        *lagged_feature_columns,
    ]
    if target_column not in modeling_columns:
        modeling_columns.append(target_column)

    candidate_df = lagged[modeling_columns].copy()
    required_inputs = [CURRENT_TARGET_COLUMN, *feature_columns, *lagged_feature_columns]
    candidate_df = candidate_df.loc[candidate_df[required_inputs].notna().all(axis=1)].reset_index(drop=True)
    return candidate_df, target_column


def _pending_rows_from_candidate_frame(candidate_df: pd.DataFrame, target_column: str) -> pd.DataFrame:
    return candidate_df.loc[candidate_df[target_column].isna()].copy().reset_index(drop=True)


def validate_inference_schema(
    *,
    asset: FrozenInferenceAsset,
    master_df: pd.DataFrame,
) -> None:
    missing_base = sorted(set(asset.input_contract_columns).difference(master_df.columns))
    if missing_base:
        raise FrozenInferenceAssetContractError(
            f"El dataset maestro actual no cumple el contrato base de {asset.run_id}; faltan {missing_base}."
        )


def _load_base_pending_forecasts_predict_only(
    *,
    profile: FrozenRunProfile,
    asset: FrozenInferenceAsset,
    master_df: pd.DataFrame,
) -> dict[int, pd.DataFrame]:
    pending_by_horizon: dict[int, pd.DataFrame] = {}
    feature_columns = list(asset.input_contract_columns)
    for horizon in asset.horizons:
        horizon_asset = asset.horizon_assets[horizon]
        candidate_df, target_column = _build_candidate_frame(
            df=master_df,
            horizon=horizon,
            feature_columns=feature_columns,
            lags=asset.lags,
            target_mode=asset.target_mode,
        )
        pending_df = _pending_rows_from_candidate_frame(candidate_df, target_column)
        if pending_df.empty:
            pending_by_horizon[horizon] = pending_df
            continue

        required_columns = list(horizon_asset.input_columns)
        missing_selected = sorted(set(required_columns).difference(pending_df.columns))
        if missing_selected:
            raise FrozenInferenceAssetContractError(
                f"El contrato congelado H{horizon} para {profile.run_id} no se puede satisfacer; faltan {missing_selected}."
            )

        estimator = load_serialized_model(horizon_asset.model_path)
        input_frame = pending_df[required_columns]
        predictions = estimator.predict(input_frame)
        pending_by_horizon[horizon] = pd.DataFrame(
            {
                DATE_COLUMN: pd.to_datetime(pending_df[DATE_COLUMN]),
                "y_current": pending_df[CURRENT_TARGET_COLUMN].astype(float),
                "y_true": np.nan,
                "y_pred": np.asarray(predictions, dtype=float),
                "y_true_model": np.nan,
                "y_pred_model": np.asarray(predictions, dtype=float),
                "prediction_source": PRIMARY_PENDING_SOURCE,
                "horizonte_sem": int(horizon),
                "run_id": profile.run_id,
                "asset_manifest_path": str(asset.manifest_path),
            }
        )
    return pending_by_horizon


def generate_pending_forecasts_for_profile(
    profile: FrozenRunProfile,
    *,
    dataset_path: Path = DEFAULT_OPERATION_DATASET,
    df_master: pd.DataFrame | None = None,
) -> PendingForecastBundle:
    try:
        asset = load_predict_only_asset(profile.run_id)
    except FrozenInferenceAssetMissingError as exc:
        raise PredictOnlyNotReadyError(str(exc)) from exc

    if asset.package_kind != PACKAGE_KIND_BASE_MODEL:
        raise PredictOnlyNotReadyError(
            f"{profile.run_id} no expone un paquete predict-only de tipo base_model."
        )

    master_df = df_master if df_master is not None else load_master_dataset(dataset_path=dataset_path)
    validate_inference_schema(asset=asset, master_df=master_df)
    horizon_frames = _load_base_pending_forecasts_predict_only(
        profile=profile,
        asset=asset,
        master_df=master_df,
    )
    return PendingForecastBundle(
        run_id=profile.run_id,
        horizon_frames=horizon_frames,
        asset_manifest_path=str(asset.manifest_path),
        package_root=str(asset.package_root),
    )


def _merge_dependency_pending_frames(
    *,
    dependency_frames: dict[str, pd.DataFrame],
    required_run_ids: tuple[str, ...],
) -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    y_current_columns: list[str] = []
    for run_id in required_run_ids:
        frame = dependency_frames.get(run_id)
        if frame is None or frame.empty:
            return pd.DataFrame()
        y_current_column = f"y_current__{run_id}"
        y_current_columns.append(y_current_column)
        contribution = frame[[DATE_COLUMN, "y_current", "y_pred"]].rename(
            columns={
                "y_current": y_current_column,
                "y_pred": run_id,
            }
        )
        if merged is None:
            merged = contribution
        else:
            merged = merged.merge(contribution, on=DATE_COLUMN, how="inner", validate="one_to_one")

    if merged is None or merged.empty:
        return pd.DataFrame()

    reference_column = y_current_columns[0]
    reference_values = merged[reference_column].to_numpy(dtype=float)
    for extra_column in y_current_columns[1:]:
        extra_values = merged[extra_column].to_numpy(dtype=float)
        if not np.allclose(reference_values, extra_values, equal_nan=True):
            raise FrozenInferenceAssetContractError(
                f"Las predicciones base para E9 no comparten el mismo y_current entre dependencias: {required_run_ids}"
            )
    merged["y_current"] = reference_values
    return merged


def generate_pending_forecasts_for_e9(
    profile: FrozenRunProfile,
    *,
    dataset_path: Path = DEFAULT_OPERATION_DATASET,
    df_master: pd.DataFrame | None = None,
) -> PendingForecastBundle:
    try:
        asset = load_predict_only_asset(profile.run_id)
    except FrozenInferenceAssetMissingError as exc:
        raise PredictOnlyNotReadyError(str(exc)) from exc

    if asset.package_kind != PACKAGE_KIND_STACKING_META_MODEL:
        raise PredictOnlyNotReadyError(
            f"{profile.run_id} no expone un paquete predict-only de tipo stacking_meta_model."
        )

    master_df = df_master if df_master is not None else load_master_dataset(dataset_path=dataset_path)

    dependency_bundles: dict[str, PendingForecastBundle] = {}
    for dependency_run_id in asset.dependencies:
        dependency_profile = load_frozen_profile(dependency_run_id)
        dependency_bundles[dependency_run_id] = generate_pending_forecasts_for_profile(
            dependency_profile,
            dataset_path=dataset_path,
            df_master=master_df,
        )

    pending_by_horizon: dict[int, pd.DataFrame] = {}
    for horizon in asset.horizons:
        horizon_asset = asset.horizon_assets[horizon]
        required_run_ids = horizon_asset.selected_features
        dependency_frames = {
            run_id: dependency_bundles[run_id].horizon_frames.get(horizon, pd.DataFrame())
            for run_id in required_run_ids
        }
        merged = _merge_dependency_pending_frames(
            dependency_frames=dependency_frames,
            required_run_ids=required_run_ids,
        )
        if merged.empty:
            pending_by_horizon[horizon] = pd.DataFrame()
            continue

        estimator = load_serialized_model(horizon_asset.model_path)
        predictions = estimator.predict(merged[list(horizon_asset.input_columns)])
        pending_by_horizon[horizon] = pd.DataFrame(
            {
                DATE_COLUMN: pd.to_datetime(merged[DATE_COLUMN]),
                "y_current": merged["y_current"].astype(float),
                "y_true": np.nan,
                "y_pred": np.asarray(predictions, dtype=float),
                "y_true_model": np.nan,
                "y_pred_model": np.asarray(predictions, dtype=float),
                "prediction_source": STACKING_PENDING_SOURCE,
                "horizonte_sem": int(horizon),
                "run_id": profile.run_id,
                "asset_manifest_path": str(asset.manifest_path),
            }
        )

    return PendingForecastBundle(
        run_id=profile.run_id,
        horizon_frames=pending_by_horizon,
        asset_manifest_path=str(asset.manifest_path),
        package_root=str(asset.package_root),
    )
