from __future__ import annotations

import json
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .config import (
    DEFAULT_LOG_LEVEL,
    PIPELINE_LOG_FILENAME,
    PUBLISHED_DIRNAME,
    PUBLISHED_EXPERIMENTAL_DIRNAME,
    PUBLISHED_POWERBI_DIRNAME,
    PUBLISHED_REPORT_INPUTS_DIRNAME,
    ROOT_DIR,
    STAGE_NAMES,
)
from ..preprocessing.normalizar_semanas_canonicas import (
    build_week_folder_name,
    normalize_to_iso_week_start,
)


ISO_WEEK_RE = re.compile(r"^(?P<year>\d{4})-W(?P<week>\d{2})$")


def now_text() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


@dataclass(frozen=True)
class WeekWindow:
    requested_value: str
    slug: str
    start_date: date
    end_date: date
    folder_name: str

    def to_dict(self) -> dict[str, str]:
        return {
            "requested_value": self.requested_value,
            "slug": self.slug,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "folder_name": self.folder_name,
        }


def resolve_week_window(value: str) -> WeekWindow:
    value = value.strip()
    match = ISO_WEEK_RE.match(value)
    if match:
        year = int(match.group("year"))
        iso_week = int(match.group("week"))
        start_date = date.fromisocalendar(year, iso_week, 1)
    else:
        try:
            start_date = normalize_to_iso_week_start(date.fromisoformat(value))
        except ValueError as exc:
            raise ValueError(
                "Semana inválida. Usa YYYY-Www o una fecha YYYY-MM-DD dentro de la semana objetivo."
            ) from exc

    iso_year, iso_week, _ = start_date.isocalendar()
    end_date = start_date + timedelta(days=6)
    return WeekWindow(
        requested_value=value,
        slug=f"{iso_year}-W{iso_week:02d}",
        start_date=start_date,
        end_date=end_date,
        folder_name=build_week_folder_name(start_date),
    )


def resolve_operational_window(
    week_value: str | None,
    date_from_value: str | None,
    date_to_value: str | None,
) -> tuple[WeekWindow, date, date]:
    week = resolve_week_window(week_value) if week_value else None

    if date_from_value or date_to_value:
        if not date_from_value or not date_to_value:
            raise ValueError("Debes proporcionar --date-from y --date-to juntos.")
        try:
            selected_start = date.fromisoformat(date_from_value)
            selected_end = date.fromisoformat(date_to_value)
        except ValueError as exc:
            raise ValueError("Las fechas deben usar el formato YYYY-MM-DD.") from exc
        if selected_end < selected_start:
            raise ValueError("--date-to no puede ser anterior a --date-from.")

        inferred_week = week or resolve_week_window(selected_start.isoformat())
        end_week = resolve_week_window(selected_end.isoformat())
        if end_week.slug != inferred_week.slug:
            raise ValueError(
                "El orquestador operativo corre una sola semana canónica por corrida. "
                "El rango indicado cruza más de una semana ISO."
            )
        if week and (selected_start < week.start_date or selected_end > week.end_date):
            raise ValueError("El rango de fechas debe quedar dentro de la semana indicada en --week.")
        return inferred_week, selected_start, selected_end

    if week:
        return week, week.start_date, week.end_date

    raise ValueError("Debes indicar --week o bien --date-from/--date-to.")


def _run_git_command(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(ROOT_DIR), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip()


def build_repo_context_snapshot() -> dict[str, Any]:
    branch = _run_git_command("branch", "--show-current")
    commit = _run_git_command("rev-parse", "HEAD")
    status_short = _run_git_command("status", "--short")
    return {
        "repo_root": str(ROOT_DIR),
        "branch": branch or "",
        "commit": commit or "",
        "dirty": bool(status_short.strip()),
        "status_short": status_short.splitlines(),
    }


@dataclass
class RadarRunContext:
    run_id: str
    week: WeekWindow
    mode: str
    artifacts_root: Path
    started_at: str
    from_stage: str
    to_stage: str
    fail_fast: bool
    allow_partial: bool
    dry_run: bool
    log_level: str = DEFAULT_LOG_LEVEL
    finished_at: str | None = None
    status: str = "planned"
    sources_requested: list[str] = field(default_factory=list)
    sources_effective: list[str] = field(default_factory=list)
    stage_states: dict[str, dict[str, Any]] = field(default_factory=dict)
    published_outputs: dict[str, list[str]] = field(default_factory=dict)
    repo_context: dict[str, Any] = field(default_factory=build_repo_context_snapshot)
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.logs_dir = self.artifacts_root / "logs"
        self.stages_dir = self.artifacts_root / "stages"
        self.published_dir = self.artifacts_root / PUBLISHED_DIRNAME
        self.published_powerbi_dir = self.published_dir / PUBLISHED_POWERBI_DIRNAME
        self.published_experimental_dir = self.published_dir / PUBLISHED_EXPERIMENTAL_DIRNAME
        self.published_report_inputs_dir = self.published_dir / PUBLISHED_REPORT_INPUTS_DIRNAME
        self.manifest_path = self.artifacts_root / "manifest.json"
        self.summary_path = self.artifacts_root / "run_summary.json"
        self.legacy_manifest_path = self.artifacts_root / "manifest_run.json"
        self.legacy_summary_path = self.artifacts_root / "summary_run.json"
        self.state_path = self.artifacts_root / "state.json"
        self.pipeline_log_path = self.logs_dir / PIPELINE_LOG_FILENAME

    def ensure_directories(self) -> None:
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.stages_dir.mkdir(parents=True, exist_ok=True)
        self.published_powerbi_dir.mkdir(parents=True, exist_ok=True)
        self.published_experimental_dir.mkdir(parents=True, exist_ok=True)
        self.published_report_inputs_dir.mkdir(parents=True, exist_ok=True)

    def stage_log_path(self, stage_name: str) -> Path:
        return self.logs_dir / f"{stage_name}.log"

    def stage_json_path(self, stage_name: str) -> Path:
        return self.stages_dir / f"{stage_name}.json"

    def record_note(self, note: str) -> None:
        self.notes.append(note)

    @property
    def selected_start_date(self) -> date:
        value = self.metadata.get("selection_start_date")
        return date.fromisoformat(value) if value else self.week.start_date

    @property
    def selected_end_date(self) -> date:
        value = self.metadata.get("selection_end_date")
        return date.fromisoformat(value) if value else self.week.end_date

    def selection_window_payload(self) -> dict[str, str]:
        return {
            "week_requested": self.week.requested_value,
            "week_slug": self.week.slug,
            "week_start": self.week.start_date.isoformat(),
            "week_end": self.week.end_date.isoformat(),
            "selected_start": self.selected_start_date.isoformat(),
            "selected_end": self.selected_end_date.isoformat(),
        }

    def _append_log(self, log_path: Path, text: str) -> None:
        self.ensure_directories()
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(text.rstrip() + "\n")

    def emit(self, message: str, *, stage_name: str | None = None) -> None:
        prefix = f"[{now_text()}] [{stage_name or 'pipeline'}]"
        line = f"{prefix} {message}"
        print(line)
        self._append_log(self.pipeline_log_path, line)
        if stage_name:
            self._append_log(self.stage_log_path(stage_name), line)

    def write_json(self, target_path: Path, payload: dict[str, Any]) -> None:
        self.ensure_directories()
        target_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def run_command(
        self,
        stage_name: str,
        label: str,
        command: list[str],
        *,
        check: bool = True,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        command_text = shlex.join(command)
        started_at = now_text()
        self._append_log(self.stage_log_path(stage_name), f"$ {command_text}")

        if self.dry_run:
            self._append_log(self.stage_log_path(stage_name), "[dry-run] comando no ejecutado")
            return {
                "label": label,
                "command": command,
                "command_text": command_text,
                "started_at": started_at,
                "finished_at": now_text(),
                "duration_sec": 0.0,
                "returncode": 0,
                "executed": False,
                "cwd": str(cwd or ROOT_DIR),
            }

        started_dt = datetime.now()
        completed = subprocess.run(
            command,
            cwd=str(cwd or ROOT_DIR),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        finished_dt = datetime.now()
        if completed.stdout:
            self._append_log(self.stage_log_path(stage_name), completed.stdout.rstrip())
        if completed.stderr:
            self._append_log(self.stage_log_path(stage_name), completed.stderr.rstrip())

        payload = {
            "label": label,
            "command": command,
            "command_text": command_text,
            "started_at": started_at,
            "finished_at": finished_dt.replace(microsecond=0).isoformat(sep=" "),
            "duration_sec": round((finished_dt - started_dt).total_seconds(), 3),
            "returncode": completed.returncode,
            "executed": True,
            "cwd": str(cwd or ROOT_DIR),
        }
        if completed.returncode != 0 and check:
            raise subprocess.CalledProcessError(
                completed.returncode,
                command,
                output=completed.stdout,
                stderr=completed.stderr,
            )
        return payload

    def build_manifest_payload(self, stages_planned: list[str]) -> dict[str, Any]:
        stage_statuses = {
            name: self.stage_states.get(name, {}).get("status", "planned")
            for name in STAGE_NAMES
        }
        stages_completed = [name for name, status in stage_statuses.items() if status in {"success", "partial_success", "stubbed"}]
        stages_failed = [name for name, status in stage_statuses.items() if status == "failed"]
        return {
            "run_id": self.run_id,
            "week": self.week.slug,
            "week_requested": self.week.requested_value,
            "week_start": self.week.start_date.isoformat(),
            "week_end": self.week.end_date.isoformat(),
            "week_folder_name": self.week.folder_name,
            "selection_window": self.selection_window_payload(),
            "mode": self.mode,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "sources_requested": self.sources_requested,
            "sources_effective": self.sources_effective,
            "stages_planned": stages_planned,
            "stages_state_snapshot": stage_statuses,
            "stages_completed": stages_completed,
            "stages_failed": stages_failed,
            "artifacts_root": str(self.artifacts_root),
            "published_outputs": self.published_outputs,
            "repo_context": self.repo_context,
            "notes": self.notes,
        }

    def build_summary_payload(self, stages_planned: list[str]) -> dict[str, Any]:
        warnings = []
        errors = []
        stage_summary = {}
        resumable_from = None

        for stage_name in STAGE_NAMES:
            stage_state = self.stage_states.get(stage_name, {})
            stage_summary[stage_name] = {
                "status": stage_state.get("status", "planned"),
                "duration_sec": stage_state.get("duration_sec"),
                "artifacts": stage_state.get("artifacts", []),
                "warnings": stage_state.get("warnings", []),
                "errors": stage_state.get("errors", []),
                "outputs": stage_state.get("outputs", {}),
            }
            warnings.extend(stage_state.get("warnings", []))
            errors.extend(stage_state.get("errors", []))
            if stage_name in stages_planned and resumable_from is None and stage_state.get("status") not in {"success", "partial_success", "skipped", "stubbed"}:
                resumable_from = stage_name

        if self.status == "failed":
            next_action = (
                f"Reanudar con --resume-run-id {self.run_id}"
                + (f" --from-stage {resumable_from}" if resumable_from else "")
            )
        elif self.dry_run:
            next_action = "Ejecutar sin --dry-run para materializar los artefactos."
        elif any(state.get("status") == "stubbed" for state in self.stage_states.values()):
            next_action = "Consumir published/powerbi y completar el generador final de reporte sobre published/report_inputs."
        else:
            next_action = "Consumir las salidas publicadas o automatizar esta CLI desde un scheduler externo."

        return {
            "run_id": self.run_id,
            "week": self.week.slug,
            "selection_window": self.selection_window_payload(),
            "status_global": self.status,
            "dry_run": self.dry_run,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duracion_total_sec": self._total_duration_sec(),
            "estado_por_etapa": stage_summary,
            "stages_requested_this_invocation": stages_planned,
            "outputs_clave": self.published_outputs,
            "warnings": warnings,
            "errors": errors,
            "corrida_reanudable": self.status != "success",
            "reanudar_desde": resumable_from,
            "siguiente_accion_recomendada": next_action,
            "notes": self.notes,
        }

    def _total_duration_sec(self) -> float | None:
        if not self.finished_at:
            return None
        started_dt = datetime.fromisoformat(self.started_at)
        finished_dt = datetime.fromisoformat(self.finished_at)
        return round((finished_dt - started_dt).total_seconds(), 3)

    def to_state_payload(self, stages_planned: list[str]) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "week": self.week.to_dict(),
            "selection_window": self.selection_window_payload(),
            "mode": self.mode,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "fail_fast": self.fail_fast,
            "allow_partial": self.allow_partial,
            "dry_run": self.dry_run,
            "log_level": self.log_level,
            "artifacts_root": str(self.artifacts_root),
            "sources_requested": self.sources_requested,
            "sources_effective": self.sources_effective,
            "stage_states": self.stage_states,
            "published_outputs": self.published_outputs,
            "repo_context": self.repo_context,
            "notes": self.notes,
            "metadata": self.metadata,
            "stages_planned": stages_planned,
        }

    @classmethod
    def from_state_payload(cls, payload: dict[str, Any]) -> "RadarRunContext":
        week_payload = payload["week"]
        week = WeekWindow(
            requested_value=week_payload["requested_value"],
            slug=week_payload["slug"],
            start_date=date.fromisoformat(week_payload["start_date"]),
            end_date=date.fromisoformat(week_payload["end_date"]),
            folder_name=week_payload["folder_name"],
        )
        selection_payload = payload.get("selection_window", {})
        metadata = dict(payload.get("metadata", {}))
        if selection_payload:
            metadata.setdefault("selection_start_date", selection_payload.get("selected_start"))
            metadata.setdefault("selection_end_date", selection_payload.get("selected_end"))
        return cls(
            run_id=payload["run_id"],
            week=week,
            mode=payload["mode"],
            artifacts_root=Path(payload["artifacts_root"]),
            started_at=payload["started_at"],
            finished_at=payload.get("finished_at"),
            status=payload.get("status", "planned"),
            from_stage=payload["from_stage"],
            to_stage=payload["to_stage"],
            fail_fast=payload.get("fail_fast", True),
            allow_partial=payload.get("allow_partial", False),
            dry_run=payload.get("dry_run", False),
            log_level=payload.get("log_level", DEFAULT_LOG_LEVEL),
            sources_requested=list(payload.get("sources_requested", [])),
            sources_effective=list(payload.get("sources_effective", [])),
            stage_states=dict(payload.get("stage_states", {})),
            published_outputs=dict(payload.get("published_outputs", {})),
            repo_context=dict(payload.get("repo_context", {})),
            notes=list(payload.get("notes", [])),
            metadata=metadata,
        )
