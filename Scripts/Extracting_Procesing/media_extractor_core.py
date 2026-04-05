#!/usr/bin/env python3
"""
Núcleo reusable del extractor de medios para Radar.

Este módulo profesionaliza la base técnica de `04_medios_extractor.py` y deja
el componente listo para usarse desde terminal, desde otro script Python o
desde un orquestador. El alcance se limita a búsqueda RSS, resolución de URLs,
descarga de artículos, persistencia estructurada y trazabilidad de corrida.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import logging
import os
import platform
import random
import re
import shutil
import socket
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from enum import IntEnum
from html import unescape
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import quote, quote_plus, urlparse

import pandas as pd
import requests

try:
    import trafilatura
except ImportError as exc:  # pragma: no cover - depende del entorno
    trafilatura = None  # type: ignore[assignment]
    TRAFILATURA_IMPORT_ERROR: Exception | None = exc
else:
    TRAFILATURA_IMPORT_ERROR = None

try:
    import cloudscraper
except ImportError:  # pragma: no cover - dependencia opcional
    cloudscraper = None  # type: ignore[assignment]

try:
    from googlenewsdecoder import gnewsdecoder
except ImportError:  # pragma: no cover - dependencia opcional
    gnewsdecoder = None  # type: ignore[assignment]

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - dependencia opcional
    sync_playwright = None  # type: ignore[assignment]


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "Datos_RAdAR" / "Medios"
DEFAULT_CACHE_DIRNAME = "_cache_media_extractor"
SCRIPT_VERSION = "2.0.0"
SCRIPT_COMPONENT = "radar.media_extractor"
SOURCE_PLATFORM = "news_media"

WEEK_MODE_EXACT = "exact_range"
WEEK_MODE_CANONICAL = "canonical_monday_sunday"
WEEK_NAME_MODE_CHOICES = (WEEK_MODE_EXACT, WEEK_MODE_CANONICAL)

DEFAULT_MEDIOS = [
    "site:oem.com.mx",
    "site:milenio.com",
]
DEFAULT_TERMINOS = [
    '"Monica Villarreal"',
    '"gobierno de tampico"',
    '"tampico"',
]
DEFAULT_MODO_QUERIES = "combinado"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_RUN_ID = "media_extract"
DEFAULT_PAUSA = 2.0
DEFAULT_PAUSA_ENTRE_QUERIES = 3.0
DEFAULT_MAX_RESULTS_PER_QUERY = 50
DEFAULT_RSS_TIMEOUT = 30
DEFAULT_RSS_MAX_REINTENTOS = 3
DEFAULT_RSS_BACKOFF_INICIAL = 5.0
DEFAULT_RSS_BACKOFF_MAX = 60.0
DEFAULT_PLAYWRIGHT_TIMEOUT = 25000
DEFAULT_PLAYWRIGHT_WAIT_AFTER_LOAD = 2000
DEFAULT_PLAYWRIGHT_HEADLESS = True
DEFAULT_PLAYWRIGHT_PAUSA_ENTRE_PAGINAS = 1.5
DEFAULT_DOMINIOS_PLAYWRIGHT_PRIORITARIO = [
    "noticiasdetampico.mx",
]
USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

MAIN_CSV_PREFIX = "media_articles"
RSS_RAW_FILENAME = "rss_items_raw.csv"
URLS_FILENAME = "urls_resueltas.csv"
DOWNLOAD_SUMMARY_FILENAME = "descarga_articulos_summary.csv"
QUERIES_FILENAME = "queries_summary.csv"
SUMMARY_FILENAME = "summary.json"
METADATA_FILENAME = "metadata_run.json"
PARAMS_FILENAME = "parametros_run.json"
MANIFEST_FILENAME = "manifest.json"
ERRORS_FILENAME = "errores_detectados.json"
LOG_FILENAME = "run.log"

ARTICLE_COLUMNS = [
    "run_id",
    "week_name",
    "source_platform",
    "medio",
    "termino",
    "query",
    "query_index",
    "article_title",
    "article_url_original",
    "article_url_resolved",
    "source_domain",
    "published_at",
    "retrieved_at",
    "article_text",
    "article_text_length",
    "extraction_method",
    "rss_source",
    "status_descarga",
    "error_type",
    "error_detail",
    "resolution_strategy",
    "cache_hit_rss",
    "cache_hit_url_resolution",
    "cache_hit_article",
    "playwright_used",
    "fallback_used",
    "attempted_methods",
]

RSS_COLUMNS = [
    "query_index",
    "query",
    "medio",
    "termino",
    "rss_source",
    "article_title",
    "article_url_original",
    "published_at",
    "published_at_raw",
    "source_name",
    "description",
    "retrieved_at",
    "cache_hit_rss",
]

URL_RESOLUTION_COLUMNS = [
    "query_index",
    "query",
    "medio",
    "termino",
    "article_title",
    "article_url_original",
    "article_url_resolved",
    "status",
    "resolution_strategy",
    "cache_hit_url_resolution",
    "error_type",
    "error_detail",
]

DOWNLOAD_SUMMARY_COLUMNS = [
    "query_index",
    "query",
    "medio",
    "termino",
    "article_title",
    "article_url_resolved",
    "source_domain",
    "status_descarga",
    "extraction_method",
    "article_text_length",
    "cache_hit_article",
    "playwright_used",
    "fallback_used",
    "attempted_methods",
    "error_type",
    "error_detail",
]

QUERY_SUMMARY_COLUMNS = [
    "query_index",
    "query",
    "medio",
    "termino",
    "status",
    "rss_items_detected",
    "urls_resolved_ok",
    "articles_attempted",
    "articles_downloaded_ok",
    "articles_downloaded_empty",
    "articles_failed",
    "duration_seconds",
]


class ExitCode(IntEnum):
    SUCCESS = 0
    PARTIAL_SUCCESS = 1
    FAILED_CONFIG = 2
    FAILED_SOURCE = 3
    FAILED_WRITE = 4


class ExtractionError(Exception):
    """Base class for media extractor failures."""


class ConfigurationError(ExtractionError):
    """Raised when runtime configuration is invalid."""


class SourceAccessError(ExtractionError):
    """Raised when RSS or article sources fail in a fatal way."""


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
class QuerySpec:
    query_index: int
    query: str
    medio: str
    termino: str
    source: str
    mode: str


@dataclass(frozen=True)
class ResolvedConfig:
    script_name: str
    script_path: Path
    helper_module_path: Path
    entrypoint_alias: str
    script_version: str
    since: date
    before: date
    week_name_mode: str
    week_partition: WeekPartition
    output_root_dir: Path
    week_dir: Path
    run_dir: Path
    cache_dir: Path
    run_id: str
    run_timestamp: str
    medios: list[str]
    terminos: list[str]
    modo_queries: str
    queries: list[QuerySpec]
    queries_source: str
    log_level: str
    overwrite: bool
    publish_canonical: bool
    omitir_semanas_existentes: bool
    pausa: float
    pausa_entre_queries: float
    max_results_per_query: int
    max_articles_per_week: int | None
    dry_run: bool
    use_playwright: bool
    ignore_cache: bool
    config_file: Path | None = None


@dataclass
class ArtifactRecord:
    name: str
    artifact_type: str
    path: str
    description: str
    timestamp: str
    size_bytes: int = 0


@dataclass
class ErrorRecord:
    stage: str
    scope: str
    message: str
    timestamp: str
    query_index: int | None = None
    query: str | None = None
    article_url: str | None = None
    fatal: bool = False
    error_type: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class RSSItemRecord:
    query_index: int
    query: str
    medio: str
    termino: str
    rss_source: str
    article_title: str
    article_url_original: str
    published_at: str
    published_at_raw: str
    source_name: str
    description: str
    retrieved_at: str
    cache_hit_rss: bool = False


@dataclass
class URLResolutionRecord:
    query_index: int
    query: str
    medio: str
    termino: str
    article_title: str
    article_url_original: str
    article_url_resolved: str
    status: str
    resolution_strategy: str
    cache_hit_url_resolution: bool
    error_type: str = ""
    error_detail: str = ""


@dataclass
class ArticleDownloadRecord:
    query_index: int
    query: str
    medio: str
    termino: str
    article_title: str
    article_url_resolved: str
    source_domain: str
    retrieved_at: str
    article_text: str
    article_text_length: int
    extraction_method: str
    status_descarga: str
    cache_hit_article: bool
    playwright_used: bool
    fallback_used: bool
    attempted_methods: list[str] = field(default_factory=list)
    error_type: str = ""
    error_detail: str = ""


@dataclass
class QueryExecutionResult:
    query_spec: QuerySpec
    status: str
    duration_seconds: float
    rss_items: list[RSSItemRecord] = field(default_factory=list)
    url_resolutions: list[URLResolutionRecord] = field(default_factory=list)
    article_downloads: list[ArticleDownloadRecord] = field(default_factory=list)
    article_rows: list[dict[str, Any]] = field(default_factory=list)
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


def serialize_for_json(value: Any) -> Any:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize_for_json(payload), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def safe_write_json_file(path: Path, payload: dict[str, Any] | list[Any], logger: logging.Logger) -> None:
    try:
        write_json_file(path, payload)
    except Exception as exc:  # pragma: no cover - ruta defensiva
        logger.error("No se pudo escribir %s: %s", path, exc)


def dataframe_to_csv(path: Path, dataframe: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False, encoding="utf-8-sig")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extractor profesional de medios para Radar: RSS de Google News, "
            "resolución de URLs y descarga de artículos con trazabilidad fuerte."
        )
    )
    parser.add_argument("--since", help="Fecha inicial de búsqueda (YYYY-MM-DD).")
    parser.add_argument("--before", help="Fecha final de búsqueda (YYYY-MM-DD).")
    parser.add_argument("--medio", dest="medios", action="append", default=None, help="Medio o site: a consultar.")
    parser.add_argument("--termino", dest="terminos", action="append", default=None, help="Término de búsqueda.")
    parser.add_argument("--queries-file", default=None, help="Archivo externo TXT/JSON/CSV con queries.")
    parser.add_argument("--modo-queries", choices=("compacto", "combinado"), default=None)
    parser.add_argument("--config-file", default=None, help="Archivo JSON opcional con configuración base.")
    parser.add_argument("--output-dir", default=None, help=f"Directorio raíz de salida. Default: {DEFAULT_OUTPUT_DIR}")
    parser.add_argument("--cache-dir", default=None, help="Directorio de caché. Default: <output-dir>/_cache_media_extractor")
    parser.add_argument("--run-id", default=None, help="Identificador semántico de corrida.")
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default=None)
    parser.add_argument("--overwrite", action="store_true", default=None, help="Permite sobrescribir artefactos canónicos.")
    parser.add_argument("--publish-canonical", action="store_true", default=None, help="Publica copia canónica semanal.")
    parser.add_argument(
        "--omitir-semanas-existentes",
        action="store_true",
        default=None,
        help="Si ya existen artefactos previos de la semana, registrar corrida como omitida.",
    )
    parser.add_argument("--ignore-cache", action="store_true", default=None, help="Ignora caché RSS, resolución y artículos.")
    parser.add_argument("--pausa", type=float, default=None, help=f"Pausa entre descargas. Default: {DEFAULT_PAUSA}")
    parser.add_argument(
        "--pausa-entre-queries",
        type=float,
        default=None,
        help=f"Pausa entre queries RSS. Default: {DEFAULT_PAUSA_ENTRE_QUERIES}",
    )
    parser.add_argument("--week-name-mode", choices=WEEK_NAME_MODE_CHOICES, default=None)
    parser.add_argument(
        "--use-playwright",
        action="store_true",
        default=None,
        help="Habilita Playwright como estrategia controlada de fallback.",
    )
    parser.add_argument("--max-results-per-query", type=int, default=None)
    parser.add_argument("--max-articles-per-week", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true", default=None)
    return parser.parse_args(argv)


def load_config_file(config_file: Path) -> dict[str, Any]:
    if not config_file.exists():
        raise ConfigurationError(f"No existe el config file: {config_file}")
    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"Config file inválido: {config_file}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError("El config file debe contener un objeto JSON.")
    return data


def merge_config_sources(args: argparse.Namespace) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    config_file_raw = getattr(args, "config_file", None)
    if config_file_raw:
        config_path = Path(config_file_raw).expanduser().resolve()
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
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ConfigurationError(f"{label} inválida '{raw_value}', usa YYYY-MM-DD.") from exc


def normalize_string_list(raw_values: Any) -> list[str]:
    if raw_values is None:
        return []
    if isinstance(raw_values, str):
        return [raw_values.strip()] if raw_values.strip() else []
    if isinstance(raw_values, list):
        return [str(value).strip() for value in raw_values if str(value).strip()]
    raise ConfigurationError("Se esperaba una lista o string para los valores configurados.")


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


def resolve_week_partition(since: date, before: date, mode: str) -> WeekPartition:
    if mode == WEEK_MODE_EXACT:
        naming_start = since
        naming_end = before
    elif mode == WEEK_MODE_CANONICAL:
        naming_start = since - timedelta(days=since.weekday())
        naming_end = before + timedelta(days=(6 - before.weekday()))
    else:  # pragma: no cover
        raise ConfigurationError(f"Modo de semana no soportado: {mode}")
    label = f"semana_{format_spanish_date(naming_start)}_{format_spanish_date(naming_end)}_{naming_end:%y}"
    week_name = f"{naming_start.isoformat()}_{label}"
    return WeekPartition(
        start_date=since,
        end_date=before,
        week_name=week_name,
        naming_start_date=naming_start,
        naming_end_date=naming_end,
    )


def load_queries_from_file(queries_file: Path, modo_queries: str) -> tuple[list[QuerySpec], str]:
    if not queries_file.exists():
        raise ConfigurationError(f"No existe el archivo de queries: {queries_file}")

    suffix = queries_file.suffix.lower()
    raw_specs: list[QuerySpec] = []
    if suffix == ".json":
        payload = json.loads(queries_file.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            for index, item in enumerate(payload, start=1):
                if isinstance(item, str):
                    query = item.strip()
                    if query:
                        raw_specs.append(QuerySpec(index, query, "", "", str(queries_file), modo_queries))
                elif isinstance(item, dict):
                    query = str(item.get("query", "")).strip()
                    if query:
                        raw_specs.append(
                            QuerySpec(
                                query_index=index,
                                query=query,
                                medio=str(item.get("medio", "")).strip(),
                                termino=str(item.get("termino", "")).strip(),
                                source=str(queries_file),
                                mode=str(item.get("mode", modo_queries)),
                            )
                        )
                else:
                    raise ConfigurationError("El JSON de queries debe contener strings o dicts.")
        else:
            raise ConfigurationError("El JSON de queries debe ser una lista.")
    elif suffix == ".csv":
        dataframe = pd.read_csv(queries_file)
        if "query" not in dataframe.columns:
            raise ConfigurationError("El CSV de queries debe incluir una columna 'query'.")
        for index, row in enumerate(dataframe.to_dict(orient="records"), start=1):
            query = str(row.get("query", "")).strip()
            if not query:
                continue
            raw_specs.append(
                QuerySpec(
                    query_index=index,
                    query=query,
                    medio=str(row.get("medio", "")).strip(),
                    termino=str(row.get("termino", "")).strip(),
                    source=str(queries_file),
                    mode=str(row.get("mode", modo_queries)),
                )
            )
    else:
        for index, line in enumerate(queries_file.read_text(encoding="utf-8").splitlines(), start=1):
            query = line.strip()
            if not query or query.startswith("#"):
                continue
            raw_specs.append(QuerySpec(index, query, "", "", str(queries_file), modo_queries))

    if not raw_specs:
        raise ConfigurationError("El archivo de queries no produjo ninguna query válida.")
    return raw_specs, str(queries_file)


def generate_queries(medios: Sequence[str], terminos: Sequence[str], modo: str, source: str) -> list[QuerySpec]:
    query_specs: list[QuerySpec] = []
    if modo == "combinado":
        index = 1
        for medio in medios:
            for termino in terminos:
                query_specs.append(
                    QuerySpec(
                        query_index=index,
                        query=f"{termino} {medio}",
                        medio=medio,
                        termino=termino,
                        source=source,
                        mode=modo,
                    )
                )
                index += 1
        return query_specs

    bloque_or = " OR ".join(terminos)
    for index, medio in enumerate(medios, start=1):
        query_specs.append(
            QuerySpec(
                query_index=index,
                query=f"({bloque_or}) {medio}",
                medio=medio,
                termino=" | ".join(terminos),
                source=source,
                mode=modo,
            )
        )
    return query_specs


def resolve_config(
    args: argparse.Namespace,
    *,
    script_name: str,
    script_path: Path,
    entrypoint_alias: str,
) -> ResolvedConfig:
    merged = merge_config_sources(args)

    since_raw = merged.get("since")
    before_raw = merged.get("before")
    if not since_raw or not before_raw:
        raise ConfigurationError("Debes definir --since y --before o proveerlos en --config-file.")

    since = parse_date_str(str(since_raw), "since")
    before = parse_date_str(str(before_raw), "before")
    if before < since:
        raise ConfigurationError("--before no puede ser menor que --since.")

    modo_queries = str(merged.get("modo_queries", DEFAULT_MODO_QUERIES))
    if modo_queries not in {"compacto", "combinado"}:
        raise ConfigurationError(f"Modo de queries no soportado: {modo_queries}")

    queries_file_raw = merged.get("queries_file")
    medios = normalize_string_list(merged.get("medios")) or list(DEFAULT_MEDIOS)
    terminos = normalize_string_list(merged.get("terminos")) or list(DEFAULT_TERMINOS)

    if queries_file_raw:
        queries_file = Path(str(queries_file_raw)).expanduser().resolve()
        queries, queries_source = load_queries_from_file(queries_file, modo_queries)
    else:
        if not medios:
            raise ConfigurationError("Debes definir al menos un --medio o proveer queries file.")
        if not terminos:
            raise ConfigurationError("Debes definir al menos un --termino o proveer queries file.")
        queries_source = "generated"
        queries = generate_queries(medios, terminos, modo_queries, source=queries_source)

    week_name_mode = str(merged.get("week_name_mode", WEEK_MODE_EXACT))
    week_partition = resolve_week_partition(since, before, week_name_mode)

    output_root_dir = Path(str(merged.get("output_dir", DEFAULT_OUTPUT_DIR))).expanduser().resolve()
    run_id = str(merged.get("run_id", DEFAULT_RUN_ID)).strip() or DEFAULT_RUN_ID
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    week_dir = output_root_dir / week_partition.week_name
    run_dir = week_dir / "runs" / f"{run_id}_{run_timestamp}"

    cache_dir_raw = merged.get("cache_dir")
    cache_dir = (
        Path(str(cache_dir_raw)).expanduser().resolve()
        if cache_dir_raw
        else output_root_dir / DEFAULT_CACHE_DIRNAME
    )

    max_results_per_query = int(merged.get("max_results_per_query", DEFAULT_MAX_RESULTS_PER_QUERY))
    if max_results_per_query <= 0:
        raise ConfigurationError("--max-results-per-query debe ser mayor que 0.")

    max_articles_per_week_raw = merged.get("max_articles_per_week")
    max_articles_per_week = None
    if max_articles_per_week_raw is not None:
        max_articles_per_week = int(max_articles_per_week_raw)
        if max_articles_per_week <= 0:
            raise ConfigurationError("--max-articles-per-week debe ser mayor que 0.")

    pausa = float(merged.get("pausa", DEFAULT_PAUSA))
    pausa_entre_queries = float(merged.get("pausa_entre_queries", DEFAULT_PAUSA_ENTRE_QUERIES))
    if pausa < 0 or pausa_entre_queries < 0:
        raise ConfigurationError("Las pausas no pueden ser negativas.")

    use_playwright = bool(merged.get("use_playwright", False))
    if use_playwright and sync_playwright is None:
        raise ConfigurationError(
            "Se solicitó --use-playwright pero Playwright no está instalado. "
            "Instala 'playwright' y ejecuta 'playwright install chromium'."
        )

    config_file_raw = merged.get("config_file")
    config_file = Path(config_file_raw).resolve() if config_file_raw else None

    return ResolvedConfig(
        script_name=script_name,
        script_path=script_path,
        helper_module_path=Path(__file__).resolve(),
        entrypoint_alias=entrypoint_alias,
        script_version=SCRIPT_VERSION,
        since=since,
        before=before,
        week_name_mode=week_name_mode,
        week_partition=week_partition,
        output_root_dir=output_root_dir,
        week_dir=week_dir,
        run_dir=run_dir,
        cache_dir=cache_dir,
        run_id=run_id,
        run_timestamp=run_timestamp,
        medios=list(medios),
        terminos=list(terminos),
        modo_queries=modo_queries,
        queries=queries,
        queries_source=queries_source,
        log_level=str(merged.get("log_level", DEFAULT_LOG_LEVEL)).upper(),
        overwrite=bool(merged.get("overwrite", False)),
        publish_canonical=bool(merged.get("publish_canonical", False)),
        omitir_semanas_existentes=bool(merged.get("omitir_semanas_existentes", False)),
        pausa=pausa,
        pausa_entre_queries=pausa_entre_queries,
        max_results_per_query=max_results_per_query,
        max_articles_per_week=max_articles_per_week,
        dry_run=bool(merged.get("dry_run", False)),
        use_playwright=use_playwright,
        ignore_cache=bool(merged.get("ignore_cache", False)),
        config_file=config_file,
    )


def setup_logging(log_level: str, log_file: Path | None = None) -> logging.Logger:
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


class CacheManager:
    """Gestor explícito de caché para RSS, resolución y artículos."""

    def __init__(self, root_dir: Path, *, enabled: bool, logger: logging.Logger) -> None:
        self.root_dir = root_dir
        self.enabled = enabled
        self.logger = logger
        self.stats = {
            "rss_hits": 0,
            "rss_writes": 0,
            "url_hits": 0,
            "url_writes": 0,
            "article_hits": 0,
            "article_writes": 0,
        }

    def _path(self, kind: str, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root_dir / kind / f"{digest}.json"

    def load(self, kind: str, key: str) -> dict[str, Any] | list[Any] | None:
        if not self.enabled:
            return None
        path = self._path(kind, key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.logger.debug("No se pudo leer caché %s: %s", path, exc)
            return None
        stats_key = {
            "rss": "rss_hits",
            "url_resolution": "url_hits",
            "article": "article_hits",
        }.get(kind)
        if stats_key:
            self.stats[stats_key] += 1
        return payload

    def save(self, kind: str, key: str, payload: dict[str, Any] | list[Any]) -> None:
        if not self.enabled:
            return
        path = self._path(kind, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(serialize_for_json(payload), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        stats_key = {
            "rss": "rss_writes",
            "url_resolution": "url_writes",
            "article": "article_writes",
        }.get(kind)
        if stats_key:
            self.stats[stats_key] += 1


class PlaywrightManager:
    """Encapsula uso opcional y explícito de Playwright."""

    def __init__(self, *, enabled: bool, logger: logging.Logger) -> None:
        self.enabled = enabled
        self.logger = logger
        self._pw = None
        self._browser = None
        self._context = None
        self.started = False
        self.used = False

    def ensure_ready(self) -> None:
        if not self.enabled:
            return
        if self._context is not None:
            return
        if sync_playwright is None:
            raise ConfigurationError(
                "Playwright no está disponible, pero se solicitó explícitamente."
            )
        try:
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(
                headless=DEFAULT_PLAYWRIGHT_HEADLESS,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )
            self._context = self._browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1366, "height": 768},
                locale="es-MX",
                timezone_id="America/Mexico_City",
            )
            self._context.route(
                "**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2,ttf,eot,mp4,webm}",
                lambda route: route.abort(),
            )
            self.started = True
            self.logger.info("Playwright inicializado correctamente para fallback de artículos.")
        except Exception as exc:
            raise ConfigurationError(
                "No se pudo inicializar Playwright. Revisa la instalación y el browser Chromium."
            ) from exc

    def fetch_text(self, url: str) -> tuple[str, list[str]]:
        self.ensure_ready()
        if self._context is None:
            return "", []

        page = None
        selectores = [
            "article",
            ".entry-content",
            ".post-content",
            ".article-body",
            ".td-post-content",
            ".content-inner",
            "main",
        ]
        try:
            page = self._context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_PLAYWRIGHT_TIMEOUT)
            page.wait_for_timeout(DEFAULT_PLAYWRIGHT_WAIT_AFTER_LOAD)
            for selector in selectores:
                try:
                    page.wait_for_selector(selector, timeout=3000)
                    break
                except Exception:
                    continue
            html = page.content()
            if not html or len(html) < 500:
                return "", ["playwright"]
            block_reason = detectar_html_bloqueado(html)
            if block_reason:
                return "", ["playwright"]
            text = extract_text_from_html(html)
            if not text:
                text = extract_dom_text_with_playwright(page, selectores)
            if text and len(text) >= 80:
                self.used = True
                return text, ["playwright"]
            return "", ["playwright"]
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass

    def close(self) -> None:
        try:
            if self._context is not None:
                self._context.close()
            if self._browser is not None:
                self._browser.close()
            if self._pw is not None:
                self._pw.stop()
        except Exception:
            pass
        self._pw = None
        self._browser = None
        self._context = None


def extract_dom_text_with_playwright(page, selectors: Sequence[str]) -> str:
    for selector in selectors:
        try:
            element = page.query_selector(selector)
            if element:
                text = element.inner_text()
                text = re.sub(r"\n{3,}", "\n\n", text)
                text = re.sub(r"[ \t]+", " ", text).strip()
                if len(text) >= 120:
                    return text
        except Exception:
            continue
    return ""


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
    canonical_path = canonical_main_csv_path(config)
    if canonical_path.exists():
        return True
    runs_dir = config.week_dir / "runs"
    if not runs_dir.exists():
        return False
    for summary_path in runs_dir.glob("*/summary.json"):
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if payload.get("status") in {"success", "partial_success"}:
            return True
    return False


def random_headers() -> dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.6",
        "Referer": "https://news.google.com/",
    }


def build_rss_url(query: str, since: date, before: date) -> str:
    query_with_dates = f"{query} after:{since.isoformat()} before:{before.isoformat()}"
    return (
        "https://news.google.com/rss/search"
        f"?q={quote_plus(query_with_dates)}"
        "&hl=es-419"
        "&gl=MX"
        "&ceid=MX:es-419"
    )


def parse_rss(xml_text: str, *, query_spec: QuerySpec, retrieved_at: str, rss_source: str) -> list[RSSItemRecord]:
    items: list[RSSItemRecord] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise SourceAccessError(f"No se pudo parsear el RSS: {exc}") from exc

    channel = root.find("channel")
    if channel is None:
        return items

    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        url_google = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()
        source_elem = item.find("source")
        source_name = (source_elem.text or "").strip() if source_elem is not None else ""

        published_at = ""
        if pub_date:
            try:
                published_at = parsedate_to_datetime(pub_date).isoformat()
            except Exception:
                published_at = ""

        items.append(
            RSSItemRecord(
                query_index=query_spec.query_index,
                query=query_spec.query,
                medio=query_spec.medio,
                termino=query_spec.termino,
                rss_source=rss_source,
                article_title=title,
                article_url_original=url_google,
                published_at=published_at,
                published_at_raw=pub_date,
                source_name=source_name,
                description=description,
                retrieved_at=retrieved_at,
            )
        )
    return items


def fetch_rss_items(
    query_spec: QuerySpec,
    config: ResolvedConfig,
    *,
    cache_manager: CacheManager,
    logger: logging.Logger,
) -> tuple[list[RSSItemRecord], list[ErrorRecord]]:
    rss_source = build_rss_url(query_spec.query, config.since, config.before)
    cached = cache_manager.load("rss", rss_source)
    retrieved_at = now_utc_text()

    if cached is not None:
        logger.info(
            "RSS cache hit | query_index=%s query=%s items=%s",
            query_spec.query_index,
            query_spec.query,
            len(cached),
        )
        items = [
            RSSItemRecord(**record, cache_hit_rss=True)
            for record in cached
        ]
        if config.max_results_per_query:
            items = items[: config.max_results_per_query]
        return items, []

    wait_seconds = DEFAULT_RSS_BACKOFF_INICIAL
    last_error: Exception | None = None
    for attempt in range(1, DEFAULT_RSS_MAX_REINTENTOS + 1):
        try:
            response = requests.get(rss_source, headers=random_headers(), timeout=DEFAULT_RSS_TIMEOUT)
            if response.status_code == 429:
                raise SourceAccessError("Google News RSS devolvió 429.")
            if response.status_code != 200:
                raise SourceAccessError(f"Google News RSS devolvió HTTP {response.status_code}.")

            items = parse_rss(
                response.text,
                query_spec=query_spec,
                retrieved_at=retrieved_at,
                rss_source=rss_source,
            )
            if config.max_results_per_query:
                items = items[: config.max_results_per_query]
            cache_manager.save("rss", rss_source, [serialize_for_json(item) for item in items])
            logger.info(
                "RSS obtenido | query_index=%s query=%s items=%s",
                query_spec.query_index,
                query_spec.query,
                len(items),
            )
            return items, []
        except Exception as exc:
            last_error = exc
            if attempt >= DEFAULT_RSS_MAX_REINTENTOS:
                break
            pause = min(wait_seconds, DEFAULT_RSS_BACKOFF_MAX) + random.uniform(1.0, 2.0)
            logger.warning(
                "Error recuperable RSS | query=%s intento=%s/%s pausa=%.1fs error=%s",
                query_spec.query,
                attempt,
                DEFAULT_RSS_MAX_REINTENTOS,
                pause,
                exc,
            )
            time.sleep(pause)
            wait_seconds = min(wait_seconds * 2, DEFAULT_RSS_BACKOFF_MAX)

    error = ErrorRecord(
        stage="fetch_rss_items",
        scope="query",
        message=str(last_error) if last_error else "Fallo RSS sin detalle",
        timestamp=now_utc_text(),
        query_index=query_spec.query_index,
        query=query_spec.query,
        fatal=False,
        error_type="rss_fetch_failed",
    )
    return [], [error]


def decode_base64_url(google_url: str) -> str | None:
    try:
        path = urlparse(google_url).path
        encoded_part = None
        for prefix in ("/rss/articles/", "/articles/", "/read/"):
            if prefix in path:
                encoded_part = path.split(prefix)[-1]
                break
        if not encoded_part:
            return None
        encoded_part = encoded_part.split("?", 1)[0]
        encoded_part = encoded_part.replace("-", "+").replace("_", "/")
        padding_needed = len(encoded_part) % 4
        if padding_needed:
            encoded_part += "=" * (4 - padding_needed)
        decoded_bytes = base64.b64decode(encoded_part)
        decoded_str = decoded_bytes.decode("utf-8", errors="ignore")
        urls = re.findall(r"https?://[^\s\"'<>]+", decoded_str)
        if not urls:
            return None
        for candidate in urls:
            if "/amp" not in candidate.lower() and ".amp." not in candidate.lower():
                return candidate.rstrip(")")
        return urls[0].rstrip(")")
    except Exception:
        return None


def extract_google_news_article_id(google_url: str) -> str | None:
    try:
        parsed = urlparse(google_url)
        if parsed.hostname != "news.google.com":
            return None
        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) < 2:
            return None
        if path_parts[-2] not in {"articles", "read"}:
            return None
        return path_parts[-1]
    except Exception:
        return None


def fetch_google_decoding_params(article_id: str) -> tuple[str, str] | None:
    endpoints = (
        f"https://news.google.com/articles/{article_id}",
        f"https://news.google.com/rss/articles/{article_id}",
    )
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, headers=random_headers(), timeout=20)
            if response.status_code != 200:
                continue
            signature_match = re.search(r'data-n-a-sg="([^"]+)"', response.text)
            timestamp_match = re.search(r'data-n-a-ts="([^"]+)"', response.text)
            if signature_match and timestamp_match:
                return signature_match.group(1), timestamp_match.group(1)
        except Exception:
            continue
    return None


def decode_with_google_batchexecute(google_url: str) -> str | None:
    article_id = extract_google_news_article_id(google_url)
    if not article_id:
        return None

    params = fetch_google_decoding_params(article_id)
    if not params:
        return None
    signature, timestamp = params

    payload = [
        "Fbv4je",
        (
            '["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
            f'"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{article_id}",{timestamp},"{signature}"]'
        ),
    ]
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "User-Agent": random.choice(USER_AGENTS),
    }

    try:
        response = requests.post(
            "https://news.google.com/_/DotsSplashUi/data/batchexecute",
            headers=headers,
            data=f"f.req={quote(json.dumps([[payload]]))}",
            timeout=20,
        )
        response.raise_for_status()
        if "\n\n" not in response.text:
            return None
        batched_payload = json.loads(response.text.split("\n\n", 1)[1])
        for entry in batched_payload:
            if not isinstance(entry, list) or len(entry) < 3:
                continue
            if entry[0] != "wrb.fr" or entry[1] != "Fbv4je":
                continue
            decoded_payload = json.loads(entry[2])
            if len(decoded_payload) < 2:
                continue
            decoded_url = decoded_payload[1]
            if decoded_url and "news.google.com" not in decoded_url:
                return decoded_url
    except Exception:
        return None
    return None


def decode_with_gnewsdecoder(google_url: str) -> str | None:
    if gnewsdecoder is None:
        return None
    try:
        result = gnewsdecoder(google_url, interval=1.0)
    except Exception:
        return None
    if not result or not result.get("status"):
        return None
    decoded_url = result.get("decoded_url", "")
    if decoded_url and "news.google.com" not in decoded_url:
        return decoded_url
    return None


def decode_with_requests(google_url: str) -> str | None:
    try:
        response = requests.head(google_url, allow_redirects=True, timeout=15, headers=random_headers())
        if response.url and "news.google.com" not in response.url:
            return response.url
        response = requests.get(google_url, allow_redirects=True, timeout=15, headers=random_headers(), stream=True)
        final_url = response.url
        response.close()
        if final_url and "news.google.com" not in final_url:
            return final_url
    except Exception:
        return None
    return None


def resolve_article_url(
    item: RSSItemRecord,
    *,
    cache_manager: CacheManager,
    logger: logging.Logger,
) -> URLResolutionRecord:
    original_url = item.article_url_original
    if not original_url:
        return URLResolutionRecord(
            query_index=item.query_index,
            query=item.query,
            medio=item.medio,
            termino=item.termino,
            article_title=item.article_title,
            article_url_original=original_url,
            article_url_resolved="",
            status="failed",
            resolution_strategy="none",
            cache_hit_url_resolution=False,
            error_type="missing_original_url",
            error_detail="El item RSS no contenía URL original.",
        )

    cached = cache_manager.load("url_resolution", original_url)
    if cached is not None:
        return URLResolutionRecord(**cached, cache_hit_url_resolution=True)

    if "news.google.com" not in original_url:
        record = URLResolutionRecord(
            query_index=item.query_index,
            query=item.query,
            medio=item.medio,
            termino=item.termino,
            article_title=item.article_title,
            article_url_original=original_url,
            article_url_resolved=original_url,
            status="success",
            resolution_strategy="passthrough",
            cache_hit_url_resolution=False,
        )
        cache_manager.save("url_resolution", original_url, serialize_for_json(record))
        return record

    strategies = (
        ("base64_direct", decode_base64_url),
        ("google_batchexecute", decode_with_google_batchexecute),
        ("gnewsdecoder", decode_with_gnewsdecoder),
        ("http_redirect", decode_with_requests),
    )
    for strategy_name, resolver in strategies:
        resolved_url = resolver(original_url)
        if resolved_url:
            record = URLResolutionRecord(
                query_index=item.query_index,
                query=item.query,
                medio=item.medio,
                termino=item.termino,
                article_title=item.article_title,
                article_url_original=original_url,
                article_url_resolved=resolved_url,
                status="success",
                resolution_strategy=strategy_name,
                cache_hit_url_resolution=False,
            )
            cache_manager.save("url_resolution", original_url, serialize_for_json(record))
            logger.debug(
                "URL resuelta | query=%s strategy=%s resolved=%s",
                item.query,
                strategy_name,
                resolved_url,
            )
            return record

    record = URLResolutionRecord(
        query_index=item.query_index,
        query=item.query,
        medio=item.medio,
        termino=item.termino,
        article_title=item.article_title,
        article_url_original=original_url,
        article_url_resolved="",
        status="failed",
        resolution_strategy="unresolved",
        cache_hit_url_resolution=False,
        error_type="url_resolution_failed",
        error_detail="No se pudo resolver la URL final del artículo.",
    )
    cache_manager.save("url_resolution", original_url, serialize_for_json(record))
    return record


def detectar_html_bloqueado(html: str) -> str:
    if not html:
        return "html_vacio"
    sample = html[:5000].lower()
    patterns = {
        "cloudflare_challenge": (
            "just a moment",
            "cf-browser-verification",
            "challenge-platform",
            "attention required",
        ),
        "access_denied": (
            "access denied",
            "forbidden",
            "request blocked",
        ),
    }
    for label, tokens in patterns.items():
        if any(token in sample for token in tokens):
            return label
    return ""


def extract_basic_text_from_html(html: str) -> str:
    if not html:
        return ""
    candidates: list[str] = []
    patterns = [
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        r'"articleBody"\s*:\s*"(.+?)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        text = unescape(match.group(1))
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) >= 120:
            candidates.append(text)
    return max(candidates, key=len, default="")


def extract_text_from_html(html: str) -> str:
    if trafilatura is None:
        return extract_basic_text_from_html(html)
    text = trafilatura.extract(html, include_comments=False) or ""
    if text:
        return text
    return extract_basic_text_from_html(html)


def source_domain_from_url(url: str) -> str:
    if not url:
        return ""
    return urlparse(url).netloc.lower()


def domain_requires_playwright(url: str) -> bool:
    domain = source_domain_from_url(url)
    return any(priority_domain in domain for priority_domain in DEFAULT_DOMINIOS_PLAYWRIGHT_PRIORITARIO)


def build_cloudscraper_session():
    if cloudscraper is None:
        return None
    try:
        return cloudscraper.create_scraper(browser={"browser": "firefox", "platform": "linux"})
    except Exception:
        return None


def download_with_trafilatura(url: str) -> tuple[str, str]:
    if trafilatura is None:
        return "", "trafilatura_no_disponible"
    try:
        html = trafilatura.fetch_url(url)
    except Exception as exc:
        return "", f"trafilatura_fetch_error:{type(exc).__name__}"
    if not html:
        return "", "trafilatura_fetch_vacio"
    block_reason = detectar_html_bloqueado(html)
    if block_reason:
        return "", f"trafilatura_bloqueado:{block_reason}"
    text = extract_text_from_html(html)
    if text:
        return text, ""
    return "", "trafilatura_sin_texto"


def download_with_cloudscraper(url: str, scraper) -> tuple[str, str]:
    if scraper is None:
        return "", "cloudscraper_no_disponible"
    try:
        response = scraper.get(url, timeout=20, headers={"User-Agent": random.choice(USER_AGENTS)})
    except Exception as exc:
        return "", f"cloudscraper_error:{type(exc).__name__}"
    if response.status_code != 200 or len(response.text) < 500:
        return "", f"cloudscraper_http_{response.status_code}"
    block_reason = detectar_html_bloqueado(response.text)
    if block_reason:
        return "", f"cloudscraper_bloqueado:{block_reason}"
    text = extract_text_from_html(response.text)
    if text:
        return text, ""
    return "", "cloudscraper_sin_texto"


def download_with_requests(url: str) -> tuple[str, str]:
    try:
        response = requests.get(url, timeout=20, headers=random_headers())
    except Exception as exc:
        return "", f"requests_error:{type(exc).__name__}"
    if response.status_code != 200 or len(response.text) < 500:
        return "", f"requests_http_{response.status_code}"
    block_reason = detectar_html_bloqueado(response.text)
    if block_reason:
        return "", f"requests_bloqueado:{block_reason}"
    text = extract_text_from_html(response.text)
    if text:
        return text, ""
    return "", "requests_sin_texto"


def download_article(
    resolution_record: URLResolutionRecord,
    *,
    cache_manager: CacheManager,
    config: ResolvedConfig,
    logger: logging.Logger,
    playwright_manager: PlaywrightManager,
    scraper,
) -> ArticleDownloadRecord:
    resolved_url = resolution_record.article_url_resolved
    if not resolved_url:
        return ArticleDownloadRecord(
            query_index=resolution_record.query_index,
            query=resolution_record.query,
            medio=resolution_record.medio,
            termino=resolution_record.termino,
            article_title=resolution_record.article_title,
            article_url_resolved=resolved_url,
            source_domain="",
            retrieved_at=now_utc_text(),
            article_text="",
            article_text_length=0,
            extraction_method="none",
            status_descarga="download_failed",
            cache_hit_article=False,
            playwright_used=False,
            fallback_used=False,
            error_type=resolution_record.error_type or "missing_resolved_url",
            error_detail=resolution_record.error_detail or "No se pudo resolver la URL del artículo.",
        )

    cached = cache_manager.load("article", resolved_url)
    if cached is not None:
        return ArticleDownloadRecord(**cached, cache_hit_article=True)

    attempted_methods: list[str] = []
    method_success = ""
    text = ""
    error_detail = ""
    fallback_used = False
    playwright_used = False

    method_order = [
        ("trafilatura", download_with_trafilatura),
        ("cloudscraper", lambda url: download_with_cloudscraper(url, scraper)),
        ("requests", download_with_requests),
    ]

    for method_name, downloader in method_order:
        attempted_methods.append(method_name)
        text, error_detail = downloader(resolved_url)
        if text:
            method_success = method_name
            fallback_used = len(attempted_methods) > 1
            break

    if not text and config.use_playwright:
        attempted_methods.append("playwright")
        try:
            if domain_requires_playwright(resolved_url) or not method_success:
                text, _ = playwright_manager.fetch_text(resolved_url)
                if text:
                    method_success = "playwright"
                    fallback_used = True
                    playwright_used = True
                else:
                    error_detail = f"playwright_sin_texto|previo:{error_detail}"
                time.sleep(DEFAULT_PLAYWRIGHT_PAUSA_ENTRE_PAGINAS)
        except Exception as exc:
            error_detail = f"playwright_error:{type(exc).__name__}|previo:{error_detail}"

    status_descarga = "downloaded_ok" if text else "download_failed"
    if not text and attempted_methods:
        status_descarga = "download_failed"

    record = ArticleDownloadRecord(
        query_index=resolution_record.query_index,
        query=resolution_record.query,
        medio=resolution_record.medio,
        termino=resolution_record.termino,
        article_title=resolution_record.article_title,
        article_url_resolved=resolved_url,
        source_domain=source_domain_from_url(resolved_url),
        retrieved_at=now_utc_text(),
        article_text=text or "",
        article_text_length=len(text or ""),
        extraction_method=method_success or "none",
        status_descarga=status_descarga if text else "download_failed",
        cache_hit_article=False,
        playwright_used=playwright_used,
        fallback_used=fallback_used,
        attempted_methods=attempted_methods,
        error_type="" if text else "article_download_failed",
        error_detail="" if text else error_detail or "No se pudo extraer texto del artículo.",
    )
    cache_manager.save("article", resolved_url, serialize_for_json(record))
    return record


def build_article_row(
    config: ResolvedConfig,
    rss_item: RSSItemRecord,
    resolution: URLResolutionRecord,
    article: ArticleDownloadRecord,
) -> dict[str, Any]:
    return {
        "run_id": config.run_id,
        "week_name": config.week_partition.week_name,
        "source_platform": SOURCE_PLATFORM,
        "medio": rss_item.medio,
        "termino": rss_item.termino,
        "query": rss_item.query,
        "query_index": rss_item.query_index,
        "article_title": rss_item.article_title,
        "article_url_original": rss_item.article_url_original,
        "article_url_resolved": resolution.article_url_resolved,
        "source_domain": article.source_domain,
        "published_at": rss_item.published_at or rss_item.published_at_raw,
        "retrieved_at": article.retrieved_at,
        "article_text": article.article_text,
        "article_text_length": article.article_text_length,
        "extraction_method": article.extraction_method,
        "rss_source": rss_item.rss_source,
        "status_descarga": article.status_descarga,
        "error_type": article.error_type,
        "error_detail": article.error_detail,
        "resolution_strategy": resolution.resolution_strategy,
        "cache_hit_rss": rss_item.cache_hit_rss,
        "cache_hit_url_resolution": resolution.cache_hit_url_resolution,
        "cache_hit_article": article.cache_hit_article,
        "playwright_used": article.playwright_used,
        "fallback_used": article.fallback_used,
        "attempted_methods": ",".join(article.attempted_methods),
    }


def extract_query_batch(
    query_spec: QuerySpec,
    config: ResolvedConfig,
    *,
    cache_manager: CacheManager,
    logger: logging.Logger,
    playwright_manager: PlaywrightManager,
    scraper,
    remaining_articles_budget: int | None,
) -> QueryExecutionResult:
    started = time.perf_counter()
    errors: list[ErrorRecord] = []
    rss_items, rss_errors = fetch_rss_items(query_spec, config, cache_manager=cache_manager, logger=logger)
    errors.extend(rss_errors)
    if rss_errors and not rss_items:
        return QueryExecutionResult(
            query_spec=query_spec,
            status="failed",
            duration_seconds=round(time.perf_counter() - started, 3),
            errors=errors,
        )

    if remaining_articles_budget is not None:
        rss_items = rss_items[:remaining_articles_budget]

    url_resolutions: list[URLResolutionRecord] = []
    article_downloads: list[ArticleDownloadRecord] = []
    article_rows: list[dict[str, Any]] = []

    for item in rss_items:
        resolution = resolve_article_url(item, cache_manager=cache_manager, logger=logger)
        url_resolutions.append(resolution)
        if resolution.status != "success":
            errors.append(
                ErrorRecord(
                    stage="resolve_article_url",
                    scope="article",
                    message=resolution.error_detail,
                    timestamp=now_utc_text(),
                    query_index=item.query_index,
                    query=item.query,
                    article_url=item.article_url_original,
                    fatal=False,
                    error_type=resolution.error_type or "url_resolution_failed",
                )
            )

        article = download_article(
            resolution,
            cache_manager=cache_manager,
            config=config,
            logger=logger,
            playwright_manager=playwright_manager,
            scraper=scraper,
        )
        article_downloads.append(article)
        if article.status_descarga != "downloaded_ok":
            errors.append(
                ErrorRecord(
                    stage="download_article",
                    scope="article",
                    message=article.error_detail,
                    timestamp=now_utc_text(),
                    query_index=item.query_index,
                    query=item.query,
                    article_url=resolution.article_url_resolved or item.article_url_original,
                    fatal=False,
                    error_type=article.error_type or "article_download_failed",
                )
            )
        article_rows.append(build_article_row(config, item, resolution, article))
        time.sleep(config.pausa)

    status = "success"
    if errors and article_rows:
        status = "partial_success"
    if errors and not article_rows:
        status = "failed"

    return QueryExecutionResult(
        query_spec=query_spec,
        status=status,
        duration_seconds=round(time.perf_counter() - started, 3),
        rss_items=rss_items,
        url_resolutions=url_resolutions,
        article_downloads=article_downloads,
        article_rows=article_rows,
        errors=errors,
    )


def build_articles_dataframe(query_results: Sequence[QueryExecutionResult]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for result in query_results:
        rows.extend(result.article_rows)
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return pd.DataFrame(columns=ARTICLE_COLUMNS)
    for column in ARTICLE_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""
    return dataframe[ARTICLE_COLUMNS]


def build_rss_dataframe(query_results: Sequence[QueryExecutionResult]) -> pd.DataFrame:
    rows = [asdict(item) for result in query_results for item in result.rss_items]
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return pd.DataFrame(columns=RSS_COLUMNS)
    for column in RSS_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""
    return dataframe[RSS_COLUMNS]


def build_url_resolution_dataframe(query_results: Sequence[QueryExecutionResult]) -> pd.DataFrame:
    rows = [asdict(item) for result in query_results for item in result.url_resolutions]
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return pd.DataFrame(columns=URL_RESOLUTION_COLUMNS)
    for column in URL_RESOLUTION_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""
    return dataframe[URL_RESOLUTION_COLUMNS]


def build_download_summary_dataframe(query_results: Sequence[QueryExecutionResult]) -> pd.DataFrame:
    rows = []
    for result in query_results:
        for item in result.article_downloads:
            row = asdict(item)
            row["attempted_methods"] = ",".join(item.attempted_methods)
            rows.append(row)
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return pd.DataFrame(columns=DOWNLOAD_SUMMARY_COLUMNS)
    rename_map = {
        "query_index": "query_index",
        "query": "query",
        "medio": "medio",
        "termino": "termino",
        "article_title": "article_title",
        "article_url_resolved": "article_url_resolved",
        "source_domain": "source_domain",
        "status_descarga": "status_descarga",
        "extraction_method": "extraction_method",
        "article_text_length": "article_text_length",
        "cache_hit_article": "cache_hit_article",
        "playwright_used": "playwright_used",
        "fallback_used": "fallback_used",
        "attempted_methods": "attempted_methods",
        "error_type": "error_type",
        "error_detail": "error_detail",
    }
    dataframe = dataframe.rename(columns=rename_map)
    for column in DOWNLOAD_SUMMARY_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""
    return dataframe[DOWNLOAD_SUMMARY_COLUMNS]


def build_queries_summary_dataframe(query_results: Sequence[QueryExecutionResult]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for result in query_results:
        rows.append(
            {
                "query_index": result.query_spec.query_index,
                "query": result.query_spec.query,
                "medio": result.query_spec.medio,
                "termino": result.query_spec.termino,
                "status": result.status,
                "rss_items_detected": len(result.rss_items),
                "urls_resolved_ok": sum(1 for item in result.url_resolutions if item.status == "success"),
                "articles_attempted": len(result.article_downloads),
                "articles_downloaded_ok": sum(1 for item in result.article_downloads if item.status_descarga == "downloaded_ok"),
                "articles_downloaded_empty": 0,
                "articles_failed": sum(1 for item in result.article_downloads if item.status_descarga != "downloaded_ok"),
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


def flatten_errors(query_results: Sequence[QueryExecutionResult]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for result in query_results:
        errors.extend(serialize_for_json(error) for error in result.errors)
    return errors


def determine_run_status(query_results: Sequence[QueryExecutionResult], *, dry_run: bool, skipped: bool) -> str:
    if dry_run or skipped:
        return "success"
    if not query_results:
        return "failed"
    statuses = [result.status for result in query_results]
    if all(status == "failed" for status in statuses):
        return "failed"
    if any(status in {"failed", "partial_success"} for status in statuses):
        return "partial_success"
    return "success"


def build_notes(config: ResolvedConfig, *, skipped: bool, status: str, playwright_used: bool) -> list[str]:
    notes = [
        "Extractor puro de medios: RSS Google News, resolución de URLs y descarga de artículos.",
        "No realiza clasificación, NLP, consolidación multi-fuente ni modelado.",
        "El texto persistido es material fuente o semi-estructurado para preprocessing posterior.",
        "La disponibilidad final depende del feed RSS, la resolubilidad de Google News y la accesibilidad de los sitios.",
    ]
    if config.week_name_mode == WEEK_MODE_CANONICAL:
        notes.append(
            "El nombre semanal se alinea a lunes-domingo, pero la búsqueda usa exactamente since y before."
        )
    else:
        notes.append(
            "El nombre semanal usa exactamente since y before, sin alineación automática a lunes-domingo."
        )
    if config.use_playwright:
        notes.append(
            "Playwright quedó habilitado como fallback controlado; su uso real se registra por artículo y en metadata."
        )
    else:
        notes.append("Playwright quedó deshabilitado; solo se usaron estrategias HTTP directas.")
    if playwright_used:
        notes.append("Se utilizó Playwright al menos una vez durante la corrida.")
    if skipped:
        notes.append("La semana se registró como omitida por existencia previa de artefactos.")
    if config.dry_run:
        notes.append("Dry run: no se consultó RSS ni se descargaron artículos.")
    if status == "partial_success":
        notes.append("La corrida terminó con errores recuperables; revisar errores_detectados.json.")
    return notes


def map_status_to_exit_code(status: str) -> int:
    if status == "success":
        return int(ExitCode.SUCCESS)
    if status == "partial_success":
        return int(ExitCode.PARTIAL_SUCCESS)
    return int(ExitCode.FAILED_SOURCE)


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
    cache_manager: CacheManager,
    playwright_manager: PlaywrightManager,
    skipped_existing_outputs: bool,
) -> dict[str, Any]:
    rss_items_detected = sum(len(result.rss_items) for result in query_results)
    urls_resolved_ok = sum(
        1 for result in query_results for item in result.url_resolutions if item.status == "success"
    )
    articles_attempted = sum(len(result.article_downloads) for result in query_results)
    articles_downloaded_ok = sum(
        1 for result in query_results for item in result.article_downloads if item.status_descarga == "downloaded_ok"
    )
    articles_failed = articles_attempted - articles_downloaded_ok
    queries_failed = sum(1 for result in query_results if result.status == "failed")
    return {
        "run_id": config.run_id,
        "status": status,
        "since": config.since.isoformat(),
        "before": config.before.isoformat(),
        "week_name": config.week_partition.week_name,
        "output_dir": str(output_dir),
        "total_queries": len(config.queries),
        "queries_processed": len(query_results),
        "queries_failed": queries_failed,
        "total_rss_items_detected": rss_items_detected,
        "total_urls_resolved": urls_resolved_ok,
        "total_articles_attempted": articles_attempted,
        "total_articles_downloaded_ok": articles_downloaded_ok,
        "total_articles_downloaded_empty": 0,
        "total_articles_failed": articles_failed,
        "playwright_used": playwright_manager.used,
        "playwright_enabled": config.use_playwright,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
        "week_name_mode": config.week_name_mode,
        "script_name": config.script_name,
        "script_version": config.script_version,
        "notes": list(notes),
        "cache": serialize_for_json(cache_manager.stats),
        "skipped_existing_outputs": skipped_existing_outputs,
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
    cache_manager: CacheManager,
    playwright_manager: PlaywrightManager,
    dependencies: dict[str, bool],
    skipped_existing_outputs: bool,
) -> dict[str, Any]:
    return {
        "script_name": config.script_name,
        "script_path": str(config.script_path),
        "helper_module_path": str(config.helper_module_path),
        "entrypoint_alias": config.entrypoint_alias,
        "script_version": config.script_version,
        "run_id": config.run_id,
        "run_timestamp": config.run_timestamp,
        "week_name": config.week_partition.week_name,
        "week_name_mode": config.week_name_mode,
        "search_window": {
            "since": config.since.isoformat(),
            "before": config.before.isoformat(),
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
            "exit_code": map_status_to_exit_code(status),
            "dry_run": config.dry_run,
            "skipped_existing_outputs": skipped_existing_outputs,
        },
        "config": serialize_for_json(config),
        "counts": {
            "queries": len(config.queries),
            "queries_failed": sum(1 for result in query_results if result.status == "failed"),
            "rss_items_detected": sum(len(result.rss_items) for result in query_results),
            "urls_resolved_ok": sum(
                1 for result in query_results for item in result.url_resolutions if item.status == "success"
            ),
            "articles_attempted": sum(len(result.article_downloads) for result in query_results),
            "articles_downloaded_ok": sum(
                1 for result in query_results for item in result.article_downloads if item.status_descarga == "downloaded_ok"
            ),
            "articles_failed": sum(
                1 for result in query_results for item in result.article_downloads if item.status_descarga != "downloaded_ok"
            ),
        },
        "artifact_paths": artifact_paths,
        "errors": list(errors),
        "notes": list(notes),
        "cache": serialize_for_json(cache_manager.stats),
        "playwright": {
            "enabled": config.use_playwright,
            "initialized": playwright_manager.started,
            "used": playwright_manager.used,
            "priority_domains": list(DEFAULT_DOMINIOS_PLAYWRIGHT_PRIORITARIO),
        },
        "dependencies": dependencies,
        "extraction_strategy": {
            "rss_source": "google_news_rss",
            "url_resolution_methods": ["base64_direct", "google_batchexecute", "gnewsdecoder", "http_redirect"],
            "article_download_methods": ["trafilatura", "cloudscraper", "requests", "playwright"],
        },
    }


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


def publish_canonical_artifacts(
    config: ResolvedConfig,
    artifact_paths: dict[str, Path],
    logger: logging.Logger,
) -> dict[str, str]:
    if not config.publish_canonical:
        return {}
    targets = {
        "articles_csv": canonical_main_csv_path(config),
        "rss_raw_csv": config.week_dir / RSS_RAW_FILENAME,
        "urls_resolved_csv": config.week_dir / URLS_FILENAME,
        "download_summary_csv": config.week_dir / DOWNLOAD_SUMMARY_FILENAME,
        "queries_csv": config.week_dir / QUERIES_FILENAME,
        "summary_json": config.week_dir / SUMMARY_FILENAME,
        "metadata_json": config.week_dir / METADATA_FILENAME,
        "parametros_json": config.week_dir / PARAMS_FILENAME,
        "manifest_json": config.week_dir / MANIFEST_FILENAME,
        "errors_json": config.week_dir / ERRORS_FILENAME,
    }
    published: dict[str, str] = {}
    for key, source_path in artifact_paths.items():
        target_path = targets.get(key)
        if target_path is None or not source_path.exists():
            continue
        if target_path.exists() and not config.overwrite:
            raise OutputWriteError(
                f"El artefacto canónico ya existe y requiere --overwrite: {target_path}"
            )
        shutil.copy2(source_path, target_path)
        published[key] = str(target_path)
        logger.info("Artefacto canónico publicado | key=%s path=%s", key, target_path)
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
    cache_manager: CacheManager,
    playwright_manager: PlaywrightManager,
    dependencies: dict[str, bool],
    skipped_existing_outputs: bool,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, str]]:
    article_df = build_articles_dataframe(query_results)
    rss_df = build_rss_dataframe(query_results)
    urls_df = build_url_resolution_dataframe(query_results)
    download_df = build_download_summary_dataframe(query_results)
    queries_df = build_queries_summary_dataframe(query_results)
    errors = flatten_errors(query_results)

    artifact_paths: dict[str, Path] = {}
    records: list[ArtifactRecord] = []

    articles_path = config.run_dir / f"{MAIN_CSV_PREFIX}_{config.week_partition.week_name}.csv"
    dataframe_to_csv(articles_path, article_df)
    artifact_paths["articles_csv"] = articles_path
    add_artifact_record(records, articles_path, "dataset", "Artículos extraídos de medios.")

    rss_path = config.run_dir / RSS_RAW_FILENAME
    dataframe_to_csv(rss_path, rss_df)
    artifact_paths["rss_raw_csv"] = rss_path
    add_artifact_record(records, rss_path, "dataset", "Items RSS materializados antes de resolución.")

    urls_path = config.run_dir / URLS_FILENAME
    dataframe_to_csv(urls_path, urls_df)
    artifact_paths["urls_resolved_csv"] = urls_path
    add_artifact_record(records, urls_path, "dataset", "Resultado de resolución de URLs de Google News.")

    download_path = config.run_dir / DOWNLOAD_SUMMARY_FILENAME
    dataframe_to_csv(download_path, download_df)
    artifact_paths["download_summary_csv"] = download_path
    add_artifact_record(records, download_path, "summary_table", "Resumen por intento de descarga de artículos.")

    queries_path = config.run_dir / QUERIES_FILENAME
    dataframe_to_csv(queries_path, queries_df)
    artifact_paths["queries_csv"] = queries_path
    add_artifact_record(records, queries_path, "summary_table", "Resumen operativo por query.")

    summary = build_summary(
        config,
        query_results,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        output_dir=config.run_dir,
        notes=notes,
        cache_manager=cache_manager,
        playwright_manager=playwright_manager,
        skipped_existing_outputs=skipped_existing_outputs,
    )
    summary_path = config.run_dir / SUMMARY_FILENAME
    write_json_file(summary_path, summary)
    artifact_paths["summary_json"] = summary_path
    add_artifact_record(records, summary_path, "summary", "Resumen global de la corrida.")

    params_payload = {
        "run_id": config.run_id,
        "script_name": config.script_name,
        "script_version": config.script_version,
        "entrypoint_alias": config.entrypoint_alias,
        "since": config.since.isoformat(),
        "before": config.before.isoformat(),
        "week_name": config.week_partition.week_name,
        "week_name_mode": config.week_name_mode,
        "medio": config.medios,
        "termino": config.terminos,
        "modo_queries": config.modo_queries,
        "queries": serialize_for_json(config.queries),
        "queries_source": config.queries_source,
        "output_root_dir": str(config.output_root_dir),
        "week_dir": str(config.week_dir),
        "run_dir": str(config.run_dir),
        "cache_dir": str(config.cache_dir),
        "cache_enabled": not config.ignore_cache,
        "use_playwright": config.use_playwright,
        "max_results_per_query": config.max_results_per_query,
        "max_articles_per_week": config.max_articles_per_week,
        "publish_canonical": config.publish_canonical,
        "overwrite": config.overwrite,
        "omitir_semanas_existentes": config.omitir_semanas_existentes,
        "dry_run": config.dry_run,
    }
    params_path = config.run_dir / PARAMS_FILENAME
    write_json_file(params_path, params_payload)
    artifact_paths["parametros_json"] = params_path
    add_artifact_record(records, params_path, "parameters", "Parámetros efectivos de la corrida.")

    metadata_path = config.run_dir / METADATA_FILENAME
    manifest_path = config.run_dir / MANIFEST_FILENAME
    artifact_paths["metadata_json"] = metadata_path
    artifact_paths["manifest_json"] = manifest_path

    log_path = config.run_dir / LOG_FILENAME
    if log_path.exists():
        artifact_paths["run_log"] = log_path
        add_artifact_record(records, log_path, "log", "Log operativo de la corrida.")

    if errors:
        errors_path = config.run_dir / ERRORS_FILENAME
        write_json_file(errors_path, errors)
        artifact_paths["errors_json"] = errors_path
        add_artifact_record(records, errors_path, "errors", "Errores detectados durante la corrida.")

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
        cache_manager=cache_manager,
        playwright_manager=playwright_manager,
        dependencies=dependencies,
        skipped_existing_outputs=skipped_existing_outputs,
    )
    write_json_file(metadata_path, metadata)
    add_artifact_record(records, metadata_path, "metadata", "Metadata completa y trazabilidad de la corrida.")

    manifest_payload = [serialize_for_json(record) for record in records]
    write_json_file(manifest_path, manifest_payload)
    add_artifact_record(records, manifest_path, "manifest", "Inventario de artefactos de la corrida.")
    manifest_payload = [serialize_for_json(record) for record in records]
    write_json_file(manifest_path, manifest_payload)

    published_paths = publish_canonical_artifacts(config, artifact_paths, logger)
    if published_paths:
        summary["published_canonical_paths"] = published_paths
        metadata["published_canonical_paths"] = published_paths
        write_json_file(summary_path, summary)
        write_json_file(metadata_path, metadata)
        write_json_file(manifest_path, manifest_payload)

    return summary, metadata, manifest_payload, {key: str(value) for key, value in artifact_paths.items()}


def build_dry_run_result(
    config: ResolvedConfig,
    logger: logging.Logger,
    *,
    cache_manager: CacheManager,
    playwright_manager: PlaywrightManager,
    dependencies: dict[str, bool],
    skipped_existing_outputs: bool,
) -> RunExecutionResult:
    started_at = now_utc_text()
    finished_at = started_at
    duration_seconds = 0.0
    query_results = [
        QueryExecutionResult(query_spec=query_spec, status="success", duration_seconds=0.0)
        for query_spec in config.queries
    ]
    status = "success"
    notes = build_notes(
        config,
        skipped=skipped_existing_outputs,
        status=status,
        playwright_used=False,
    )
    summary, metadata, manifest, artifact_paths = persist_outputs(
        config,
        query_results,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        logger=logger,
        notes=notes,
        cache_manager=cache_manager,
        playwright_manager=playwright_manager,
        dependencies=dependencies,
        skipped_existing_outputs=skipped_existing_outputs,
    )
    return RunExecutionResult(
        status=status,
        exit_code=int(ExitCode.SUCCESS),
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
        errors=[],
    )


def run_extraction(config: ResolvedConfig, logger: logging.Logger) -> RunExecutionResult:
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
        "Parámetros efectivos | since=%s before=%s total_queries=%s max_results_per_query=%s max_articles_per_week=%s use_playwright=%s",
        config.since,
        config.before,
        len(config.queries),
        config.max_results_per_query,
        config.max_articles_per_week,
        config.use_playwright,
    )
    if trafilatura is None:
        logger.warning(
            "trafilatura no está disponible; se usará extracción HTML básica y la calidad de texto puede bajar."
        )

    if config.omitir_semanas_existentes and week_has_existing_outputs(config):
        logger.info("La semana ya tiene artefactos previos; se registrará corrida omitida.")
        cache_manager = CacheManager(config.cache_dir, enabled=not config.ignore_cache, logger=logger)
        playwright_manager = PlaywrightManager(enabled=False, logger=logger)
        dependencies = {
            "trafilatura": trafilatura is not None,
            "cloudscraper": cloudscraper is not None,
            "googlenewsdecoder": gnewsdecoder is not None,
            "playwright": sync_playwright is not None,
        }
        return build_dry_run_result(
            config,
            logger,
            cache_manager=cache_manager,
            playwright_manager=playwright_manager,
            dependencies=dependencies,
            skipped_existing_outputs=True,
        )

    cache_manager = CacheManager(config.cache_dir, enabled=not config.ignore_cache, logger=logger)
    scraper = build_cloudscraper_session()
    playwright_manager = PlaywrightManager(enabled=config.use_playwright, logger=logger)
    if config.use_playwright:
        playwright_manager.ensure_ready()

    dependencies = {
        "trafilatura": trafilatura is not None,
        "cloudscraper": cloudscraper is not None,
        "googlenewsdecoder": gnewsdecoder is not None,
        "playwright": sync_playwright is not None,
    }

    if config.dry_run:
        return build_dry_run_result(
            config,
            logger,
            cache_manager=cache_manager,
            playwright_manager=playwright_manager,
            dependencies=dependencies,
            skipped_existing_outputs=False,
        )

    started_at = now_utc_text()
    started_perf = time.perf_counter()
    query_results: list[QueryExecutionResult] = []
    remaining_budget = config.max_articles_per_week

    try:
        for index, query_spec in enumerate(config.queries, start=1):
            if remaining_budget is not None and remaining_budget <= 0:
                logger.info("Se alcanzó max_articles_per_week; no se procesarán más queries.")
                break
            logger.info(
                "Procesando query %s/%s | query=%s",
                index,
                len(config.queries),
                query_spec.query,
            )
            result = extract_query_batch(
                query_spec,
                config,
                cache_manager=cache_manager,
                logger=logger,
                playwright_manager=playwright_manager,
                scraper=scraper,
                remaining_articles_budget=remaining_budget,
            )
            query_results.append(result)
            if remaining_budget is not None:
                remaining_budget -= len(result.rss_items)
            if index < len(config.queries):
                time.sleep(config.pausa_entre_queries)
    finally:
        playwright_manager.close()

    finished_at = now_utc_text()
    duration_seconds = round(time.perf_counter() - started_perf, 3)
    status = determine_run_status(query_results, dry_run=False, skipped=False)
    notes = build_notes(
        config,
        skipped=False,
        status=status,
        playwright_used=playwright_manager.used,
    )
    summary, metadata, manifest, artifact_paths = persist_outputs(
        config,
        query_results,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        logger=logger,
        notes=notes,
        cache_manager=cache_manager,
        playwright_manager=playwright_manager,
        dependencies=dependencies,
        skipped_existing_outputs=False,
    )
    errors = flatten_errors(query_results)
    logger.info(
        "Cierre de corrida | status=%s rss_items=%s urls_resueltas=%s artículos_ok=%s run_dir=%s",
        status,
        summary["total_rss_items_detected"],
        summary["total_urls_resolved"],
        summary["total_articles_downloaded_ok"],
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
    ensure_failure_output_layout(config)
    summary = {
        "run_id": config.run_id,
        "status": status,
        "since": config.since.isoformat(),
        "before": config.before.isoformat(),
        "week_name": config.week_partition.week_name,
        "output_dir": str(config.run_dir),
        "total_queries": len(config.queries),
        "queries_processed": 0,
        "queries_failed": len(config.queries),
        "total_rss_items_detected": 0,
        "total_urls_resolved": 0,
        "total_articles_attempted": 0,
        "total_articles_downloaded_ok": 0,
        "total_articles_downloaded_empty": 0,
        "total_articles_failed": 0,
        "playwright_used": False,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": 0.0,
        "week_name_mode": config.week_name_mode,
        "script_name": config.script_name,
        "script_version": config.script_version,
        "notes": build_notes(config, skipped=False, status=status, playwright_used=False) + [message],
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
        "errors": list(errors),
        "config": serialize_for_json(config),
    }
    safe_write_json_file(config.run_dir / SUMMARY_FILENAME, summary, logger)
    safe_write_json_file(config.run_dir / METADATA_FILENAME, metadata, logger)
    safe_write_json_file(config.run_dir / PARAMS_FILENAME, serialize_for_json(config), logger)
    if errors:
        safe_write_json_file(config.run_dir / ERRORS_FILENAME, list(errors), logger)


def main(
    argv: Sequence[str] | None = None,
    *,
    script_name: str = "media_extractor.py",
    script_path: Path | None = None,
    entrypoint_alias: str = "canonical_entrypoint",
) -> int:
    args = parse_args(argv)
    bootstrap_logger = setup_logging((args.log_level or DEFAULT_LOG_LEVEL).upper())
    started_at = now_utc_text()
    script_path = script_path or Path(__file__).resolve().with_name(script_name)
    config: ResolvedConfig | None = None

    try:
        config = resolve_config(
            args,
            script_name=script_name,
            script_path=script_path,
            entrypoint_alias=entrypoint_alias,
        )
        result = run_extraction(config, bootstrap_logger)
        return int(result.exit_code)
    except ConfigurationError as exc:
        bootstrap_logger.error("Error de configuración: %s", exc)
        if config is not None:
            write_failure_artifacts(
                config=config,
                logger=bootstrap_logger,
                status="failed",
                exit_code=int(ExitCode.FAILED_CONFIG),
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
                            error_type="configuration_error",
                        )
                    )
                ],
            )
        return int(ExitCode.FAILED_CONFIG)
    except OutputWriteError as exc:
        bootstrap_logger.error("Error de persistencia: %s", exc)
        if config is not None:
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
                            error_type="output_write_error",
                        )
                    )
                ],
            )
        return int(ExitCode.FAILED_WRITE)
    except Exception as exc:  # pragma: no cover - catch defensivo de CLI
        bootstrap_logger.exception("Fallo no controlado del extractor de medios: %s", exc)
        if config is not None:
            write_failure_artifacts(
                config=config,
                logger=bootstrap_logger,
                status="failed",
                exit_code=int(ExitCode.FAILED_SOURCE),
                started_at=started_at,
                finished_at=now_utc_text(),
                message=str(exc),
                errors=[
                    serialize_for_json(
                        ErrorRecord(
                            stage="runtime",
                            scope="run",
                            message=str(exc),
                            timestamp=now_utc_text(),
                            fatal=True,
                            error_type="runtime_error",
                        )
                    )
                ],
            )
        return int(ExitCode.FAILED_SOURCE)
