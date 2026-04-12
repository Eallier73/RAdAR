#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
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


def _decode_csv_bytes(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Some source files contain Windows-1252 bytes but still include an UTF-8 BOM.
        # Decode as cp1252 and strip BOM marker from the header later.
        return raw.decode("cp1252", errors="replace")


def _parse_utc_time_local(value: str, tz: ZoneInfo) -> dt.datetime | None:
    value = (value or "").strip()
    if not value:
        return None

    # 1) ISO-like with timezone (e.g. 2025-04-01 01:34:56+00:00)
    # Treat naive values as UTC (the column is UTC_Time).
    try:
        iso_value = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = dt.datetime.fromisoformat(iso_value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
        return parsed.astimezone(tz)
    except ValueError:
        pass

    # 2) m/d/yy H:MM (older export format)
    for fmt in ("%m/%d/%y %H:%M", "%m/%d/%Y %H:%M", "%m/%d/%y %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
        try:
            parsed = dt.datetime.strptime(value, fmt).replace(tzinfo=ZoneInfo("UTC"))
            return parsed.astimezone(tz)
        except ValueError:
            pass
    return None


def has_twitter_file(week_dir: Path) -> bool:
    for f in week_dir.iterdir():
        if f.is_file() and f.name.lower().startswith("twitter_"):
            return True
    return False


def output_path_for_week(week_dir: Path) -> Path:
    semana_part = week_dir.name.split("_", 1)[1] if "_" in week_dir.name else week_dir.name
    return week_dir / f"Twitter_{semana_part}.csv"


def _clean_header_line(line: str) -> str:
    # Handle UTF-8 BOM or cp1252-decoded BOM ("ï»¿").
    if line.startswith("\ufeff"):
        line = line.lstrip("\ufeff")
    if line.startswith("ï»¿"):
        line = line[len("ï»¿") :]
    return line


def main() -> int:
    p = argparse.ArgumentParser(
        description="Divide CSV mensuales de X/Twitter en CSV semanales en data/raw/radar_weekly_flat (sin sampling)."
    )
    p.add_argument(
        "--src",
        default="/home/emilio/Documentos/Lab/tampico_env/Proyectos/IPSEL_Tampico/Ml_Monica_Villarreal/Datos/X_Twitter",
        help="Directorio con Tweets_MV_GT_*.csv",
    )
    p.add_argument(
        "--dest",
        default="/home/emilio/Documentos/RAdAR/data/raw/radar_weekly_flat",
        help="Directorio con carpetas semanales YYYY-MM-DD_semana_*",
    )
    p.add_argument(
        "--timezone",
        default="America/Mexico_City",
        help="Zona horaria para asignar filas a semana (default: America/Mexico_City)",
    )
    p.add_argument(
        "--date-column",
        default="UTC_Time",
        help="Columna de fecha/hora para dividir (default: UTC_Time)",
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

    src_files = sorted(src_dir.glob("Tweets_MV_GT_*.csv"))
    if not src_files:
        raise SystemExit(f"No encontré archivos Tweets_MV_GT_*.csv en: {str(src_dir)!r}")

    weeks_missing = [w.path for w in week_index.weeks if not has_twitter_file(w.path)]
    weeks_missing_set = {p.resolve() for p in weeks_missing}
    print(f"Semanas sin archivo Twitter_*: {len(weeks_missing)}")

    by_week: dict[Path, list[tuple[dt.datetime, dict[str, str]]]] = defaultdict(list)
    fieldnames: list[str] | None = None

    stats = Counter()
    for csv_path in src_files:
        raw = csv_path.read_bytes()
        text = _decode_csv_bytes(raw)
        sio = io.StringIO(text, newline="")

        header_line = sio.readline()
        if not header_line:
            continue
        header_line = _clean_header_line(header_line.rstrip("\n\r"))
        header_fields = next(csv.reader([header_line], delimiter=","))
        if fieldnames is None:
            fieldnames = list(header_fields)

        reader = csv.DictReader(sio, fieldnames=header_fields, delimiter=",")
        for row in reader:
            stats["rows_total"] += 1
            local_dt = _parse_utc_time_local(row.get(args.date_column, ""), tz)
            if not local_dt:
                stats["rows_bad_date"] += 1
                continue
            week_dir = week_index.resolve(local_dt.date())
            if not week_dir:
                stats["rows_outside_weeks"] += 1
                continue
            if week_dir.resolve() not in weeks_missing_set:
                stats["rows_week_already_has_twitter"] += 1
                continue
            by_week[week_dir].append((local_dt, row))
            stats["rows_assigned"] += 1

    if fieldnames is None:
        raise SystemExit("No pude leer encabezados de los CSV fuente.")

    created = 0
    skipped_no_data = 0
    skipped_output_exists = 0

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = dest_root / f"fill_twitter_weekly_from_monthly_{ts}.csv"
    with log_path.open("w", newline="", encoding="utf-8") as log_fp:
        log_w = csv.writer(log_fp)
        log_w.writerow(["week_folder", "output_path", "rows_total", "rows_written", "action"])

        for week_dir in weeks_missing:
            out_path = output_path_for_week(week_dir)
            if out_path.exists():
                skipped_output_exists += 1
                log_w.writerow([week_dir.name, str(out_path), "", "", "skip_output_exists"])
                continue

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
    print(f"Filas en semanas que ya tenían Twitter: {stats['rows_week_already_has_twitter']}")
    print(f"Semanas sin filas en fuente: {skipped_no_data}")
    print(f"Saltados (output ya existía): {skipped_output_exists}")
    print(f"Log: {str(log_path)}")
    if args.apply:
        print(f"Archivos creados: {created}")
    else:
        print("Dry-run: no se escribieron archivos. Usa --apply para escribir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
