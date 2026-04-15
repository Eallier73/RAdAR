#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.preprocessing.normalizar_semanas_canonicas import build_week_folder_name


DATE_RANGE_RE = re.compile(r"_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})(?P<ext>\.[^./]+)$")
CANONICAL_MAIN_RE = re.compile(r"^facebook_institutional_raw_(?P<week>\d{4}-\d{2}-\d{2}_semana_.+)\.csv$")

MONTHS_ES = {
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

RAW_WEEKLY_ROOT = REPO_ROOT / "data" / "raw" / "radar_weekly_flat"
PREPROCESSING_LOGS_DIR = REPO_ROOT / "artifacts" / "logs" / "preprocessing"


@dataclass(frozen=True)
class MoveOp:
    src: Path
    dest_dir: Path
    dest: Path
    start: dt.date
    end: dt.date


_DM_RE = re.compile(r"^(?P<day>\d{2})(?P<month>[a-zA-ZáéíóúñÑ]+)$")
_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_")

MONTHS_NAME_TO_NUM = {v: k for k, v in MONTHS_ES.items()}
MONTHS_NAME_TO_NUM["setiembre"] = 9


def parse_date(s: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        return None


def extract_range(path: Path) -> tuple[dt.date, dt.date] | None:
    m = DATE_RANGE_RE.search(path.name)
    if not m:
        return None
    start = parse_date(m.group(1))
    end = parse_date(m.group(2))
    if not start or not end:
        return None
    return start, end


def _parse_day_month(token: str) -> tuple[int, int] | None:
    m = _DM_RE.match(token)
    if not m:
        return None
    day = int(m.group("day"))
    month_name = m.group("month").lower()
    month = MONTHS_NAME_TO_NUM.get(month_name)
    if not month:
        return None
    return day, month


def _yy_to_yyyy(yy: str) -> int:
    return 2000 + int(yy)


def _infer_start_year(*, start_m: int, start_d: int, end_m: int, end_d: int, end_year: int) -> int:
    if (start_m, start_d) <= (end_m, end_d):
        return end_year
    return end_year - 1


def parse_week_range(folder_name: str) -> tuple[dt.date, dt.date] | None:
    name = folder_name.strip()
    name = _DATE_PREFIX_RE.sub("", name, count=1)
    if not name.startswith("semana_"):
        return None
    rest = name[len("semana_") :]
    parts = rest.split("_")
    if len(parts) == 4:
        start_dm, start_yy, end_dm, end_yy = parts
        start_year = _yy_to_yyyy(start_yy)
        end_year = _yy_to_yyyy(end_yy)
    elif len(parts) == 3:
        start_dm, end_dm, end_yy = parts
        end_year = _yy_to_yyyy(end_yy)
        start_year = None
    else:
        return None

    s = _parse_day_month(start_dm)
    e = _parse_day_month(end_dm)
    if not s or not e:
        return None
    start_day, start_month = s
    end_day, end_month = e

    if start_year is None:
        start_year = _infer_start_year(
            start_m=start_month,
            start_d=start_day,
            end_m=end_month,
            end_d=end_day,
            end_year=end_year,
        )

    try:
        start = dt.date(start_year, start_month, start_day)
        end = dt.date(end_year, end_month, end_day)
    except ValueError:
        return None
    return start, end


def folder_name_for_range(start: dt.date, end: dt.date) -> str:
    _ = end
    return build_week_folder_name(start)


def build_enddate_index(dest_root: Path) -> dict[dt.date, Path]:
    idx: dict[dt.date, Path] = {}
    for entry in sorted(dest_root.iterdir()):
        if not entry.is_dir():
            continue
        rng = parse_week_range(entry.name)
        if not rng:
            continue
        _, end = rng
        idx[end] = entry
    return idx


def resolve_week_folder(dest_root: Path, *, end_index: dict[dt.date, Path], end: dt.date) -> Path:
    existing = end_index.get(end)
    if existing:
        return existing
    # Legacy compatibility: infer the canonical folder from the 7-day window
    # encoded in filenames that still ship explicit start/end dates.
    start = end - dt.timedelta(days=6)
    return dest_root / folder_name_for_range(start, end)

# Contrato vigente:
#   - facebook_institutional_raw_<semana>.csv  → salida canónica del extractor directo a Apify
# Compatibilidad legacy:
#   - posts_comentarios_*.csv                  → salida del extractor viejo
#   - urls_*.txt                              → auditoría histórica de URLs
_CSV_PREFIJOS_PROMOVER = ("facebook_institutional_raw_", "posts_comentarios_")
_TXT_PREFIJOS_PROMOVER = ("urls_",)


def _debe_promover(src: Path) -> bool:
    """True si este archivo debe promoverse a la estructura canónica."""
    name = src.name
    if src.suffix.lower() == ".csv":
        return any(name.startswith(p) for p in _CSV_PREFIJOS_PROMOVER)
    if src.suffix.lower() == ".txt":
        return any(name.startswith(p) for p in _TXT_PREFIJOS_PROMOVER)
    return False


def _is_nested_run_artifact(src_root: Path, src: Path) -> bool:
    try:
        relative = src.relative_to(src_root)
    except ValueError:
        return False
    return "runs" in relative.parts


def _resolve_canonical_week(src: Path) -> tuple[Path, dt.date, dt.date] | None:
    match = CANONICAL_MAIN_RE.match(src.name)
    if not match:
        return None
    week_name = match.group("week")
    parsed = parse_week_range(week_name)
    if not parsed:
        return None
    start, end = parsed
    return Path(week_name), start, end


def build_ops(src_root: Path, dest_root: Path, *, max_span_days: int) -> tuple[list[MoveOp], list[str]]:
    ops: list[MoveOp] = []
    warnings: list[str] = []
    end_index = build_enddate_index(dest_root)

    for src in sorted(src_root.rglob("*")):
        if not src.is_file():
            continue
        if _is_nested_run_artifact(src_root, src):
            continue
        if not _debe_promover(src):
            continue
        canonical_week = _resolve_canonical_week(src)
        if canonical_week:
            week_name, start, end = canonical_week
            dest_dir = dest_root / week_name
        else:
            rng = extract_range(src)
            if not rng:
                continue
            start, end = rng
            span = (end - start).days
            if span < 0 or span > max_span_days:
                continue
            dest_dir = resolve_week_folder(dest_root, end_index=end_index, end=end)

        canonical_name = f"{dest_dir.name}_facebook{src.suffix.lower()}"
        dest = dest_dir / canonical_name
        ops.append(MoveOp(src=src, dest_dir=dest_dir, dest=dest, start=start, end=end))

    return ops, warnings


def write_log(ops: list[MoveOp]) -> Path:
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    PREPROCESSING_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = PREPROCESSING_LOGS_DIR / f"move_facebook_log_{ts}.csv"
    with log_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["src", "dest", "week_folder", "start", "end"])
        for op in ops:
            w.writerow([str(op.src), str(op.dest), str(op.dest_dir), op.start.isoformat(), op.end.isoformat()])
    return log_path


def apply_ops(ops: list[MoveOp]) -> None:
    for op in ops:
        op.dest_dir.mkdir(parents=True, exist_ok=True)
        if op.dest.exists():
            if op.dest.is_dir():
                shutil.rmtree(op.dest)
            else:
                op.dest.unlink()
        op.dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(op.src), str(op.dest))


def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "Promueve artefactos semanales de Facebook a la estructura canónica "
            "en data/raw/radar_weekly_flat."
        )
    )
    p.add_argument(
        "--src",
        required=True,
        help="Directorio origen con artefactos semanales de extracción de Facebook.",
    )
    p.add_argument(
        "--dest",
        default=str(RAW_WEEKLY_ROOT),
        help=f"Directorio destino dentro del repo. Default: {RAW_WEEKLY_ROOT}",
    )
    p.add_argument(
        "--max-span-days",
        type=int,
        default=7,
        help="Máximo tamaño del rango (end-start) en días para considerar el archivo (default: 7).",
    )
    p.add_argument("--apply", action="store_true", help="Aplica los movimientos (sin esto solo dry-run).")
    args = p.parse_args()

    src_root = Path(args.src).expanduser().resolve()
    dest_root = Path(args.dest).expanduser().resolve()
    if not src_root.exists() or not src_root.is_dir():
        raise SystemExit(f"Ruta origen inválida: {str(src_root)!r}")
    if not dest_root.exists() or not dest_root.is_dir():
        raise SystemExit(f"Ruta destino inválida: {str(dest_root)!r}")

    ops, warnings = build_ops(src_root, dest_root, max_span_days=args.max_span_days)
    for w in warnings:
        print("WARN:", w)

    if not ops:
        print("No encontré archivos que mover.")
        return 0

    print(f"Archivos a mover: {len(ops)} (max-span-days={args.max_span_days})")
    for op in ops[:50]:
        print(f"  {op.src.name} -> {op.dest_dir.name}/")
    if len(ops) > 50:
        print(f"  ... +{len(ops) - 50} más")

    if not args.apply:
        print("\nDry-run: no se aplicaron cambios. Usa --apply para mover/sobreescribir.")
        return 0

    log_path = write_log(ops)
    apply_ops(ops)
    print(f"\nOK: movidos {len(ops)} archivos. Log: {str(log_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
