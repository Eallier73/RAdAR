"""
Etapa de preflight — RAdAR pipeline.

Valida antes de correr extraccion:
  - Secrets requeridos por cada fuente activa.
  - State persistente de Twitter/X (x_state.json).
  - Rutas de runtime clave.

Comportamiento:
  - Todos listos                       → status="success"
  - Alguna fuente bloqueada + allow_partial + otras listas  → status="partial_success",
                                         actualiza context.sources_effective
  - Alguna fuente bloqueada sin escape  → status="failed"

No hace login ni gestiona autenticacion. Solo verifica y reporta.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from src.shared.runtime_paths import TWITTER_STATE_PATH, RAW_WEEKLY_ROOT
from src.shared.secrets import check_secrets_for_source, SECRETS_BY_SOURCE

from ..config import OPERATIONS_ARTIFACTS_ROOT
from ..contracts import StageContract, StageResult
from ..run_context import RadarRunContext, now_text


# ── Chequeos por fuente ──────────────────────────────────────────────────────

def _check_twitter_state() -> dict[str, Any]:
    exists = TWITTER_STATE_PATH.exists()
    readable = False
    size_bytes = None
    if exists:
        try:
            size_bytes = TWITTER_STATE_PATH.stat().st_size
            readable = size_bytes > 0
        except OSError:
            readable = False
    return {
        "path": str(TWITTER_STATE_PATH),
        "exists": exists,
        "readable": readable,
        "size_bytes": size_bytes,
    }


def _check_source_preconditions(source: str) -> dict[str, Any]:
    """
    Verifica precondiciones de una fuente.
    Devuelve: {ready, secrets, state, issues}
    """
    if source == "twitter":
        state = _check_twitter_state()
        ready = state["exists"] and state["readable"]
        issues: list[str] = []
        if not state["exists"]:
            issues.append(
                f"Falta x_state.json en {TWITTER_STATE_PATH}. "
                "Genera el state con el script de login de Playwright "
                "(ver docs/operations/secrets_and_runtime.md)."
            )
        elif not state["readable"]:
            issues.append(
                f"x_state.json existe pero esta vacio o no es legible: {TWITTER_STATE_PATH}"
            )
        return {"source": source, "ready": ready, "secrets": {}, "state": state, "issues": issues}

    # Fuentes con secretos de entorno
    secrets = check_secrets_for_source(source)
    missing = [name for name, available in secrets.items() if not available]
    ready = len(missing) == 0
    issues = [
        f"Variable de entorno faltante: {name}. Agrega '{name}=tu_valor' en .env."
        for name in missing
    ]
    return {"source": source, "ready": ready, "secrets": secrets, "state": None, "issues": issues}


def _check_runtime_paths() -> dict[str, Any]:
    checks = {
        "raw_weekly_root": {
            "path": str(RAW_WEEKLY_ROOT),
            "exists": RAW_WEEKLY_ROOT.exists(),
        },
        "operations_artifacts_root": {
            "path": str(OPERATIONS_ARTIFACTS_ROOT),
            "exists": OPERATIONS_ARTIFACTS_ROOT.exists() or True,  # Se crea en cada run
        },
        "twitter_state_dir": {
            "path": str(TWITTER_STATE_PATH.parent),
            "exists": TWITTER_STATE_PATH.parent.exists(),
        },
    }
    return checks


# ── Stage runner ─────────────────────────────────────────────────────────────

def run_stage(context: RadarRunContext, contract: StageContract) -> StageResult:
    started_at = now_text()
    started_dt = datetime.fromisoformat(started_at)

    source_checks: dict[str, Any] = {}
    sources_blocked: list[str] = []
    all_issues: list[str] = []

    for source in list(context.sources_effective):
        check = _check_source_preconditions(source)
        source_checks[source] = check
        if not check["ready"]:
            sources_blocked.append(source)
            all_issues.extend(check["issues"])

    path_checks = _check_runtime_paths()

    warnings: list[str] = []
    errors: list[str] = []

    if sources_blocked:
        if context.allow_partial and len(sources_blocked) < len(context.sources_effective):
            # Al menos una fuente lista: continuar sin las bloqueadas
            original = list(context.sources_effective)
            context.sources_effective = [s for s in context.sources_effective if s not in sources_blocked]
            warnings.append(
                f"Fuentes bloqueadas por precondicion faltante: {sources_blocked}. "
                f"Pipeline continuara con: {context.sources_effective}."
            )
            status = "partial_success"
        else:
            errors.extend(all_issues)
            if len(sources_blocked) == len(context.sources_effective):
                errors.append("Todas las fuentes estan bloqueadas. No es posible continuar.")
            status = "failed"
    else:
        status = "success"

    outputs: dict[str, Any] = {
        "sources": source_checks,
        "runtime_paths": path_checks,
        "sources_requested": list(context.sources_requested),
        "sources_effective_after_preflight": list(context.sources_effective),
    }

    finished_at = now_text()
    return StageResult(
        stage_name="preflight",
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_sec=round(
            (datetime.fromisoformat(finished_at) - started_dt).total_seconds(), 3
        ),
        inputs={
            "sources_requested": list(context.sources_requested),
            "fail_fast": context.fail_fast,
            "allow_partial": context.allow_partial,
        },
        outputs=outputs,
        artifacts=[],
        metrics={
            "sources_total": len(context.sources_requested),
            "sources_ready": len(context.sources_effective),
            "sources_blocked": len(sources_blocked),
        },
        warnings=warnings,
        errors=errors,
        notes=[
            "Preflight solo verifica — no hace login ni modifica credenciales.",
            "Para configurar credenciales: ver docs/operations/secrets_and_runtime.md.",
            "Para inicializar state de Twitter/X: ver docs/operations/secrets_and_runtime.md#twitter-state.",
        ],
        commands=[],
    )
