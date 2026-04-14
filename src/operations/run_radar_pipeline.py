from __future__ import annotations

import argparse
import sys

from .config import (
    ALLOWED_MODES,
    DEFAULT_ALLOW_PARTIAL,
    DEFAULT_FAIL_FAST,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MODEL_DATASET,
    DEFAULT_MODEL_RUNNER,
    DEFAULT_SOURCES,
    SOURCE_NAMES,
    STAGE_NAMES,
)
from .pipeline_orchestrator import PipelineRequest, RadarPipelineOrchestrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Entry point operativo único del pipeline Radar. "
            "Coordina extracción, preprocessing, NLP, modelado, exportación y empaquetado de reporte."
        )
    )
    parser.add_argument(
        "--week",
        help="Semana objetivo. Usa YYYY-Www o la fecha de inicio canónica YYYY-MM-DD.",
    )
    parser.add_argument("--date-from", help="Fecha inicial de operación dentro de la semana objetivo. Formato YYYY-MM-DD.")
    parser.add_argument("--date-to", help="Fecha final de operación dentro de la semana objetivo. Formato YYYY-MM-DD.")
    parser.add_argument(
        "--mode",
        choices=ALLOWED_MODES,
        default=ALLOWED_MODES[0],
        help=f"Modo operativo permitido. Default: {ALLOWED_MODES[0]}",
    )
    parser.add_argument("--from-stage", choices=STAGE_NAMES, help="Primera etapa a ejecutar.")
    parser.add_argument("--to-stage", choices=STAGE_NAMES, help="Última etapa a ejecutar.")
    parser.add_argument("--resume-run-id", help="Rehidrata y continúa una corrida previa.")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=SOURCE_NAMES,
        default=list(DEFAULT_SOURCES),
        help=f"Fuentes a considerar en extracción/preprocessing. Default: {' '.join(DEFAULT_SOURCES)}",
    )
    parser.add_argument("--fail-fast", dest="fail_fast", action="store_true", default=DEFAULT_FAIL_FAST)
    parser.add_argument("--no-fail-fast", dest="fail_fast", action="store_false")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        default=DEFAULT_ALLOW_PARTIAL,
        help="Permite continuar y cerrar corrida como partial_success cuando una etapa lo soporte.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Planifica y valida contratos sin ejecutar scripts.")
    parser.add_argument(
        "--log-level",
        default=DEFAULT_LOG_LEVEL,
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help=f"Nivel de verbosidad operativo. Default: {DEFAULT_LOG_LEVEL}",
    )
    parser.add_argument(
        "--model-runner",
        default=DEFAULT_MODEL_RUNNER,
        help=f"Runner canónico de modelado a invocar. Default: {DEFAULT_MODEL_RUNNER}",
    )
    parser.add_argument("--model-run-id", help="Run_ID explícito para el runner de modelado.")
    parser.add_argument(
        "--model-arg",
        action="append",
        default=[],
        help="Argumento extra que se pasa tal cual al runner de modelado. Repite el flag para varios.",
    )
    parser.add_argument(
        "--model-dataset-path",
        default=str(DEFAULT_MODEL_DATASET),
        help=f"Dataset maestro consumido por modeling. Default: {DEFAULT_MODEL_DATASET}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    orchestrator = RadarPipelineOrchestrator()
    request = PipelineRequest(
        week=args.week,
        date_from=args.date_from,
        date_to=args.date_to,
        mode=args.mode,
        from_stage=args.from_stage,
        to_stage=args.to_stage,
        resume_run_id=args.resume_run_id,
        sources=list(args.sources),
        fail_fast=args.fail_fast,
        allow_partial=args.allow_partial,
        dry_run=args.dry_run,
        log_level=args.log_level,
        model_runner=args.model_runner,
        model_run_id=args.model_run_id,
        model_args=list(args.model_arg),
        model_dataset_path=args.model_dataset_path,
    )
    try:
        context = orchestrator.run(request)
    except Exception as exc:
        print(f"fatal_error={exc}", file=sys.stderr)
        return 2
    print(f"run_id={context.run_id}")
    print(f"status={context.status}")
    print(f"summary={context.summary_path}")
    return 0 if context.status in {"success", "partial_success", "skipped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
