from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..contracts import StageContract, StageResult
from ..run_context import RadarRunContext, now_text


def run_stage(context: RadarRunContext, contract: StageContract) -> StageResult:
    started_at = now_text()
    started_dt = datetime.fromisoformat(started_at)
    published_key = "powerbi" if context.mode == "controlled" else "experimental"
    powerbi_outputs = list(context.published_outputs.get(published_key, []))
    inputs = {"published_outputs": powerbi_outputs, "mode": context.mode}

    if context.dry_run:
        finished_at = now_text()
        return StageResult(
            stage_name="report",
            status="skipped",
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
            inputs=inputs,
            outputs={"planned_targets": str(context.published_report_inputs_dir)},
            artifacts=[],
            metrics={},
            warnings=[],
            errors=[],
            notes=["Dry-run: no se generó paquete de insumos para reporte."],
            commands=[],
        )

    if not powerbi_outputs:
        finished_at = now_text()
        return StageResult(
            stage_name="report",
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
            inputs=inputs,
            outputs={},
            artifacts=[],
            metrics={},
            warnings=[],
            errors=["No existen salidas publicadas en powerbi para empaquetar insumos de reporte."],
            notes=[],
            commands=[],
        )

    if context.mode == "experimental":
        manifest_path = context.published_report_inputs_dir / "report_inputs_manifest.json"
        manifest_payload = {
            "run_id": context.run_id,
            "week": context.week.slug,
            "mode": context.mode,
            "generated_at": now_text(),
            "status": "skipped",
            "notes": [
                "La etapa de reporte no publica paquete final en modo experimental.",
                "Los artefactos experimentales quedan disponibles bajo published/experimental.",
            ],
        }
        manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        context.published_outputs["report_inputs"] = [str(manifest_path)]
        finished_at = now_text()
        return StageResult(
            stage_name="report",
            status="skipped",
            started_at=started_at,
            finished_at=finished_at,
            duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
            inputs=inputs,
            outputs={"report_inputs_manifest": str(manifest_path)},
            artifacts=[str(manifest_path)],
            metrics={"published_inputs": len(powerbi_outputs)},
            warnings=["Modo experimental: se omite empaquetado de reporte final."],
            errors=[],
            notes=["La separación entre controlled y experimental evita publicar insumos de reporte como si fueran operativos."],
            commands=[],
        )

    manifest_path = context.published_report_inputs_dir / "report_inputs_manifest.json"
    overview_path = context.published_report_inputs_dir / "report_inputs_overview.md"

    manifest_payload = {
        "run_id": context.run_id,
        "week": context.week.slug,
        "generated_at": now_text(),
        "status": "stubbed",
        "report_inputs": powerbi_outputs,
        "notes": [
            "No existe todavía un generador final de reporte dentro del flujo canónico.",
            "Este paquete define el contrato de entrada para la capa de reporte futura.",
        ],
    }
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    overview_path.write_text(
        "\n".join(
            [
                "# Report Inputs",
                "",
                f"- run_id: `{context.run_id}`",
                f"- week: `{context.week.slug}`",
                f"- generated_at: `{manifest_payload['generated_at']}`",
                "",
                "## Published Inputs",
                *[f"- `{path}`" for path in powerbi_outputs],
                "",
                "## Status",
                "- `stubbed`: la corrida deja insumos auditables pero no compone aún el reporte final.",
            ]
        ),
        encoding="utf-8",
    )
    context.published_outputs["report_inputs"] = [str(manifest_path), str(overview_path)]

    finished_at = now_text()
    return StageResult(
        stage_name="report",
        status="stubbed",
        started_at=started_at,
        finished_at=finished_at,
        duration_sec=round((datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3),
        inputs=inputs,
        outputs={
            "report_inputs_manifest": str(manifest_path),
            "report_inputs_overview": str(overview_path),
        },
        artifacts=[str(manifest_path), str(overview_path)],
        metrics={"published_inputs": len(powerbi_outputs)},
        warnings=["La etapa de reporte queda como stub controlado hasta integrar el generador final."],
        errors=[],
        notes=["El contrato de salida ya existe y puede ser consumido por una futura automatización de reporte."],
        commands=[],
    )
