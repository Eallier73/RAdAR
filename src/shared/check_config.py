"""
Checker standalone de configuracion — RAdAR.

Verifica que secrets, state y paths esten listos antes de correr el pipeline.
No requiere --week ni contexto de corrida.

USO:
    conda run -n RadaR_3_11 python -m src.shared.check_config
    conda run -n RadaR_3_11 python -m src.shared.check_config --sources facebook twitter
    conda run -n RadaR_3_11 python -m src.shared.check_config --sources youtube medios

CODIGOS DE SALIDA:
    0: Todo listo.
    1: Uno o mas componentes bloqueados.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .runtime_paths import DOT_ENV_PATH, TWITTER_STATE_PATH
from .secrets import SECRETS_BY_SOURCE, check_secrets_for_source, load_env

SOURCE_NAMES = ("facebook", "twitter", "youtube", "medios")

_OK   = "\u2713"  # ✓
_FAIL = "\u2717"  # ✗
_WARN = "\u26a0"  # ⚠


def _check_dot_env() -> dict:
    exists = DOT_ENV_PATH.exists()
    loaded = load_env()  # Intentar cargar (idempotente si ya se cargo)
    return {
        "path": str(DOT_ENV_PATH),
        "exists": exists,
        "loaded": loaded or exists,  # Podria haber sido cargado al importar
    }


def _check_twitter_state() -> dict:
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


def _check_source(source: str) -> dict:
    """Verifica precondiciones de una fuente especifica."""
    if source == "twitter":
        state = _check_twitter_state()
        ready = state["exists"] and state["readable"]
        issues = []
        if not state["exists"]:
            issues.append(
                f"Falta {TWITTER_STATE_PATH}. "
                "Genera x_state.json con el script de login de Playwright "
                "(ver docs/operations/secrets_and_runtime.md)."
            )
        elif not state["readable"]:
            issues.append(
                f"x_state.json existe pero esta vacio o no es legible: {TWITTER_STATE_PATH}"
            )
        return {
            "source": source,
            "ready": ready,
            "secrets": {},
            "state": state,
            "issues": issues,
        }

    secrets = check_secrets_for_source(source)
    missing = [name for name, available in secrets.items() if not available]
    ready = len(missing) == 0
    issues = []
    for name in missing:
        issues.append(
            f"Variable de entorno faltante: {name}. "
            f"Agrega '{name}=tu_valor' en {DOT_ENV_PATH}."
        )
    return {
        "source": source,
        "ready": ready,
        "secrets": secrets,
        "state": None,
        "issues": issues,
    }


def run_check(sources: list[str]) -> dict:
    """Ejecuta el chequeo completo y devuelve el resultado estructurado."""
    env_check = _check_dot_env()
    results = {}
    for source in sources:
        results[source] = _check_source(source)

    all_ready = all(r["ready"] for r in results.values())
    return {
        "dot_env": env_check,
        "sources": results,
        "all_ready": all_ready,
    }


def _print_report(check: dict) -> None:
    env = check["dot_env"]
    icon = _OK if env["exists"] else _WARN
    print(f"\n{icon}  .env: {env['path']}", end="")
    print(" [encontrado]" if env["exists"] else " [no encontrado — se usaran solo variables del entorno]")
    print()

    for source, result in check["sources"].items():
        icon = _OK if result["ready"] else _FAIL
        print(f"  {icon}  {source.upper()}")

        # Secrets
        if result["secrets"]:
            for name, available in result["secrets"].items():
                si = _OK if available else _FAIL
                print(f"       {si}  {name}", end="")
                print(" [disponible]" if available else " [FALTANTE]")

        # State
        if result["state"] is not None:
            st = result["state"]
            si = _OK if st["exists"] and st["readable"] else _FAIL
            print(f"       {si}  x_state.json ({st['path']})", end="")
            if st["exists"] and st["readable"]:
                print(f" [{st['size_bytes']} bytes]")
            elif st["exists"]:
                print(" [existe pero vacio/ilegible]")
            else:
                print(" [NO EXISTE]")

        # Sin requisitos
        if not result["secrets"] and result["state"] is None:
            print("       (sin requisitos de credenciales)")

        # Issues
        if result["issues"]:
            for issue in result["issues"]:
                print(f"       {_FAIL}  {issue}")

        print()

    if check["all_ready"]:
        print(f"{_OK}  Todo listo para correr el pipeline.\n")
    else:
        blocked = [s for s, r in check["sources"].items() if not r["ready"]]
        print(f"{_FAIL}  Fuentes bloqueadas: {', '.join(blocked)}")
        print("   Corrige los errores anteriores o usa --allow-partial al correr el pipeline.\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verifica que secrets, state y paths esten listos para correr el pipeline RAdAR. "
            "Sin efectos secundarios: solo lee, nunca escribe."
        )
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=SOURCE_NAMES,
        default=list(SOURCE_NAMES),
        metavar="SOURCE",
        help=f"Fuentes a verificar. Default: todas ({' '.join(SOURCE_NAMES)})",
    )
    args = parser.parse_args()

    check = run_check(args.sources)
    _print_report(check)
    return 0 if check["all_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
