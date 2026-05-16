"""
Checker standalone de configuracion — RAdAR.

Verifica que secrets, state, paths y directorios de runtime esten listos
antes de correr el pipeline. No requiere --week ni contexto de corrida.

USO:
    conda run -n radar-ops-py311 python -m src.shared.check_config
    conda run -n radar-ops-py311 python -m src.shared.check_config --sources facebook twitter
    conda run -n radar-ops-py311 python -m src.shared.check_config --sources youtube medios
    conda run -n radar-ops-py311 python -m src.shared.check_config --ensure-dirs

CODIGOS DE SALIDA:
    0: Todo listo.
    1: Uno o mas componentes bloqueados.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .runtime_paths import (
    CACHE_DIR,
    DOT_ENV_PATH,
    LOGS_PREPROCESSING_DIR,
    RAW_WEEKLY_ROOT,
    STATE_DIR,
    TEXT_WEEKLY_ROOT,
    TWITTER_STATE_PATH,
)
from .secrets import SECRETS_BY_SOURCE, check_secrets_for_source, load_env

SOURCE_NAMES = ("facebook", "twitter", "youtube", "medios")

_OK   = "\u2713"  # ✓
_FAIL = "\u2717"  # ✗
_WARN = "\u26a0"  # ⚠

# Directorios de runtime que deben existir para operacion limpia.
# Se verifican (y opcionalmente crean) independientemente de los secrets.
RUNTIME_DIRS: list[Path] = [
    STATE_DIR,
    CACHE_DIR,
    LOGS_PREPROCESSING_DIR,
    RAW_WEEKLY_ROOT,
    TEXT_WEEKLY_ROOT,
]


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


def _check_runtime_dirs(ensure: bool = False) -> list[dict]:
    """
    Verifica existencia de directorios de runtime.

    Si ensure=True, crea los que no existen (mkdir -p equivalente).
    Nunca falla: errores de creacion se reportan como advertencias.
    """
    results = []
    for d in RUNTIME_DIRS:
        existed = d.exists()
        created = False
        create_error = None
        if ensure and not existed:
            try:
                d.mkdir(parents=True, exist_ok=True)
                created = True
            except OSError as exc:
                create_error = str(exc)
        results.append({
            "path": str(d),
            "existed": existed,
            "created": created,
            "error": create_error,
        })
    return results


def run_check(sources: list[str], ensure_dirs: bool = False) -> dict:
    """Ejecuta el chequeo completo y devuelve el resultado estructurado."""
    env_check = _check_dot_env()
    results = {}
    for source in sources:
        results[source] = _check_source(source)

    runtime_dirs = _check_runtime_dirs(ensure=ensure_dirs)

    all_ready = all(r["ready"] for r in results.values())
    return {
        "dot_env": env_check,
        "sources": results,
        "runtime_dirs": runtime_dirs,
        "ensure_dirs": ensure_dirs,
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

    # Directorios de runtime
    dirs = check.get("runtime_dirs", [])
    if dirs:
        print("  Directorios de runtime:")
        for d in dirs:
            if d["error"]:
                icon = _FAIL
                suffix = f" [ERROR al crear: {d['error']}]"
            elif d["created"]:
                icon = _OK
                suffix = " [creado]"
            elif d["existed"]:
                icon = _OK
                suffix = " [ok]"
            else:
                icon = _WARN
                suffix = " [no existe — usa --ensure-dirs para crearlo]"
            print(f"       {icon}  {d['path']}{suffix}")
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
            "Sin efectos secundarios por defecto: solo lee, nunca escribe. "
            "Con --ensure-dirs: crea los directorios de runtime que falten."
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
    parser.add_argument(
        "--ensure-dirs",
        action="store_true",
        default=False,
        help=(
            "Crea los directorios de runtime que no existan "
            "(artifacts/state, artifacts/cache, artifacts/logs/preprocessing, "
            "data/raw/radar_weekly_flat, data/text/radar_weekly_flat)."
        ),
    )
    args = parser.parse_args()

    check = run_check(args.sources, ensure_dirs=args.ensure_dirs)
    _print_report(check)
    return 0 if check["all_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
