from __future__ import annotations

import json
import re
from pathlib import Path

from .config import OPERATIONS_ARTIFACTS_ROOT, STAGE_NAMES
from .run_context import RadarRunContext


RUN_ID_RE = re.compile(r"^radar_(?P<week>\d{4}W\d{2})_(?P<seq>\d{3})$")


class OperationStateStore:
    def __init__(self, operations_root: Path = OPERATIONS_ARTIFACTS_ROOT) -> None:
        self.operations_root = operations_root

    def build_run_root(self, week_slug: str, run_id: str) -> Path:
        year = week_slug[:4]
        return self.operations_root / year / week_slug / run_id

    def next_run_id(self, week_slug: str) -> str:
        token = week_slug.replace("-W", "W")
        week_dir = self.operations_root / week_slug[:4] / week_slug
        existing = []
        if week_dir.exists():
            for entry in week_dir.iterdir():
                if not entry.is_dir():
                    continue
                match = RUN_ID_RE.match(entry.name)
                if match and match.group("week") == token:
                    existing.append(int(match.group("seq")))
        next_seq = max(existing, default=0) + 1
        return f"radar_{token}_{next_seq:03d}"

    def resolve_run_root(self, run_id: str) -> Path:
        matches = list(self.operations_root.glob(f"*/*/{run_id}"))
        if not matches:
            raise FileNotFoundError(f"No se encontró el run_id {run_id} dentro de {self.operations_root}.")
        if len(matches) > 1:
            raise RuntimeError(f"run_id ambiguo {run_id}: {matches}")
        return matches[0]

    def load_context(self, run_id: str) -> tuple[RadarRunContext, list[str]]:
        run_root = self.resolve_run_root(run_id)
        state_path = run_root / "state.json"
        if not state_path.exists():
            raise FileNotFoundError(f"No existe state.json para {run_id}: {state_path}")
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        context = RadarRunContext.from_state_payload(payload)
        stages_planned = list(payload.get("stages_planned", STAGE_NAMES))
        return context, stages_planned

    def persist_run(self, context: RadarRunContext, stages_planned: list[str]) -> None:
        context.ensure_directories()
        context.write_json(context.state_path, context.to_state_payload(stages_planned))
        context.write_json(context.manifest_path, context.build_manifest_payload(stages_planned))
        context.write_json(context.legacy_manifest_path, context.build_manifest_payload(stages_planned))
        context.write_json(context.summary_path, context.build_summary_payload(stages_planned))
        context.write_json(context.legacy_summary_path, context.build_summary_payload(stages_planned))

    def persist_stage(self, context: RadarRunContext, stage_name: str, stage_payload: dict, stages_planned: list[str]) -> None:
        context.write_json(context.stage_json_path(stage_name), stage_payload)
        context.stage_states[stage_name] = stage_payload
        self.persist_run(context, stages_planned)
