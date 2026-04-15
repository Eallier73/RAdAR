"""
Capa central de secrets y configuracion de entorno — RAdAR.

Carga .env desde la raiz del repo una sola vez al importar.
Provee validacion de secretos sin exponer valores.
Reutilizable por extractores y orquestador.

USO TIPICO:
    # En un extractor:
    from src.shared.secrets import require_secret, get_secret

    api_key = require_secret("YOUTUBE_API_KEY", component="youtube_extractor")
    token    = require_secret("APIFY_TOKEN",      component="facebook_extractor")

    # Solo verificar disponibilidad (sin lanzar excepcion):
    if not get_secret("APIFY_TOKEN"):
        print("APIFY_TOKEN no configurada")
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# ── Paths canónicos ─────────────────────────────────────────────────────────
_REPO_ROOT: Path = Path(__file__).resolve().parents[2]
_DOT_ENV_PATH: Path = _REPO_ROOT / ".env"

# ── Carga de .env ─────────────────────────────────────────────────────────────
_env_loaded: bool = False


def _parse_dot_env(path: Path) -> None:
    """Parser mínimo de .env: KEY=value, KEY="value", KEY='value'. Sin dependencias externas."""
    with path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            # Quitar comillas si las hay
            value = value.strip()
            if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
                value = value[1:-1]
            # Las variables ya presentes en el entorno tienen prioridad
            if key and key not in os.environ:
                os.environ[key] = value


def load_env(force: bool = False) -> bool:
    """
    Carga .env desde la raiz del repo si existe y no se ha cargado todavia.

    Args:
        force: Si True, recarga aunque ya se haya cargado antes.

    Returns:
        True si se cargo el archivo, False si no existe o ya estaba cargado.
    """
    global _env_loaded
    if _env_loaded and not force:
        return False
    if _DOT_ENV_PATH.exists():
        _parse_dot_env(_DOT_ENV_PATH)
        _env_loaded = True
        return True
    _env_loaded = True  # Marcar como "intentado" aunque no exista
    return False


# Carga automatica al importar el modulo
load_env()


# ── Secretos requeridos por fuente ──────────────────────────────────────────
#
# "medios" usa Google News RSS gratuito — sin API key.
# "twitter" usa Playwright state (x_state.json) — sin env var.
# "facebook" requiere SERPER_API_KEY (busqueda URL) + APIFY_TOKEN (comentarios).
# "youtube" requiere YOUTUBE_API_KEY.
#
SECRETS_BY_SOURCE: dict[str, list[str]] = {
    "facebook": ["SERPER_API_KEY", "APIFY_TOKEN"],
    "twitter":  [],
    "youtube":  ["YOUTUBE_API_KEY"],
    "medios":   [],
}


# ── API publica ──────────────────────────────────────────────────────────────

def get_secret(name: str) -> str | None:
    """
    Devuelve el valor del secreto o None si no esta configurado.
    No lanza excepcion. No expone el valor en ninguna salida.
    """
    return os.environ.get(name) or None


def require_secret(name: str, component: str | None = None) -> str:
    """
    Devuelve el valor del secreto.
    Lanza ValueError con mensaje claro si falta o esta vacio.
    No expone el valor en el mensaje de error.

    Args:
        name:      Nombre de la variable de entorno.
        component: Nombre del extractor/componente que la necesita (para el mensaje).

    Raises:
        ValueError: Si la variable no esta definida o esta vacia.
    """
    value = os.environ.get(name)
    if not value:
        where = f" (requerido por {component})" if component else ""
        raise ValueError(
            f"Variable de entorno requerida no encontrada: {name}{where}. "
            f"Configura '{name}=tu_valor' en {_DOT_ENV_PATH} "
            f"o exportala como variable de entorno."
        )
    return value


def check_secrets(names: list[str]) -> dict[str, bool]:
    """
    Verifica disponibilidad de multiples secretos.
    Devuelve {nombre: disponible_bool} sin exponer valores.
    """
    return {name: bool(os.environ.get(name)) for name in names}


def check_secrets_for_source(source: str) -> dict[str, bool]:
    """
    Verifica disponibilidad de todos los secretos requeridos por una fuente.
    Devuelve {nombre: disponible_bool}.
    """
    names = SECRETS_BY_SOURCE.get(source, [])
    return check_secrets(names)


def source_secrets_ready(source: str) -> bool:
    """True si todos los secretos requeridos para la fuente estan disponibles."""
    return all(check_secrets_for_source(source).values())


def secrets_summary() -> dict[str, Any]:
    """
    Resumen de estado de secretos por fuente para reporting/preflight.
    No expone valores, solo disponibilidad booleana.
    """
    summary: dict[str, Any] = {}
    for source, names in SECRETS_BY_SOURCE.items():
        if not names:
            summary[source] = {"secrets_required": [], "all_available": True, "detail": {}}
        else:
            detail = check_secrets(names)
            summary[source] = {
                "secrets_required": names,
                "all_available": all(detail.values()),
                "detail": detail,
            }
    return summary
