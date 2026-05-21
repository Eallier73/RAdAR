#!/usr/bin/env python3
"""
Nucleo reusable del extractor institucional de Facebook para Radar.

La base metodologica es `03_facebook_extractor_apify_Tampico.py`, pero la
implementacion se reorganiza como componente profesional de automatizacion:
configuracion por CLI, sampling durante la extraccion, trazabilidad fuerte,
artefactos auditables y contrato de salida estable para integracion futura con
preprocessing y orquestadores.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import platform
import shutil
import socket
import sys
import time
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, timedelta, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import parse_qs, urlparse

import pandas as pd

try:
    from apify_client import ApifyClient
except ImportError as exc:  # pragma: no cover - depende del entorno
    ApifyClient = None  # type: ignore[assignment]
    APIFY_IMPORT_ERROR: Exception | None = exc
else:
    APIFY_IMPORT_ERROR = None


def resolve_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in (current.parent, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current.parents[4]


ROOT_DIR = resolve_repo_root()
DEFAULT_OUTPUT_DIR = ROOT_DIR / "Datos_RAdAR" / "Facebook"
DEFAULT_PAGES_FILE = Path(__file__).with_name("facebook_institutional_pages_canonical.csv")
SCRIPT_VERSION = "2.0.0"
SCRIPT_COMPONENT = "radar.facebook_institutional_extractor"
SOURCE_PLATFORM = "facebook"
SOURCE_SCOPE = "institutional_tampico"

WEEK_MODE_EXACT = "exact_range"
WEEK_MODE_CANONICAL = "canonical_w_tue"
WEEK_NAME_MODE_CHOICES = (WEEK_MODE_EXACT, WEEK_MODE_CANONICAL)

DEFAULT_RUN_ID = "facebook_institutional_extract"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_SEED = 42
DEFAULT_WEEKLY_COMMENT_CAP_PER_PAGE = 100
DEFAULT_MAX_POSTS_PER_PAGE_PER_WEEK = 8
DEFAULT_MAX_COMMENTS_PER_POST = 25
DEFAULT_DISCOVERY_MULTIPLIER = 3
DEFAULT_MIN_DISCOVERY_POSTS = 15
DEFAULT_DISCOVERY_RESULTS_PER_PAGE = 100
DEFAULT_ACTOR_POSTS = "apify/facebook-posts-scraper"
DEFAULT_ACTOR_COMMENTS = "apify/facebook-comments-scraper"
DEFAULT_APIFY_TOKEN_ENV = "APIFY_TOKEN"
DEFAULT_MEMORY_MB = 2048
DEFAULT_TIMEOUT_SECONDS = 1800

MAIN_CSV_PREFIX = "facebook_institutional_raw"
POSTS_FILENAME = "posts_selected.csv"
COMMENTS_FILENAME = "comments_selected.csv"
AUDIT_FILENAME = "selection_audit.csv"
SUMMARY_FILENAME = "summary.json"
METADATA_FILENAME = "metadata_run.json"
PARAMS_FILENAME = "parametros_run.json"
MANIFEST_FILENAME = "manifest.json"
ERRORS_FILENAME = "errores_detectados.json"
LOG_FILENAME = "run.log"

CANONICAL_PAGES = {
    "964877296876825": {"label": "MonicaVillarreal", "handle": "monicavtampico"},
    "474462132406835": {"label": "GobiernoTampico", "handle": "TampicoGob"},
}

SAMPLING_MODE = "two_level_sampling_posts_then_comments_with_weekly_page_cap"
POST_SELECTION_RULE = "temporal_even_spacing_by_created_time_with_seed_tiebreak"
COMMENT_PROCESSING_RULE = "reverse_chronological_selected_posts_until_page_cap"

ABSORBED_COMMENTS_LOGIC = [
    "extraer_texto_post_desde_item: recuperacion multi-campo de texto del post desde items del actor.",
    "procesar_items_posts: priorizacion del texto mas informativo y relleno de metadata faltante del post padre.",
]

DISCARDED_COMMENTS_LOGIC = [
    "Dependencia de CSV manual intermedio como insumo obligatorio: descartada para mantener pipeline directo.",
    "Enriquecimiento del post padre via scraping adicional de URL Facebook: descartado por costo y fragilidad operativa.",
    "Cualquier logica que aumente llamadas sin mejorar materialmente trazabilidad/costo: descartada.",
]

MAIN_COLUMNS = [
    "run_id",
    "week_name",
    "source_platform",
    "source_scope",
    "page_id",
    "page_label",
    "post_id",
    "comment_id",
    "parent_post_id",
    "record_type",
    "post_url",
    "comment_url",
    "created_time",
    "week_label",
    "text",
    "post_text",
    "comment_count_post",
    "selection_stage",
    "selection_rule",
    "weekly_page_cap",
    "max_comments_per_post",
    "page_week_counter",
    "post_comment_counter",
    "status_extraccion",
    "error_type",
    "error_detail",
    "seed",
    "selected_for_comment_sampling",
    "post_selection_rank",
    "processing_rank",
    "comments_requested_for_post",
    "comments_retrieved_for_post",
    "enrichment_applied",
    "enrichment_source",
    "absorbed_comment_logic",
    "is_reply",
]

AUDIT_COLUMNS = [
    "run_id",
    "week_name",
    "page_id",
    "page_label",
    "post_id",
    "post_url",
    "created_time",
    "week_label",
    "comment_count_post",
    "selection_stage",
    "selection_rule",
    "selected_for_comment_sampling",
    "selection_rank",
    "processing_rank",
    "status_extraccion",
    "decision_reason",
    "seed",
]


class ExitCode(IntEnum):
    SUCCESS = 0
    PARTIAL_SUCCESS = 1
    FAILED_CONFIG = 2
    FAILED_API = 3
    FAILED_WRITE = 4


class FacebookExtractorError(Exception):
    """Base de errores del extractor institucional."""


class ConfigurationError(FacebookExtractorError):
    """Error fatal de configuracion."""


class ApiAuthenticationError(FacebookExtractorError):
    """Error fatal de token o autenticacion con Apify."""


class ApiExecutionError(FacebookExtractorError):
    """Error fatal de ejecucion general contra la plataforma."""


class PlatformDependencyError(FacebookExtractorError):
    """Error fatal por dependencias requeridas para el modo elegido."""


class OutputWriteError(FacebookExtractorError):
    """Error fatal de persistencia."""


@dataclass(frozen=True)
class WeekPartition:
    start_date: date
    end_date: date
    week_name: str
    naming_start_date: date
    naming_end_date: date


@dataclass(frozen=True)
class PageTarget:
    page_id: str
    page_label: str
    page_handle: str
    page_url: str
    enabled: bool = True
    source: str = "canonical"
    notes: str = ""


@dataclass(frozen=True)
class ResolvedConfig:
    script_name: str
    script_path: Path
    helper_module_path: Path
    entrypoint_alias: str
    script_version: str
    since: date
    until: date
    week_name_mode: str
    week_partition: WeekPartition
    output_root_dir: Path
    week_dir: Path
    run_dir: Path
    run_id: str
    run_timestamp: str
    pages: list[PageTarget]
    pages_source: str
    apify_token_env: str
    actor_name_posts: str
    actor_name_comments: str
    memory_mb: int
    timeout_seconds: int
    seed: int
    weekly_comment_cap_per_page: int
    max_posts_per_page_per_week: int
    max_comments_per_post: int
    discovery_results_per_page: int
    include_replies: bool
    log_level: str
    overwrite: bool
    publish_canonical: bool
    dry_run: bool
    config_file: Path | None = None


@dataclass(frozen=True)
class ArtifactRecord:
    name: str
    artifact_type: str
    path: str
    description: str
    timestamp: str
    size_bytes: int = 0


@dataclass(frozen=True)
class ErrorRecord:
    stage: str
    scope: str
    message: str
    timestamp: str
    fatal: bool
    error_type: str
    page_id: str | None = None
    page_label: str | None = None
    post_id: str | None = None
    comment_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CandidatePost:
    page_id: str
    page_label: str
    page_url: str
    post_id: str
    post_url: str
    created_time: str
    created_dt: datetime | None
    week_label: str
    post_text: str
    comment_count_post: int | None
    reaction_count_post: int | None
    author_name: str
    selection_stage: str = "candidate_detected"
    selection_rule: str = POST_SELECTION_RULE
    selected_for_comment_sampling: bool = False
    selection_rank: int | None = None
    processing_rank: int | None = None
    comments_requested_for_post: int = 0
    comments_retrieved_for_post: int = 0
    page_week_counter: int | None = None
    status_extraccion: str = "candidate_detected"
    error_type: str = ""
    error_detail: str = ""
    enrichment_applied: bool = False
    enrichment_source: str = ""
    absorbed_comment_logic: str = ""


@dataclass(frozen=True)
class CommentRecord:
    page_id: str
    page_label: str
    post_id: str
    comment_id: str
    parent_post_id: str
    post_url: str
    comment_url: str
    created_time: str
    created_dt: datetime | None
    week_label: str
    text: str
    post_text: str
    comment_count_post: int | None
    selection_stage: str
    selection_rule: str
    weekly_page_cap: int
    max_comments_per_post: int
    page_week_counter: int | None
    post_comment_counter: int | None
    status_extraccion: str
    error_type: str
    error_detail: str
    seed: int
    selected_for_comment_sampling: bool
    post_selection_rank: int | None
    processing_rank: int | None
    comments_requested_for_post: int
    comments_retrieved_for_post: int
    enrichment_applied: bool
    enrichment_source: str
    absorbed_comment_logic: str
    is_reply: bool


@dataclass(frozen=True)
class SelectionAuditRecord:
    run_id: str
    week_name: str
    page_id: str
    page_label: str
    post_id: str
    post_url: str
    created_time: str
    week_label: str
    comment_count_post: int | None
    selection_stage: str
    selection_rule: str
    selected_for_comment_sampling: bool
    selection_rank: int | None
    processing_rank: int | None
    status_extraccion: str
    decision_reason: str
    seed: int


@dataclass(frozen=True)
class CapEvent:
    page_id: str
    page_label: str
    cap_value: int
    comments_saved_when_reached: int
    reached_at_post_id: str
    timestamp: str
    reason: str


@dataclass
class PageExecutionResult:
    page: PageTarget
    status: str
    candidate_posts: list[CandidatePost] = field(default_factory=list)
    selected_posts: list[CandidatePost] = field(default_factory=list)
    comments: list[CommentRecord] = field(default_factory=list)
    selection_audit: list[SelectionAuditRecord] = field(default_factory=list)
    cap_events: list[CapEvent] = field(default_factory=list)
    errors: list[ErrorRecord] = field(default_factory=list)
    total_candidate_posts_detected: int = 0
    total_posts_selected: int = 0
    total_comments_attempted: int = 0
    total_comments_saved: int = 0
    total_comments_skipped_by_cap: int = 0
    total_posts_enriched: int = 0
    total_items_failed: int = 0
    posts_actor_usage_usd: float = 0.0
    comments_actor_usage_usd: float = 0.0


@dataclass
class RunExecutionResult:
    status: str
    exit_code: int
    started_at: str
    finished_at: str
    duration_seconds: float
    page_results: list[PageExecutionResult]
    errors: list[ErrorRecord]
    notes: list[str]
    summary: dict[str, Any]
    metadata: dict[str, Any]
    manifest: list[dict[str, Any]]
    artifact_paths: dict[str, str]


def now_utc_text() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def serialize_for_json(value: Any) -> Any:
    if is_dataclass(value):
        return {key: serialize_for_json(item) for key, item in asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): serialize_for_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize_for_json(item) for item in value]
    return value


def format_spanish_date(raw_date: date) -> str:
    months = {
        1: "enero",
        2: "febrero",
        3: "marzo",
        4: "abril",
        5: "mayo",
        6: "junio",
        7: "julio",
        8: "agosto",
        9: "septiembre",
        10: "octubre",
        11: "noviembre",
        12: "diciembre",
    }
    return f"{raw_date:%d}{months[raw_date.month]}"


def parse_date_str(value: str, field_name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ConfigurationError(f"{field_name} debe usar formato YYYY-MM-DD: {value}") from exc


def resolve_w_tue_end(raw_date: date) -> date:
    return raw_date + timedelta(days=((1 - raw_date.weekday()) % 7))


def resolve_w_tue_start(raw_date: date) -> date:
    return resolve_w_tue_end(raw_date) - timedelta(days=6)


def derive_week_label_from_datetime(value: datetime | None) -> str:
    if value is None:
        return ""
    return resolve_w_tue_end(value.date()).isoformat()


def resolve_week_partition(since: date, until: date, mode: str) -> WeekPartition:
    if mode == WEEK_MODE_EXACT:
        naming_start = since
        naming_end = until
    elif mode == WEEK_MODE_CANONICAL:
        naming_start = resolve_w_tue_start(since)
        naming_end = resolve_w_tue_end(until)
    else:  # pragma: no cover - argparse ya valida
        raise ConfigurationError(f"Modo de nombre semanal no soportado: {mode}")

    label = f"semana_{format_spanish_date(naming_start)}_{format_spanish_date(naming_end)}_{naming_end:%y}"
    week_name = f"{naming_start.isoformat()}_{label}"
    return WeekPartition(
        start_date=since,
        end_date=until,
        week_name=week_name,
        naming_start_date=naming_start,
        naming_end_date=naming_end,
    )


def merge_config_sources(args: argparse.Namespace) -> dict[str, Any]:
    merged = vars(args).copy()
    config_file = merged.get("config_file")
    if not config_file:
        return merged

    config_path = Path(str(config_file)).expanduser().resolve()
    if not config_path.exists():
        raise ConfigurationError(f"No existe --config-file: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ConfigurationError("--config-file debe contener un objeto JSON.")

    for key, value in payload.items():
        if merged.get(key) is None:
            merged[key] = value
    merged["config_file"] = str(config_path)
    return merged


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extractor institucional de Facebook para Radar con sampling integrado a la extraccion.",
    )
    parser.add_argument("--since", default=None, help="Fecha inicial del rango de extraccion en formato YYYY-MM-DD.")
    parser.add_argument("--until", default=None, help="Fecha final inclusiva del rango de extraccion en formato YYYY-MM-DD.")
    parser.add_argument("--before", dest="before", default=None, help="Alias operativo de --until.")
    parser.add_argument("--pages-file", default=None, help="CSV o JSON con paginas institucionales objetivo.")
    parser.add_argument("--page-id", action="append", default=None, help="Filtra una o mas paginas canonicas por ID. Repetible.")
    parser.add_argument("--output-dir", default=None, help="Directorio raiz de salida.")
    parser.add_argument("--run-id", default=None, help="Identificador logico de la corrida.")
    parser.add_argument("--log-level", default=None, help="Nivel de logging: DEBUG, INFO, WARNING o ERROR.")
    parser.add_argument("--overwrite", action="store_true", default=None, help="Permite sobrescribir artefactos canonicos.")
    parser.add_argument("--publish-canonical", action="store_true", default=None, help="Publica una copia canonica semanal en el week_dir.")
    parser.add_argument("--week-name-mode", choices=WEEK_NAME_MODE_CHOICES, default=None, help="Politica de naming semanal.")
    parser.add_argument("--seed", type=int, default=None, help="Semilla reproducible para la seleccion de posts.")
    parser.add_argument("--weekly-comment-cap-per-page", type=int, default=None, help="Cap semanal de comentarios por pagina.")
    parser.add_argument("--max-posts-per-page-per-week", type=int, default=None, help="Maximo de posts candidatos a comments por pagina y semana.")
    parser.add_argument("--max-comments-per-post", type=int, default=None, help="Maximo de comentarios a recuperar por post.")
    parser.add_argument("--discovery-results-per-page", type=int, default=None, help="Profundidad de descubrimiento del actor de posts por pagina. Equivale al maximo de posts del extractor historico.")
    parser.add_argument("--include-replies", action="store_true", default=None, help="Incluye replies si el actor los devuelve. En la configuración canónica quedan activados para preservar comparabilidad histórica.")
    parser.add_argument("--dry-run", action="store_true", default=None, help="No llama a Apify; solo materializa artefactos vacios y metadata.")
    parser.add_argument("--apify-token-env", default=None, help="Nombre de la variable de entorno que contiene el token de Apify.")
    parser.add_argument("--actor-name-posts", default=None, help="Nombre del actor de Apify para descubrir posts.")
    parser.add_argument("--actor-name-comments", default=None, help="Nombre del actor de Apify para bajar comentarios.")
    parser.add_argument("--memory-mb", type=int, default=None, help="Memoria solicitada a la corrida del actor.")
    parser.add_argument("--timeout-seconds", type=int, default=None, help="Timeout maximo de la corrida del actor.")
    parser.add_argument("--config-file", default=None, help="Archivo JSON opcional con configuracion base.")
    return parser.parse_args(argv)


def normalize_target_handle(raw_value: str) -> str:
    value = str(raw_value or "").strip()
    if not value:
        return ""
    if "facebook.com" in value.lower():
        parsed = urlparse(value if "://" in value else f"https://{value.lstrip('/')}")
        path = (parsed.path or "").strip("/")
        if not path:
            return ""
        return path.split("/")[0].lower()
    return value.removeprefix("@").strip("/").lower()


def normalize_page_id(raw_value: str) -> str:
    digits = "".join(ch for ch in str(raw_value).strip() if ch.isdigit())
    return digits


def default_page_url(page_id: str, page_handle: str = "") -> str:
    if page_handle:
        return f"https://www.facebook.com/{page_handle}"
    return f"https://www.facebook.com/profile.php?id={page_id}"


def extract_handle_from_facebook_url(url: str) -> str:
    raw = str(url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = f"https://{raw.lstrip('/')}"
    try:
        parsed = urlparse(raw)
    except Exception:
        return ""
    path = (parsed.path or "").strip("/")
    if not path:
        return ""
    head = path.split("/")[0].strip()
    if not head or head.lower() in {"profile.php", "story.php", "photo.php", "watch"}:
        return ""
    return head.lower()


def raw_facebook_url(url: str) -> str:
    return str(url or "").strip()


def load_pages_from_csv(path: Path) -> list[PageTarget]:
    pages: list[PageTarget] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"page_id", "page_label"}
        if not required.issubset(reader.fieldnames or []):
            raise ConfigurationError(
                f"El archivo de paginas requiere al menos columnas {sorted(required)}: {path}"
            )
        for row in reader:
            page_id = normalize_page_id(row.get("page_id", ""))
            if not page_id:
                continue
            enabled_raw = str(row.get("enabled", "true")).strip().lower()
            enabled = enabled_raw not in {"0", "false", "no", "off"}
            default_meta = CANONICAL_PAGES.get(page_id, {})
            page_label = str(row.get("page_label", "")).strip() or str(default_meta.get("label") or page_id)
            page_handle = normalize_target_handle(
                str(row.get("page_handle", "")).strip() or str(default_meta.get("handle") or "")
            )
            page_url_raw = str(row.get("page_url", "")).strip()
            page_url = page_url_raw or default_page_url(page_id, page_handle)
            if not page_handle:
                page_handle = extract_handle_from_facebook_url(page_url)
            pages.append(
                PageTarget(
                    page_id=page_id,
                    page_label=page_label,
                    page_handle=page_handle,
                    page_url=page_url,
                    enabled=enabled,
                    source=str(path),
                    notes=str(row.get("notes", "")).strip(),
                )
            )
    return pages


def load_pages_from_json(path: Path) -> list[PageTarget]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ConfigurationError("--pages-file en JSON debe contener una lista de paginas.")
    pages: list[PageTarget] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        page_id = normalize_page_id(item.get("page_id", ""))
        if not page_id:
            continue
        enabled = bool(item.get("enabled", True))
        default_meta = CANONICAL_PAGES.get(page_id, {})
        page_label = str(item.get("page_label", "")).strip() or str(default_meta.get("label") or page_id)
        page_handle = normalize_target_handle(
            str(item.get("page_handle", "")).strip() or str(default_meta.get("handle") or "")
        )
        page_url_raw = str(item.get("page_url", "")).strip()
        page_url = page_url_raw or default_page_url(page_id, page_handle)
        if not page_handle:
            page_handle = extract_handle_from_facebook_url(page_url)
        pages.append(
            PageTarget(
                page_id=page_id,
                page_label=page_label,
                page_handle=page_handle,
                page_url=page_url,
                enabled=enabled,
                source=str(path),
                notes=str(item.get("notes", "")).strip(),
            )
        )
    return pages


def load_pages_from_file(path: Path) -> list[PageTarget]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_pages_from_csv(path)
    if suffix == ".json":
        return load_pages_from_json(path)
    raise ConfigurationError(f"Formato de --pages-file no soportado: {path}")


def load_default_pages() -> tuple[list[PageTarget], str]:
    if not DEFAULT_PAGES_FILE.exists():
        pages = [
            PageTarget(
                page_id=page_id,
                page_label=str(meta["label"]),
                page_handle=normalize_target_handle(str(meta["handle"])),
                page_url=default_page_url(page_id, normalize_target_handle(str(meta["handle"]))),
            )
            for page_id, meta in CANONICAL_PAGES.items()
        ]
        return pages, "embedded_default"
    return load_pages_from_file(DEFAULT_PAGES_FILE), str(DEFAULT_PAGES_FILE)


def resolve_pages(merged: dict[str, Any]) -> tuple[list[PageTarget], str]:
    pages_file_raw = merged.get("pages_file")
    if pages_file_raw:
        pages_file = Path(str(pages_file_raw)).expanduser().resolve()
        if not pages_file.exists():
            raise ConfigurationError(f"No existe --pages-file: {pages_file}")
        pages = load_pages_from_file(pages_file)
        pages_source = str(pages_file)
    else:
        pages, pages_source = load_default_pages()

    active_pages = [page for page in pages if page.enabled]
    selected_ids_raw = merged.get("page_id") or []
    selected_ids = {normalize_page_id(value) for value in selected_ids_raw if normalize_page_id(value)}
    if selected_ids:
        active_pages = [page for page in active_pages if page.page_id in selected_ids]
        missing = selected_ids.difference({page.page_id for page in active_pages})
        if missing:
            raise ConfigurationError(
                "Se solicitaron --page-id fuera del set institucional canónico activo: "
                + ", ".join(sorted(missing))
            )

    if not active_pages:
        raise ConfigurationError("La seleccion final de paginas institucionales quedo vacia.")

    invalid_enabled = [page.page_id for page in active_pages if page.page_id not in CANONICAL_PAGES]
    if invalid_enabled:
        raise ConfigurationError(
            "Este componente esta restringido a Facebook institucional de Tampico. "
            "Las paginas activas fuera del set canónico deben permanecer desactivadas: "
            + ", ".join(sorted(invalid_enabled))
        )

    return active_pages, pages_source


def resolve_config(
    args: argparse.Namespace,
    *,
    script_name: str,
    script_path: Path,
    entrypoint_alias: str,
) -> ResolvedConfig:
    merged = merge_config_sources(args)

    since_raw = merged.get("since")
    until_raw = merged.get("until") or merged.get("before")
    if not since_raw or not until_raw:
        raise ConfigurationError("Debes definir --since y --until/--before, o proveerlos en --config-file.")

    since = parse_date_str(str(since_raw), "since")
    until = parse_date_str(str(until_raw), "until")
    if until < since:
        raise ConfigurationError("until no puede ser menor que since.")

    week_name_mode = str(merged.get("week_name_mode") or WEEK_MODE_CANONICAL).strip() or WEEK_MODE_CANONICAL
    week_partition = resolve_week_partition(since, until, week_name_mode)

    pages, pages_source = resolve_pages(merged)

    output_root_dir = Path(str(merged.get("output_dir") or DEFAULT_OUTPUT_DIR)).expanduser().resolve()
    run_id = str(merged.get("run_id") or DEFAULT_RUN_ID).strip() or DEFAULT_RUN_ID
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    week_dir = output_root_dir / week_partition.week_name
    run_dir = week_dir / "runs" / f"{run_id}_{run_timestamp}"

    seed = int(merged.get("seed") if merged.get("seed") is not None else DEFAULT_SEED)
    weekly_cap = int(
        merged.get("weekly_comment_cap_per_page")
        if merged.get("weekly_comment_cap_per_page") is not None
        else DEFAULT_WEEKLY_COMMENT_CAP_PER_PAGE
    )
    max_posts = int(
        merged.get("max_posts_per_page_per_week")
        if merged.get("max_posts_per_page_per_week") is not None
        else DEFAULT_MAX_POSTS_PER_PAGE_PER_WEEK
    )
    max_comments = int(
        merged.get("max_comments_per_post")
        if merged.get("max_comments_per_post") is not None
        else DEFAULT_MAX_COMMENTS_PER_POST
    )
    discovery_results_per_page = int(
        merged.get("discovery_results_per_page")
        if merged.get("discovery_results_per_page") is not None
        else DEFAULT_DISCOVERY_RESULTS_PER_PAGE
    )
    memory_mb = int(merged.get("memory_mb") if merged.get("memory_mb") is not None else DEFAULT_MEMORY_MB)
    timeout_seconds = int(
        merged.get("timeout_seconds") if merged.get("timeout_seconds") is not None else DEFAULT_TIMEOUT_SECONDS
    )

    for field_name, value in {
        "seed": seed,
        "weekly_comment_cap_per_page": weekly_cap,
        "max_posts_per_page_per_week": max_posts,
        "max_comments_per_post": max_comments,
        "discovery_results_per_page": discovery_results_per_page,
        "memory_mb": memory_mb,
        "timeout_seconds": timeout_seconds,
    }.items():
        if value <= 0:
            raise ConfigurationError(f"{field_name} debe ser mayor que 0.")
    if discovery_results_per_page > 100:
        raise ConfigurationError(
            "discovery_results_per_page no puede exceder 100 porque "
            "la ruta canonica conserva ese tope operativo por comparabilidad "
            "historica y costo controlado."
        )

    discovery_results_per_page = max(discovery_results_per_page, max_posts)

    config_file = merged.get("config_file")
    config_file_path = Path(str(config_file)).resolve() if config_file else None

    return ResolvedConfig(
        script_name=script_name,
        script_path=script_path,
        helper_module_path=Path(__file__).resolve(),
        entrypoint_alias=entrypoint_alias,
        script_version=SCRIPT_VERSION,
        since=since,
        until=until,
        week_name_mode=week_name_mode,
        week_partition=week_partition,
        output_root_dir=output_root_dir,
        week_dir=week_dir,
        run_dir=run_dir,
        run_id=run_id,
        run_timestamp=run_timestamp,
        pages=pages,
        pages_source=pages_source,
        apify_token_env=str(merged.get("apify_token_env") or DEFAULT_APIFY_TOKEN_ENV).strip() or DEFAULT_APIFY_TOKEN_ENV,
        actor_name_posts=str(merged.get("actor_name_posts") or DEFAULT_ACTOR_POSTS).strip() or DEFAULT_ACTOR_POSTS,
        actor_name_comments=str(merged.get("actor_name_comments") or DEFAULT_ACTOR_COMMENTS).strip() or DEFAULT_ACTOR_COMMENTS,
        memory_mb=memory_mb,
        timeout_seconds=timeout_seconds,
        seed=seed,
        weekly_comment_cap_per_page=weekly_cap,
        max_posts_per_page_per_week=max_posts,
        max_comments_per_post=max_comments,
        discovery_results_per_page=discovery_results_per_page,
        include_replies=(
            bool(merged.get("include_replies"))
            if merged.get("include_replies") is not None
            else True
        ),
        log_level=str(merged.get("log_level") or DEFAULT_LOG_LEVEL).upper(),
        overwrite=bool(merged.get("overwrite", False)),
        publish_canonical=bool(merged.get("publish_canonical", False)),
        dry_run=bool(merged.get("dry_run", False)),
        config_file=config_file_path,
    )


def setup_logging(log_level: str, log_file: Path | None = None) -> logging.Logger:
    logger = logging.getLogger(SCRIPT_COMPONENT)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logger.level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logger.level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


def configure_output_layout(config: ResolvedConfig) -> None:
    config.week_dir.mkdir(parents=True, exist_ok=True)
    config.run_dir.mkdir(parents=True, exist_ok=True)


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(serialize_for_json(payload), handle, ensure_ascii=False, indent=2)


def dataframe_to_csv(path: Path, dataframe: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False, encoding="utf-8-sig")


def add_artifact_record(records: list[ArtifactRecord], path: Path, artifact_type: str, description: str) -> None:
    size_bytes = path.stat().st_size if path.exists() else 0
    records.append(
        ArtifactRecord(
            name=path.name,
            artifact_type=artifact_type,
            path=str(path),
            description=description,
            timestamp=now_utc_text(),
            size_bytes=size_bytes,
        )
    )


def ensure_publish_target(target_path: Path, overwrite: bool) -> None:
    if target_path.exists() and not overwrite:
        raise OutputWriteError(f"El artefacto canonico ya existe y requiere --overwrite: {target_path}")
    target_path.parent.mkdir(parents=True, exist_ok=True)


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def parse_datetime_value(value: Any) -> datetime | None:
    if value in (None, "", "None", "NaT"):
        return None

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    if isinstance(value, (int, float)):
        raw = float(value)
        if raw > 10_000_000_000:
            raw = raw / 1000.0
        try:
            return datetime.fromtimestamp(raw, tz=timezone.utc)
        except (ValueError, OSError):
            return None

    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    try:
        parsed = pd.to_datetime(text, utc=True, errors="raise")
    except Exception:
        return None
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()


def parse_datetime_from_item(item: dict[str, Any], keys: Sequence[str]) -> datetime | None:
    for key in keys:
        if key in item:
            parsed = parse_datetime_value(item.get(key))
            if parsed is not None:
                return parsed
    return None


def date_in_range(value: datetime | None, since: date, until: date) -> bool:
    if value is None:
        return False
    current = value.date()
    return since <= current <= until


def extract_text_from_posts_actor_item(item: dict[str, Any]) -> str:
    candidates: list[Any] = [
        item.get("text"),
        item.get("postText"),
        item.get("message"),
        item.get("content"),
    ]
    for candidate in candidates:
        text = str(candidate).strip() if isinstance(candidate, str) else ""
        if text:
            return text
    return ""


def extract_text_from_comment_actor_item(item: dict[str, Any]) -> str:
    candidates: list[Any] = [
        item.get("postText"),
        item.get("postMessage"),
        item.get("postDescription"),
        item.get("postContent"),
        item.get("postCaption"),
        item.get("message"),
        item.get("description"),
    ]
    post_obj = item.get("post")
    if isinstance(post_obj, dict):
        candidates.extend(
            [
                post_obj.get("text"),
                post_obj.get("message"),
                post_obj.get("description"),
            ]
        )
    for candidate in candidates:
        text = str(candidate).strip() if isinstance(candidate, str) else ""
        if len(text) >= 5:
            return text
    return ""


def parse_intish(value: Any) -> int | None:
    if value in (None, "", "None", "NaN"):
        return None
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return None


def candidate_belongs_to_target(post_url: str, page_url: str, page: PageTarget) -> bool:
    if not page.page_handle:
        return True

    target_handle = normalize_target_handle(page.page_handle)
    if not target_handle:
        return True

    candidates = {
        extract_handle_from_facebook_url(page_url),
        extract_handle_from_facebook_url(post_url),
    }
    if target_handle in candidates:
        return True

    page_url_l = page_url.lower()
    post_url_l = post_url.lower()
    token = f"/{target_handle}/"
    return token in page_url_l or token in post_url_l


def derive_post_id(item: dict[str, Any], post_url: str) -> str:
    candidates = [
        item.get("postId"),
        item.get("postID"),
        item.get("id"),
        item.get("objectId"),
        item.get("post_id"),
    ]
    for candidate in candidates:
        value = normalize_text(str(candidate)) if candidate is not None else ""
        if value and value.lower() not in {"none", "nan"}:
            return value

    parsed = urlparse(post_url)
    query = parse_qs(parsed.query)
    for key in ("story_fbid", "fbid", "v"):
        values = query.get(key)
        if values:
            return values[0]

    path_parts = [part for part in parsed.path.split("/") if part]
    markers = {"posts", "videos", "photos", "permalink"}
    for index, part in enumerate(path_parts[:-1]):
        if part.lower() in markers:
            return path_parts[index + 1]
    if path_parts:
        return path_parts[-1]
    return hashlib.sha1(post_url.encode("utf-8")).hexdigest()[:20]


def derive_comment_id(item: dict[str, Any], comment_url: str, post_id: str, text: str, created_time: str) -> str:
    candidates = [
        item.get("commentId"),
        item.get("commentID"),
        item.get("id"),
        item.get("objectId"),
    ]
    for candidate in candidates:
        value = normalize_text(str(candidate)) if candidate is not None else ""
        if value and value.lower() not in {"none", "nan"}:
            return value

    parsed = urlparse(comment_url)
    query = parse_qs(parsed.query)
    for key in ("comment_id", "commentid", "reply_comment_id"):
        values = query.get(key)
        if values:
            return values[0]

    raw = f"{post_id}|{created_time}|{text[:120]}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def stable_seed_tiebreak(seed: int, value: str) -> str:
    return hashlib.sha1(f"{seed}|{value}".encode("utf-8")).hexdigest()


def equispaced_indices(total: int, count: int) -> list[int]:
    if count <= 0 or total <= 0:
        return []
    if count >= total:
        return list(range(total))
    if count == 1:
        return [0]

    raw = [round(index * (total - 1) / (count - 1)) for index in range(count)]
    selected: list[int] = []
    used: set[int] = set()
    for candidate in raw:
        current = candidate
        while current in used and current < total:
            current += 1
        if current >= total:
            current = candidate
            while current in used and current >= 0:
                current -= 1
        if current not in used and 0 <= current < total:
            selected.append(current)
            used.add(current)

    if len(selected) < count:
        for candidate in range(total):
            if candidate not in used:
                selected.append(candidate)
                used.add(candidate)
            if len(selected) == count:
                break
    return sorted(selected[:count])


def call_actor(
    client: Any,
    actor_name: str,
    run_input: dict[str, Any],
    config: ResolvedConfig,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if client is None:
        raise ApiExecutionError("No existe cliente de Apify para ejecutar actores.")

    call_kwargs: dict[str, Any] = {"run_input": run_input}
    if config.memory_mb:
        call_kwargs["memory_mbytes"] = config.memory_mb
    if config.timeout_seconds:
        call_kwargs["timeout_secs"] = config.timeout_seconds

    run = client.actor(actor_name).call(**call_kwargs)
    if not run:
        raise ApiExecutionError(f"El actor {actor_name} no retorno resultado.")

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        raise ApiExecutionError(f"El actor {actor_name} no devolvio dataset.")

    items = list(client.dataset(dataset_id).iterate_items())
    return items, {
        "status": run.get("status", "UNKNOWN"),
        "usageTotalUsd": float(run.get("usageTotalUsd") or 0.0),
        "defaultDatasetId": dataset_id,
        "actor_name": actor_name,
    }


def build_apify_client(config: ResolvedConfig) -> Any:
    if APIFY_IMPORT_ERROR is not None:
        raise PlatformDependencyError(
            "Falta dependencia critica: apify-client. Instala con `pip install apify-client`."
        )
    token = os.environ.get(config.apify_token_env, "").strip()
    if not token:
        raise ApiAuthenticationError(
            f"No existe el token requerido en la variable de entorno {config.apify_token_env}."
        )
    return ApifyClient(token)


def normalize_candidate_post(item: dict[str, Any], page: PageTarget) -> CandidatePost | None:
    post_url = raw_facebook_url(
        str(
            item.get("url")
            or item.get("postUrl")
            or item.get("postURL")
            or item.get("facebookUrl")
            or ""
        )
    )
    if not post_url:
        return None

    created_dt = parse_datetime_from_item(
        item,
        keys=("date", "timestamp", "postDate", "postTimestamp", "createdTime", "createdAt", "publishedAt"),
    )
    post_text = extract_text_from_posts_actor_item(item)
    author = item.get("author") if isinstance(item.get("author"), dict) else {}
    page_url = raw_facebook_url(
        str(
            item.get("pageUrl")
            or item.get("authorProfileUrl")
            or author.get("profileUrl")
            or author.get("url")
            or page.page_url
        )
    )
    author_name = normalize_text(
        str(item.get("authorName") or author.get("name") or item.get("pageName") or page.page_label)
    )
    comment_count = parse_intish(item.get("commentsCount") or item.get("comments") or item.get("numComments"))
    reaction_count = parse_intish(item.get("reactionsCount") or item.get("likes") or item.get("reactions"))

    created_time = created_dt.isoformat() if created_dt else ""
    week_label = derive_week_label_from_datetime(created_dt)
    post_id = derive_post_id(item, post_url)
    return CandidatePost(
        page_id=page.page_id,
        page_label=page.page_label,
        page_url=page_url,
        post_id=post_id,
        post_url=post_url,
        created_time=created_time,
        created_dt=created_dt,
        week_label=week_label,
        post_text=post_text,
        comment_count_post=comment_count,
        reaction_count_post=reaction_count,
        author_name=author_name,
    )


def discover_candidate_posts(
    client: Any,
    page: PageTarget,
    config: ResolvedConfig,
    logger: logging.Logger,
) -> tuple[list[CandidatePost], float]:
    run_input = {
        "startUrls": [{"url": page.page_url}],
        "resultsLimit": config.discovery_results_per_page,
        "captionText": True,
        # Align the automation path with the historical extractor that
        # successfully backfilled weekly windows by pushing the date filter
        # down to the actor instead of discovering only recent posts locally.
        "onlyPostsNewerThan": config.since.isoformat(),
        "onlyPostsOlderThan": config.until.isoformat(),
    }
    logger.info(
        "Descubriendo posts candidatos | page_id=%s page_label=%s results_limit=%s since=%s until=%s",
        page.page_id,
        page.page_label,
        config.discovery_results_per_page,
        config.since,
        config.until,
    )
    items, run_meta = call_actor(client, config.actor_name_posts, run_input, config)
    logger.info(
        "Posts actor completado | page_id=%s status=%s usage_usd=%.4f items=%s",
        page.page_id,
        run_meta["status"],
        run_meta["usageTotalUsd"],
        len(items),
    )

    deduped: dict[str, CandidatePost] = {}
    for item in items:
        post = normalize_candidate_post(item, page)
        if post is None:
            continue
        if not candidate_belongs_to_target(post.post_url, post.page_url, page):
            continue
        if not date_in_range(post.created_dt, config.since, config.until):
            continue
        dedupe_key = post.post_url
        existing = deduped.get(dedupe_key)
        if existing is None:
            deduped[dedupe_key] = post
            continue
        if len(post.post_text) > len(existing.post_text):
            deduped[dedupe_key] = post

    posts = sorted(
        deduped.values(),
        key=lambda post: (
            post.created_dt or datetime.min.replace(tzinfo=timezone.utc),
            stable_seed_tiebreak(config.seed, post.post_id or post.post_url),
        ),
    )
    return posts, float(run_meta["usageTotalUsd"])


def select_posts_for_comment_sampling(
    candidate_posts: list[CandidatePost],
    config: ResolvedConfig,
    logger: logging.Logger,
) -> list[CandidatePost]:
    if not candidate_posts:
        return []

    if len(candidate_posts) <= config.max_posts_per_page_per_week:
        selected = list(candidate_posts)
    else:
        indices = equispaced_indices(len(candidate_posts), config.max_posts_per_page_per_week)
        selected = [candidate_posts[index] for index in indices]

    for rank, post in enumerate(selected, start=1):
        post.selected_for_comment_sampling = True
        post.selection_stage = "selected_for_comment_sampling"
        post.selection_rule = POST_SELECTION_RULE
        post.selection_rank = rank
        post.page_week_counter = rank
        post.status_extraccion = "selected_post"

    logger.info(
        "Posts seleccionados por sampling | seleccionados=%s candidatos=%s regla=%s",
        len(selected),
        len(candidate_posts),
        POST_SELECTION_RULE,
    )
    return selected


def build_processing_queue(selected_posts: list[CandidatePost]) -> list[CandidatePost]:
    return sorted(
        selected_posts,
        key=lambda post: (
            -(post.created_dt.timestamp()) if post.created_dt else float("inf"),
            stable_seed_tiebreak(post.selection_rank or 0, post.post_id or post.post_url),
        ),
    )


def enrich_post_from_comment_items(post: CandidatePost, items: Iterable[dict[str, Any]]) -> tuple[bool, str]:
    best_text = post.post_text
    best_created_dt = post.created_dt
    best_comment_count = post.comment_count_post
    enriched = False

    for item in items:
        candidate_text = extract_text_from_comment_actor_item(item)
        if len(candidate_text) > len(best_text):
            best_text = candidate_text
            enriched = True

        if best_created_dt is None:
            candidate_dt = parse_datetime_from_item(
                item,
                keys=("postDate", "postTimestamp", "date", "timestamp"),
            )
            if candidate_dt is not None:
                best_created_dt = candidate_dt
                enriched = True

        candidate_comment_count = parse_intish(
            item.get("commentsCount") or item.get("numComments") or item.get("comments")
        )
        if candidate_comment_count is not None and not best_comment_count:
            best_comment_count = candidate_comment_count
            enriched = True

    if enriched:
        post.post_text = best_text
        post.created_dt = best_created_dt
        post.created_time = best_created_dt.isoformat() if best_created_dt else post.created_time
        post.week_label = derive_week_label_from_datetime(best_created_dt) or post.week_label
        post.comment_count_post = best_comment_count
        post.enrichment_applied = True
        post.enrichment_source = "comment_actor_item_fields"
        post.absorbed_comment_logic = "; ".join(ABSORBED_COMMENTS_LOGIC)
        return True, post.enrichment_source
    return False, ""


def normalize_comment_text(item: dict[str, Any]) -> str:
    return str(item.get("text") or item.get("commentText") or item.get("body") or "").strip()


def comment_in_historical_range(value: datetime | None, since: date) -> bool:
    if value is None:
        return False
    current = value.date()
    return current >= since


def extract_comments_for_post(
    client: Any,
    page: PageTarget,
    post: CandidatePost,
    config: ResolvedConfig,
    *,
    remaining_page_cap: int,
    page_counter_start: int,
    logger: logging.Logger,
) -> tuple[list[CommentRecord], list[ErrorRecord], int, float, bool]:
    requested = min(config.max_comments_per_post, remaining_page_cap)
    post.comments_requested_for_post = requested
    if requested <= 0:
        return [], [], 0, 0.0, False

    run_input = {
        "startUrls": [{"url": post.post_url}],
        "resultsPerPost": requested,
        "includeReplies": bool(config.include_replies),
    }
    run_input["onlyCommentsNewerThan"] = config.since.isoformat()

    logger.info(
        "Bajando comentarios | page_id=%s post_id=%s requested=%s remaining_page_cap=%s include_replies=%s",
        page.page_id,
        post.post_id,
        requested,
        remaining_page_cap,
        config.include_replies,
    )

    try:
        items, run_meta = call_actor(client, config.actor_name_comments, run_input, config)
    except Exception as exc:
        return (
            [],
            [
                ErrorRecord(
                    stage="fetch_comments_for_post",
                    scope="post",
                    message=str(exc),
                    timestamp=now_utc_text(),
                    fatal=False,
                    error_type=f"comment_actor_error:{type(exc).__name__}",
                    page_id=page.page_id,
                    page_label=page.page_label,
                    post_id=post.post_id,
                )
            ],
            0,
            0.0,
            False,
        )

    enriched, _ = enrich_post_from_comment_items(post, items)

    rows: list[CommentRecord] = []
    errors: list[ErrorRecord] = []
    seen: set[str] = set()
    page_counter = page_counter_start
    post_counter = 0
    for item in items:
        is_reply = bool(item.get("isReply", False))
        if is_reply and not config.include_replies:
            continue

        text = normalize_comment_text(item)
        if len(text) < 5:
            continue

        created_dt = parse_datetime_from_item(item, keys=("date", "timestamp", "commentDate", "createdTime"))
        if not comment_in_historical_range(created_dt, config.since):
            continue

        comment_url = raw_facebook_url(str(item.get("url") or item.get("commentUrl") or ""))
        created_time = created_dt.isoformat() if created_dt else ""
        comment_id = derive_comment_id(item, comment_url, post.post_id, text, created_time)
        dedupe_key = f"{post.post_url}|{text[:150]}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        post_counter += 1
        page_counter += 1
        rows.append(
            CommentRecord(
                page_id=page.page_id,
                page_label=page.page_label,
                post_id=post.post_id,
                comment_id=comment_id,
                parent_post_id=post.post_id,
                post_url=post.post_url,
                comment_url=comment_url,
                created_time=created_time,
                created_dt=created_dt,
                week_label=derive_week_label_from_datetime(created_dt),
                text=text,
                post_text=post.post_text,
                comment_count_post=post.comment_count_post,
                selection_stage="comment_saved_under_cap",
                selection_rule=COMMENT_PROCESSING_RULE,
                weekly_page_cap=config.weekly_comment_cap_per_page,
                max_comments_per_post=config.max_comments_per_post,
                page_week_counter=page_counter,
                post_comment_counter=post_counter,
                status_extraccion="saved",
                error_type="",
                error_detail="",
                seed=config.seed,
                selected_for_comment_sampling=True,
                post_selection_rank=post.selection_rank,
                processing_rank=post.processing_rank,
                comments_requested_for_post=requested,
                comments_retrieved_for_post=0,
                enrichment_applied=post.enrichment_applied,
                enrichment_source=post.enrichment_source,
                absorbed_comment_logic=post.absorbed_comment_logic,
                is_reply=is_reply,
            )
        )
        if len(rows) >= requested:
            break

    post.comments_retrieved_for_post = len(rows)
    post.status_extraccion = "selected_post_with_comments" if rows else "selected_post_no_comments"
    post.error_type = ""
    post.error_detail = ""
    for row_index, row in enumerate(rows):
        rows[row_index] = CommentRecord(
            **{
                **asdict(row),
                "comments_retrieved_for_post": len(rows),
            }
        )

    logger.info(
        "Comentarios materializados | page_id=%s post_id=%s status=%s usage_usd=%.4f rows=%s enriched=%s",
        page.page_id,
        post.post_id,
        post.status_extraccion,
        run_meta["usageTotalUsd"],
        len(rows),
        enriched,
    )
    return rows, errors, requested, float(run_meta["usageTotalUsd"]), enriched


def build_selection_audit(
    config: ResolvedConfig,
    page_result: PageExecutionResult,
) -> list[SelectionAuditRecord]:
    selected_map = {post.post_id: post for post in page_result.selected_posts}
    audit: list[SelectionAuditRecord] = []
    cap_reached = bool(page_result.cap_events)
    for candidate in page_result.candidate_posts:
        selected = candidate.post_id in selected_map
        selected_post = selected_map.get(candidate.post_id)
        if selected_post is not None:
            status = selected_post.status_extraccion
            stage = selected_post.selection_stage
            decision_reason = "Selected by temporal coverage rule and processed under page cap."
            if status == "selected_post_no_comments":
                decision_reason = "Selected but no comments within range were materialized."
            elif status == "comment_fetch_failed":
                decision_reason = "Selected but comment extraction failed for this post."
        else:
            status = "not_selected_due_sampling"
            stage = "candidate_rejected_by_sampling"
            decision_reason = "Excluded by temporal even-spacing sampling before comments actor."
            if cap_reached and len(page_result.selected_posts) >= config.max_posts_per_page_per_week:
                decision_reason = "Candidate not selected because sampling and page cap already constrained the weekly universe."

        audit.append(
            SelectionAuditRecord(
                run_id=config.run_id,
                week_name=config.week_partition.week_name,
                page_id=page_result.page.page_id,
                page_label=page_result.page.page_label,
                post_id=candidate.post_id,
                post_url=candidate.post_url,
                created_time=candidate.created_time,
                week_label=candidate.week_label,
                comment_count_post=candidate.comment_count_post,
                selection_stage=stage,
                selection_rule=POST_SELECTION_RULE,
                selected_for_comment_sampling=selected,
                selection_rank=selected_post.selection_rank if selected_post else None,
                processing_rank=selected_post.processing_rank if selected_post else None,
                status_extraccion=status,
                decision_reason=decision_reason,
                seed=config.seed,
            )
        )
    return audit


def extract_page_batch(
    client: Any,
    page: PageTarget,
    config: ResolvedConfig,
    logger: logging.Logger,
) -> PageExecutionResult:
    result = PageExecutionResult(page=page, status="success")

    try:
        candidate_posts, usage_usd = discover_candidate_posts(client, page, config, logger)
        result.candidate_posts = candidate_posts
        result.posts_actor_usage_usd = usage_usd
        result.total_candidate_posts_detected = len(candidate_posts)
    except Exception as exc:
        result.status = "failed"
        result.errors.append(
            ErrorRecord(
                stage="discover_candidate_posts",
                scope="page",
                message=str(exc),
                timestamp=now_utc_text(),
                fatal=False,
                error_type=f"discover_posts_error:{type(exc).__name__}",
                page_id=page.page_id,
                page_label=page.page_label,
            )
        )
        result.total_items_failed += 1
        result.selection_audit = []
        return result

    selected_posts = select_posts_for_comment_sampling(candidate_posts, config, logger)
    processing_queue = build_processing_queue(selected_posts)
    for processing_rank, post in enumerate(processing_queue, start=1):
        post.processing_rank = processing_rank
    result.selected_posts = selected_posts
    result.total_posts_selected = len(selected_posts)

    page_comments_saved = 0
    page_counter = 0
    for post in processing_queue:
        if page_comments_saved >= config.weekly_comment_cap_per_page:
            result.cap_events.append(
                CapEvent(
                    page_id=page.page_id,
                    page_label=page.page_label,
                    cap_value=config.weekly_comment_cap_per_page,
                    comments_saved_when_reached=page_comments_saved,
                    reached_at_post_id=post.post_id,
                    timestamp=now_utc_text(),
                    reason="Weekly page cap reached before expanding more posts.",
                )
            )
            logger.info(
                "Cap semanal alcanzado | page_id=%s page_label=%s cap=%s comments_saved=%s",
                page.page_id,
                page.page_label,
                config.weekly_comment_cap_per_page,
                page_comments_saved,
            )
            break

        remaining_cap = config.weekly_comment_cap_per_page - page_comments_saved
        comments, errors, attempted, usage_usd, enriched = extract_comments_for_post(
            client,
            page,
            post,
            config,
            remaining_page_cap=remaining_cap,
            page_counter_start=page_counter,
            logger=logger,
        )
        result.comments_actor_usage_usd += usage_usd
        result.total_comments_attempted += attempted
        if errors:
            post.status_extraccion = "comment_fetch_failed"
            post.error_type = errors[0].error_type
            post.error_detail = errors[0].message
            result.errors.extend(errors)
            result.total_items_failed += len(errors)
            if result.status == "success":
                result.status = "partial_success"
            continue

        if enriched:
            result.total_posts_enriched += 1

        result.comments.extend(comments)
        page_comments_saved += len(comments)
        page_counter = page_comments_saved
        result.total_comments_saved = page_comments_saved
        estimated_available = post.comment_count_post or 0
        if estimated_available > attempted:
            result.total_comments_skipped_by_cap += max(0, estimated_available - attempted)

    if result.errors and result.status == "success":
        result.status = "partial_success"
    if not result.comments and result.errors and not result.candidate_posts:
        result.status = "failed"

    result.selection_audit = build_selection_audit(config, result)
    return result


def determine_run_status(page_results: Sequence[PageExecutionResult], errors: Sequence[ErrorRecord]) -> str:
    if not page_results:
        return "failed"
    if all(result.status == "failed" for result in page_results):
        return "failed"
    if errors:
        if any(result.total_comments_saved > 0 for result in page_results):
            return "partial_success"
        if any(result.total_candidate_posts_detected > 0 for result in page_results):
            return "partial_success"
        return "failed"
    return "success"


def map_status_to_exit_code(status: str) -> int:
    if status == "success":
        return int(ExitCode.SUCCESS)
    if status == "partial_success":
        return int(ExitCode.PARTIAL_SUCCESS)
    return int(ExitCode.FAILED_API)


def flatten_errors(page_results: Sequence[PageExecutionResult]) -> list[ErrorRecord]:
    flattened: list[ErrorRecord] = []
    for result in page_results:
        flattened.extend(result.errors)
    return flattened


def build_main_dataframe(page_results: Sequence[PageExecutionResult], config: ResolvedConfig) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for page_result in page_results:
        for post in page_result.selected_posts:
            rows.append(
                {
                    "run_id": config.run_id,
                    "week_name": config.week_partition.week_name,
                    "source_platform": SOURCE_PLATFORM,
                    "source_scope": SOURCE_SCOPE,
                    "page_id": post.page_id,
                    "page_label": post.page_label,
                    "post_id": post.post_id,
                    "comment_id": "",
                    "parent_post_id": "",
                    "record_type": "post_parent",
                    "post_url": post.post_url,
                    "comment_url": "",
                    "created_time": post.created_time,
                    "week_label": post.week_label,
                    "text": post.post_text,
                    "post_text": post.post_text,
                    "comment_count_post": post.comment_count_post,
                    "selection_stage": post.selection_stage,
                    "selection_rule": post.selection_rule,
                    "weekly_page_cap": config.weekly_comment_cap_per_page,
                    "max_comments_per_post": config.max_comments_per_post,
                    "page_week_counter": post.page_week_counter,
                    "post_comment_counter": "",
                    "status_extraccion": post.status_extraccion,
                    "error_type": post.error_type,
                    "error_detail": post.error_detail,
                    "seed": config.seed,
                    "selected_for_comment_sampling": post.selected_for_comment_sampling,
                    "post_selection_rank": post.selection_rank,
                    "processing_rank": post.processing_rank,
                    "comments_requested_for_post": post.comments_requested_for_post,
                    "comments_retrieved_for_post": post.comments_retrieved_for_post,
                    "enrichment_applied": post.enrichment_applied,
                    "enrichment_source": post.enrichment_source,
                    "absorbed_comment_logic": post.absorbed_comment_logic,
                    "is_reply": False,
                }
            )
        for comment in page_result.comments:
            rows.append(
                {
                    "run_id": config.run_id,
                    "week_name": config.week_partition.week_name,
                    "source_platform": SOURCE_PLATFORM,
                    "source_scope": SOURCE_SCOPE,
                    "page_id": comment.page_id,
                    "page_label": comment.page_label,
                    "post_id": comment.post_id,
                    "comment_id": comment.comment_id,
                    "parent_post_id": comment.parent_post_id,
                    "record_type": "reply" if comment.is_reply else "comment",
                    "post_url": comment.post_url,
                    "comment_url": comment.comment_url,
                    "created_time": comment.created_time,
                    "week_label": comment.week_label,
                    "text": comment.text,
                    "post_text": comment.post_text,
                    "comment_count_post": comment.comment_count_post,
                    "selection_stage": comment.selection_stage,
                    "selection_rule": comment.selection_rule,
                    "weekly_page_cap": comment.weekly_page_cap,
                    "max_comments_per_post": comment.max_comments_per_post,
                    "page_week_counter": comment.page_week_counter,
                    "post_comment_counter": comment.post_comment_counter,
                    "status_extraccion": comment.status_extraccion,
                    "error_type": comment.error_type,
                    "error_detail": comment.error_detail,
                    "seed": comment.seed,
                    "selected_for_comment_sampling": comment.selected_for_comment_sampling,
                    "post_selection_rank": comment.post_selection_rank,
                    "processing_rank": comment.processing_rank,
                    "comments_requested_for_post": comment.comments_requested_for_post,
                    "comments_retrieved_for_post": comment.comments_retrieved_for_post,
                    "enrichment_applied": comment.enrichment_applied,
                    "enrichment_source": comment.enrichment_source,
                    "absorbed_comment_logic": comment.absorbed_comment_logic,
                    "is_reply": comment.is_reply,
                }
            )
    if not rows:
        return pd.DataFrame(columns=MAIN_COLUMNS)
    return pd.DataFrame(rows, columns=MAIN_COLUMNS)


def build_posts_dataframe(page_results: Sequence[PageExecutionResult], config: ResolvedConfig) -> pd.DataFrame:
    main_df = build_main_dataframe(page_results, config)
    if main_df.empty:
        return pd.DataFrame(columns=MAIN_COLUMNS)
    return main_df[main_df["record_type"] == "post_parent"].reset_index(drop=True)


def build_comments_dataframe(page_results: Sequence[PageExecutionResult], config: ResolvedConfig) -> pd.DataFrame:
    main_df = build_main_dataframe(page_results, config)
    if main_df.empty:
        return pd.DataFrame(columns=MAIN_COLUMNS)
    return main_df[main_df["record_type"] != "post_parent"].reset_index(drop=True)


def build_selection_audit_dataframe(page_results: Sequence[PageExecutionResult]) -> pd.DataFrame:
    rows = [asdict(record) for result in page_results for record in result.selection_audit]
    if not rows:
        return pd.DataFrame(columns=AUDIT_COLUMNS)
    return pd.DataFrame(rows, columns=AUDIT_COLUMNS)


def build_notes(config: ResolvedConfig, *, status: str, dry_run: bool) -> list[str]:
    notes = [
        "Extractor restringido a Facebook institucional de Tampico.",
        f"Sampling mode: {SAMPLING_MODE}.",
        f"Post selection rule: {POST_SELECTION_RULE}.",
        f"Comment processing rule: {COMMENT_PROCESSING_RULE}.",
        "La unidad principal de interes analitico es el comentario; el post se conserva como contexto y trazabilidad.",
        "Se absorbio logica de enriquecimiento liviano desde Facebook_Extractor_Comments_Apify_Tampico.py sin depender de CSV manual.",
        "Se descarto enriquecimiento adicional por scraping de URL del post para no romper costo ni control operacional.",
    ]
    if config.include_replies:
        notes.append("Replies incluidos para preservar comparabilidad con el extractor histórico de comentarios.")
    else:
        notes.append("Replies deshabilitados por configuracion; esto reduce comparabilidad frente al extractor historico.")
    if dry_run:
        notes.append("Dry-run activo: no se ejecutaron actores de Apify.")
    if status != "success":
        notes.append("La corrida termino con incidencias recuperables o fallas parciales.")
    return notes


def build_summary(
    config: ResolvedConfig,
    page_results: Sequence[PageExecutionResult],
    *,
    status: str,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    output_dir: Path,
    notes: Sequence[str],
) -> dict[str, Any]:
    total_candidate_posts = sum(result.total_candidate_posts_detected for result in page_results)
    total_posts_selected = sum(result.total_posts_selected for result in page_results)
    total_comments_attempted = sum(result.total_comments_attempted for result in page_results)
    total_comments_saved = sum(result.total_comments_saved for result in page_results)
    total_comments_skipped = sum(result.total_comments_skipped_by_cap for result in page_results)
    total_posts_enriched = sum(result.total_posts_enriched for result in page_results)
    total_items_failed = sum(result.total_items_failed for result in page_results)
    total_usage_usd = round(
        sum(result.posts_actor_usage_usd + result.comments_actor_usage_usd for result in page_results),
        6,
    )
    pages_without_candidate_posts = [
        {"page_id": result.page.page_id, "page_label": result.page.page_label, "page_handle": result.page.page_handle}
        for result in page_results
        if result.total_candidate_posts_detected == 0
    ]
    pages_without_comments_saved = [
        {"page_id": result.page.page_id, "page_label": result.page.page_label, "page_handle": result.page.page_handle}
        for result in page_results
        if result.total_comments_saved == 0
    ]
    return {
        "run_id": config.run_id,
        "status": status,
        "since": config.since.isoformat(),
        "until": config.until.isoformat(),
        "week_name": config.week_partition.week_name,
        "output_dir": str(output_dir),
        "institutional_pages_targeted": [page.page_label for page in config.pages],
        "page_ids_targeted": [page.page_id for page in config.pages],
        "page_handles_targeted": [page.page_handle for page in config.pages],
        "seed": config.seed,
        "weekly_comment_caps": {page.page_id: config.weekly_comment_cap_per_page for page in config.pages},
        "total_candidate_posts_detected": total_candidate_posts,
        "total_posts_selected": total_posts_selected,
        "total_comments_attempted": total_comments_attempted,
        "total_comments_saved": total_comments_saved,
        "total_comments_skipped_by_cap": total_comments_skipped,
        "total_posts_enriched": total_posts_enriched,
        "total_items_failed": total_items_failed,
        "pages_without_candidate_posts": pages_without_candidate_posts,
        "pages_without_comments_saved": pages_without_comments_saved,
        "sampling_mode": SAMPLING_MODE,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
        "week_name_mode": config.week_name_mode,
        "script_name": config.script_name,
        "script_version": config.script_version,
        "apify_usage_total_usd": total_usage_usd,
        "include_replies": config.include_replies,
        "notes": list(notes),
        "exit_code": map_status_to_exit_code(status),
    }


def build_metadata(
    config: ResolvedConfig,
    page_results: Sequence[PageExecutionResult],
    *,
    status: str,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    artifact_paths: dict[str, str],
    errors: Sequence[ErrorRecord],
    notes: Sequence[str],
) -> dict[str, Any]:
    total_posts_actor_usage = round(sum(result.posts_actor_usage_usd for result in page_results), 6)
    total_comments_actor_usage = round(sum(result.comments_actor_usage_usd for result in page_results), 6)
    return {
        "script_name": config.script_name,
        "script_path": str(config.script_path),
        "helper_module_path": str(config.helper_module_path),
        "entrypoint_alias": config.entrypoint_alias,
        "script_version": config.script_version,
        "run_id": config.run_id,
        "run_timestamp": config.run_timestamp,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
        "environment": platform.platform(),
        "hostname": socket.gethostname(),
        "user": os.environ.get("USER") or os.environ.get("USERNAME") or "",
        "parameters": serialize_for_json(config),
        "token_env_name_used": config.apify_token_env,
        "errors": [serialize_for_json(error) for error in errors],
        "artifact_paths": artifact_paths,
        "sampling_strategy": {
            "mode": SAMPLING_MODE,
            "post_selection_rule": POST_SELECTION_RULE,
            "comment_processing_rule": COMMENT_PROCESSING_RULE,
            "weekly_comment_cap_per_page": config.weekly_comment_cap_per_page,
            "max_posts_per_page_per_week": config.max_posts_per_page_per_week,
            "max_comments_per_post": config.max_comments_per_post,
            "seed": config.seed,
        },
        "page_level_counts": {
            result.page.page_id: {
                "page_label": result.page.page_label,
                "page_handle": result.page.page_handle,
                "candidate_posts_detected": result.total_candidate_posts_detected,
                "posts_selected": result.total_posts_selected,
                "comments_attempted": result.total_comments_attempted,
                "comments_saved": result.total_comments_saved,
                "comments_skipped_by_cap": result.total_comments_skipped_by_cap,
                "posts_enriched": result.total_posts_enriched,
                "items_failed": result.total_items_failed,
                "status": result.status,
            }
            for result in page_results
        },
        "apify_usage": {
            "posts_actor_usage_usd": total_posts_actor_usage,
            "comments_actor_usage_usd": total_comments_actor_usage,
            "total_usage_usd": round(total_posts_actor_usage + total_comments_actor_usage, 6),
        },
        "components_absorbed_from_comments_script": ABSORBED_COMMENTS_LOGIC,
        "discarded_comments_script_logic": DISCARDED_COMMENTS_LOGIC,
        "notes": list(notes),
    }


def publish_canonical_artifacts(
    config: ResolvedConfig,
    artifact_paths: dict[str, Path],
    logger: logging.Logger,
) -> dict[str, str]:
    if not config.publish_canonical:
        return {}

    published: dict[str, str] = {}
    targets = {
        "main_csv": config.week_dir / f"{MAIN_CSV_PREFIX}_{config.week_partition.week_name}.csv",
        "posts_csv": config.week_dir / POSTS_FILENAME,
        "comments_csv": config.week_dir / COMMENTS_FILENAME,
        "audit_csv": config.week_dir / AUDIT_FILENAME,
        "summary_json": config.week_dir / SUMMARY_FILENAME,
        "metadata_json": config.week_dir / METADATA_FILENAME,
        "parametros_json": config.week_dir / PARAMS_FILENAME,
        "manifest_json": config.week_dir / MANIFEST_FILENAME,
        "errors_json": config.week_dir / ERRORS_FILENAME,
        "run_log": config.week_dir / LOG_FILENAME,
    }
    for key, source_path in artifact_paths.items():
        target_path = targets.get(key)
        if target_path is None:
            continue
        ensure_publish_target(target_path, config.overwrite)
        shutil.copy2(source_path, target_path)
        published[key] = str(target_path)
        logger.info("Artefacto canonico publicado | source=%s target=%s", source_path, target_path)
    return published


def persist_outputs(
    config: ResolvedConfig,
    page_results: Sequence[PageExecutionResult],
    *,
    status: str,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    logger: logging.Logger,
    notes: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, str]]:
    main_df = build_main_dataframe(page_results, config)
    posts_df = build_posts_dataframe(page_results, config)
    comments_df = build_comments_dataframe(page_results, config)
    audit_df = build_selection_audit_dataframe(page_results)
    errors = flatten_errors(page_results)

    artifact_paths: dict[str, Path] = {}
    artifact_records: list[ArtifactRecord] = []

    main_path = config.run_dir / f"{MAIN_CSV_PREFIX}_{config.week_partition.week_name}.csv"
    dataframe_to_csv(main_path, main_df)
    artifact_paths["main_csv"] = main_path
    add_artifact_record(artifact_records, main_path, "dataset", "Extraccion cruda institucional de Facebook con posts padre y comentarios.")

    posts_path = config.run_dir / POSTS_FILENAME
    dataframe_to_csv(posts_path, posts_df)
    artifact_paths["posts_csv"] = posts_path
    add_artifact_record(artifact_records, posts_path, "dataset", "Posts seleccionados para comentario bajo logica muestral.")

    comments_path = config.run_dir / COMMENTS_FILENAME
    dataframe_to_csv(comments_path, comments_df)
    artifact_paths["comments_csv"] = comments_path
    add_artifact_record(artifact_records, comments_path, "dataset", "Comentarios materializados para el corpus institucional.")

    audit_path = config.run_dir / AUDIT_FILENAME
    dataframe_to_csv(audit_path, audit_df)
    artifact_paths["audit_csv"] = audit_path
    add_artifact_record(artifact_records, audit_path, "audit", "Auditoria de seleccion de posts y decisiones muestrales.")

    summary = build_summary(
        config,
        page_results,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        output_dir=config.run_dir,
        notes=notes,
    )
    summary_path = config.run_dir / SUMMARY_FILENAME
    write_json_file(summary_path, summary)
    artifact_paths["summary_json"] = summary_path
    add_artifact_record(artifact_records, summary_path, "summary", "Resumen operativo y de costo de la corrida.")

    params_payload = {
        "run_id": config.run_id,
        "script_name": config.script_name,
        "script_version": config.script_version,
        "entrypoint_alias": config.entrypoint_alias,
        "since": config.since.isoformat(),
        "until": config.until.isoformat(),
        "week_name_mode": config.week_name_mode,
        "week_name": config.week_partition.week_name,
        "naming_start_date": config.week_partition.naming_start_date.isoformat(),
        "naming_end_date": config.week_partition.naming_end_date.isoformat(),
        "output_root_dir": str(config.output_root_dir),
        "week_dir": str(config.week_dir),
        "run_dir": str(config.run_dir),
        "pages": [serialize_for_json(page) for page in config.pages],
        "pages_source": config.pages_source,
        "apify_token_env": config.apify_token_env,
        "actor_name_posts": config.actor_name_posts,
        "actor_name_comments": config.actor_name_comments,
        "memory_mb": config.memory_mb,
        "timeout_seconds": config.timeout_seconds,
        "seed": config.seed,
        "weekly_comment_cap_per_page": config.weekly_comment_cap_per_page,
        "max_posts_per_page_per_week": config.max_posts_per_page_per_week,
        "max_comments_per_post": config.max_comments_per_post,
        "discovery_results_per_page": config.discovery_results_per_page,
        "include_replies": config.include_replies,
        "publish_canonical": config.publish_canonical,
        "overwrite": config.overwrite,
        "dry_run": config.dry_run,
    }
    params_path = config.run_dir / PARAMS_FILENAME
    write_json_file(params_path, params_payload)
    artifact_paths["parametros_json"] = params_path
    add_artifact_record(artifact_records, params_path, "parameters", "Parametros efectivos de la corrida.")

    metadata_path = config.run_dir / METADATA_FILENAME
    metadata = build_metadata(
        config,
        page_results,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        artifact_paths={key: str(value) for key, value in artifact_paths.items()},
        errors=errors,
        notes=notes,
    )
    write_json_file(metadata_path, metadata)
    artifact_paths["metadata_json"] = metadata_path
    add_artifact_record(artifact_records, metadata_path, "metadata", "Metadata completa y trazabilidad de la corrida.")

    if errors:
        errors_path = config.run_dir / ERRORS_FILENAME
        write_json_file(errors_path, [serialize_for_json(error) for error in errors])
        artifact_paths["errors_json"] = errors_path
        add_artifact_record(artifact_records, errors_path, "errors", "Errores recuperables registrados durante la corrida.")
    elif config.publish_canonical and config.overwrite:
        stale_errors_path = config.week_dir / ERRORS_FILENAME
        if stale_errors_path.exists():
            stale_errors_path.unlink()

    log_path = config.run_dir / LOG_FILENAME
    if log_path.exists():
        artifact_paths["run_log"] = log_path
        add_artifact_record(artifact_records, log_path, "log", "Log operativo de la corrida.")

    manifest_path = config.run_dir / MANIFEST_FILENAME
    manifest_payload = [serialize_for_json(record) for record in artifact_records]
    write_json_file(manifest_path, manifest_payload)
    artifact_paths["manifest_json"] = manifest_path
    add_artifact_record(artifact_records, manifest_path, "manifest", "Inventario de artefactos de la corrida.")
    manifest_payload = [serialize_for_json(record) for record in artifact_records]
    write_json_file(manifest_path, manifest_payload)

    published_paths = publish_canonical_artifacts(config, artifact_paths, logger)
    if published_paths:
        summary["published_canonical_paths"] = published_paths
        metadata["published_canonical_paths"] = published_paths
        write_json_file(summary_path, summary)
        write_json_file(metadata_path, metadata)
        shutil.copy2(summary_path, config.week_dir / SUMMARY_FILENAME)
        shutil.copy2(metadata_path, config.week_dir / METADATA_FILENAME)

    return summary, metadata, manifest_payload, {key: str(value) for key, value in artifact_paths.items()}


def write_failure_artifacts(
    config: ResolvedConfig,
    logger: logging.Logger,
    *,
    error: Exception,
    exit_code: ExitCode,
) -> None:
    configure_output_layout(config)
    error_record = ErrorRecord(
        stage="fatal_runtime",
        scope="run",
        message=str(error),
        timestamp=now_utc_text(),
        fatal=True,
        error_type=f"fatal:{type(error).__name__}",
    )
    started_at = now_utc_text()
    finished_at = started_at
    summary = {
        "run_id": config.run_id,
        "status": "failed",
        "since": config.since.isoformat(),
        "until": config.until.isoformat(),
        "week_name": config.week_partition.week_name,
        "output_dir": str(config.run_dir),
        "institutional_pages_targeted": [page.page_label for page in config.pages],
        "page_ids_targeted": [page.page_id for page in config.pages],
        "page_handles_targeted": [page.page_handle for page in config.pages],
        "seed": config.seed,
        "weekly_comment_caps": {page.page_id: config.weekly_comment_cap_per_page for page in config.pages},
        "total_candidate_posts_detected": 0,
        "total_posts_selected": 0,
        "total_comments_attempted": 0,
        "total_comments_saved": 0,
        "total_comments_skipped_by_cap": 0,
        "total_posts_enriched": 0,
        "total_items_failed": 1,
        "sampling_mode": SAMPLING_MODE,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": 0.0,
        "script_name": config.script_name,
        "script_version": config.script_version,
        "notes": build_notes(config, status="failed", dry_run=config.dry_run) + [str(error)],
        "exit_code": int(exit_code),
    }
    metadata = {
        "script_name": config.script_name,
        "script_path": str(config.script_path),
        "helper_module_path": str(config.helper_module_path),
        "entrypoint_alias": config.entrypoint_alias,
        "script_version": config.script_version,
        "run_id": config.run_id,
        "run_timestamp": config.run_timestamp,
        "status": "failed",
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": 0.0,
        "token_env_name_used": config.apify_token_env,
        "parameters": serialize_for_json(config),
        "errors": [serialize_for_json(error_record)],
        "components_absorbed_from_comments_script": ABSORBED_COMMENTS_LOGIC,
        "discarded_comments_script_logic": DISCARDED_COMMENTS_LOGIC,
    }
    summary_path = config.run_dir / SUMMARY_FILENAME
    metadata_path = config.run_dir / METADATA_FILENAME
    params_path = config.run_dir / PARAMS_FILENAME
    errors_path = config.run_dir / ERRORS_FILENAME
    manifest_path = config.run_dir / MANIFEST_FILENAME
    write_json_file(summary_path, summary)
    write_json_file(metadata_path, metadata)
    write_json_file(params_path, serialize_for_json(config))
    write_json_file(errors_path, [serialize_for_json(error_record)])

    records: list[ArtifactRecord] = []
    add_artifact_record(records, summary_path, "summary", "Resumen de falla fatal de la corrida.")
    add_artifact_record(records, metadata_path, "metadata", "Metadata de falla fatal de la corrida.")
    add_artifact_record(records, params_path, "parameters", "Parametros efectivos de la corrida fallida.")
    add_artifact_record(records, errors_path, "errors", "Errores fatales registrados en la corrida fallida.")
    write_json_file(manifest_path, [serialize_for_json(record) for record in records])
    logger.error("Artefactos de falla escritos | run_dir=%s", config.run_dir)


def build_dry_run_result(config: ResolvedConfig, logger: logging.Logger) -> RunExecutionResult:
    started_at = now_utc_text()
    finished_at = started_at
    notes = build_notes(config, status="success", dry_run=True)
    page_results = [
        PageExecutionResult(
            page=page,
            status="success",
            selection_audit=[],
        )
        for page in config.pages
    ]
    summary, metadata, manifest, artifact_paths = persist_outputs(
        config,
        page_results,
        status="success",
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=0.0,
        logger=logger,
        notes=notes,
    )
    return RunExecutionResult(
        status="success",
        exit_code=int(ExitCode.SUCCESS),
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=0.0,
        page_results=page_results,
        errors=[],
        notes=notes,
        summary=summary,
        metadata=metadata,
        manifest=manifest,
        artifact_paths=artifact_paths,
    )


def run_extraction(config: ResolvedConfig, logger: logging.Logger) -> RunExecutionResult:
    configure_output_layout(config)
    if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
        logger = setup_logging(config.log_level, config.run_dir / LOG_FILENAME)

    logger.info(
        "Inicio de corrida | run_id=%s week_name=%s output_root=%s week_name_mode=%s",
        config.run_id,
        config.week_partition.week_name,
        config.output_root_dir,
        config.week_name_mode,
    )
    logger.info(
        "Parametros efectivos | since=%s until=%s pages=%s seed=%s weekly_cap=%s max_posts=%s max_comments_per_post=%s include_replies=%s dry_run=%s",
        config.since,
        config.until,
        len(config.pages),
        config.seed,
        config.weekly_comment_cap_per_page,
        config.max_posts_per_page_per_week,
        config.max_comments_per_post,
        config.include_replies,
        config.dry_run,
    )
    logger.info(
        "Paginas institucionales objetivo | pages=%s",
        ", ".join(f"{page.page_label}:{page.page_id}:{page.page_handle or 'sin_handle'}" for page in config.pages),
    )

    if config.dry_run:
        logger.info("Dry-run activo; no se llamara a Apify.")
        return build_dry_run_result(config, logger)

    client = build_apify_client(config)
    started_at = now_utc_text()
    started_perf = time.perf_counter()
    page_results: list[PageExecutionResult] = []
    for index, page in enumerate(config.pages, start=1):
        logger.info(
            "Procesando pagina %s/%s | page_id=%s page_label=%s page_handle=%s",
            index,
            len(config.pages),
            page.page_id,
            page.page_label,
            page.page_handle or "",
        )
        page_result = extract_page_batch(client, page, config, logger)
        page_results.append(page_result)

    errors = flatten_errors(page_results)
    status = determine_run_status(page_results, errors)
    duration_seconds = round(time.perf_counter() - started_perf, 3)
    notes = build_notes(config, status=status, dry_run=False)
    summary, metadata, manifest, artifact_paths = persist_outputs(
        config,
        page_results,
        status=status,
        started_at=started_at,
        finished_at=now_utc_text(),
        duration_seconds=duration_seconds,
        logger=logger,
        notes=notes,
    )
    logger.info(
        "Resumen final | status=%s candidate_posts=%s posts_selected=%s comments_saved=%s total_usage_usd=%.4f",
        status,
        sum(result.total_candidate_posts_detected for result in page_results),
        sum(result.total_posts_selected for result in page_results),
        sum(result.total_comments_saved for result in page_results),
        sum(result.posts_actor_usage_usd + result.comments_actor_usage_usd for result in page_results),
    )
    return RunExecutionResult(
        status=status,
        exit_code=map_status_to_exit_code(status),
        started_at=started_at,
        finished_at=summary["finished_at"],
        duration_seconds=duration_seconds,
        page_results=page_results,
        errors=errors,
        notes=notes,
        summary=summary,
        metadata=metadata,
        manifest=manifest,
        artifact_paths=artifact_paths,
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    script_name: str,
    script_path: Path,
    entrypoint_alias: str,
) -> int:
    args = parse_args(argv)
    logger = setup_logging(getattr(args, "log_level", DEFAULT_LOG_LEVEL) or DEFAULT_LOG_LEVEL)

    try:
        config = resolve_config(
            args,
            script_name=script_name,
            script_path=script_path,
            entrypoint_alias=entrypoint_alias,
        )
    except ConfigurationError as exc:
        logger.error("Error de configuracion: %s", exc)
        return int(ExitCode.FAILED_CONFIG)

    try:
        result = run_extraction(config, logger)
        return int(result.exit_code)
    except ApiAuthenticationError as exc:
        logger.error("Error fatal de autenticacion con Apify: %s", exc)
        try:
            write_failure_artifacts(config, logger, error=exc, exit_code=ExitCode.FAILED_API)
        except Exception as write_exc:
            logger.error("No se pudieron escribir artefactos de falla: %s", write_exc)
        return int(ExitCode.FAILED_API)
    except PlatformDependencyError as exc:
        logger.error("Error fatal de dependencias/plataforma: %s", exc)
        try:
            write_failure_artifacts(config, logger, error=exc, exit_code=ExitCode.FAILED_API)
        except Exception as write_exc:
            logger.error("No se pudieron escribir artefactos de falla: %s", write_exc)
        return int(ExitCode.FAILED_API)
    except ApiExecutionError as exc:
        logger.error("Error fatal de plataforma/API: %s", exc)
        try:
            write_failure_artifacts(config, logger, error=exc, exit_code=ExitCode.FAILED_API)
        except Exception as write_exc:
            logger.error("No se pudieron escribir artefactos de falla: %s", write_exc)
        return int(ExitCode.FAILED_API)
    except OutputWriteError as exc:
        logger.error("Error fatal de persistencia: %s", exc)
        return int(ExitCode.FAILED_WRITE)
    except Exception as exc:  # pragma: no cover - salvaguarda final
        logger.error("Error fatal no controlado: %s", exc)
        try:
            write_failure_artifacts(config, logger, error=exc, exit_code=ExitCode.FAILED_API)
        except Exception as write_exc:
            logger.error("No se pudieron escribir artefactos de falla: %s", write_exc)
        return int(ExitCode.FAILED_API)
