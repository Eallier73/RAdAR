from __future__ import annotations

import traceback
from dataclasses import dataclass
from typing import Any

from .config import (
    ALLOWED_MODES,
    DEFAULT_ALLOW_PARTIAL,
    DEFAULT_FAIL_FAST,
    DEFAULT_SOURCES,
    STAGE_NAMES,
    SUCCESS_LIKE_STAGE_STATUSES,
)
from .contracts import STAGE_CONTRACTS, StageResult, validate_stage_name
from .run_context import (
    RadarRunContext,
    build_repo_context_snapshot,
    now_text,
    resolve_operational_window,
    resolve_week_window,
)
from .state_store import OperationStateStore
from .stages import (
    run_extraction_stage,
    run_modeling_stage,
    run_nlp_stage,
    run_preflight_stage,
    run_preprocessing_stage,
)


STAGE_RUNNERS = {
    "preflight": run_preflight_stage,
    "extraction": run_extraction_stage,
    "preprocessing": run_preprocessing_stage,
    "nlp": run_nlp_stage,
    "modeling": run_modeling_stage,
}


@dataclass
class PipelineRequest:
    week: str | None
    date_from: str | None
    date_to: str | None
    mode: str
    stages: list[str] | None
    from_stage: str | None
    to_stage: str | None
    resume_run_id: str | None
    sources: list[str]
    fail_fast: bool = DEFAULT_FAIL_FAST
    allow_partial: bool = DEFAULT_ALLOW_PARTIAL
    dry_run: bool = False
    log_level: str = "INFO"


class RadarPipelineOrchestrator:
    def __init__(self, state_store: OperationStateStore | None = None) -> None:
        self.state_store = state_store or OperationStateStore()

    def run(self, request: PipelineRequest) -> RadarRunContext:
        self._validate_request(request)
        if request.resume_run_id:
            context, previous_plan = self.state_store.load_context(request.resume_run_id)
            if request.week and resolve_week_window(request.week).slug != context.week.slug:
                raise ValueError("El --week proporcionado no coincide con el run que se intenta reanudar.")
            context.mode = request.mode
            context.fail_fast = request.fail_fast
            context.allow_partial = request.allow_partial
            context.dry_run = request.dry_run
            context.log_level = request.log_level
            context.sources_requested = request.sources or context.sources_requested
            context.sources_effective = request.sources or context.sources_effective
            context.repo_context = build_repo_context_snapshot()
            if request.date_from or request.date_to or request.week:
                resolved_week, selected_start, selected_end = resolve_operational_window(
                    request.week or context.week.requested_value,
                    request.date_from,
                    request.date_to,
                )
                if resolved_week.slug != context.week.slug:
                    raise ValueError(
                        "La reanudación solo permite conservar la misma semana canónica del run original."
                    )
                context.metadata["selection_start_date"] = selected_start.isoformat()
                context.metadata["selection_end_date"] = selected_end.isoformat()
            if request.stages:
                stages_planned = self._normalize_stage_selection(request.stages)
                context.from_stage = stages_planned[0]
                context.to_stage = stages_planned[-1]
                self._reset_selected_stages(context, stages_planned)
            elif request.from_stage:
                context.from_stage = request.from_stage
                self._reset_stages_from(context, request.from_stage)
            else:
                inferred = self._infer_resume_stage(context)
                context.from_stage = inferred
            if request.to_stage and not request.stages:
                context.to_stage = request.to_stage
            if not request.stages:
                stages_planned = self._build_stage_plan(context.from_stage, context.to_stage)
        else:
            week, selected_start, selected_end = resolve_operational_window(
                request.week,
                request.date_from,
                request.date_to,
            )
            if request.stages:
                stages_planned = self._normalize_stage_selection(request.stages)
                from_stage = stages_planned[0]
                to_stage = stages_planned[-1]
            else:
                from_stage = request.from_stage or STAGE_NAMES[0]
                to_stage = request.to_stage or STAGE_NAMES[-1]
                stages_planned = self._build_stage_plan(from_stage, to_stage)
            run_id = self.state_store.next_run_id(week.slug)
            artifacts_root = self.state_store.build_run_root(week.slug, run_id)
            context = RadarRunContext(
                run_id=run_id,
                week=week,
                mode=request.mode,
                artifacts_root=artifacts_root,
                started_at=now_text(),
                from_stage=from_stage,
                to_stage=to_stage,
                fail_fast=request.fail_fast,
                allow_partial=request.allow_partial,
                dry_run=request.dry_run,
                log_level=request.log_level,
                sources_requested=request.sources or list(DEFAULT_SOURCES),
                sources_effective=request.sources or list(DEFAULT_SOURCES),
                repo_context=build_repo_context_snapshot(),
            )
            context.metadata["selection_start_date"] = selected_start.isoformat()
            context.metadata["selection_end_date"] = selected_end.isoformat()
            self._initialize_stage_states(context, stages_planned)

        context.ensure_directories()
        self.state_store.persist_run(context, stages_planned)
        context.emit(
            f"Run preparado: {context.run_id} | semana={context.week.slug} | etapas={stages_planned}",
            stage_name=None,
        )

        for stage_name in stages_planned:
            contract = STAGE_CONTRACTS[stage_name]
            if context.stage_states.get(stage_name, {}).get("status") in SUCCESS_LIKE_STAGE_STATUSES and request.resume_run_id and not request.from_stage:
                context.emit(f"Etapa ya completada en corrida previa; se conserva: {stage_name}", stage_name=stage_name)
                continue

            context.stage_states[stage_name] = {
                **context.stage_states.get(stage_name, {}),
                "stage_name": stage_name,
                "status": "running",
                "started_at": now_text(),
                "warnings": [],
                "errors": [],
                "artifacts": [],
            }
            self.state_store.persist_run(context, stages_planned)
            context.emit(f"Iniciando etapa {stage_name}", stage_name=stage_name)

            try:
                result = STAGE_RUNNERS[stage_name](context, contract)
            except Exception as exc:
                result = self._build_failure_result(stage_name, exc)

            self.state_store.persist_stage(context, stage_name, result.to_dict(), stages_planned)
            context.emit(f"Etapa {stage_name} -> {result.status}", stage_name=stage_name)

            if result.status == "failed" and context.fail_fast:
                break
            if result.status == "partial_success" and not (context.allow_partial or contract.partial_allowed) and context.fail_fast:
                break

        context.finished_at = now_text()
        context.status = self._resolve_global_status(context, stages_planned)
        self.state_store.persist_run(context, stages_planned)
        context.emit(f"Run finalizado con estado {context.status}", stage_name=None)
        return context

    def _validate_request(self, request: PipelineRequest) -> None:
        if request.mode not in ALLOWED_MODES:
            raise ValueError(f"Modo no soportado: {request.mode}. Usa {ALLOWED_MODES}.")
        if not request.resume_run_id and not request.week:
            if not (request.date_from and request.date_to):
                raise ValueError("Debes indicar --week o un rango --date-from/--date-to cuando no usas --resume-run-id.")
        if (request.date_from and not request.date_to) or (request.date_to and not request.date_from):
            raise ValueError("Debes proporcionar --date-from y --date-to juntos.")
        if request.stages and (request.from_stage or request.to_stage):
            raise ValueError("Usa --stages o bien --from-stage/--to-stage, pero no ambos a la vez.")
        if request.stages:
            self._normalize_stage_selection(request.stages)
        if request.from_stage:
            validate_stage_name(request.from_stage)
        if request.to_stage:
            validate_stage_name(request.to_stage)
        if request.from_stage and request.to_stage:
            from_idx = STAGE_NAMES.index(request.from_stage)
            to_idx = STAGE_NAMES.index(request.to_stage)
            if from_idx > to_idx:
                raise ValueError("--from-stage no puede ir después de --to-stage.")

    def _build_stage_plan(self, from_stage: str, to_stage: str) -> list[str]:
        from_idx = STAGE_NAMES.index(validate_stage_name(from_stage))
        to_idx = STAGE_NAMES.index(validate_stage_name(to_stage))
        return list(STAGE_NAMES[from_idx : to_idx + 1])

    def _normalize_stage_selection(self, stages: list[str]) -> list[str]:
        selected = {validate_stage_name(stage) for stage in stages}
        normalized = [stage for stage in STAGE_NAMES if stage in selected]
        if not normalized:
            raise ValueError("Debes seleccionar al menos una etapa.")
        return normalized

    def _initialize_stage_states(self, context: RadarRunContext, stages_planned: list[str]) -> None:
        for stage_name in STAGE_NAMES:
            if stage_name in stages_planned:
                context.stage_states[stage_name] = {
                    "stage_name": stage_name,
                    "status": "planned",
                    "warnings": [],
                    "errors": [],
                    "artifacts": [],
                    "outputs": {},
                }
            else:
                context.stage_states[stage_name] = {
                    "stage_name": stage_name,
                    "status": "skipped",
                    "warnings": [],
                    "errors": [],
                    "artifacts": [],
                    "outputs": {"reason": "Fuera de la selección de etapas solicitada por CLI."},
                    "notes": ["Etapa omitida por selección explícita de etapas o por rango from_stage/to_stage."],
                }

    def _infer_resume_stage(self, context: RadarRunContext) -> str:
        for stage_name in STAGE_NAMES:
            if context.stage_states.get(stage_name, {}).get("status") not in SUCCESS_LIKE_STAGE_STATUSES:
                return stage_name
        return context.to_stage

    def _reset_stages_from(self, context: RadarRunContext, from_stage: str) -> None:
        reset = False
        for stage_name in STAGE_NAMES:
            if stage_name == from_stage:
                reset = True
            if reset:
                context.stage_states[stage_name] = {
                    "stage_name": stage_name,
                    "status": "planned",
                    "warnings": [],
                    "errors": [],
                    "artifacts": [],
                    "outputs": {},
                }

    def _reset_selected_stages(self, context: RadarRunContext, stages_planned: list[str]) -> None:
        for stage_name in STAGE_NAMES:
            if stage_name in stages_planned:
                context.stage_states[stage_name] = {
                    "stage_name": stage_name,
                    "status": "planned",
                    "warnings": [],
                    "errors": [],
                    "artifacts": [],
                    "outputs": {},
                }
            else:
                existing = context.stage_states.get(stage_name, {})
                context.stage_states[stage_name] = {
                    "stage_name": stage_name,
                    "status": existing.get("status", "skipped"),
                    "warnings": existing.get("warnings", []),
                    "errors": existing.get("errors", []),
                    "artifacts": existing.get("artifacts", []),
                    "outputs": existing.get("outputs", {"reason": "Fuera de la selección de etapas solicitada por CLI."}),
                }

    def _build_failure_result(self, stage_name: str, exc: Exception) -> StageResult:
        finished_at = now_text()
        traceback_text = traceback.format_exc()
        return StageResult(
            stage_name=stage_name,
            status="failed",
            started_at=finished_at,
            finished_at=finished_at,
            duration_sec=0.0,
            inputs={},
            outputs={},
            artifacts=[],
            metrics={},
            warnings=[],
            errors=[str(exc), traceback_text],
            notes=["La excepción quedó persistida en el estado y en el log de etapa."],
            commands=[],
        )

    def _resolve_global_status(self, context: RadarRunContext, stages_planned: list[str]) -> str:
        statuses = [context.stage_states.get(stage_name, {}).get("status", "planned") for stage_name in stages_planned]
        if any(status == "failed" for status in statuses):
            return "failed"
        if statuses and all(status == "skipped" for status in statuses):
            return "skipped"
        if any(status in {"partial_success", "stubbed"} for status in statuses):
            return "partial_success"
        if any(status == "running" for status in statuses):
            return "running"
        return "success"
