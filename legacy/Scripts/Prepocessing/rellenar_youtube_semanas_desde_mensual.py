#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo


WEEK_DIR_RE = re.compile(r"^(?P<start>\d{4}-\d{2}-\d{2})_semana_")


@dataclass(frozen=True)
class WeekFolder:
    start: dt.date
    path: Path


class WeekIndex:
    def __init__(self, dest_root: Path) -> None:
        weeks: list[WeekFolder] = []
        for entry in sorted(dest_root.iterdir()):
            if not entry.is_dir():
                continue
            m = WEEK_DIR_RE.match(entry.name)
            if not m:
                continue
            try:
                start = dt.date.fromisoformat(m.group("start"))
            except ValueError:
                continue
            weeks.append(WeekFolder(start=start, path=entry))

        self._weeks = sorted(weeks, key=lambda w: w.start)
        self._starts = [w.start for w in self._weeks]

    def __len__(self) -> int:
        return len(self._weeks)

    @property
    def weeks(self) -> list[WeekFolder]:
        return list(self._weeks)

    def resolve(self, day: dt.date) -> Path | None:
        if not self._weeks:
            return None
        import bisect

        idx = bisect.bisect_right(self._starts, day) - 1
        if idx < 0:
            return None
        start = self._starts[idx]
        end_exclusive = (
            self._starts[idx + 1] if idx + 1 < len(self._starts) else start + dt.timedelta(days=7)
        )
        if start <= day < end_exclusive:
            return self._weeks[idx].path
        return None


def _parse_published_at_local(value: str, tz: ZoneInfo) -> dt.datetime | None:
    value = (value or "").strip()
    if not value:
        return None

    # ISO with Z (UTC)
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
    return parsed.astimezone(tz)


def has_youtube_file(week_dir: Path) -> bool:
    for f in week_dir.iterdir():
        if f.is_file() and f.name.lower().startswith("youtube_"):
            return True
    return False


def output_path_for_week(week_dir: Path) -> Path:
    semana_part = week_dir.name.split("_", 1)[1] if "_" in week_dir.name else week_dir.name
    return week_dir / f"Youtube_{semana_part}.csv"


def main() -> int:
    p = argparse.ArgumentParser(
        description="Divide CSV mensuales de YouTube en CSV semanales en Datos_RAdAR (sin sampling)."
    )
    p.add_argument(
        "--src",
        default="/home/emilio/Documentos/Lab/tampico_env/Proyectos/IPSEL_Tampico/Ml_Monica_Villarreal/Datos/Youtube",
        help="Directorio con Youtube_MV_*.csv",
    )
    p.add_argument(
        "--dest",
        default="/home/emilio/Documentos/RAdAR/Datos_RAdAR",
        help="Directorio con carpetas semanales YYYY-MM-DD_semana_*",
    )
    p.add_argument(
        "--timezone",
        default="America/Mexico_City",
        help="Zona horaria para asignar filas a semana (default: America/Mexico_City)",
    )
    p.add_argument(
        "--date-column",
        default="published_at",
        help="Columna de fecha/hora para dividir (default: published_at)",
    )
    p.add_argument("--apply", action="store_true", help="Escribe archivos (sin esto solo dry-run).")
    args = p.parse_args()

    src_dir = Path(args.src).expanduser().resolve()
    dest_root = Path(args.dest).expanduser().resolve()
    if not src_dir.exists() or not src_dir.is_dir():
        raise SystemExit(f"Ruta --src inválida: {str(src_dir)!r}")
    if not dest_root.exists() or not dest_root.is_dir():
        raise SystemExit(f"Ruta --dest inválida: {str(dest_root)!r}")

    tz = ZoneInfo(args.timezone)
    week_index = WeekIndex(dest_root)
    if len(week_index) == 0:
        raise SystemExit(f"No encontré carpetas semanales en: {str(dest_root)!r}")

    src_files = sorted(src_dir.glob("Youtube_MV_*.csv"))
    if not src_files:
        raise SystemExit(f"No encontré archivos Youtube_MV_*.csv en: {str(src_dir)!r}")

    # Accumulate rows per week for weeks that currently don't have YouTube files.
    weeks_missing = [w.path for w in week_index.weeks if not has_youtube_file(w.path)]
    weeks_missing_set = {p.resolve() for p in weeks_missing}
    print(f"Semanas sin archivo Youtube_*: {len(weeks_missing)}")

    by_week: dict[Path, list[tuple[dt.datetime, dict[str, str]]]] = defaultdict(list)
    fieldnames: list[str] | None = None

    stats = Counter()
    for csv_path in src_files:
        with csv_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
            reader = csv.DictReader(f, delimiter=",")
            if not reader.fieldnames:
                continue
            if fieldnames is None:
                fieldnames = list(reader.fieldnames)
            for row in reader:
                stats["rows_total"] += 1
                published = _parse_published_at_local(row.get(args.date_column, ""), tz)
                if not published:
                    stats["rows_bad_date"] += 1
                    continue
                week_dir = week_index.resolve(published.date())
                if not week_dir:
                    stats["rows_outside_weeks"] += 1
                    continue
                if week_dir.resolve() not in weeks_missing_set:
                    stats["rows_week_already_has_youtube"] += 1
                    continue
                by_week[week_dir].append((published, row))
                stats["rows_assigned"] += 1

    if fieldnames is None:
        raise SystemExit("No pude leer encabezados de los CSV fuente.")

    created = 0
    skipped_no_data = 0

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = dest_root / f"fill_youtube_weekly_from_monthly_{ts}.csv"
    with log_path.open("w", newline="", encoding="utf-8") as log_fp:
        log_w = csv.writer(log_fp)
        log_w.writerow(["week_folder", "output_path", "rows_total", "rows_written", "action"])

        for week_dir in weeks_missing:
            out_path = output_path_for_week(week_dir)
            rows = by_week.get(week_dir, [])
            if not rows:
                skipped_no_data += 1
                log_w.writerow([week_dir.name, str(out_path), 0, 0, "skip_no_rows"])
                continue

            rows.sort(key=lambda t: t[0])
            action = "would_write" if not args.apply else "written"
            if args.apply:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with out_path.open("w", encoding="utf-8-sig", newline="") as out_fp:
                    writer = csv.DictWriter(
                        out_fp,
                        fieldnames=fieldnames,
                        delimiter=",",
                        quotechar='"',
                        quoting=csv.QUOTE_MINIMAL,
                        extrasaction="ignore",
                    )
                    writer.writeheader()
                    for _, row in rows:
                        writer.writerow(row)
                created += 1

            log_w.writerow([week_dir.name, str(out_path), len(rows), len(rows), action])

    print(f"Leídos: {stats['rows_total']} filas")
    print(f"Asignados a semanas (faltantes): {stats['rows_assigned']}")
    print(f"Fechas inválidas: {stats['rows_bad_date']}")
    print(f"Fuera del rango de semanas: {stats['rows_outside_weeks']}")
    print(f"Filas en semanas que ya tenían Youtube: {stats['rows_week_already_has_youtube']}")
    print(f"Semanas sin filas en fuente: {skipped_no_data}")
    print(f"Log: {str(log_path)}")
    if args.apply:
        print(f"Archivos creados: {created}")
    else:
        print("Dry-run: no se escribieron archivos. Usa --apply para escribir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

