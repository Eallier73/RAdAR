from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import STAGE_NAMES, STAGE_STATUS_VALUES


@dataclass(frozen=True)
class StageContract:
    name: str
    description: str
    required_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    required_artifacts: tuple[str, ...]
    allowed_statuses: tuple[str, ...] = STAGE_STATUS_VALUES
    partial_allowed: bool = False


@dataclass
class StageResult:
    stage_name: str
    status: str
    started_at: str
    finished_at: str
    duration_sec: float
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    commands: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_sec": self.duration_sec,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "artifacts": self.artifacts,
            "metrics": self.metrics,
            "warnings": self.warnings,
            "errors": self.errors,
            "notes": self.notes,
            "commands": self.commands,
        }


def validate_stage_name(stage_name: str) -> str:
    if stage_name not in STAGE_NAMES:
        raise ValueError(f"Etapa no soportada: {stage_name}. Usa una de {STAGE_NAMES}.")
    return stage_name


STAGE_CONTRACTS: dict[str, StageContract] = {
    "preflight": StageContract(
        name="preflight",
        description=(
            "Valida precondiciones antes de extraer: secrets por fuente, "
            "state de Twitter/X, rutas de runtime. "
            "Si falta algo y allow_partial=True, excluye fuentes bloqueadas y continua. "
            "Si falta algo y allow_partial=False, detiene el pipeline."
        ),
        required_inputs=("sources", "fail_fast", "allow_partial"),
        expected_outputs=("source_checks", "runtime_path_checks", "sources_effective_after_preflight"),
        required_artifacts=("logs/preflight.log", "stages/preflight.json"),
        partial_allowed=True,
    ),
    "extraction": StageContract(
        name="extraction",
        description="Coordina extractores canónicos por fuente y registra resultados por origen.",
        required_inputs=("week", "sources", "source_credentials_if_needed"),
        expected_outputs=(
            "raw_weekly_files_for_twitter_youtube_medios",
            "facebook_extraction_artifacts_when_requested",
        ),
        required_artifacts=("logs/extraction.log", "stages/extraction.json"),
        partial_allowed=True,
    ),
    "preprocessing": StageContract(
        name="preprocessing",
        description="Normaliza el raw semanal, promueve texto y audita inputs/outputs por fuente.",
        required_inputs=("raw_weekly_inputs", "week", "sources"),
        expected_outputs=("canonical_raw_week_folder", "canonical_text_files_for_requested_sources"),
        required_artifacts=("logs/preprocessing.log", "stages/preprocessing.json"),
        partial_allowed=True,
    ),
    "nlp": StageContract(
        name="nlp",
        description="Construye sentimiento y datasets analíticos intermedios consumibles por modelado.",
        required_inputs=("text_weekly_inputs", "dictionary_assets", "processed_modeling_inputs"),
        expected_outputs=(
            "aceptacion_digital_redes_medios_sentimiento_semanal.xlsx",
            "encuestas_y_sentimiento_mensual_unificado.xlsx",
            "datos_ml_0.xlsx",
            "canonical_modeling_dataset_or_explicit_reuse_note",
        ),
        required_artifacts=("logs/nlp.log", "stages/nlp.json"),
        partial_allowed=True,
    ),
    "modeling": StageContract(
        name="modeling",
        description="Ejecuta un runner canónico de modelado en modo controlado y registra artefactos del run.",
        required_inputs=("canonical_modeling_dataset", "controlled_model_runner"),
        expected_outputs=("experiment_run_dir", "prediction_files", "modeling_summary_json"),
        required_artifacts=("logs/modeling.log", "stages/modeling.json"),
        partial_allowed=False,
    ),
    "export": StageContract(
        name="export",
        description="Publica tablas finales y artefactos clave en una ruta estable para consumo externo.",
        required_inputs=("processed_modeling_outputs", "modeling_outputs_if_available"),
        expected_outputs=("published/powerbi", "powerbi_export_manifest.json"),
        required_artifacts=("logs/export.log", "stages/export.json"),
        partial_allowed=True,
    ),
    "report": StageContract(
        name="report",
        description="Empaqueta insumos para reporte y deja stub controlado si no existe generador final.",
        required_inputs=("published/powerbi",),
        expected_outputs=("published/report_inputs", "report_inputs_manifest.json"),
        required_artifacts=("logs/report.log", "stages/report.json"),
        partial_allowed=True,
    ),
}
