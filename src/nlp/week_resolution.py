from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


LEGACY_TEXT_RE = re.compile(r"^(?P<anio>\d{2})_(?P<semana>\d{2})_(?P<fuente>[a-z]+)\.txt$")
CANONICAL_TEXT_RE = re.compile(r"^(?P<start>\d{4}-\d{2}-\d{2})_(?P<fuente>[a-z]+)\.txt$")
ISO_WEEK_RE = re.compile(r"^(?P<anio>\d{4})-W(?P<semana>\d{2})$")
LEGACY_WEEK_RE = re.compile(r"^(?P<anio>\d{2})_(?P<semana>\d{2})$")
KNOWN_SOURCES = ("facebook", "twitter", "youtube", "medios")


@dataclass(frozen=True)
class WeekFileResolution:
    path: Path
    source: str
    start_date: date
    iso_year: int
    iso_week: int
    priority: int

    @property
    def period_key(self) -> tuple[int, int]:
        return (self.iso_year, self.iso_week)

    @property
    def week_start_label(self) -> str:
        return self.start_date.isoformat()

    @property
    def semana_iso(self) -> str:
        return f"{self.iso_year}-W{self.iso_week:02d}"

    @property
    def iso_yearweek_num(self) -> int:
        return self.iso_year * 100 + self.iso_week


def normalize_to_iso_week_start(anchor: date) -> date:
    return anchor - timedelta(days=anchor.weekday())


def _strip_source_suffix(token: str) -> str:
    lowered = token.lower()
    for source in KNOWN_SOURCES:
        suffix = f"_{source}"
        if lowered.endswith(suffix):
            return token[: -len(suffix)]
    return token


def parse_week_token(value: str) -> date:
    token = _strip_source_suffix(Path(str(value).strip()).stem)

    match = LEGACY_WEEK_RE.match(token)
    if match:
        iso_year = 2000 + int(match.group("anio"))
        iso_week = int(match.group("semana"))
        return date.fromisocalendar(iso_year, iso_week, 1)

    match = ISO_WEEK_RE.match(token)
    if match:
        iso_year = int(match.group("anio"))
        iso_week = int(match.group("semana"))
        return date.fromisocalendar(iso_year, iso_week, 1)

    try:
        return normalize_to_iso_week_start(date.fromisoformat(token))
    except ValueError as exc:
        raise ValueError(f"No se pudo resolver la semana desde: {value!r}") from exc


def resolve_text_week_file(path: Path, expected_source: str | None = None) -> WeekFileResolution:
    match = LEGACY_TEXT_RE.match(path.name)
    if match:
        source = match.group("fuente")
        if expected_source and source != expected_source:
            raise ValueError(f"Se esperaba fuente {expected_source!r} pero se obtuvo {source!r} en {path.name}")
        iso_year = 2000 + int(match.group("anio"))
        iso_week = int(match.group("semana"))
        start_date = date.fromisocalendar(iso_year, iso_week, 1)
        return WeekFileResolution(
            path=path,
            source=source,
            start_date=start_date,
            iso_year=iso_year,
            iso_week=iso_week,
            priority=1,
        )

    match = CANONICAL_TEXT_RE.match(path.name)
    if not match:
        raise ValueError(f"Nombre de archivo no reconocido: {path.name}")

    source = match.group("fuente")
    if expected_source and source != expected_source:
        raise ValueError(f"Se esperaba fuente {expected_source!r} pero se obtuvo {source!r} en {path.name}")
    start_date = normalize_to_iso_week_start(date.fromisoformat(match.group("start")))
    iso_year, iso_week, _ = start_date.isocalendar()
    return WeekFileResolution(
        path=path,
        source=source,
        start_date=start_date,
        iso_year=iso_year,
        iso_week=iso_week,
        priority=2,
    )


def index_preferred_week_files(
    directory: Path,
    expected_source: str,
    *,
    through_date: date | None = None,
) -> dict[tuple[int, int], WeekFileResolution]:
    selected: dict[tuple[int, int], WeekFileResolution] = {}

    for path in sorted(directory.glob("*.txt")):
        resolved = resolve_text_week_file(path, expected_source=expected_source)
        if through_date and resolved.start_date > through_date:
            continue

        current = selected.get(resolved.period_key)
        if current is None or resolved.priority > current.priority:
            selected[resolved.period_key] = resolved
            continue
        if resolved.priority == current.priority and resolved.path != current.path:
            raise ValueError(
                f"Semana duplicada para {expected_source}: {resolved.path.name} y {current.path.name}"
            )

    return selected


def list_preferred_week_files(
    directory: Path,
    expected_source: str,
    *,
    through_date: date | None = None,
) -> list[WeekFileResolution]:
    indexed = index_preferred_week_files(directory, expected_source, through_date=through_date)
    return sorted(indexed.values(), key=lambda item: (item.start_date, item.path.name))
