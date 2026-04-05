#!/usr/bin/env python3
"""
Nucleo reusable del extractor de YouTube para Radar.

El modulo concentra la configuracion, extraccion, persistencia y trazabilidad
del componente de ingesta. El entrypoint CLI vive en
`01_youtube_extractor_Tampico.py`, pero otros scripts pueden importar
`run_extraction` para orquestar esta pieza sin depender del nombre numerado
del archivo.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import shutil
import socket
import sys
import time
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, time as dt_time, timedelta
from enum import IntEnum
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as exc:  # pragma: no cover - depende del entorno
    build = None
    HttpError = Exception  # type: ignore[assignment]
    GOOGLE_API_IMPORT_ERROR: Exception | None = exc
else:
    GOOGLE_API_IMPORT_ERROR = None


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "Datos_RAdAR"
SCRIPT_VERSION = "2.0.0"
SCRIPT_COMPONENT = "radar.youtube_extractor"
SOURCE_PLATFORM = "youtube"
COMMENT_LEVEL_TOP = "top_level"

WEEK_MODE_EXACT = "exact_range"
WEEK_MODE_CANONICAL = "canonical_monday_sunday"
WEEK_NAME_MODE_CHOICES = (WEEK_MODE_EXACT, WEEK_MODE_CANONICAL)

DEFAULT_MAX_RESULTS_SEARCH = 50
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_RUN_ID = "youtube_extract"
DEFAULT_API_ENV = "YOUTUBE_API_KEY"

COMMENTS_FILENAME_PREFIX = "youtube_comentarios"
VIDEOS_FILENAME = "videos_encontrados.csv"
QUERIES_FILENAME = "queries_summary.csv"
METADATA_FILENAME = "metadata_run.json"
PARAMS_FILENAME = "parametros_run.json"
SUMMARY_FILENAME = "summary.json"
MANIFEST_FILENAME = "manifest.json"
ERRORS_FILENAME = "errores_detectados.json"
LOG_FILENAME = "run.log"

COMMENT_COLUMNS = [
    "video_id",
    "comment_id",
    "author",
    "comment_text",
    "published_at",
    "like_count",
    "query",
    "video_title",
    "channel_title",
    "video_published_at",
    "fecha_extraccion",
    "run_id",
    "week_name",
    "source_platform",
    "comment_level",
    "video_url",
    "query_index",
]

VIDEO_COLUMNS = [
    "query_index",
    "query",
    "video_rank",
    "video_id",
    "video_title",
    "channel_title",
    "video_published_at",
    "video_url",
    "comments_extracted",
    "status",
    "error_message",
]

QUERY_SUMMARY_COLUMNS = [
    "query_index",
    "query",
    "status",
    "videos_found",
    "videos_with_comments",
    "comments_extracted",
    "video_errors",
    "query_errors",
    "duration_seconds",
]


class ExitCode(IntEnum):
    SUCCESS = 0
    PARTIAL_SUCCESS = 1
    FAILED_CONFIG = 2
    FAILED_API = 3
    FAILED_WRITE = 4


class ExtractionError(Exception):
    """Base class for extractor-specific failures."""


class ConfigurationError(ExtractionError):
    """Raised when configuration or inputs are invalid."""


class ApiAuthenticationError(ExtractionError):
    """Raised when the YouTube API key or quota prevents execution."""


class ApiExecutionError(ExtractionError):
    """Raised when the API fails in a fatal way during extraction."""


class OutputWriteError(ExtractionError):
    """Raised when outputs cannot be written or published."""


@dataclass(frozen=True)
class WeekPartition:
    start_date: date
    end_date: date
    week_name: str
    naming_start_date: date
    naming_end_date: date


@dataclass(frozen=True)
class ResolvedConfig:
    script_name: str
    script_path: Path
    helper_module_path: Path
    script_version: str
    start_date: date
    end_date: date
    search_start_datetime: datetime
    search_end_datetime: datetime
    queries: list[str]
    queries_source: str
    output_root_dir: Path
    week_dir: Path
    run_dir: Path
    run_timestamp: str
    run_id: str
    youtube_api_key_env: str
    api_key_source: str
    week_name_mode: str
    week_partition: WeekPartition
    max_results_search: int
    max_comments_per_video: int | None
    log_level: str
    overwrite: bool
    publish_canonical: bool
    include_replies: bool
    include_replies_implemented: bool
    country: str | None
    language: str | None
    dry_run: bool
    config_file: Path | None = None


@dataclass
class ArtifactRecord:
    name: str
    artifact_type: str
    path: str
    description: str
    timestamp: str


@dataclass
class ErrorRecord:
    stage: str
    scope: str
    message: str
    timestamp: str
    query_index: int | None = None
    query: str | None = None
    video_id: str | None = None
    fatal: bool = False
    http_status: int | None = None
    http_reasons: list[str] = field(default_factory=list)


@dataclass
class VideoExtractionRecord:
    query_index: int
    query: str
    video_rank: int
    video_id: str
    video_title: str
    channel_title: str
    video_published_at: str
    video_url: str
    comments_extracted: int
    status: str
    error_message: str = ""


@dataclass
class QueryExecutionResult:
    query_index: int
    query: str
    status: str
    videos_found: int
    videos_with_comments: int
    comments_extracted: int
    video_errors: int
    query_errors: int
    duration_seconds: float
    videos: list[VideoExtractionRecord] = field(default_factory=list)
    comments: list[dict[str, Any]] = field(default_factory=list)
    errors: list[ErrorRecord] = field(default_factory=list)


@dataclass
class RunExecutionResult:
    status: str
    exit_code: int
    started_at: str
    finished_at: str
    duration_seconds: float
    config: ResolvedConfig
    query_results: list[QueryExecutionResult]
    summary: dict[str, Any]
    metadata: dict[str, Any]
    manifest: list[dict[str, Any]]
    artifact_paths: dict[str, str]
    notes: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)


def now_utc_text() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def now_local_text() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the extractor entrypoint."""

    parser = argparse.ArgumentParser(
        description=(
            "Extractor profesional de YouTube para Radar. Busca videos por query "
            "y rango temporal, extrae comentarios top-level y guarda artefactos "
            "trazables por corrida."
        )
    )
    parser.add_argument("--start-date", help="Fecha inicial de busqueda (YYYY-MM-DD).")
    parser.add_argument("--end-date", help="Fecha final de busqueda (YYYY-MM-DD).")
    parser.add_argument(
        "--queries-file",
        help="Archivo externo con queries. Soporta TXT, JSON o CSV.",
    )
    parser.add_argument(
        "--queries",
        nargs="+",
        help="Queries directas por CLI. Usa comillas para queries con espacios.",
    )
    parser.add_argument(
        "--config-file",
        help="Archivo JSON opcional para precargar parametros. CLI tiene prioridad.",
    )
    parser.add_argument(
        "--output-dir",
        help=f"Directorio raiz de salida. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--youtube-api-key-env",
        default=None,
        help=f"Nombre de la variable de entorno con la API key. Default: {DEFAULT_API_ENV}",
    )
    parser.add_argument(
        "--week-name-mode",
        choices=WEEK_NAME_MODE_CHOICES,
        default=None,
        help="Politica de naming semanal: exact_range o canonical_monday_sunday.",
    )
    parser.add_argument(
        "--max-results-search",
        type=int,
        default=None,
        help=f"Maximo de videos a recuperar por query. Default: {DEFAULT_MAX_RESULTS_SEARCH}",
    )
    parser.add_argument(
        "--max-comments-per-video",
        type=int,
        default=None,
        help="Limite opcional de comentarios top-level por video.",
    )
    parser.add_argument(
        "--country",
        default=None,
        help="Codigo de pais opcional para la busqueda de YouTube, por ejemplo MX.",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Idioma relevante opcional para la busqueda, por ejemplo es.",
    )
    parser.add_argument(
        "--include-replies",
        action="store_true",
        default=None,
        help="Acepta la bandera pero esta version no implementa replies; queda documentado.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        help="Valida parametros, construye estructura de salida y escribe metadata sin llamar a la API.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help=f"Identificador semantico de corrida. Default: {DEFAULT_RUN_ID}",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=None,
        help="Permite sobrescribir artefactos canónicos si se publica salida semanal.",
    )
    parser.add_argument(
        "--publish-canonical",
        action="store_true",
        default=None,
        help="Publica una copia canonica en la carpeta semanal ademas del run_dir.",
    )
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default=None,
        help=f"Nivel de logging. Default: {DEFAULT_LOG_LEVEL}",
    )
    return parser.parse_args(argv)


def load_config_file(config_file: Path) -> dict[str, Any]:
    """Load an optional JSON config file for the extractor."""

    if not config_file.exists():
        raise ConfigurationError(f"No existe el config file: {config_file}")
    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"Config file invalido: {config_file}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError("El config file debe contener un objeto JSON.")
    return data


def merge_config_sources(args: argparse.Namespace) -> dict[str, Any]:
    """Merge CLI args with an optional JSON config file, giving CLI precedence."""

    merged: dict[str, Any] = {}
    config_file_value = getattr(args, "config_file", None)
    if config_file_value:
        config_path = Path(config_file_value).expanduser().resolve()
        merged.update(load_config_file(config_path))
        merged["config_file"] = str(config_path)

    for key, value in vars(args).items():
        if value is None:
            continue
        if isinstance(value, list) and not value:
            continue
        merged[key] = value

    return merged


def parse_date_str(raw_value: str, label: str) -> date:
    """Parse a YYYY-MM-DD string into a date object."""

    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ConfigurationError(f"{label} invalida '{raw_value}', usa YYYY-MM-DD.") from exc


def load_queries_from_file(queries_file: Path) -> list[str]:
    """Load queries from TXT, JSON or CSV files."""

    if not queries_file.exists():
        raise ConfigurationError(f"No existe el archivo de queries: {queries_file}")

    suffix = queries_file.suffix.lower()
    if suffix == ".json":
        payload = json.loads(queries_file.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            queries = [str(item).strip() for item in payload]
        elif isinstance(payload, dict):
            raw_queries = payload.get("queries")
            if not isinstance(raw_queries, list):
                raise ConfigurationError(
                    "El JSON de queries debe ser una lista o un objeto con clave 'queries'."
                )
            queries = [str(item).strip() for item in raw_queries]
        else:
            raise ConfigurationError(
                "El JSON de queries debe ser una lista o un objeto con clave 'queries'."
            )
        return [query for query in queries if query]

    if suffix == ".csv":
        dataframe = pd.read_csv(queries_file)
        candidate_columns = ("query", "queries", "term", "termino")
        selected_column = next((column for column in candidate_columns if column in dataframe.columns), None)
        if selected_column is None:
            raise ConfigurationError(
                "El CSV de queries debe incluir una columna 'query', 'queries', 'term' o 'termino'."
            )
        return [
            str(value).strip()
            for value in dataframe[selected_column].dropna().tolist()
            if str(value).strip()
        ]

    return [
        line.strip()
        for line in queries_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def format_spanish_date(raw_date: date) -> str:
    """Format a date as DDmes in Spanish, preserving leading zero in day."""

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


def resolve_week_partition(start_date: date, end_date: date, mode: str) -> WeekPartition:
    """Resolve the weekly naming partition used by Radar."""

    if mode == WEEK_MODE_EXACT:
        naming_start = start_date
        naming_end = end_date
    elif mode == WEEK_MODE_CANONICAL:
        naming_start = start_date - timedelta(days=start_date.weekday())
        naming_end = end_date + timedelta(days=(6 - end_date.weekday()))
    else:  # pragma: no cover - argparse and resolve_config already validate
        raise ConfigurationError(f"Modo de nombre semanal no soportado: {mode}")

    label = f"semana_{format_spanish_date(naming_start)}_{format_spanish_date(naming_end)}_{naming_end:%y}"
    week_name = f"{naming_start.isoformat()}_{label}"
    return WeekPartition(
        start_date=start_date,
        end_date=end_date,
        week_name=week_name,
        naming_start_date=naming_start,
        naming_end_date=naming_end,
    )


def resolve_config(args: argparse.Namespace) -> ResolvedConfig:
    """Resolve and validate the effective extractor configuration."""

    merged = merge_config_sources(args)

    start_date_raw = merged.get("start_date")
    end_date_raw = merged.get("end_date")
    if not start_date_raw or not end_date_raw:
        raise ConfigurationError("Debes definir --start-date y --end-date o proveerlos en --config-file.")

    start_date = parse_date_str(str(start_date_raw), "start_date")
    end_date = parse_date_str(str(end_date_raw), "end_date")
    if end_date < start_date:
        raise ConfigurationError("end_date no puede ser menor que start_date.")

    queries_cli = merged.get("queries")
    queries_file_raw = merged.get("queries_file")
    if queries_cli and queries_file_raw:
        raise ConfigurationError("Usa --queries-file o --queries, no ambos a la vez.")

    queries_source = ""
    if queries_file_raw:
        queries_file = Path(str(queries_file_raw)).expanduser().resolve()
        queries = load_queries_from_file(queries_file)
        queries_source = str(queries_file)
    elif queries_cli:
        queries = [str(query).strip() for query in queries_cli if str(query).strip()]
        queries_source = "cli"
    else:
        raise ConfigurationError("Debes proporcionar queries via --queries-file o --queries.")

    if not queries:
        raise ConfigurationError("La lista final de queries no puede quedar vacia.")

    output_root_dir = Path(str(merged.get("output_dir", DEFAULT_OUTPUT_DIR))).expanduser().resolve()
    week_name_mode = str(merged.get("week_name_mode", WEEK_MODE_EXACT))
    week_partition = resolve_week_partition(start_date, end_date, week_name_mode)

    run_id = str(merged.get("run_id", DEFAULT_RUN_ID)).strip() or DEFAULT_RUN_ID
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    week_dir = output_root_dir / week_partition.week_name
    run_dir = week_dir / "runs" / f"{run_id}_{run_timestamp}"

    max_results_search = int(merged.get("max_results_search", DEFAULT_MAX_RESULTS_SEARCH))
    if max_results_search <= 0:
        raise ConfigurationError("--max-results-search debe ser mayor que 0.")

    max_comments_per_video_raw = merged.get("max_comments_per_video")
    max_comments_per_video = None
    if max_comments_per_video_raw is not None:
        max_comments_per_video = int(max_comments_per_video_raw)
        if max_comments_per_video <= 0:
            raise ConfigurationError("--max-comments-per-video debe ser mayor que 0.")

    youtube_api_key_env = str(merged.get("youtube_api_key_env", DEFAULT_API_ENV)).strip() or DEFAULT_API_ENV
    include_replies = bool(merged.get("include_replies", False))
    search_start_datetime = datetime.combine(start_date, dt_time.min)
    search_end_datetime = datetime.combine(end_date, dt_time.max.replace(microsecond=0))

    config_file = merged.get("config_file")
    config_file_path = Path(config_file).resolve() if config_file else None

    return ResolvedConfig(
        script_name="01_youtube_extractor_Tampico.py",
        script_path=Path(__file__).resolve().with_name("01_youtube_extractor_Tampico.py"),
        helper_module_path=Path(__file__).resolve(),
        script_version=SCRIPT_VERSION,
        start_date=start_date,
        end_date=end_date,
        search_start_datetime=search_start_datetime,
        search_end_datetime=search_end_datetime,
        queries=queries,
        queries_source=queries_source,
        output_root_dir=output_root_dir,
        week_dir=week_dir,
        run_dir=run_dir,
        run_timestamp=run_timestamp,
        run_id=run_id,
        youtube_api_key_env=youtube_api_key_env,
        api_key_source=f"env:{youtube_api_key_env}",
        week_name_mode=week_name_mode,
        week_partition=week_partition,
        max_results_search=max_results_search,
        max_comments_per_video=max_comments_per_video,
        log_level=str(merged.get("log_level", DEFAULT_LOG_LEVEL)).upper(),
        overwrite=bool(merged.get("overwrite", False)),
        publish_canonical=bool(merged.get("publish_canonical", False)),
        include_replies=include_replies,
        include_replies_implemented=False,
        country=str(merged.get("country")).strip() if merged.get("country") else None,
        language=str(merged.get("language")).strip() if merged.get("language") else None,
        dry_run=bool(merged.get("dry_run", False)),
        config_file=config_file_path,
    )


def setup_logging(log_level: str, log_file: Path | None = None) -> logging.Logger:
    """Configure console and optional file logging for the extractor."""

    logger = logging.getLogger(SCRIPT_COMPONENT)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logger.level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logger.level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def configure_output_layout(config: ResolvedConfig) -> None:
    """Create the week/run directory structure for the extractor."""

    config.week_dir.mkdir(parents=True, exist_ok=True)
    if config.run_dir.exists():
        if config.overwrite:
            shutil.rmtree(config.run_dir)
        else:
            raise OutputWriteError(
                f"El run_dir ya existe y no se permite sobrescribirlo: {config.run_dir}"
            )
    config.run_dir.mkdir(parents=True, exist_ok=True)


def rfc3339(dt_value: datetime) -> str:
    """Convert a naive datetime into the RFC3339 format expected by YouTube."""

    return dt_value.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_video_url(video_id: str) -> str:
    """Build a canonical YouTube video URL."""

    return f"https://www.youtube.com/watch?v={video_id}"


def serialize_for_json(value: Any) -> Any:
    """Convert nested values into JSON-serializable data."""

    if is_dataclass(value):
        return serialize_for_json(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): serialize_for_json(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [serialize_for_json(item) for item in value]
    return value


def write_json_file(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    """Write JSON using UTF-8 and stable formatting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize_for_json(payload), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def safe_write_json_file(
    path: Path,
    payload: dict[str, Any] | list[Any],
    logger: logging.Logger,
) -> None:
    """Best-effort JSON writer used during fatal error handling."""

    try:
        write_json_file(path, payload)
    except Exception as exc:  # pragma: no cover - fallback defensive path
        logger.error("No se pudo escribir JSON de fallback en %s: %s", path, exc)


def ensure_publish_target(target_path: Path, overwrite: bool) -> None:
    """Validate canonical publication target policy."""

    if target_path.exists() and not overwrite:
        raise OutputWriteError(
            f"El artefacto canonico ya existe y requiere --overwrite: {target_path}"
        )


def http_error_details(error: HttpError) -> tuple[int | None, str, list[str]]:
    """Extract status, message and reasons from a YouTube HttpError."""

    status = getattr(getattr(error, "resp", None), "status", None)
    reasons: list[str] = []
    message = str(error)
    raw_content = getattr(error, "content", None)
    if raw_content:
        try:
            payload = json.loads(raw_content.decode("utf-8"))
        except Exception:
            return status, message, reasons
        error_payload = payload.get("error", {})
        message = error_payload.get("message", message)
        reasons = [
            detail.get("reason", "")
            for detail in error_payload.get("errors", [])
            if isinstance(detail, dict) and detail.get("reason")
        ]
    return status, message, reasons


def is_auth_or_quota_error(status: int | None, message: str, reasons: Sequence[str]) -> bool:
    """Detect fatal authentication or quota errors from YouTube API responses."""

    reason_tokens = {reason.lower() for reason in reasons}
    message_lower = message.lower()
    markers = {
        "accessnotconfigured",
        "dailylimitexceeded",
        "forbidden",
        "ipreferernotallowed",
        "keyexpired",
        "keyinvalid",
        "quotaexceeded",
        "quota_limit_exceeded",
        "usagelimits",
    }
    if status == 401:
        return True
    if status in {400, 403} and (
        reason_tokens.intersection(markers)
        or "api key" in message_lower
        or "quota" in message_lower
        or "access not configured" in message_lower
    ):
        return True
    return False


def build_youtube_client(config: ResolvedConfig):
    """Create a YouTube API client from the configured environment variable."""

    if GOOGLE_API_IMPORT_ERROR is not None or build is None:
        raise ConfigurationError(
            "Falta la dependencia google-api-python-client. "
            "Instalala antes de usar el extractor."
        ) from GOOGLE_API_IMPORT_ERROR

    api_key = os.getenv(config.youtube_api_key_env)
    if not api_key:
        raise ConfigurationError(
            f"No se encontro la variable de entorno requerida: {config.youtube_api_key_env}"
        )

    try:
        return build("youtube", "v3", developerKey=api_key, cache_discovery=False)
    except Exception as exc:
        raise ApiAuthenticationError("No se pudo inicializar el cliente de YouTube.") from exc


def search_videos(
    youtube,
    *,
    query: str,
    config: ResolvedConfig,
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """Search videos for a given query and date range."""

    results: list[dict[str, Any]] = []
    next_page_token: str | None = None
    seen_ids: set[str] = set()

    while len(results) < config.max_results_search:
        remaining = config.max_results_search - len(results)
        request_kwargs: dict[str, Any] = {
            "q": query,
            "part": "id,snippet",
            "maxResults": min(50, remaining),
            "type": "video",
            "order": "date",
            "publishedAfter": rfc3339(config.search_start_datetime),
            "publishedBefore": rfc3339(config.search_end_datetime),
        }
        if config.country:
            request_kwargs["regionCode"] = config.country
        if config.language:
            request_kwargs["relevanceLanguage"] = config.language
        if next_page_token:
            request_kwargs["pageToken"] = next_page_token

        try:
            response = youtube.search().list(**request_kwargs).execute()
        except HttpError as exc:
            status, message, reasons = http_error_details(exc)
            if is_auth_or_quota_error(status, message, reasons):
                raise ApiAuthenticationError(message) from exc
            raise ApiExecutionError(message) from exc

        for item in response.get("items", []):
            if item.get("id", {}).get("kind") != "youtube#video":
                continue
            video_id = item.get("id", {}).get("videoId")
            if not video_id or video_id in seen_ids:
                continue
            seen_ids.add(video_id)
            results.append(
                {
                    "video_id": video_id,
                    "video_rank": len(results) + 1,
                    "search_title": item.get("snippet", {}).get("title", ""),
                    "search_channel_title": item.get("snippet", {}).get("channelTitle", ""),
                    "search_published_at": item.get("snippet", {}).get("publishedAt", ""),
                }
            )
            if len(results) >= config.max_results_search:
                break

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

        logger.debug(
            "Pagina adicional de busqueda recuperada | query=%s videos_acumulados=%s",
            query,
            len(results),
        )
        time.sleep(0.1)

    return results


def get_video_details(
    youtube,
    video_ids: Sequence[str],
    logger: logging.Logger,
) -> dict[str, dict[str, str]]:
    """Fetch snippet metadata for a collection of video IDs."""

    details: dict[str, dict[str, str]] = {}
    for index in range(0, len(video_ids), 50):
        batch = list(video_ids[index : index + 50])
        if not batch:
            continue
        try:
            response = youtube.videos().list(part="snippet", id=",".join(batch)).execute()
        except HttpError as exc:
            status, message, reasons = http_error_details(exc)
            if is_auth_or_quota_error(status, message, reasons):
                raise ApiAuthenticationError(message) from exc
            raise ApiExecutionError(message) from exc
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            details[item.get("id", "")] = {
                "title": snippet.get("title", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
            }
        logger.debug(
            "Detalles de videos recuperados | lote_desde=%s lote_hasta=%s",
            index,
            index + len(batch),
        )
    return details


def get_video_comments(
    youtube,
    *,
    video_id: str,
    query: str,
    query_index: int,
    config: ResolvedConfig,
    video_details: dict[str, str],
    extraction_timestamp: str,
    logger: logging.Logger,
) -> tuple[list[dict[str, Any]], ErrorRecord | None]:
    """Fetch top-level comments for a single video."""

    comments: list[dict[str, Any]] = []
    next_page_token: str | None = None

    if config.include_replies and not config.include_replies_implemented:
        logger.debug(
            "include_replies fue solicitado pero no se implementa en esta version | video_id=%s",
            video_id,
        )

    while True:
        if config.max_comments_per_video is not None and len(comments) >= config.max_comments_per_video:
            break

        remaining = None
        if config.max_comments_per_video is not None:
            remaining = config.max_comments_per_video - len(comments)
        request_kwargs: dict[str, Any] = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": min(100, remaining) if remaining is not None else 100,
            "textFormat": "plainText",
        }
        if next_page_token:
            request_kwargs["pageToken"] = next_page_token

        try:
            response = youtube.commentThreads().list(**request_kwargs).execute()
        except HttpError as exc:
            status, message, reasons = http_error_details(exc)
            if is_auth_or_quota_error(status, message, reasons):
                raise ApiAuthenticationError(message) from exc
            return comments, ErrorRecord(
                stage="get_video_comments",
                scope="video",
                message=message,
                timestamp=now_utc_text(),
                query_index=query_index,
                query=query,
                video_id=video_id,
                fatal=False,
                http_status=status,
                http_reasons=list(reasons),
            )

        for item in response.get("items", []):
            snippet = (
                item.get("snippet", {})
                .get("topLevelComment", {})
                .get("snippet", {})
            )
            comments.append(
                {
                    "video_id": video_id,
                    "comment_id": item.get("id", ""),
                    "author": snippet.get("authorDisplayName", ""),
                    "comment_text": snippet.get("textDisplay", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "like_count": snippet.get("likeCount", 0),
                    "query": query,
                    "video_title": video_details.get("title", ""),
                    "channel_title": video_details.get("channel_title", ""),
                    "video_published_at": video_details.get("published_at", ""),
                    "fecha_extraccion": extraction_timestamp,
                    "run_id": config.run_id,
                    "week_name": config.week_partition.week_name,
                    "source_platform": SOURCE_PLATFORM,
                    "comment_level": COMMENT_LEVEL_TOP,
                    "video_url": make_video_url(video_id),
                    "query_index": query_index,
                }
            )
            if config.max_comments_per_video is not None and len(comments) >= config.max_comments_per_video:
                break

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
        time.sleep(0.1)

    logger.debug(
        "Comentarios extraidos de video | video_id=%s query=%s comentarios=%s",
        video_id,
        query,
        len(comments),
    )
    return comments, None


def extract_query_batch(
    youtube,
    *,
    query: str,
    query_index: int,
    config: ResolvedConfig,
    extraction_timestamp: str,
    logger: logging.Logger,
) -> QueryExecutionResult:
    """Execute the full extraction flow for a single query."""

    started_at = time.perf_counter()
    query_errors: list[ErrorRecord] = []
    videos_found = 0
    videos_with_comments = 0
    comments_extracted = 0
    video_errors = 0
    videos: list[VideoExtractionRecord] = []
    comments_rows: list[dict[str, Any]] = []

    logger.info("Procesando query %s/%s | query=%s", query_index, len(config.queries), query)

    try:
        search_rows = search_videos(youtube, query=query, config=config, logger=logger)
    except ApiAuthenticationError:
        raise
    except ApiExecutionError as exc:
        query_errors.append(
            ErrorRecord(
                stage="search_videos",
                scope="query",
                message=str(exc),
                timestamp=now_utc_text(),
                query_index=query_index,
                query=query,
                fatal=False,
            )
        )
        return QueryExecutionResult(
            query_index=query_index,
            query=query,
            status="failed",
            videos_found=0,
            videos_with_comments=0,
            comments_extracted=0,
            video_errors=0,
            query_errors=1,
            duration_seconds=round(time.perf_counter() - started_at, 3),
            errors=query_errors,
        )

    videos_found = len(search_rows)
    logger.info("Query con videos encontrados | query=%s videos=%s", query, videos_found)

    if not search_rows:
        return QueryExecutionResult(
            query_index=query_index,
            query=query,
            status="success",
            videos_found=0,
            videos_with_comments=0,
            comments_extracted=0,
            video_errors=0,
            query_errors=0,
            duration_seconds=round(time.perf_counter() - started_at, 3),
            videos=[],
            comments=[],
            errors=[],
        )

    video_ids = [row["video_id"] for row in search_rows]
    try:
        detail_map = get_video_details(youtube, video_ids, logger)
    except ApiAuthenticationError:
        raise
    except ApiExecutionError as exc:
        query_errors.append(
            ErrorRecord(
                stage="get_video_details",
                scope="query",
                message=str(exc),
                timestamp=now_utc_text(),
                query_index=query_index,
                query=query,
                fatal=False,
            )
        )
        detail_map = {}

    for row in search_rows:
        video_id = row["video_id"]
        details = detail_map.get(
            video_id,
            {
                "title": row.get("search_title", ""),
                "channel_title": row.get("search_channel_title", ""),
                "published_at": row.get("search_published_at", ""),
            },
        )
        logger.info(
            "Extrayendo comentarios de video | query=%s video_rank=%s video_id=%s",
            query,
            row["video_rank"],
            video_id,
        )
        try:
            video_comments, video_error = get_video_comments(
                youtube,
                video_id=video_id,
                query=query,
                query_index=query_index,
                config=config,
                video_details=details,
                extraction_timestamp=extraction_timestamp,
                logger=logger,
            )
        except ApiAuthenticationError:
            raise

        comments_rows.extend(video_comments)
        comments_extracted += len(video_comments)
        if video_comments:
            videos_with_comments += 1

        if video_error is not None:
            video_errors += 1
            query_errors.append(video_error)
            logger.warning(
                "Error recuperable en video | query=%s video_id=%s mensaje=%s",
                query,
                video_id,
                video_error.message,
            )

        videos.append(
            VideoExtractionRecord(
                query_index=query_index,
                query=query,
                video_rank=row["video_rank"],
                video_id=video_id,
                video_title=details.get("title", ""),
                channel_title=details.get("channel_title", ""),
                video_published_at=details.get("published_at", ""),
                video_url=make_video_url(video_id),
                comments_extracted=len(video_comments),
                status="warning" if video_error else "success",
                error_message=video_error.message if video_error else "",
            )
        )

    status = "success"
    if query_errors and videos_found > 0:
        status = "partial_success"
    if query_errors and videos_with_comments == 0 and comments_extracted == 0:
        status = "failed"

    duration_seconds = round(time.perf_counter() - started_at, 3)
    logger.info(
        "Query finalizada | query=%s status=%s videos=%s videos_con_comentarios=%s comentarios=%s",
        query,
        status,
        videos_found,
        videos_with_comments,
        comments_extracted,
    )
    return QueryExecutionResult(
        query_index=query_index,
        query=query,
        status=status,
        videos_found=videos_found,
        videos_with_comments=videos_with_comments,
        comments_extracted=comments_extracted,
        video_errors=video_errors,
        query_errors=sum(1 for error in query_errors if error.scope == "query"),
        duration_seconds=duration_seconds,
        videos=videos,
        comments=comments_rows,
        errors=query_errors,
    )


def build_comments_dataframe(
    query_results: Sequence[QueryExecutionResult],
) -> pd.DataFrame:
    """Build the canonical comments dataframe for the run."""

    rows: list[dict[str, Any]] = []
    for result in query_results:
        rows.extend(result.comments)
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return pd.DataFrame(columns=COMMENT_COLUMNS)
    for column in COMMENT_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""
    return dataframe[COMMENT_COLUMNS]


def build_videos_dataframe(
    query_results: Sequence[QueryExecutionResult],
) -> pd.DataFrame:
    """Build the dataframe of discovered videos."""

    rows: list[dict[str, Any]] = []
    for result in query_results:
        rows.extend(asdict(video) for video in result.videos)
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return pd.DataFrame(columns=VIDEO_COLUMNS)
    for column in VIDEO_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""
    return dataframe[VIDEO_COLUMNS]


def build_queries_summary_dataframe(
    query_results: Sequence[QueryExecutionResult],
) -> pd.DataFrame:
    """Build a per-query summary dataframe."""

    rows = [
        {
            "query_index": result.query_index,
            "query": result.query,
            "status": result.status,
            "videos_found": result.videos_found,
            "videos_with_comments": result.videos_with_comments,
            "comments_extracted": result.comments_extracted,
            "video_errors": result.video_errors,
            "query_errors": result.query_errors,
            "duration_seconds": result.duration_seconds,
        }
        for result in query_results
    ]
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return pd.DataFrame(columns=QUERY_SUMMARY_COLUMNS)
    for column in QUERY_SUMMARY_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""
    return dataframe[QUERY_SUMMARY_COLUMNS]


def flatten_errors(query_results: Sequence[QueryExecutionResult]) -> list[dict[str, Any]]:
    """Collect and serialize all query/video errors for JSON output."""

    errors: list[dict[str, Any]] = []
    for result in query_results:
        errors.extend(serialize_for_json(error) for error in result.errors)
    return errors


def determine_run_status(query_results: Sequence[QueryExecutionResult], *, dry_run: bool = False) -> str:
    """Derive the final execution status from individual query results."""

    if dry_run:
        return "success"
    if not query_results:
        return "failed"
    statuses = [result.status for result in query_results]
    if all(status == "failed" for status in statuses):
        return "failed"
    if any(status in {"failed", "partial_success"} for status in statuses):
        return "partial_success"
    return "success"


def build_notes(config: ResolvedConfig, status: str) -> list[str]:
    """Build user-facing notes for summary and metadata."""

    notes = [
        "Extractor puro de YouTube: busqueda por query/rango, metadata de video y comentarios top-level.",
        "No se extraen replies por defecto ni se implementan en esta version.",
        "No se realiza NLP, deduplicacion de negocio, consolidacion maestra ni modelado.",
        "La disponibilidad final depende de la API de YouTube y sus limites de cuota.",
    ]
    if config.week_name_mode == WEEK_MODE_CANONICAL:
        notes.append(
            "El nombre semanal se alinea a lunes-domingo, pero la busqueda usa exactamente start_date y end_date."
        )
    else:
        notes.append(
            "El nombre semanal usa exactamente start_date y end_date, sin alineacion automatica a lunes-domingo."
        )
    if config.include_replies and not config.include_replies_implemented:
        notes.append(
            "Se recibio --include-replies, pero esta version conserva el alcance top_level."
        )
    if config.dry_run:
        notes.append("Dry run: no se invocaron endpoints de YouTube.")
    if status == "partial_success":
        notes.append("La corrida termino con errores recuperables; revisa errores_detectados.json.")
    return notes


def build_summary(
    config: ResolvedConfig,
    query_results: Sequence[QueryExecutionResult],
    *,
    status: str,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    output_dir: Path,
    notes: Sequence[str],
) -> dict[str, Any]:
    """Build the run summary JSON payload."""

    total_videos_found = sum(result.videos_found for result in query_results)
    total_videos_with_comments = sum(result.videos_with_comments for result in query_results)
    total_comments_extracted = sum(result.comments_extracted for result in query_results)
    queries_failed = sum(1 for result in query_results if result.status == "failed")

    return {
        "run_id": config.run_id,
        "status": status,
        "start_date": config.start_date.isoformat(),
        "end_date": config.end_date.isoformat(),
        "search_start_datetime": config.search_start_datetime.isoformat(),
        "search_end_datetime": config.search_end_datetime.isoformat(),
        "week_name": config.week_partition.week_name,
        "week_name_mode": config.week_name_mode,
        "output_dir": str(output_dir),
        "week_dir": str(config.week_dir),
        "total_queries": len(config.queries),
        "queries_processed": len(query_results),
        "queries_failed": queries_failed,
        "total_videos_found": total_videos_found,
        "total_videos_with_comments": total_videos_with_comments,
        "total_comments_extracted": total_comments_extracted,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
        "api_key_source": config.api_key_source,
        "script_name": config.script_name,
        "script_version": config.script_version,
        "notes": list(notes),
    }


def build_metadata(
    config: ResolvedConfig,
    *,
    status: str,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    artifact_paths: dict[str, str],
    errors: Sequence[dict[str, Any]],
    query_results: Sequence[QueryExecutionResult],
    notes: Sequence[str],
) -> dict[str, Any]:
    """Build the detailed run metadata JSON payload."""

    return {
        "script_name": config.script_name,
        "script_path": str(config.script_path),
        "helper_module_path": str(config.helper_module_path),
        "script_version": config.script_version,
        "run_id": config.run_id,
        "run_timestamp": config.run_timestamp,
        "week_name": config.week_partition.week_name,
        "week_name_mode": config.week_name_mode,
        "search_window": {
            "start_date": config.start_date.isoformat(),
            "end_date": config.end_date.isoformat(),
            "search_start_datetime": config.search_start_datetime.isoformat(),
            "search_end_datetime": config.search_end_datetime.isoformat(),
            "naming_start_date": config.week_partition.naming_start_date.isoformat(),
            "naming_end_date": config.week_partition.naming_end_date.isoformat(),
        },
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "hostname": socket.gethostname(),
            "user": os.getenv("USER") or os.getenv("USERNAME") or "",
            "cwd": str(Path.cwd()),
        },
        "execution": {
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_seconds": duration_seconds,
            "status": status,
            "exit_code": int(map_status_to_exit_code(status)),
            "dry_run": config.dry_run,
        },
        "config": serialize_for_json(config),
        "counts": {
            "queries": len(config.queries),
            "queries_failed": sum(1 for result in query_results if result.status == "failed"),
            "videos_found": sum(result.videos_found for result in query_results),
            "videos_with_comments": sum(result.videos_with_comments for result in query_results),
            "comments_extracted": sum(result.comments_extracted for result in query_results),
            "video_errors": sum(result.video_errors for result in query_results),
        },
        "artifact_paths": artifact_paths,
        "errors": list(errors),
        "notes": list(notes),
    }


def map_status_to_exit_code(status: str) -> int:
    """Map execution status to documented exit codes."""

    if status == "success":
        return int(ExitCode.SUCCESS)
    if status == "partial_success":
        return int(ExitCode.PARTIAL_SUCCESS)
    return int(ExitCode.FAILED_API)


def dataframe_to_csv(path: Path, dataframe: pd.DataFrame) -> None:
    """Write a dataframe with consistent encoding for Radar artifacts."""

    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False, encoding="utf-8-sig")


def publish_canonical_artifacts(
    config: ResolvedConfig,
    artifact_paths: dict[str, Path],
    logger: logging.Logger,
) -> dict[str, str]:
    """Publish selected run artifacts at the weekly canonical location."""

    if not config.publish_canonical:
        return {}

    published: dict[str, str] = {}
    canonical_targets = {
        "comments_csv": config.week_dir / f"{COMMENTS_FILENAME_PREFIX}_{config.week_partition.week_name}.csv",
        "videos_csv": config.week_dir / VIDEOS_FILENAME,
        "queries_csv": config.week_dir / QUERIES_FILENAME,
        "metadata_json": config.week_dir / METADATA_FILENAME,
        "parametros_json": config.week_dir / PARAMS_FILENAME,
        "summary_json": config.week_dir / SUMMARY_FILENAME,
        "manifest_json": config.week_dir / MANIFEST_FILENAME,
        "errors_json": config.week_dir / ERRORS_FILENAME,
    }

    for key, source_path in artifact_paths.items():
        if key not in canonical_targets:
            continue
        if not source_path.exists():
            continue
        target_path = canonical_targets[key]
        ensure_publish_target(target_path, config.overwrite)
        shutil.copy2(source_path, target_path)
        published[key] = str(target_path)
        logger.info("Artefacto canonico publicado | key=%s path=%s", key, target_path)

    return published


def persist_outputs(
    config: ResolvedConfig,
    query_results: Sequence[QueryExecutionResult],
    *,
    status: str,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    logger: logging.Logger,
    notes: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, str]]:
    """Persist the full set of run artifacts."""

    comments_df = build_comments_dataframe(query_results)
    videos_df = build_videos_dataframe(query_results)
    queries_df = build_queries_summary_dataframe(query_results)
    errors = flatten_errors(query_results)

    artifact_records: list[ArtifactRecord] = []
    artifact_paths: dict[str, Path] = {}

    comments_path = config.run_dir / f"{COMMENTS_FILENAME_PREFIX}_{config.week_partition.week_name}.csv"
    dataframe_to_csv(comments_path, comments_df)
    artifact_paths["comments_csv"] = comments_path
    artifact_records.append(
        ArtifactRecord(
            name=comments_path.name,
            artifact_type="dataset",
            path=str(comments_path),
            description="Comentarios top-level extraidos de YouTube.",
            timestamp=now_utc_text(),
        )
    )

    videos_path = config.run_dir / VIDEOS_FILENAME
    dataframe_to_csv(videos_path, videos_df)
    artifact_paths["videos_csv"] = videos_path
    artifact_records.append(
        ArtifactRecord(
            name=videos_path.name,
            artifact_type="dataset",
            path=str(videos_path),
            description="Inventario de videos encontrados por query.",
            timestamp=now_utc_text(),
        )
    )

    queries_path = config.run_dir / QUERIES_FILENAME
    dataframe_to_csv(queries_path, queries_df)
    artifact_paths["queries_csv"] = queries_path
    artifact_records.append(
        ArtifactRecord(
            name=queries_path.name,
            artifact_type="summary_table",
            path=str(queries_path),
            description="Resumen por query de la corrida de extraccion.",
            timestamp=now_utc_text(),
        )
    )

    summary = build_summary(
        config,
        query_results,
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
    artifact_records.append(
        ArtifactRecord(
            name=summary_path.name,
            artifact_type="summary",
            path=str(summary_path),
            description="Resumen operativo de la corrida.",
            timestamp=now_utc_text(),
        )
    )

    params_payload = {
        "run_id": config.run_id,
        "script_name": config.script_name,
        "script_version": config.script_version,
        "queries": config.queries,
        "queries_source": config.queries_source,
        "week_name": config.week_partition.week_name,
        "week_name_mode": config.week_name_mode,
        "search_start_datetime": config.search_start_datetime.isoformat(),
        "search_end_datetime": config.search_end_datetime.isoformat(),
        "naming_start_date": config.week_partition.naming_start_date.isoformat(),
        "naming_end_date": config.week_partition.naming_end_date.isoformat(),
        "output_root_dir": str(config.output_root_dir),
        "week_dir": str(config.week_dir),
        "run_dir": str(config.run_dir),
        "youtube_api_key_env": config.youtube_api_key_env,
        "api_key_source": config.api_key_source,
        "max_results_search": config.max_results_search,
        "max_comments_per_video": config.max_comments_per_video,
        "country": config.country,
        "language": config.language,
        "publish_canonical": config.publish_canonical,
        "overwrite": config.overwrite,
        "dry_run": config.dry_run,
    }
    params_path = config.run_dir / PARAMS_FILENAME
    write_json_file(params_path, params_payload)
    artifact_paths["parametros_json"] = params_path
    artifact_records.append(
        ArtifactRecord(
            name=params_path.name,
            artifact_type="parameters",
            path=str(params_path),
            description="Parametros efectivos de la corrida.",
            timestamp=now_utc_text(),
        )
    )

    metadata_path = config.run_dir / METADATA_FILENAME
    artifact_paths["metadata_json"] = metadata_path

    if errors:
        errors_path = config.run_dir / ERRORS_FILENAME
        write_json_file(errors_path, errors)
        artifact_paths["errors_json"] = errors_path
        artifact_records.append(
            ArtifactRecord(
                name=errors_path.name,
                artifact_type="errors",
                path=str(errors_path),
                description="Errores recuperables y fallas registradas durante la corrida.",
                timestamp=now_utc_text(),
            )
        )

    log_path = config.run_dir / LOG_FILENAME
    if log_path.exists():
        artifact_paths["run_log"] = log_path
        artifact_records.append(
            ArtifactRecord(
                name=log_path.name,
                artifact_type="log",
                path=str(log_path),
                description="Log operativo de la corrida.",
                timestamp=now_utc_text(),
            )
        )

    manifest_payload = [serialize_for_json(record) for record in artifact_records]
    manifest_path = config.run_dir / MANIFEST_FILENAME
    artifact_paths["manifest_json"] = manifest_path

    artifact_records.append(
        ArtifactRecord(
            name=manifest_path.name,
            artifact_type="manifest",
            path=str(manifest_path),
            description="Inventario de artefactos producidos por la corrida.",
            timestamp=now_utc_text(),
        )
    )
    manifest_payload = [serialize_for_json(record) for record in artifact_records]

    metadata = build_metadata(
        config,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        artifact_paths={key: str(value) for key, value in artifact_paths.items()},
        errors=errors,
        query_results=query_results,
        notes=notes,
    )
    write_json_file(metadata_path, metadata)
    artifact_records.append(
        ArtifactRecord(
            name=metadata_path.name,
            artifact_type="metadata",
            path=str(metadata_path),
            description="Metadata completa y trazabilidad de la corrida.",
            timestamp=now_utc_text(),
        )
    )
    manifest_payload = [serialize_for_json(record) for record in artifact_records]
    write_json_file(manifest_path, manifest_payload)

    published_paths = publish_canonical_artifacts(config, artifact_paths, logger)
    if published_paths:
        summary["published_canonical_paths"] = published_paths
        metadata["published_canonical_paths"] = published_paths
        write_json_file(summary_path, summary)
        write_json_file(metadata_path, metadata)
        write_json_file(manifest_path, manifest_payload)

    return summary, metadata, manifest_payload, {key: str(value) for key, value in artifact_paths.items()}


def build_dry_run_result(config: ResolvedConfig, logger: logging.Logger) -> RunExecutionResult:
    """Persist a dry-run execution without calling the YouTube API."""

    started_at = now_utc_text()
    finished_at = started_at
    duration_seconds = 0.0
    notes = build_notes(config, "success")
    dry_results = [
        QueryExecutionResult(
            query_index=index,
            query=query,
            status="success",
            videos_found=0,
            videos_with_comments=0,
            comments_extracted=0,
            video_errors=0,
            query_errors=0,
            duration_seconds=0.0,
        )
        for index, query in enumerate(config.queries, start=1)
    ]
    summary, metadata, manifest, artifact_paths = persist_outputs(
        config,
        dry_results,
        status="success",
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        logger=logger,
        notes=notes,
    )
    logger.info("Dry run completado | run_dir=%s", config.run_dir)
    return RunExecutionResult(
        status="success",
        exit_code=int(ExitCode.SUCCESS),
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        config=config,
        query_results=dry_results,
        summary=summary,
        metadata=metadata,
        manifest=manifest,
        artifact_paths=artifact_paths,
        notes=notes,
        errors=[],
    )


def ensure_failure_output_layout(config: ResolvedConfig) -> None:
    """Create failure directories without deleting partial artifacts."""

    config.week_dir.mkdir(parents=True, exist_ok=True)
    config.run_dir.mkdir(parents=True, exist_ok=True)


def run_extraction(config: ResolvedConfig, logger: logging.Logger) -> RunExecutionResult:
    """Run the full extraction workflow and persist structured outputs."""

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

    logger.info(
        "Inicio de corrida | run_id=%s week_name=%s output_root=%s week_name_mode=%s",
        config.run_id,
        config.week_partition.week_name,
        config.output_root_dir,
        config.week_name_mode,
    )
    logger.info(
        "Parametros efectivos | start_date=%s end_date=%s total_queries=%s max_results_search=%s max_comments_per_video=%s",
        config.start_date,
        config.end_date,
        len(config.queries),
        config.max_results_search,
        config.max_comments_per_video,
    )

    if config.dry_run:
        return build_dry_run_result(config, logger)

    youtube = build_youtube_client(config)
    started_at = now_utc_text()
    extraction_timestamp = now_local_text()
    started_perf = time.perf_counter()
    query_results: list[QueryExecutionResult] = []

    for query_index, query in enumerate(config.queries, start=1):
        result = extract_query_batch(
            youtube,
            query=query,
            query_index=query_index,
            config=config,
            extraction_timestamp=extraction_timestamp,
            logger=logger,
        )
        query_results.append(result)

    finished_at = now_utc_text()
    duration_seconds = round(time.perf_counter() - started_perf, 3)
    status = determine_run_status(query_results)
    notes = build_notes(config, status)

    summary, metadata, manifest, artifact_paths = persist_outputs(
        config,
        query_results,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        logger=logger,
        notes=notes,
    )
    errors = flatten_errors(query_results)

    logger.info(
        "Cierre de corrida | status=%s comentarios=%s videos=%s run_dir=%s",
        status,
        summary["total_comments_extracted"],
        summary["total_videos_found"],
        config.run_dir,
    )

    return RunExecutionResult(
        status=status,
        exit_code=map_status_to_exit_code(status),
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        config=config,
        query_results=query_results,
        summary=summary,
        metadata=metadata,
        manifest=manifest,
        artifact_paths=artifact_paths,
        notes=notes,
        errors=errors,
    )


def write_failure_artifacts(
    *,
    config: ResolvedConfig,
    logger: logging.Logger,
    status: str,
    exit_code: int,
    started_at: str,
    finished_at: str,
    message: str,
    errors: Sequence[dict[str, Any]],
) -> None:
    """Best-effort failure payloads when execution aborts before normal persistence."""

    configure_output_layout(config)
    summary = {
        "run_id": config.run_id,
        "status": status,
        "start_date": config.start_date.isoformat(),
        "end_date": config.end_date.isoformat(),
        "week_name": config.week_partition.week_name,
        "output_dir": str(config.run_dir),
        "total_queries": len(config.queries),
        "queries_processed": 0,
        "queries_failed": len(config.queries),
        "total_videos_found": 0,
        "total_videos_with_comments": 0,
        "total_comments_extracted": 0,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": 0.0,
        "api_key_source": config.api_key_source,
        "week_name_mode": config.week_name_mode,
        "script_name": config.script_name,
        "script_version": config.script_version,
        "notes": build_notes(config, status) + [message],
        "exit_code": exit_code,
    }
    metadata = {
        "script_name": config.script_name,
        "script_path": str(config.script_path),
        "helper_module_path": str(config.helper_module_path),
        "run_id": config.run_id,
        "run_dir": str(config.run_dir),
        "status": status,
        "exit_code": exit_code,
        "started_at": started_at,
        "finished_at": finished_at,
        "error_message": message,
        "errors": errors,
        "config": serialize_for_json(config),
    }
    safe_write_json_file(config.run_dir / SUMMARY_FILENAME, summary, logger)
    safe_write_json_file(config.run_dir / METADATA_FILENAME, metadata, logger)
    safe_write_json_file(config.run_dir / PARAMS_FILENAME, serialize_for_json(config), logger)
    if errors:
        safe_write_json_file(config.run_dir / ERRORS_FILENAME, list(errors), logger)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint used by the numbered wrapper script."""

    args = parse_args(argv)
    bootstrap_logger = setup_logging((args.log_level or DEFAULT_LOG_LEVEL).upper())
    started_at = now_utc_text()
    config: ResolvedConfig | None = None

    try:
        config = resolve_config(args)
        result = run_extraction(config, bootstrap_logger)
        return int(result.exit_code)
    except ConfigurationError as exc:
        bootstrap_logger.error("Error de configuracion: %s", exc)
        return int(ExitCode.FAILED_CONFIG)
    except ApiAuthenticationError as exc:
        bootstrap_logger.error("Error de API/autenticacion: %s", exc)
        if config is None:
            return int(ExitCode.FAILED_API)
        write_failure_artifacts(
            config=config,
            logger=bootstrap_logger,
            status="failed",
            exit_code=int(ExitCode.FAILED_API),
            started_at=started_at,
            finished_at=now_utc_text(),
            message=str(exc),
            errors=[
                serialize_for_json(
                    ErrorRecord(
                        stage="bootstrap",
                        scope="run",
                        message=str(exc),
                        timestamp=now_utc_text(),
                        fatal=True,
                    )
                )
            ],
        )
        return int(ExitCode.FAILED_API)
    except OutputWriteError as exc:
        bootstrap_logger.error("Error de escritura: %s", exc)
        if config is None:
            return int(ExitCode.FAILED_WRITE)
        write_failure_artifacts(
            config=config,
            logger=bootstrap_logger,
            status="failed",
            exit_code=int(ExitCode.FAILED_WRITE),
            started_at=started_at,
            finished_at=now_utc_text(),
            message=str(exc),
            errors=[
                serialize_for_json(
                    ErrorRecord(
                        stage="persist_outputs",
                        scope="run",
                        message=str(exc),
                        timestamp=now_utc_text(),
                        fatal=True,
                    )
                )
            ],
        )
        return int(ExitCode.FAILED_WRITE)
    except Exception as exc:  # pragma: no cover - defensive catch for CLI
        bootstrap_logger.exception("Fallo no controlado del extractor: %s", exc)
        return int(ExitCode.FAILED_API)
