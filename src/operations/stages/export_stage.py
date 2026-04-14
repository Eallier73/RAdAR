from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import DEFAULT_EXPORT_FILES
from ..contracts import StageContract, StageResult
from ..run_context import RadarRunContext, now_text


def _copy_file(source: Path, target: Path) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return {
        "source": str(source),
        "target": str(target),
        "size_bytes": target.stat().st_size,
    }


def run_stage(context: RadarRunContext, contract: StageContract) -> StageResult:
    started_at = now_text()
    started_dt = datetime.fromisoformat(started_at)
    warnings: list[str] = []
    errors: list[str] = []
    artifacts: list[str] = []
    published: list[str] = []
    exports: dict[str, Any] = {}
    target_dir = context.published_powerbi_dir if context.mode == "controlled" else context.published_experimental_dir
    output_key = "powerbi" if context.mode == "controlled" else "experimental"

    inputs = {
        "default_export_files": {name: str(path) for name, path in DEFAULT_EXPORT_FILES.items()},
        "modeling_state": context.stage_states.get("modeling", {}),
    }

    if context.dry_run:
        finished_at = now_text()
        return StageResult(
            stage_name="export",
            status="skipped",
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
            inputs=inputs,
            outputs={"planned_targets": str(target_dir), "mode": context.mode},
            artifacts=[],
            metrics={},
            warnings=[],
            errors=[],
            notes=["Dry-run: no se copiaron salidas publicadas."],
            commands=[],
        )

    for label, source in DEFAULT_EXPORT_FILES.items():
        if not source.exists():
            errors.append(f"Falta artefacto base para exportación: {source}")
            continue
        target = target_dir / source.name
        exports[label] = _copy_file(source, target)
        artifacts.append(str(target))
        published.append(str(target))

    modeling_run_dir = context.stage_states.get("modeling", {}).get("outputs", {}).get("model_run_dir")
    if modeling_run_dir:
        run_dir = Path(modeling_run_dir)
        if run_dir.exists():
            modeling_target_dir = target_dir / "modeling" / run_dir.name
            modeling_target_dir.mkdir(parents=True, exist_ok=True)
            copied = []
            for source_path in sorted(run_dir.glob("*")):
                if not source_path.is_file():
                    continue
                copied_payload = _copy_file(source_path, modeling_target_dir / source_path.name)
                copied.append(copied_payload)
                artifacts.append(copied_payload["target"])
                published.append(copied_payload["target"])
            exports["modeling_run"] = {"run_dir": str(run_dir), "files": copied}
        else:
            warnings.append(f"El directorio de modelado referido ya no existe: {run_dir}")
    else:
        warnings.append("No se encontró model_run_dir en el estado de la corrida; se exportaron solo tablas base.")

    manifest_name = "powerbi_export_manifest.json" if context.mode == "controlled" else "experimental_export_manifest.json"
    manifest_path = target_dir / manifest_name
    manifest_payload = {
        "run_id": context.run_id,
        "week": context.week.slug,
        "mode": context.mode,
        "published_at": now_text(),
        "exports": exports,
    }
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    artifacts.append(str(manifest_path))
    published.append(str(manifest_path))
    context.published_outputs[output_key] = published

    if errors and not exports:
        status = "failed"
    elif errors:
        status = "partial_success"
    else:
        status = "success"

    finished_at = now_text()
    return StageResult(
        stage_name="export",
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
        inputs=inputs,
        outputs={"exports": exports, "manifest_path": str(manifest_path)},
        artifacts=artifacts,
        metrics={"published_files": len(published)},
        warnings=warnings,
        errors=errors,
        notes=["La exportación publica una ruta estable para consumo posterior, en particular Power BI."],
        commands=[],
    )
