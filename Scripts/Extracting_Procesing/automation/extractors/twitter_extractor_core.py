#!/usr/bin/env python3
"""
Núcleo reusable del extractor de X/Twitter para Radar.

El módulo concentra configuración, navegación con Playwright, extracción,
persistencia y trazabilidad del componente. Los wrappers
`twitter_extractor.py` y `02_twitter_extractor_Tampico.py` preservan CLI
estable y compatibilidad operacional.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import platform
import re
import shutil
import socket
import sys
import time
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, timedelta
from enum import IntEnum
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import quote

import pandas as pd

try:
    from playwright.async_api import Browser, BrowserContext, Error as PlaywrightError, Page, async_playwright
except ImportError as exc:  # pragma: no cover - depende del entorno
    Browser = Any  # type: ignore[misc,assignment]
    BrowserContext = Any  # type: ignore[misc,assignment]
    Page = Any  # type: ignore[misc,assignment]
    PlaywrightError = Exception  # type: ignore[assignment]
    async_playwright = None  # type: ignore[assignment]
    PLAYWRIGHT_IMPORT_ERROR: Exception | None = exc
else:
    PLAYWRIGHT_IMPORT_ERROR = None


def resolve_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in (current.parent, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current.parents[4]


ROOT_DIR = resolve_repo_root()
DEFAULT_OUTPUT_DIR = ROOT_DIR / "Datos_RAdAR" / "Twitter"
DEFAULT_SESSION_STATE_FILE = ROOT_DIR / "Scripts" / "state" / "x_state.json"
DEFAULT_QUERIES_FILE = Path(__file__).with_name("twitter_queries_canonical.txt")
SCRIPT_VERSION = "2.0.0"
SCRIPT_COMPONENT = "radar.twitter_extractor"
SOURCE_PLATFORM = "x_twitter"

WEEK_MODE_EXACT = "exact_range"
WEEK_MODE_CANONICAL = "canonical_monday_sunday"
WEEK_NAME_MODE_CHOICES = (WEEK_MODE_EXACT, WEEK_MODE_CANONICAL)

DEFAULT_HEADLESS = True
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_RUN_ID = "twitter_extract"
DEFAULT_MAX_SCROLLS = 10
DEFAULT_MAX_TWEETS_PER_QUERY = 3000
DEFAULT_MAX_REPLIES_PER_TWEET = 200
DEFAULT_REPLY_SCROLLS = 8
DEFAULT_PAUSE_SECONDS = 1.0
DEFAULT_NAV_TIMEOUT_MS = 90000
DEFAULT_NAV_RETRIES = 3
DEFAULT_VIEWPORT = {"width": 1280, "height": 900}
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

MAIN_CSV_PREFIX = "twitter_data"
RAW_JSONL_FILENAME = "tweets_raw.jsonl"
QUERIES_FILENAME = "queries_summary.csv"
SUMMARY_FILENAME = "summary.json"
METADATA_FILENAME = "metadata_run.json"
PARAMS_FILENAME = "parametros_run.json"
MANIFEST_FILENAME = "manifest.json"
ERRORS_FILENAME = "errores_detectados.json"
LOG_FILENAME = "run.log"

DEFAULT_CANONICAL_QUERIES = [
    "to:MonicaVTampico",
    "from:MonicaVTampico",
    "to:TampicoGob",
    "from:TampicoGob",
    "@TampicoGob",
    "@MonicaVTampico",
]

DATA_COLUMNS = [
    "run_id",
    "week_name",
    "source_platform",
    "query",
    "query_index",
    "tweet_url",
    "tweet_id",
    "tweet_text",
    "tweet_author",
    "tweet_published_at",
    "reply_count",
    "retweet_count",
    "like_count",
    "view_count",
    "conversation_id",
    "is_reply",
    "parent_tweet_url",
    "extraction_method",
    "retrieved_at",
    "status_extraccion",
    "error_type",
    "error_detail",
    "session_state_file",
    "headless",
    "text_expansion_attempted",
    "text_expanded",
]

QUERY_SUMMARY_COLUMNS = [
    "query_index",
    "query",
    "status",
    "tweets_detected",
    "tweets_saved",
    "replies_saved",
    "items_failed",
    "scrolls_executed",
    "duration_seconds",
]


class ExitCode(IntEnum):
    SUCCESS = 0
    PARTIAL_SUCCESS = 1
    FAILED_CONFIG = 2
    FAILED_PLATFORM = 3
    FAILED_WRITE = 4


class TwitterExtractorError(Exception):
    """Base de errores del extractor."""


class ConfigurationError(TwitterExtractorError):
    """Error fatal de configuración."""


class SessionStateError(TwitterExtractorError):
    """Error fatal relacionado con sesión persistida."""


class PlatformRuntimeError(TwitterExtractorError):
    """Error fatal de Playwright, navegación o plataforma."""


class OutputWriteError(TwitterExtractorError):
    """Error fatal de escritura o publicación."""


@dataclass(slots=True)
class WeekPartition:
    start_date: date
    end_date: date
    week_name: str
    naming_start_date: date
    naming_end_date: date


@dataclass(slots=True)
class QuerySpec:
    query_index: int
    query: str
    source: str


@dataclass(slots=True)
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
    session_state_file: Path
    run_id: str
    run_timestamp: str
    queries: list[QuerySpec]
    queries_source: str
    log_level: str
    overwrite: bool
    publish_canonical: bool
    max_scrolls: int
    max_tweets_per_query: int
    max_replies_per_tweet: int
    include_replies: bool
    headless: bool
    pause_seconds: float
    dry_run: bool
    config_file: Path | None = None


@dataclass(slots=True)
class ArtifactRecord:
    name: str
    artifact_type: str
    path: str
    description: str
    timestamp: str
    size_bytes: int


@dataclass(slots=True)
class ErrorRecord:
    stage: str
    scope: str
    message: str
    timestamp: str
    fatal: bool
    error_type: str
    query_index: int | None = None
    query: str | None = None
    tweet_url: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TweetExtractionRecord:
    run_id: str
    week_name: str
    source_platform: str
    query: str
    query_index: int
    tweet_url: str
    tweet_id: str
    tweet_text: str
    tweet_author: str
    tweet_published_at: str
    reply_count: int | None
    retweet_count: int | None
    like_count: int | None
    view_count: int | None
    conversation_id: str
    is_reply: bool
    parent_tweet_url: str
    extraction_method: str
    retrieved_at: str
    status_extraccion: str
    error_type: str
    error_detail: str
    session_state_file: str
    headless: bool
    text_expansion_attempted: bool
    text_expanded: bool


@dataclass(slots=True)
class QueryExecutionResult:
    query_spec: QuerySpec
    status: str
    tweets_detected: int
    tweets_saved: int
    replies_saved: int
    items_failed: int
    scrolls_executed: int
    duration_seconds: float
    rows: list[TweetExtractionRecord] = field(default_factory=list)
    errors: list[ErrorRecord] = field(default_factory=list)


@dataclass(slots=True)
class RunExecutionResult:
    status: str
    exit_code: int
    started_at: str
    finished_at: str
    duration_seconds: float
    query_results: list[QueryExecutionResult]
    artifact_paths: dict[str, Path]
    artifact_records: list[ArtifactRecord]
    errors: list[ErrorRecord]
    notes: list[str]
    playwright_used: bool
    session_state_used: str
    session_state_validated: bool
    skipped_existing_outputs: bool = False


def now_utc_text() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def serialize_for_json(value: Any) -> Any:
    if is_dataclass(value):
        return {key: serialize_for_json(item) for key, item in asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): serialize_for_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [serialize_for_json(item) for item in value]
    return value


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extractor profesional de X/Twitter para Radar. Busca tweets por query "
            "y rango temporal, extrae tweets visibles y replies opcionales, y guarda "
            "artefactos trazables por corrida."
        )
    )
    parser.add_argument("--since", help="Fecha inicial de búsqueda (YYYY-MM-DD).")
    parser.add_argument("--until", help="Fecha final de búsqueda (YYYY-MM-DD).")
    parser.add_argument(
        "--queries-file",
        help="Archivo TXT/JSON/CSV con queries. Si se omite, usa twitter_queries_canonical.txt.",
    )
    parser.add_argument(
        "--query",
        dest="queries",
        action="append",
        default=[],
        help="Query directa por CLI. Repite --query para varias.",
    )
    parser.add_argument("--config-file", help="Archivo JSON opcional con configuración base.")
    parser.add_argument(
        "--output-dir",
        help=f"Directorio raíz de salida. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--session-state-file",
        help=f"Archivo de sesión persistida de X/Twitter. Default: {DEFAULT_SESSION_STATE_FILE}",
    )
    parser.add_argument("--run-id", help=f"Identificador semántico de corrida. Default: {DEFAULT_RUN_ID}")
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help=f"Nivel de logging. Default: {DEFAULT_LOG_LEVEL}",
    )
    parser.add_argument("--overwrite", action="store_true", help="Permite sobrescribir artefactos canónicos.")
    parser.add_argument(
        "--publish-canonical",
        action="store_true",
        help="Publica una copia canónica al nivel de la semana además del run_dir.",
    )
    parser.add_argument(
        "--week-name-mode",
        choices=WEEK_NAME_MODE_CHOICES,
        help="Política de naming semanal: exact_range o canonical_monday_sunday.",
    )
    parser.add_argument(
        "--max-scrolls",
        type=int,
        help=f"Máximo de scrolls por query. Default: {DEFAULT_MAX_SCROLLS}",
    )
    parser.add_argument(
        "--max-tweets-per-query",
        type=int,
        help=f"Máximo de tweets top-level por query. Default: {DEFAULT_MAX_TWEETS_PER_QUERY}",
    )
    parser.add_argument(
        "--max-replies-per-tweet",
        type=int,
        help=f"Máximo de replies a guardar por tweet. Default: {DEFAULT_MAX_REPLIES_PER_TWEET}",
    )
    parser.add_argument("--headless", dest="headless", action="store_true", help="Ejecuta el navegador en modo headless.")
    parser.add_argument("--headed", dest="headless", action="store_false", help="Ejecuta el navegador en modo visible.")
    parser.set_defaults(headless=DEFAULT_HEADLESS)
    parser.add_argument(
        "--pause",
        type=float,
        help=f"Pausa base entre scrolls y navegación en segundos. Default: {DEFAULT_PAUSE_SECONDS}",
    )
    parser.add_argument(
        "--include-replies",
        dest="include_replies",
        action="store_true",
        help="Extrae replies para cada tweet extraído.",
    )
    parser.add_argument(
        "--no-replies",
        dest="include_replies",
        action="store_false",
        help="Desactiva la extracción de replies.",
    )
    parser.set_defaults(include_replies=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida configuración, crea artefactos base y evita abrir navegador.",
    )
    return parser.parse_args(argv)


def load_config_file(config_file: Path) -> dict[str, Any]:
    if not config_file.exists():
        raise ConfigurationError(f"No existe el archivo de configuración: {config_file}")
    try:
        payload = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"JSON inválido en config-file: {config_file}") from exc
    if not isinstance(payload, dict):
        raise ConfigurationError("El config-file debe contener un objeto JSON.")
    return payload


def merge_config_sources(args: argparse.Namespace) -> dict[str, Any]:
    cli = vars(args).copy()
    merged: dict[str, Any] = {}
    config_file_raw = cli.get("config_file")
    if config_file_raw:
        merged.update(load_config_file(Path(str(config_file_raw)).expanduser().resolve()))

    for key, value in cli.items():
        if key == "queries":
            if value:
                merged[key] = value
            continue
        if value is not None:
            merged[key] = value
    return merged


def parse_date_str(raw_value: str, label: str) -> date:
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ConfigurationError(f"{label} inválida '{raw_value}', usa YYYY-MM-DD.") from exc


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


def resolve_week_partition(since: date, until: date, mode: str) -> WeekPartition:
    if mode == WEEK_MODE_EXACT:
        naming_start = since
        naming_end = until
    elif mode == WEEK_MODE_CANONICAL:
        naming_start = since - timedelta(days=since.weekday())
        naming_end = until + timedelta(days=(6 - until.weekday()))
    else:  # pragma: no cover
        raise ConfigurationError(f"Modo semanal no soportado: {mode}")
    label = f"semana_{format_spanish_date(naming_start)}_{format_spanish_date(naming_end)}_{naming_end:%y}"
    week_name = f"{naming_start.isoformat()}_{label}"
    return WeekPartition(
        start_date=since,
        end_date=until,
        week_name=week_name,
        naming_start_date=naming_start,
        naming_end_date=naming_end,
    )


def load_queries_from_file(queries_file: Path) -> tuple[list[QuerySpec], str]:
    if not queries_file.exists():
        raise ConfigurationError(f"No existe el archivo de queries: {queries_file}")

    suffix = queries_file.suffix.lower()
    query_specs: list[QuerySpec] = []
    if suffix == ".json":
        payload = json.loads(queries_file.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ConfigurationError("El JSON de queries debe ser una lista.")
        for index, item in enumerate(payload, start=1):
            if isinstance(item, str):
                query = item.strip()
            elif isinstance(item, dict):
                query = str(item.get("query", "")).strip()
            else:
                raise ConfigurationError("El JSON de queries debe contener strings o dicts.")
            if query:
                query_specs.append(QuerySpec(query_index=index, query=query, source=str(queries_file)))
    elif suffix == ".csv":
        dataframe = pd.read_csv(queries_file)
        if "query" not in dataframe.columns:
            raise ConfigurationError("El CSV de queries debe incluir la columna 'query'.")
        for index, row in enumerate(dataframe.to_dict(orient="records"), start=1):
            query = str(row.get("query", "")).strip()
            if query:
                query_specs.append(QuerySpec(query_index=index, query=query, source=str(queries_file)))
    else:
        logical_index = 0
        for line in queries_file.read_text(encoding="utf-8").splitlines():
            query = line.strip()
            if not query or query.startswith("#"):
                continue
            logical_index += 1
            query_specs.append(QuerySpec(query_index=logical_index, query=query, source=str(queries_file)))

    if not query_specs:
        raise ConfigurationError("El archivo de queries no produjo ninguna query válida.")
    return query_specs, str(queries_file)


def load_queries_from_cli(queries: Sequence[str]) -> tuple[list[QuerySpec], str]:
    query_specs = [
        QuerySpec(query_index=index, query=query.strip(), source="cli")
        for index, query in enumerate(queries, start=1)
        if query and query.strip()
    ]
    if not query_specs:
        raise ConfigurationError("Las queries enviadas por CLI no contienen valores válidos.")
    return query_specs, "cli"


def load_default_queries() -> tuple[list[QuerySpec], str]:
    if DEFAULT_QUERIES_FILE.exists():
        return load_queries_from_file(DEFAULT_QUERIES_FILE)
    query_specs = [
        QuerySpec(query_index=index, query=query, source="default_builtin")
        for index, query in enumerate(DEFAULT_CANONICAL_QUERIES, start=1)
    ]
    return query_specs, "default_builtin"


def resolve_config(
    args: argparse.Namespace,
    *,
    script_name: str,
    script_path: Path,
    entrypoint_alias: str,
) -> ResolvedConfig:
    merged = merge_config_sources(args)

    since_raw = merged.get("since")
    until_raw = merged.get("until")
    if not since_raw or not until_raw:
        raise ConfigurationError("Debes definir --since y --until o proveerlos en --config-file.")

    since = parse_date_str(str(since_raw), "since")
    until = parse_date_str(str(until_raw), "until")
    if until < since:
        raise ConfigurationError("--until no puede ser menor que --since.")

    queries_file_raw = merged.get("queries_file")
    queries_cli = merged.get("queries", [])
    if queries_file_raw:
        queries_file = Path(str(queries_file_raw)).expanduser().resolve()
        queries, queries_source = load_queries_from_file(queries_file)
    elif queries_cli:
        queries, queries_source = load_queries_from_cli(queries_cli)
    else:
        queries, queries_source = load_default_queries()

    week_name_mode = str(merged.get("week_name_mode", WEEK_MODE_EXACT))
    week_partition = resolve_week_partition(since, until, week_name_mode)

    output_root_dir = Path(str(merged.get("output_dir", DEFAULT_OUTPUT_DIR))).expanduser().resolve()
    session_state_file = Path(str(merged.get("session_state_file", DEFAULT_SESSION_STATE_FILE))).expanduser().resolve()
    run_id = str(merged.get("run_id", DEFAULT_RUN_ID)).strip() or DEFAULT_RUN_ID
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    week_dir = output_root_dir / week_partition.week_name
    run_dir = week_dir / "runs" / f"{run_id}_{run_timestamp}"

    max_scrolls = int(merged.get("max_scrolls", DEFAULT_MAX_SCROLLS))
    max_tweets_per_query = int(merged.get("max_tweets_per_query", DEFAULT_MAX_TWEETS_PER_QUERY))
    max_replies_per_tweet = int(merged.get("max_replies_per_tweet", DEFAULT_MAX_REPLIES_PER_TWEET))
    pause_seconds = float(merged.get("pause", DEFAULT_PAUSE_SECONDS))

    if max_scrolls <= 0:
        raise ConfigurationError("--max-scrolls debe ser mayor que 0.")
    if max_tweets_per_query <= 0:
        raise ConfigurationError("--max-tweets-per-query debe ser mayor que 0.")
    if max_replies_per_tweet <= 0:
        raise ConfigurationError("--max-replies-per-tweet debe ser mayor que 0.")
    if pause_seconds < 0:
        raise ConfigurationError("--pause no puede ser negativo.")

    config_file_raw = merged.get("config_file")
    config_file = Path(str(config_file_raw)).expanduser().resolve() if config_file_raw else None

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
        session_state_file=session_state_file,
        run_id=run_id,
        run_timestamp=run_timestamp,
        queries=queries,
        queries_source=queries_source,
        log_level=str(merged.get("log_level", DEFAULT_LOG_LEVEL)).upper(),
        overwrite=bool(merged.get("overwrite", False)),
        publish_canonical=bool(merged.get("publish_canonical", False)),
        max_scrolls=max_scrolls,
        max_tweets_per_query=max_tweets_per_query,
        max_replies_per_tweet=max_replies_per_tweet,
        include_replies=bool(merged.get("include_replies", True)),
        headless=bool(merged.get("headless", DEFAULT_HEADLESS)),
        pause_seconds=pause_seconds,
        dry_run=bool(merged.get("dry_run", False)),
        config_file=config_file,
    )


def setup_logging(level: str) -> logging.Logger:
    logger = logging.getLogger(SCRIPT_COMPONENT)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    if logger.handlers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    return logger


def configure_output_layout(config: ResolvedConfig) -> None:
    config.week_dir.mkdir(parents=True, exist_ok=True)
    if config.run_dir.exists():
        if config.overwrite:
            shutil.rmtree(config.run_dir)
        else:
            raise OutputWriteError(f"El run_dir ya existe y requiere overwrite: {config.run_dir}")
    config.run_dir.mkdir(parents=True, exist_ok=True)


def ensure_failure_output_layout(config: ResolvedConfig) -> None:
    config.week_dir.mkdir(parents=True, exist_ok=True)
    config.run_dir.mkdir(parents=True, exist_ok=True)


def canonical_main_csv_path(config: ResolvedConfig) -> Path:
    return config.week_dir / f"{MAIN_CSV_PREFIX}_{config.week_partition.week_name}.csv"


def week_has_existing_outputs(config: ResolvedConfig) -> bool:
    return canonical_main_csv_path(config).exists()


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


def safe_json_load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SessionStateError(f"JSON inválido en session-state-file: {path}") from exc


def parse_metric_value(raw_value: str | None) -> int | None:
    if not raw_value:
        return None
    normalized = raw_value.replace(",", "").strip().upper()
    match = re.search(r"(\d+(?:\.\d+)?)([KMB])?", normalized)
    if not match:
        return None
    base_value = float(match.group(1))
    suffix = match.group(2)
    multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(suffix, 1)
    return int(base_value * multiplier)


def extract_tweet_id(tweet_url: str) -> str:
    if not tweet_url:
        return ""
    match = re.search(r"/status/(\d+)", tweet_url)
    return match.group(1) if match else ""


def clean_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def parse_datetime(raw_value: str | None) -> datetime | None:
    if not raw_value:
        return None
    value = raw_value.strip()
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def detect_login_required(page_url: str) -> bool:
    lowered = page_url.lower()
    return any(token in lowered for token in ("/i/flow/login", "/login", "/account/access"))


def build_query_search_string(query: str, since: date, until: date) -> str:
    return f"{query} since:{since.isoformat()} until:{until.isoformat()}"


async def load_session_state(config: ResolvedConfig) -> None:
    if not config.session_state_file.exists():
        raise SessionStateError(
            f"No existe el archivo de sesión: {config.session_state_file}. "
            "Genera primero x_state.json con un login válido."
        )
    payload = safe_json_load(config.session_state_file)
    if not payload:
        raise SessionStateError(f"El archivo de sesión está vacío o inválido: {config.session_state_file}")


async def build_browser_context(config: ResolvedConfig, logger: logging.Logger) -> tuple[Any, Browser, BrowserContext, Page]:
    if async_playwright is None:
        raise PlatformRuntimeError(
            "Playwright no está instalado. Instala 'playwright' y ejecuta 'playwright install chromium'."
        ) from PLAYWRIGHT_IMPORT_ERROR

    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.launch(headless=config.headless)
        context = await browser.new_context(
            storage_state=str(config.session_state_file),
            viewport=DEFAULT_VIEWPORT,
            user_agent=DEFAULT_USER_AGENT,
            locale="es-MX",
            timezone_id="America/Mexico_City",
        )
        context.set_default_timeout(DEFAULT_NAV_TIMEOUT_MS)
        context.set_default_navigation_timeout(DEFAULT_NAV_TIMEOUT_MS)
        page = await context.new_page()
        logger.info(
            "Playwright inicializado | headless=%s session_state_file=%s",
            config.headless,
            config.session_state_file,
        )
        return playwright, browser, context, page
    except Exception as exc:
        try:
            await playwright.stop()
        except Exception:
            pass
        raise PlatformRuntimeError("No se pudo inicializar Playwright o abrir Chromium.") from exc


async def close_browser_resources(playwright: Any, browser: Browser | None, context: BrowserContext | None) -> None:
    try:
        if context is not None:
            await context.close()
    except Exception:
        pass
    try:
        if browser is not None:
            await browser.close()
    except Exception:
        pass
    try:
        if playwright is not None:
            await playwright.stop()
    except Exception:
        pass


async def validate_session(page: Page, logger: logging.Logger) -> None:
    await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=DEFAULT_NAV_TIMEOUT_MS)
    await page.wait_for_timeout(1500)
    if detect_login_required(page.url):
        raise SessionStateError("La sesión persistida parece expirada o X/Twitter solicitó login.")
    logger.info("Sesión persistida validada correctamente contra X/Twitter.")


async def expand_tweet_text(page: Page, article: Any) -> tuple[bool, bool]:
    attempted = False
    selectors = [
        'text=/^(Show more|Mostrar más)$/i',
        'text=/^(Read more|Leer más)$/i',
    ]
    for selector in selectors:
        try:
            locator = article.locator(selector)
            if await locator.count():
                attempted = True
                await locator.first.click(timeout=1500)
                await page.wait_for_timeout(250)
                return attempted, True
        except Exception:
            attempted = True
            continue
    return attempted, False


async def extract_tweet_text(page: Page, article: Any) -> tuple[str, bool, bool]:
    attempted, expanded = await expand_tweet_text(page, article)
    text_locator = article.locator('[data-testid="tweetText"]')
    if not await text_locator.count():
        return "", attempted, expanded

    try:
        text_parts = await text_locator.evaluate_all(
            """nodes => nodes
            .map(node => (node.textContent || '').replace(/\\s+/g, ' ').trim())
            .filter(Boolean)"""
        )
    except Exception:
        text_parts = [clean_text(item) for item in await text_locator.all_inner_texts()]

    unique_parts: list[str] = []
    seen: set[str] = set()
    for part in text_parts:
        cleaned = clean_text(part)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique_parts.append(cleaned)
    return " ".join(unique_parts).strip(), attempted, expanded


async def extract_engagement_metrics(article: Any) -> dict[str, int | None]:
    metrics = {
        "reply_count": None,
        "retweet_count": None,
        "like_count": None,
        "view_count": None,
    }
    selectors = {
        "reply_count": '[data-testid="reply"]',
        "retweet_count": '[data-testid="retweet"]',
        "like_count": '[data-testid="like"]',
    }
    for field, selector in selectors.items():
        try:
            locator = article.locator(selector)
            if await locator.count():
                aria_label = await locator.first.get_attribute("aria-label")
                if not aria_label:
                    aria_label = clean_text(await locator.first.inner_text())
                metrics[field] = parse_metric_value(aria_label)
        except Exception:
            continue

    try:
        analytics_locator = article.locator('a[href*="/analytics"]')
        if await analytics_locator.count():
            analytics_text = await analytics_locator.first.get_attribute("aria-label")
            if not analytics_text:
                analytics_text = clean_text(await analytics_locator.first.inner_text())
            metrics["view_count"] = parse_metric_value(analytics_text)
    except Exception:
        pass
    return metrics


async def extract_tweet_card(
    page: Page,
    article: Any,
    *,
    config: ResolvedConfig,
    query_spec: QuerySpec,
    is_reply: bool,
    parent_tweet_url: str,
    retrieved_at: str,
    extraction_method: str,
) -> tuple[TweetExtractionRecord | None, list[ErrorRecord]]:
    errors: list[ErrorRecord] = []

    try:
        tweet_text, expansion_attempted, text_expanded = await extract_tweet_text(page, article)

        time_locator = article.locator("time")
        tweet_published_at = ""
        tweet_url = ""
        if await time_locator.count():
            tweet_published_at = await time_locator.first.get_attribute("datetime") or ""
            parent_link = time_locator.first.locator("xpath=ancestor::a[1]")
            if await parent_link.count():
                href = await parent_link.get_attribute("href")
                if href:
                    tweet_url = "https://x.com" + href

        author = ""
        user_locator = article.locator('[data-testid="User-Name"]')
        if await user_locator.count():
            user_text = clean_text(await user_locator.first.inner_text())
            handle_match = re.search(r"@\w+", user_text)
            author = handle_match.group(0) if handle_match else user_text

        metrics = await extract_engagement_metrics(article)
        tweet_id = extract_tweet_id(tweet_url)
        conversation_id = extract_tweet_id(parent_tweet_url) if is_reply and parent_tweet_url else tweet_id

        if not tweet_text and not tweet_url:
            errors.append(
                ErrorRecord(
                    stage="extract_tweet_card",
                    scope="tweet",
                    message="No se pudo extraer texto ni URL del tweet visible.",
                    timestamp=now_utc_text(),
                    fatal=False,
                    error_type="tweet_parse_empty",
                    query_index=query_spec.query_index,
                    query=query_spec.query,
                )
            )
            return None, errors

        record = TweetExtractionRecord(
            run_id=config.run_id,
            week_name=config.week_partition.week_name,
            source_platform=SOURCE_PLATFORM,
            query=query_spec.query,
            query_index=query_spec.query_index,
            tweet_url=tweet_url,
            tweet_id=tweet_id,
            tweet_text=tweet_text,
            tweet_author=author,
            tweet_published_at=tweet_published_at,
            reply_count=metrics["reply_count"],
            retweet_count=metrics["retweet_count"],
            like_count=metrics["like_count"],
            view_count=metrics["view_count"],
            conversation_id=conversation_id,
            is_reply=is_reply,
            parent_tweet_url=parent_tweet_url,
            extraction_method=extraction_method,
            retrieved_at=retrieved_at,
            status_extraccion="extracted_ok",
            error_type="",
            error_detail="",
            session_state_file=str(config.session_state_file),
            headless=config.headless,
            text_expansion_attempted=expansion_attempted,
            text_expanded=text_expanded,
        )
        return record, errors
    except Exception as exc:
        errors.append(
            ErrorRecord(
                stage="extract_tweet_card",
                scope="tweet",
                message=str(exc),
                timestamp=now_utc_text(),
                fatal=False,
                error_type=f"tweet_parse_error:{type(exc).__name__}",
                query_index=query_spec.query_index,
                query=query_spec.query,
                tweet_url=parent_tweet_url if is_reply else None,
            )
        )
        return None, errors


async def goto_search(page: Page, query: str, logger: logging.Logger) -> str:
    query_encoded = quote(query.strip(), safe=":@()")
    url = f"https://x.com/search?q={query_encoded}&src=typed_query&f=live"
    last_error: Exception | None = None
    for attempt in range(1, DEFAULT_NAV_RETRIES + 1):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_NAV_TIMEOUT_MS)
            await page.wait_for_timeout(2500)
            if detect_login_required(page.url):
                raise SessionStateError("La sesión fue rechazada al abrir la búsqueda en X/Twitter.")
            logger.info("Búsqueda abierta | query=%s", query)
            return url
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Intento de navegación fallido | query=%s intento=%s/%s error=%s",
                query,
                attempt,
                DEFAULT_NAV_RETRIES,
                exc,
            )
            await page.wait_for_timeout(1500)
    raise PlatformRuntimeError(
        f"No se pudo abrir la búsqueda tras {DEFAULT_NAV_RETRIES} intentos. URL: {url}. Último error: {last_error}"
    )


async def extract_visible_tweets(
    page: Page,
    *,
    config: ResolvedConfig,
    query_spec: QuerySpec,
    is_reply: bool,
    parent_tweet_url: str,
    extraction_method: str,
) -> tuple[list[TweetExtractionRecord], list[ErrorRecord]]:
    records: list[TweetExtractionRecord] = []
    errors: list[ErrorRecord] = []
    articles = page.locator('article[data-testid="tweet"]')
    article_count = await articles.count()
    retrieved_at = now_utc_text()
    for index in range(article_count):
        article = articles.nth(index)
        record, record_errors = await extract_tweet_card(
            page,
            article,
            config=config,
            query_spec=query_spec,
            is_reply=is_reply,
            parent_tweet_url=parent_tweet_url,
            retrieved_at=retrieved_at,
            extraction_method=extraction_method,
        )
        if record:
            records.append(record)
        errors.extend(record_errors)
    return records, errors


def build_dedupe_key(record: TweetExtractionRecord) -> tuple[str, str, str]:
    return (
        record.tweet_url or "",
        record.tweet_published_at or "",
        record.tweet_text[:120],
    )


async def extract_replies(
    page: Page,
    *,
    config: ResolvedConfig,
    query_spec: QuerySpec,
    tweet_url: str,
    logger: logging.Logger,
) -> tuple[list[TweetExtractionRecord], list[ErrorRecord]]:
    if not tweet_url:
        return [], []

    replies: list[TweetExtractionRecord] = []
    errors: list[ErrorRecord] = []
    seen: set[tuple[str, str, str]] = set()
    stagnation_count = 0
    last_count = 0
    iteration = 0

    logger.info("Extrayendo replies | query=%s tweet_url=%s", query_spec.query, tweet_url)
    await page.goto(tweet_url, wait_until="domcontentloaded", timeout=DEFAULT_NAV_TIMEOUT_MS)
    await page.wait_for_timeout(2000)
    if detect_login_required(page.url):
        raise SessionStateError("La sesión fue rechazada al abrir la vista de replies.")

    while (
        len(replies) < config.max_replies_per_tweet
        and stagnation_count < 6
        and iteration < DEFAULT_REPLY_SCROLLS
    ):
        visible_records, visible_errors = await extract_visible_tweets(
            page,
            config=config,
            query_spec=query_spec,
            is_reply=True,
            parent_tweet_url=tweet_url,
            extraction_method="playwright_reply_page",
        )
        errors.extend(visible_errors)
        for record in visible_records:
            if record.tweet_url == tweet_url:
                continue
            key = build_dedupe_key(record)
            if key in seen:
                continue
            seen.add(key)
            parsed_dt = parse_datetime(record.tweet_published_at)
            if not parsed_dt:
                errors.append(
                    ErrorRecord(
                        stage="extract_replies",
                        scope="tweet",
                        message="No se pudo parsear la fecha del reply.",
                        timestamp=now_utc_text(),
                        fatal=False,
                        error_type="reply_datetime_invalid",
                        query_index=query_spec.query_index,
                        query=query_spec.query,
                        tweet_url=record.tweet_url,
                    )
                )
                continue
            if config.since <= parsed_dt.date() <= config.until:
                replies.append(record)
                if len(replies) >= config.max_replies_per_tweet:
                    break

        await page.mouse.wheel(0, 2600)
        await page.wait_for_timeout(int(config.pause_seconds * 1000))
        if len(replies) == last_count:
            stagnation_count += 1
        else:
            stagnation_count = 0
            last_count = len(replies)
        iteration += 1

    return replies, errors


async def search_query(
    page: Page,
    *,
    config: ResolvedConfig,
    query_spec: QuerySpec,
    logger: logging.Logger,
) -> QueryExecutionResult:
    started = time.perf_counter()
    errors: list[ErrorRecord] = []
    rows: list[TweetExtractionRecord] = []
    seen: set[tuple[str, str, str]] = set()
    processed_reply_urls: set[str] = set()
    stagnation_count = 0
    last_count = 0
    scrolls_executed = 0
    tweets_detected = 0

    search_string = build_query_search_string(query_spec.query, config.since, config.until)
    await goto_search(page, search_string, logger)

    while (
        len([row for row in rows if not row.is_reply]) < config.max_tweets_per_query
        and stagnation_count < 8
        and scrolls_executed < config.max_scrolls
    ):
        visible_records, visible_errors = await extract_visible_tweets(
            page,
            config=config,
            query_spec=query_spec,
            is_reply=False,
            parent_tweet_url="",
            extraction_method="playwright_live_search",
        )
        errors.extend(visible_errors)
        tweets_detected += len(visible_records)

        visible_dates: list[date] = []
        for record in visible_records:
            key = build_dedupe_key(record)
            if key in seen:
                continue
            seen.add(key)

            parsed_dt = parse_datetime(record.tweet_published_at)
            if not parsed_dt:
                errors.append(
                    ErrorRecord(
                        stage="search_query",
                        scope="tweet",
                        message="No se pudo parsear la fecha del tweet.",
                        timestamp=now_utc_text(),
                        fatal=False,
                        error_type="tweet_datetime_invalid",
                        query_index=query_spec.query_index,
                        query=query_spec.query,
                        tweet_url=record.tweet_url,
                    )
                )
                continue

            visible_dates.append(parsed_dt.date())
            if config.since <= parsed_dt.date() <= config.until:
                rows.append(record)
                if len([row for row in rows if not row.is_reply]) >= config.max_tweets_per_query:
                    break

        if visible_dates and min(visible_dates) < config.since:
            logger.info("Se alcanzaron tweets anteriores al rango | query=%s", query_spec.query)
            break

        await page.mouse.wheel(0, 2600)
        await page.wait_for_timeout(int(config.pause_seconds * 1000))
        scrolls_executed += 1
        top_level_count = len([row for row in rows if not row.is_reply])
        if top_level_count == last_count:
            stagnation_count += 1
        else:
            stagnation_count = 0
            last_count = top_level_count

    if config.include_replies:
        top_level_rows = [row for row in rows if not row.is_reply]
        for record in top_level_rows:
            if not record.tweet_url or record.tweet_url in processed_reply_urls:
                continue
            processed_reply_urls.add(record.tweet_url)
            try:
                replies, reply_errors = await extract_replies(
                    page,
                    config=config,
                    query_spec=query_spec,
                    tweet_url=record.tweet_url,
                    logger=logger,
                )
                errors.extend(reply_errors)
                for reply in replies:
                    key = build_dedupe_key(reply)
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(reply)
            except SessionStateError:
                raise
            except Exception as exc:
                errors.append(
                    ErrorRecord(
                        stage="extract_replies",
                        scope="tweet",
                        message=str(exc),
                        timestamp=now_utc_text(),
                        fatal=False,
                        error_type=f"reply_extraction_error:{type(exc).__name__}",
                        query_index=query_spec.query_index,
                        query=query_spec.query,
                        tweet_url=record.tweet_url,
                    )
                )

    top_level_rows = [row for row in rows if not row.is_reply]
    reply_rows = [row for row in rows if row.is_reply]
    items_failed = len(errors)
    status = "success"
    if errors and rows:
        status = "partial_success"
    if errors and not rows:
        status = "failed"

    logger.info(
        "Query procesada | query_index=%s query=%s tweets_guardados=%s replies_guardados=%s errores=%s scrolls=%s",
        query_spec.query_index,
        query_spec.query,
        len(top_level_rows),
        len(reply_rows),
        items_failed,
        scrolls_executed,
    )

    return QueryExecutionResult(
        query_spec=query_spec,
        status=status,
        tweets_detected=tweets_detected,
        tweets_saved=len(top_level_rows),
        replies_saved=len(reply_rows),
        items_failed=items_failed,
        scrolls_executed=scrolls_executed,
        duration_seconds=round(time.perf_counter() - started, 3),
        rows=rows,
        errors=errors,
    )


def build_dataframe(query_results: Sequence[QueryExecutionResult]) -> pd.DataFrame:
    rows = [serialize_for_json(record) for result in query_results for record in result.rows]
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return pd.DataFrame(columns=DATA_COLUMNS)
    for column in DATA_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""
    return dataframe[DATA_COLUMNS]


def build_queries_summary_dataframe(query_results: Sequence[QueryExecutionResult]) -> pd.DataFrame:
    rows = []
    for result in query_results:
        rows.append(
            {
                "query_index": result.query_spec.query_index,
                "query": result.query_spec.query,
                "status": result.status,
                "tweets_detected": result.tweets_detected,
                "tweets_saved": result.tweets_saved,
                "replies_saved": result.replies_saved,
                "items_failed": result.items_failed,
                "scrolls_executed": result.scrolls_executed,
                "duration_seconds": result.duration_seconds,
            }
        )
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return pd.DataFrame(columns=QUERY_SUMMARY_COLUMNS)
    for column in QUERY_SUMMARY_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""
    return dataframe[QUERY_SUMMARY_COLUMNS]


def flatten_errors(query_results: Sequence[QueryExecutionResult]) -> list[ErrorRecord]:
    return [error for result in query_results for error in result.errors]


def determine_run_status(query_results: Sequence[QueryExecutionResult], errors: Sequence[ErrorRecord]) -> str:
    rows_count = sum(len(result.rows) for result in query_results)
    if rows_count and not errors:
        return "success"
    if rows_count and errors:
        return "partial_success"
    return "failed"


def build_notes(config: ResolvedConfig, run_status: str, session_state_validated: bool, playwright_used: bool) -> list[str]:
    notes = [
        "Extractor puro de X/Twitter: búsqueda live, sesión persistida, extracción de tweets y replies opcionales.",
        "No realiza NLP, clasificación, scoring político, consolidación multi-fuente ni modelado.",
        "Las queries canónicas son específicas al caso Tampico y no incluyen la query ambigua 'presidenta municipal'.",
    ]
    if config.week_name_mode == WEEK_MODE_EXACT:
        notes.append("El nombre semanal usa exactamente since y until, sin alineación automática a lunes-domingo.")
    else:
        notes.append("El nombre semanal se alinea a lunes-domingo; la búsqueda real mantiene since y until exactos.")
    if session_state_validated:
        notes.append("La sesión persistida de X/Twitter se validó correctamente antes de extraer.")
    else:
        notes.append("La validación de sesión no se ejecutó porque la corrida fue dry-run.")
    if config.include_replies:
        notes.append("La extracción de replies quedó habilitada y limitada por max_replies_per_tweet.")
    else:
        notes.append("La extracción de replies quedó deshabilitada por configuración.")
    if config.headless:
        notes.append("Playwright quedó configurado en modo headless.")
    else:
        notes.append("Playwright quedó configurado en modo visible para debugging.")
    if playwright_used:
        notes.append("Playwright se utilizó efectivamente durante la corrida.")
    if run_status == "partial_success":
        notes.append("La corrida terminó con errores recuperables; revisar errores_detectados.json.")
    if run_status == "failed":
        notes.append("La corrida no logró materializar tweets válidos; revisar summary y errores_detectados.json.")
    return notes


def map_status_to_exit_code(status: str) -> int:
    if status == "success":
        return ExitCode.SUCCESS
    if status == "partial_success":
        return ExitCode.PARTIAL_SUCCESS
    return ExitCode.FAILED_PLATFORM


def build_summary(
    config: ResolvedConfig,
    result: RunExecutionResult,
) -> dict[str, Any]:
    total_tweets_saved = sum(item.tweets_saved for item in result.query_results)
    total_replies_saved = sum(item.replies_saved for item in result.query_results)
    query_error_count = sum(len(item.errors) for item in result.query_results)
    run_level_error_count = max(0, len(result.errors) - query_error_count)
    return {
        "run_id": config.run_id,
        "status": result.status,
        "since": config.since.isoformat(),
        "until": config.until.isoformat(),
        "week_name": config.week_partition.week_name,
        "output_dir": str(config.run_dir),
        "total_queries": len(config.queries),
        "queries_processed": len(result.query_results),
        "queries_failed": sum(1 for item in result.query_results if item.status == "failed"),
        "total_tweets_detected": sum(item.tweets_detected for item in result.query_results),
        "total_tweets_saved": total_tweets_saved,
        "total_replies_saved": total_replies_saved,
        "total_items_failed": sum(item.items_failed for item in result.query_results) + run_level_error_count,
        "session_state_used": str(config.session_state_file),
        "session_state_validated": result.session_state_validated,
        "headless": config.headless,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "duration_seconds": result.duration_seconds,
        "week_name_mode": config.week_name_mode,
        "script_name": config.script_name,
        "script_version": config.script_version,
        "notes": list(result.notes),
    }


def build_metadata(
    config: ResolvedConfig,
    result: RunExecutionResult,
    artifact_paths: dict[str, Path],
) -> dict[str, Any]:
    query_error_count = sum(len(item.errors) for item in result.query_results)
    run_level_error_count = max(0, len(result.errors) - query_error_count)
    return {
        "run_id": config.run_id,
        "run_timestamp": config.run_timestamp,
        "script_name": config.script_name,
        "script_path": str(config.script_path),
        "script_version": config.script_version,
        "entrypoint_alias": config.entrypoint_alias,
        "helper_module_path": str(config.helper_module_path),
        "week_name": config.week_partition.week_name,
        "week_name_mode": config.week_name_mode,
        "search_window": {
            "since": config.since.isoformat(),
            "until": config.until.isoformat(),
            "naming_start_date": config.week_partition.naming_start_date.isoformat(),
            "naming_end_date": config.week_partition.naming_end_date.isoformat(),
        },
        "environment": {
            "cwd": os.getcwd(),
            "user": os.environ.get("USER") or os.environ.get("USERNAME") or "",
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        },
        "config": serialize_for_json(config),
        "execution": {
            "status": result.status,
            "exit_code": result.exit_code,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "duration_seconds": result.duration_seconds,
            "dry_run": config.dry_run,
            "skipped_existing_outputs": result.skipped_existing_outputs,
        },
        "counts": {
            "queries": len(config.queries),
            "queries_failed": sum(1 for item in result.query_results if item.status == "failed"),
            "tweets_detected": sum(item.tweets_detected for item in result.query_results),
            "tweets_saved": sum(item.tweets_saved for item in result.query_results),
            "replies_saved": sum(item.replies_saved for item in result.query_results),
            "items_failed": sum(item.items_failed for item in result.query_results) + run_level_error_count,
        },
        "session": {
            "session_state_file": str(config.session_state_file),
            "used": result.session_state_used,
            "validated": result.session_state_validated,
        },
        "playwright": {
            "required": True,
            "available": async_playwright is not None,
            "headless": config.headless,
            "used": result.playwright_used,
        },
        "dependencies": {
            "playwright": async_playwright is not None,
        },
        "artifact_paths": {key: str(path) for key, path in artifact_paths.items()},
        "errors": serialize_for_json(result.errors),
        "notes": list(result.notes),
        "navigation_strategy": {
            "search_mode": "x_live_search",
            "text_expansion": "show_more_click",
            "reply_strategy": "tweet_detail_page",
        },
    }


def publish_canonical_artifacts(
    config: ResolvedConfig,
    artifact_paths: dict[str, Path],
) -> dict[str, str]:
    if not config.publish_canonical:
        return {}
    targets = {
        "main_csv": canonical_main_csv_path(config),
        "raw_jsonl": config.week_dir / RAW_JSONL_FILENAME,
        "queries_csv": config.week_dir / QUERIES_FILENAME,
        "summary_json": config.week_dir / SUMMARY_FILENAME,
        "metadata_json": config.week_dir / METADATA_FILENAME,
        "parametros_json": config.week_dir / PARAMS_FILENAME,
        "manifest_json": config.week_dir / MANIFEST_FILENAME,
    }
    if "errors_json" in artifact_paths:
        targets["errors_json"] = config.week_dir / ERRORS_FILENAME
    published: dict[str, str] = {}
    for key, source_path in artifact_paths.items():
        target = targets.get(key)
        if not target:
            continue
        if target.exists():
            if config.overwrite:
                if target.is_file():
                    target.unlink()
                else:
                    shutil.rmtree(target)
            else:
                raise OutputWriteError(f"El artefacto canónico ya existe y requiere overwrite: {target}")
        shutil.copy2(source_path, target)
        published[key] = str(target)
    return published


def persist_outputs(
    config: ResolvedConfig,
    *,
    dataframe: pd.DataFrame,
    queries_summary_df: pd.DataFrame,
    raw_records: list[dict[str, Any]],
    result: RunExecutionResult,
    logger: logging.Logger,
) -> tuple[dict[str, Path], list[ArtifactRecord]]:
    artifact_paths: dict[str, Path] = {}
    artifact_records: list[ArtifactRecord] = []

    main_csv_path = config.run_dir / f"{MAIN_CSV_PREFIX}_{config.week_partition.week_name}.csv"
    dataframe.to_csv(main_csv_path, index=False, encoding="utf-8")
    artifact_paths["main_csv"] = main_csv_path
    add_artifact_record(artifact_records, main_csv_path, "dataset", "Tweets y replies materializados.")

    raw_jsonl_path = config.run_dir / RAW_JSONL_FILENAME
    with raw_jsonl_path.open("w", encoding="utf-8") as handle:
        for row in raw_records:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    artifact_paths["raw_jsonl"] = raw_jsonl_path
    add_artifact_record(artifact_records, raw_jsonl_path, "dataset", "Registro raw JSONL de tweets extraídos.")

    queries_path = config.run_dir / QUERIES_FILENAME
    queries_summary_df.to_csv(queries_path, index=False, encoding="utf-8")
    artifact_paths["queries_csv"] = queries_path
    add_artifact_record(artifact_records, queries_path, "summary_table", "Resumen operativo por query.")

    params_path = config.run_dir / PARAMS_FILENAME
    params_path.write_text(json.dumps(serialize_for_json(config), indent=2, ensure_ascii=False), encoding="utf-8")
    artifact_paths["parametros_json"] = params_path
    add_artifact_record(artifact_records, params_path, "parameters", "Parámetros efectivos de la corrida.")

    summary_payload = build_summary(config, result)
    summary_path = config.run_dir / SUMMARY_FILENAME
    summary_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    artifact_paths["summary_json"] = summary_path
    add_artifact_record(artifact_records, summary_path, "summary", "Resumen global de la corrida.")

    if result.errors:
        errors_path = config.run_dir / ERRORS_FILENAME
        errors_path.write_text(json.dumps(serialize_for_json(result.errors), indent=2, ensure_ascii=False), encoding="utf-8")
        artifact_paths["errors_json"] = errors_path
        add_artifact_record(artifact_records, errors_path, "errors", "Errores detectados durante la corrida.")

    log_path = config.run_dir / LOG_FILENAME
    if log_path.exists():
        artifact_paths["run_log"] = log_path
        add_artifact_record(artifact_records, log_path, "log", "Log operativo de la corrida.")

    metadata_path = config.run_dir / METADATA_FILENAME
    manifest_path = config.run_dir / MANIFEST_FILENAME
    artifact_paths["metadata_json"] = metadata_path
    artifact_paths["manifest_json"] = manifest_path

    metadata_payload = build_metadata(config, result, artifact_paths)
    metadata_path.write_text(json.dumps(metadata_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    add_artifact_record(artifact_records, metadata_path, "metadata", "Metadata completa y trazabilidad de la corrida.")

    manifest_record = ArtifactRecord(
        name=manifest_path.name,
        artifact_type="manifest",
        path=str(manifest_path),
        description="Inventario de artefactos de la corrida.",
        timestamp=now_utc_text(),
        size_bytes=0,
    )
    manifest_payload = [serialize_for_json(record) for record in artifact_records] + [serialize_for_json(manifest_record)]
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest_record.size_bytes = manifest_path.stat().st_size
    manifest_payload = [serialize_for_json(record) for record in artifact_records] + [serialize_for_json(manifest_record)]
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    artifact_records.append(manifest_record)

    published = publish_canonical_artifacts(config, artifact_paths)
    if published:
        logger.info("Artefactos canónicos publicados | total=%s", len(published))

    return artifact_paths, artifact_records


def build_dry_run_result(config: ResolvedConfig, logger: logging.Logger) -> RunExecutionResult:
    started_at = now_utc_text()
    finished_at = started_at
    duration_seconds = 0.0
    notes = build_notes(
        config,
        run_status="success",
        session_state_validated=False,
        playwright_used=False,
    )
    result = RunExecutionResult(
        status="success",
        exit_code=ExitCode.SUCCESS,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        query_results=[],
        artifact_paths={},
        artifact_records=[],
        errors=[],
        notes=notes,
        playwright_used=False,
        session_state_used=str(config.session_state_file),
        session_state_validated=False,
        skipped_existing_outputs=False,
    )
    dataframe = pd.DataFrame(columns=DATA_COLUMNS)
    queries_summary_df = pd.DataFrame(columns=QUERY_SUMMARY_COLUMNS)
    artifact_paths, artifact_records = persist_outputs(
        config,
        dataframe=dataframe,
        queries_summary_df=queries_summary_df,
        raw_records=[],
        result=result,
        logger=logger,
    )
    result.artifact_paths = artifact_paths
    result.artifact_records = artifact_records
    return result


async def run_extraction(config: ResolvedConfig, logger: logging.Logger) -> RunExecutionResult:
    configure_output_layout(config)
    log_path = config.run_dir / LOG_FILENAME
    if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logger.level)
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)

    logger.info(
        "Inicio de corrida | run_id=%s week_name=%s output_root=%s week_name_mode=%s",
        config.run_id,
        config.week_partition.week_name,
        config.output_root_dir,
        config.week_name_mode,
    )
    logger.info(
        "Parámetros efectivos | since=%s until=%s total_queries=%s max_scrolls=%s max_tweets_per_query=%s include_replies=%s headless=%s",
        config.since,
        config.until,
        len(config.queries),
        config.max_scrolls,
        config.max_tweets_per_query,
        config.include_replies,
        config.headless,
    )
    logger.info("Archivo de sesión | session_state_file=%s", config.session_state_file)

    if config.dry_run:
        logger.info("Dry-run activo; no se abrirá navegador ni se validará sesión.")
        return build_dry_run_result(config, logger)

    await load_session_state(config)

    playwright = None
    browser = None
    context = None
    page = None
    started_at = now_utc_text()
    started_perf = time.perf_counter()
    query_results: list[QueryExecutionResult] = []
    session_state_validated = False
    try:
        playwright, browser, context, page = await build_browser_context(config, logger)
        await validate_session(page, logger)
        session_state_validated = True

        for index, query_spec in enumerate(config.queries, start=1):
            logger.info("Procesando query %s/%s | query=%s", index, len(config.queries), query_spec.query)
            try:
                query_result = await search_query(page, config=config, query_spec=query_spec, logger=logger)
            except SessionStateError:
                raise
            except Exception as exc:
                query_result = QueryExecutionResult(
                    query_spec=query_spec,
                    status="failed",
                    tweets_detected=0,
                    tweets_saved=0,
                    replies_saved=0,
                    items_failed=1,
                    scrolls_executed=0,
                    duration_seconds=0.0,
                    rows=[],
                    errors=[
                        ErrorRecord(
                            stage="search_query",
                            scope="query",
                            message=str(exc),
                            timestamp=now_utc_text(),
                            fatal=False,
                            error_type=f"query_runtime_error:{type(exc).__name__}",
                            query_index=query_spec.query_index,
                            query=query_spec.query,
                        )
                    ],
                )
                logger.warning(
                    "Query con error recuperable | query_index=%s query=%s error=%s",
                    query_spec.query_index,
                    query_spec.query,
                    exc,
                )
            query_results.append(query_result)

        errors = flatten_errors(query_results)
        run_status = determine_run_status(query_results, errors)
        notes = build_notes(
            config,
            run_status=run_status,
            session_state_validated=session_state_validated,
            playwright_used=True,
        )
        result = RunExecutionResult(
            status=run_status,
            exit_code=map_status_to_exit_code(run_status),
            started_at=started_at,
            finished_at=now_utc_text(),
            duration_seconds=round(time.perf_counter() - started_perf, 3),
            query_results=query_results,
            artifact_paths={},
            artifact_records=[],
            errors=errors,
            notes=notes,
            playwright_used=True,
            session_state_used=str(config.session_state_file),
            session_state_validated=session_state_validated,
            skipped_existing_outputs=False,
        )
        dataframe = build_dataframe(query_results)
        queries_summary_df = build_queries_summary_dataframe(query_results)
        raw_records = dataframe.to_dict(orient="records")
        artifact_paths, artifact_records = persist_outputs(
            config,
            dataframe=dataframe,
            queries_summary_df=queries_summary_df,
            raw_records=raw_records,
            result=result,
            logger=logger,
        )
        result.artifact_paths = artifact_paths
        result.artifact_records = artifact_records
        logger.info(
            "Cierre de corrida | status=%s tweets_detected=%s tweets_saved=%s replies_saved=%s run_dir=%s",
            result.status,
            sum(item.tweets_detected for item in query_results),
            sum(item.tweets_saved for item in query_results),
            sum(item.replies_saved for item in query_results),
            config.run_dir,
        )
        return result
    finally:
        await close_browser_resources(playwright, browser, context)


def write_failure_artifacts(
    config: ResolvedConfig,
    logger: logging.Logger,
    *,
    error: Exception,
    exit_code: int,
) -> None:
    ensure_failure_output_layout(config)
    log_path = config.run_dir / LOG_FILENAME
    if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logger.level)
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)

    failure_error = ErrorRecord(
        stage="run_extraction",
        scope="run",
        message=str(error),
        timestamp=now_utc_text(),
        fatal=True,
        error_type=f"fatal:{type(error).__name__}",
    )
    started_at = now_utc_text()
    notes = [
        "La corrida falló antes de completar la extracción.",
        "Revisar errores_detectados.json, metadata_run.json y run.log para diagnóstico.",
    ]
    result = RunExecutionResult(
        status="failed",
        exit_code=exit_code,
        started_at=started_at,
        finished_at=started_at,
        duration_seconds=0.0,
        query_results=[],
        artifact_paths={},
        artifact_records=[],
        errors=[failure_error],
        notes=notes,
        playwright_used=False,
        session_state_used=str(config.session_state_file),
        session_state_validated=False,
        skipped_existing_outputs=False,
    )
    dataframe = pd.DataFrame(columns=DATA_COLUMNS)
    queries_summary_df = pd.DataFrame(columns=QUERY_SUMMARY_COLUMNS)
    artifact_paths, artifact_records = persist_outputs(
        config,
        dataframe=dataframe,
        queries_summary_df=queries_summary_df,
        raw_records=[],
        result=result,
        logger=logger,
    )
    result.artifact_paths = artifact_paths
    result.artifact_records = artifact_records


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
        logger.error("Error de configuración: %s", exc)
        return ExitCode.FAILED_CONFIG

    try:
        result = asyncio.run(run_extraction(config, logger))
        return result.exit_code
    except SessionStateError as exc:
        logger.error("Error fatal de sesión: %s", exc)
        try:
            write_failure_artifacts(config, logger, error=exc, exit_code=ExitCode.FAILED_PLATFORM)
        except Exception as write_exc:
            logger.error("No se pudieron escribir artefactos de falla: %s", write_exc)
        return ExitCode.FAILED_PLATFORM
    except PlatformRuntimeError as exc:
        logger.error("Error fatal de plataforma/navegación: %s", exc)
        try:
            write_failure_artifacts(config, logger, error=exc, exit_code=ExitCode.FAILED_PLATFORM)
        except Exception as write_exc:
            logger.error("No se pudieron escribir artefactos de falla: %s", write_exc)
        return ExitCode.FAILED_PLATFORM
    except OutputWriteError as exc:
        logger.error("Error fatal de persistencia: %s", exc)
        return ExitCode.FAILED_WRITE
    except Exception as exc:  # pragma: no cover - salvaguarda final
        logger.error("Error fatal no controlado: %s", exc)
        try:
            write_failure_artifacts(config, logger, error=exc, exit_code=ExitCode.FAILED_PLATFORM)
        except Exception as write_exc:
            logger.error("No se pudieron escribir artefactos de falla: %s", write_exc)
        return ExitCode.FAILED_PLATFORM
