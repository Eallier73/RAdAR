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


POST_W10_OPERATION_PROFILE = "post_w10_controlled"
POST_W10_OPERATION_STAGE_ORDER = ("extraction", "preprocessing", "nlp", "modeling")


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
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=STAGE_NAMES,
        help="Lista explícita de etapas a ejecutar, permitiendo selección salteada.",
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
    parser.add_argument(
        "--operation-profile",
        choices=(POST_W10_OPERATION_PROFILE,),
        help=(
            "Perfil operativo integrado. "
            "Actualmente soporta la operación mínima controlada post-W10 sin tocar src/modeling."
        ),
    )
    parser.add_argument("--operation-from-week", help="Semana inicial para operación integrada post-W10. Formato YYYY-Www.")
    parser.add_argument("--operation-to-week", help="Semana final para operación integrada post-W10. Formato YYYY-Www.")
    parser.add_argument("--operation-id", help="Identificador explícito para la corrida operativa integrada.")
    parser.add_argument("--operation-comment", default="", help="Comentario operativo para el registro de emisiones.")
    parser.add_argument("--operation-ops-python", help="Override opcional para el Python de operación/NLP.")
    parser.add_argument("--operation-modeling-python", help="Override opcional para el Python de modelado.")
    return parser.parse_args()


def _validate_integrated_operation_profile(args: argparse.Namespace) -> None:
    if args.mode != ALLOWED_MODES[0]:
        raise ValueError("La operación integrada post-W10 solo soporta --mode controlled.")
    forbidden_pairs = {
        "--week": args.week,
        "--date-from": args.date_from,
        "--date-to": args.date_to,
        "--resume-run-id": args.resume_run_id,
    }
    invalid = [flag for flag, value in forbidden_pairs.items() if value]
    if invalid:
        raise ValueError(
            "La operación integrada post-W10 no usa selección semanal del orquestador estándar. "
            f"No combines {', '.join(invalid)} con --operation-profile."
        )
    if args.resume_run_id:
        raise ValueError("La operación integrada post-W10 no soporta --resume-run-id.")


def _resolve_operation_stage_bounds(args: argparse.Namespace) -> tuple[str, str]:
    if args.stages:
        selected = [stage for stage in STAGE_NAMES if stage in set(args.stages)]
        unsupported = [stage for stage in selected if stage not in POST_W10_OPERATION_STAGE_ORDER]
        if unsupported:
            raise ValueError(
                "La operación integrada post-W10 solo soporta etapas entre extraction y modeling. "
                f"Etapas no soportadas: {unsupported}"
            )
        if not selected:
            raise ValueError("Debes seleccionar al menos una etapa para la operación integrada post-W10.")
        expected_slice = list(
            POST_W10_OPERATION_STAGE_ORDER[
                POST_W10_OPERATION_STAGE_ORDER.index(selected[0]) : POST_W10_OPERATION_STAGE_ORDER.index(selected[-1]) + 1
            ]
        )
        if selected != expected_slice:
            raise ValueError(
                "La operación integrada post-W10 solo soporta selección contigua de etapas. "
                f"Seleccionado={selected}, esperado={expected_slice}"
            )
        return selected[0], selected[-1]

    from_stage = args.from_stage or POST_W10_OPERATION_STAGE_ORDER[0]
    to_stage = args.to_stage or POST_W10_OPERATION_STAGE_ORDER[-1]
    unsupported = [stage for stage in (from_stage, to_stage) if stage not in POST_W10_OPERATION_STAGE_ORDER]
    if unsupported:
        raise ValueError(
            "La operación integrada post-W10 solo soporta etapas entre extraction y modeling. "
            f"Etapas no soportadas: {unsupported}"
        )
    if POST_W10_OPERATION_STAGE_ORDER.index(from_stage) > POST_W10_OPERATION_STAGE_ORDER.index(to_stage):
        raise ValueError("--from-stage no puede ir después de --to-stage en la operación integrada post-W10.")
    return from_stage, to_stage


def _run_integrated_operation_profile(args: argparse.Namespace) -> int:
    _validate_integrated_operation_profile(args)
    if args.operation_profile != POST_W10_OPERATION_PROFILE:
        raise ValueError(f"Perfil operativo no soportado: {args.operation_profile}")

    from .run_operacion_minima_post_w10 import main as run_post_w10

    operation_from_stage, operation_to_stage = _resolve_operation_stage_bounds(args)
    delegated_args: list[str] = []
    if args.operation_from_week:
        delegated_args.extend(["--from-week", args.operation_from_week])
    if args.operation_to_week:
        delegated_args.extend(["--to-week", args.operation_to_week])
    if args.operation_id:
        delegated_args.extend(["--operation-id", args.operation_id])
    if args.operation_comment:
        delegated_args.extend(["--comment", args.operation_comment])
    if args.operation_ops_python:
        delegated_args.extend(["--ops-python", args.operation_ops_python])
    if args.operation_modeling_python:
        delegated_args.extend(["--modeling-python", args.operation_modeling_python])
    delegated_args.extend(["--pipeline-from-stage", operation_from_stage, "--pipeline-to-stage", operation_to_stage])
    if args.sources:
        delegated_args.extend(["--sources", *list(args.sources)])
    delegated_args.append("--fail-fast" if args.fail_fast else "--no-fail-fast")
    if args.dry_run:
        delegated_args.append("--dry-run")
    return run_post_w10(delegated_args)


def main() -> int:
    args = parse_args()
    if args.operation_profile:
        try:
            return _run_integrated_operation_profile(args)
        except Exception as exc:
            print(f"fatal_error={exc}", file=sys.stderr)
            return 2
    orchestrator = RadarPipelineOrchestrator()
    request = PipelineRequest(
        week=args.week,
        date_from=args.date_from,
        date_to=args.date_to,
        mode=args.mode,
        stages=list(args.stages) if args.stages else None,
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
