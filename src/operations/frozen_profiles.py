from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .config import EXPERIMENTS_RUNS_DIR, EXPERIMENTS_WORKBOOK, MODELING_PYTHON, PROCESSED_MODELING_ROOT, ROOT_DIR
from ..nlp.week_resolution import list_preferred_week_files


VALIDATED_HISTORY_LAST_START = date(2026, 3, 2)
VALIDATED_HISTORY_LAST_WEEK = "2026-W10"
CONTROLLED_OPERATION_START = date(2026, 3, 9)
CONTROLLED_OPERATION_START_WEEK = "2026-W11"

DEFAULT_OPERATION_DATASET = PROCESSED_MODELING_ROOT / "datos_ml_master_indice_aceptacion_digital.xlsx"
E9_CURATED_TABLE_PATH = ROOT_DIR / "experiments" / "audit" / "tabla_maestra_experimentos_radar_e9_curada.xlsx"

NUMERIC_PRIMARY_RUN_ID = "E1_v5_clean"
RISK_PRIMARY_RUN_ID = "E9_v2_clean"
RISK_SUPPORT_RUN_IDS = ("E2_v3_clean", "E3_v2_clean", "E5_v4_clean", "E7_v3_clean")
PRIMARY_OPERATION_RUN_IDS = (NUMERIC_PRIMARY_RUN_ID, RISK_PRIMARY_RUN_ID)
ALL_OPERATION_RUN_IDS = (NUMERIC_PRIMARY_RUN_ID, *RISK_SUPPORT_RUN_IDS, RISK_PRIMARY_RUN_ID)

ROLE_NUMERIC_PRIMARY = "numeric_primary"
ROLE_RISK_PRIMARY = "risk_primary"
ROLE_RISK_SUPPORT = "risk_support"

RUN_ROLE_BY_ID = {
    NUMERIC_PRIMARY_RUN_ID: ROLE_NUMERIC_PRIMARY,
    RISK_PRIMARY_RUN_ID: ROLE_RISK_PRIMARY,
    "E2_v3_clean": ROLE_RISK_SUPPORT,
    "E3_v2_clean": ROLE_RISK_SUPPORT,
    "E5_v4_clean": ROLE_RISK_SUPPORT,
    "E7_v3_clean": ROLE_RISK_SUPPORT,
}


@dataclass(frozen=True)
class FrozenRunProfile:
    run_id: str
    role: str
    canonical_run_dir: Path
    metadata_path: Path
    parameters_path: Path
    runner_module: str
    metadata: dict[str, Any]
    parameters: dict[str, Any]

    @property
    def script_name(self) -> str:
        return Path(self.metadata["script_path"]).name

    @property
    def model_name(self) -> str:
        return str(self.metadata.get("model", ""))

    @property
    def family(self) -> str:
        return str(self.metadata.get("family", ""))

    @property
    def horizons(self) -> tuple[int, ...]:
        return tuple(int(value) for value in self.parameters.get("horizons", []))

    @property
    def lags(self) -> tuple[int, ...]:
        return tuple(int(value) for value in self.parameters.get("lags", []))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_latest_canonical_run_dir(run_id: str) -> Path:
    candidates = sorted(EXPERIMENTS_RUNS_DIR.glob(f"{run_id}_*"))
    if not candidates:
        raise FileNotFoundError(f"No se encontró corrida canónica para {run_id} en {EXPERIMENTS_RUNS_DIR}.")
    return candidates[-1]


def load_frozen_profile(run_id: str) -> FrozenRunProfile:
    canonical_run_dir = resolve_latest_canonical_run_dir(run_id)
    metadata_path = canonical_run_dir / "metadata_run.json"
    parameters_path = canonical_run_dir / "parametros_run.json"
    metadata = _load_json(metadata_path)
    parameters = _load_json(parameters_path)
    script_name = Path(metadata["script_path"]).name
    runner_module = f"src.modeling.runners.{script_name.removesuffix('.py')}"
    return FrozenRunProfile(
        run_id=run_id,
        role=RUN_ROLE_BY_ID[run_id],
        canonical_run_dir=canonical_run_dir,
        metadata_path=metadata_path,
        parameters_path=parameters_path,
        runner_module=runner_module,
        metadata=metadata,
        parameters=parameters,
    )


def load_all_operation_profiles() -> dict[str, FrozenRunProfile]:
    return {run_id: load_frozen_profile(run_id) for run_id in ALL_OPERATION_RUN_IDS}


def latest_common_text_week_start() -> date:
    directories = {
        "facebook": ROOT_DIR / "data" / "text" / "radar_weekly_flat" / "facebook_semana_texto",
        "twitter": ROOT_DIR / "data" / "text" / "radar_weekly_flat" / "twitter_semana_texto",
        "youtube": ROOT_DIR / "data" / "text" / "radar_weekly_flat" / "youtube_semana_texto",
        "medios": ROOT_DIR / "data" / "text" / "radar_weekly_flat" / "medios_semana_texto",
    }
    common_periods: set[date] | None = None
    for source, directory in directories.items():
        week_files = list_preferred_week_files(directory, expected_source=source)
        source_weeks = {item.start_date for item in week_files}
        if common_periods is None:
            common_periods = source_weeks
        else:
            common_periods &= source_weeks
    if not common_periods:
        raise ValueError("No se pudo resolver una semana canónica común en data/text/radar_weekly_flat.")
    return max(common_periods)


def iter_week_starts(start: date, end: date) -> list[date]:
    weeks: list[date] = []
    cursor = start
    while cursor <= end:
        weeks.append(cursor)
        cursor = date.fromordinal(cursor.toordinal() + 7)
    return weeks


def week_slug(week_start: date) -> str:
    iso_year, iso_week, _ = week_start.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def comma_join(values: list[Any] | tuple[Any, ...]) -> str:
    return ",".join(str(value) for value in values)


def _bool_flag(true_flag: str, false_flag: str, value: bool) -> list[str]:
    return [true_flag if value else false_flag]


def _logspace_bounds(values: list[float] | tuple[float, ...]) -> tuple[float, float, int]:
    raw = [float(value) for value in values]
    if not raw:
        raise ValueError("No se puede derivar grid logspace desde una secuencia vacía.")
    return math.log10(min(raw)), math.log10(max(raw)), len(raw)


def _common_runner_args(
    profile: FrozenRunProfile,
    *,
    python_executable: str,
    runtime_run_id: str,
    dataset_path: Path,
    workbook_path: Path,
    runs_dir: Path,
) -> list[str]:
    params = profile.parameters
    args = [
        python_executable,
        "-m",
        profile.runner_module,
        "--run-id",
        runtime_run_id,
        "--dataset-path",
        str(dataset_path),
        "--workbook",
        str(workbook_path),
        "--runs-dir",
        str(runs_dir),
    ]
    if "sheet_name" in params:
        args.extend(["--sheet-name", str(params["sheet_name"])])
    if "target_mode" in params:
        args.extend(["--target-mode", str(params["target_mode"])])
    if "feature_mode" in params:
        args.extend(["--feature-mode", str(params["feature_mode"])])
    if "lags" in params:
        args.extend(["--lags", comma_join(params["lags"])])
    if "horizons" in params:
        args.extend(["--horizons", comma_join(params["horizons"])])
    if "initial_train_size" in params:
        args.extend(["--initial-train-size", str(params["initial_train_size"])])
    return args


def _build_e1_command(
    profile: FrozenRunProfile,
    *,
    python_executable: str,
    runtime_run_id: str,
    dataset_path: Path,
    workbook_path: Path,
    runs_dir: Path,
) -> list[str]:
    params = profile.parameters
    model_params = params["model_params"]
    alpha_min_exp, alpha_max_exp, alpha_points = _logspace_bounds(model_params["alpha_grid"])
    args = _common_runner_args(
        profile,
        python_executable=python_executable,
        runtime_run_id=runtime_run_id,
        dataset_path=dataset_path,
        workbook_path=workbook_path,
        runs_dir=runs_dir,
    )
    args.extend(
        [
            "--transform-mode",
            str(params["transform_mode"]),
            "--winsor-lower-quantile",
            str(model_params["winsor_lower_quantile"]),
            "--winsor-upper-quantile",
            str(model_params["winsor_upper_quantile"]),
            "--alpha-grid-min-exp",
            str(alpha_min_exp),
            "--alpha-grid-max-exp",
            str(alpha_max_exp),
            "--alpha-grid-points",
            str(alpha_points),
            "--inner-splits",
            str(model_params["inner_splits"]),
            "--alpha-selection-metric",
            str(model_params["alpha_selection_metric"]),
        ]
    )
    return args


def _build_e2_command(
    profile: FrozenRunProfile,
    *,
    python_executable: str,
    runtime_run_id: str,
    dataset_path: Path,
    workbook_path: Path,
    runs_dir: Path,
) -> list[str]:
    params = profile.parameters
    model_params = params["model_params"]
    param_grid = model_params["param_grid"]
    alpha_min_exp, alpha_max_exp, alpha_points = _logspace_bounds(param_grid["alpha"])
    args = _common_runner_args(
        profile,
        python_executable=python_executable,
        runtime_run_id=runtime_run_id,
        dataset_path=dataset_path,
        workbook_path=workbook_path,
        runs_dir=runs_dir,
    )
    args.extend(
        [
            "--hypothesis-note",
            str(model_params.get("hypothesis_note", "")),
            "--transform-mode",
            str(model_params["transform_mode"]),
            "--winsor-lower-quantile",
            str(model_params["winsor_lower_quantile"]),
            "--winsor-upper-quantile",
            str(model_params["winsor_upper_quantile"]),
            "--epsilon-grid",
            comma_join(param_grid["epsilon"]),
            "--alpha-grid-min-exp",
            str(alpha_min_exp),
            "--alpha-grid-max-exp",
            str(alpha_max_exp),
            "--alpha-grid-points",
            str(alpha_points),
            "--max-iter-grid",
            comma_join(param_grid["max_iter"]),
            "--tol-grid",
            comma_join(param_grid["tol"]),
            "--inner-splits",
            str(model_params["inner_splits"]),
            "--tuning-metric",
            str(model_params["tuning_metric"]),
        ]
    )
    return args


def _build_e3_command(
    profile: FrozenRunProfile,
    *,
    python_executable: str,
    runtime_run_id: str,
    dataset_path: Path,
    workbook_path: Path,
    runs_dir: Path,
) -> list[str]:
    model_params = profile.parameters["model_params"]
    args = _common_runner_args(
        profile,
        python_executable=python_executable,
        runtime_run_id=runtime_run_id,
        dataset_path=dataset_path,
        workbook_path=workbook_path,
        runs_dir=runs_dir,
    )
    args.extend(
        [
            "--tree-model",
            str(model_params["tree_model"]),
            "--n-estimators",
            str(model_params["n_estimators"]),
            "--max-depth",
            str(model_params["max_depth"]),
            "--min-samples-leaf",
            str(model_params["min_samples_leaf"]),
            "--min-samples-split",
            str(model_params["min_samples_split"]),
            "--max-features",
            str(model_params["max_features"]),
            "--random-state",
            str(model_params["random_state"]),
        ]
    )
    args.extend(_bool_flag("--bootstrap", "--no-bootstrap", bool(model_params["bootstrap"])))
    return args


def _build_e5_command(
    profile: FrozenRunProfile,
    *,
    python_executable: str,
    runtime_run_id: str,
    dataset_path: Path,
    workbook_path: Path,
    runs_dir: Path,
) -> list[str]:
    model_params = profile.parameters["model_params"]
    args = _common_runner_args(
        profile,
        python_executable=python_executable,
        runtime_run_id=runtime_run_id,
        dataset_path=dataset_path,
        workbook_path=workbook_path,
        runs_dir=runs_dir,
    )
    args.extend(
        [
            "--iterations",
            str(model_params["iterations"]),
            "--depth",
            str(model_params["depth"]),
            "--learning-rate",
            str(model_params["learning_rate"]),
            "--l2-leaf-reg",
            str(model_params["l2_leaf_reg"]),
            "--subsample",
            str(model_params["subsample"]),
            "--loss-function",
            str(model_params["loss_function"]),
            "--random-seed",
            str(model_params["random_seed"]),
        ]
    )
    if model_params.get("tuning_strategy") == "tscv_param_grid_temporal":
        param_grid = model_params.get("param_grid", {})
        args.append("--use-inner-tuning")
        args.extend(["--inner-splits", str(model_params["inner_splits"])])
        args.extend(["--tuning-metric", str(model_params["tuning_metric"])])
        if param_grid.get("iterations"):
            args.extend(["--iterations-grid", comma_join(param_grid["iterations"])])
        if param_grid.get("depth"):
            args.extend(["--depth-grid", comma_join(param_grid["depth"])])
        if param_grid.get("learning_rate"):
            args.extend(["--learning-rate-grid", comma_join(param_grid["learning_rate"])])
        if param_grid.get("l2_leaf_reg"):
            args.extend(["--l2-leaf-reg-grid", comma_join(param_grid["l2_leaf_reg"])])
        if param_grid.get("subsample"):
            args.extend(["--subsample-grid", comma_join(param_grid["subsample"])])
    return args


def _build_e7_command(
    profile: FrozenRunProfile,
    *,
    python_executable: str,
    runtime_run_id: str,
    dataset_path: Path,
    workbook_path: Path,
    runs_dir: Path,
) -> list[str]:
    model_params = profile.parameters["model_params"]
    args = _common_runner_args(
        profile,
        python_executable=python_executable,
        runtime_run_id=runtime_run_id,
        dataset_path=dataset_path,
        workbook_path=workbook_path,
        runs_dir=runs_dir,
    )
    args.extend(
        [
            "--changepoint-prior-scale",
            str(model_params["changepoint_prior_scale"]),
            "--seasonality-mode",
            str(model_params["seasonality_mode"]),
        ]
    )
    if bool(model_params["weekly_seasonality"]):
        args.append("--weekly-seasonality")
    if bool(model_params["yearly_seasonality"]):
        args.append("--yearly-seasonality")
    if bool(model_params["daily_seasonality"]):
        args.append("--daily-seasonality")
    return args


def _build_e9_command(
    profile: FrozenRunProfile,
    *,
    python_executable: str,
    runtime_run_id: str,
    dataset_path: Path,
    workbook_path: Path,
    runs_dir: Path,
) -> list[str]:
    params = profile.parameters
    args = [
        python_executable,
        "-m",
        profile.runner_module,
        "--run-id",
        runtime_run_id,
        "--dataset-path",
        str(dataset_path),
        "--workbook",
        str(workbook_path),
        "--runs-dir",
        str(runs_dir),
        "--table-path",
        str(E9_CURATED_TABLE_PATH),
        "--sheet-name",
        str(params["sheet_name"]),
        "--horizons",
        comma_join(params["horizons"]),
        "--initial-train-size",
        str(params["initial_train_size"]),
        "--meta-model",
        str(params["meta_model"]),
        "--alpha-grid-size",
        str(params["alpha_grid_size"]),
        "--alpha-grid-min-exp",
        str(params["alpha_grid_min_exp"]),
        "--alpha-grid-max-exp",
        str(params["alpha_grid_max_exp"]),
        "--inner-splits",
        str(params["inner_splits"]),
        "--alpha-selection-metric",
        str(params["alpha_selection_metric"]),
    ]
    if bool(params.get("use_only_complete_rows", True)):
        args.append("--use-only-complete-rows")
    return args


def build_frozen_runner_command(
    profile: FrozenRunProfile,
    *,
    python_executable: str = MODELING_PYTHON,
    runtime_run_id: str,
    dataset_path: Path = DEFAULT_OPERATION_DATASET,
    workbook_path: Path = EXPERIMENTS_WORKBOOK,
    runs_dir: Path = EXPERIMENTS_RUNS_DIR,
) -> list[str]:
    script_name = profile.script_name
    if script_name == "run_e1_ridge_clean.py":
        return _build_e1_command(
            profile,
            python_executable=python_executable,
            runtime_run_id=runtime_run_id,
            dataset_path=dataset_path,
            workbook_path=workbook_path,
            runs_dir=runs_dir,
        )
    if script_name == "run_e2_huber_clean.py":
        return _build_e2_command(
            profile,
            python_executable=python_executable,
            runtime_run_id=runtime_run_id,
            dataset_path=dataset_path,
            workbook_path=workbook_path,
            runs_dir=runs_dir,
        )
    if script_name == "run_e3_random_forest.py":
        return _build_e3_command(
            profile,
            python_executable=python_executable,
            runtime_run_id=runtime_run_id,
            dataset_path=dataset_path,
            workbook_path=workbook_path,
            runs_dir=runs_dir,
        )
    if script_name == "run_e5_catboost.py":
        return _build_e5_command(
            profile,
            python_executable=python_executable,
            runtime_run_id=runtime_run_id,
            dataset_path=dataset_path,
            workbook_path=workbook_path,
            runs_dir=runs_dir,
        )
    if script_name == "run_e7_prophet.py":
        return _build_e7_command(
            profile,
            python_executable=python_executable,
            runtime_run_id=runtime_run_id,
            dataset_path=dataset_path,
            workbook_path=workbook_path,
            runs_dir=runs_dir,
        )
    if script_name == "run_e9_stacking.py":
        return _build_e9_command(
            profile,
            python_executable=python_executable,
            runtime_run_id=runtime_run_id,
            dataset_path=dataset_path,
            workbook_path=workbook_path,
            runs_dir=runs_dir,
        )
    raise ValueError(f"No hay builder de comando congelado para {script_name}.")
