#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
from dataclasses import dataclass
from pathlib import Path


MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


_DM_RE = re.compile(r"^(?P<day>\d{2})(?P<month>[a-zA-ZáéíóúñÑ]+)$")
_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_")


@dataclass(frozen=True)
class Rename:
    old: str
    new: str
    start_date: dt.date


def _parse_day_month(token: str) -> tuple[int, int] | None:
    m = _DM_RE.match(token)
    if not m:
        return None
    day = int(m.group("day"))
    month_name = m.group("month").lower()
    month = MONTHS.get(month_name)
    if not month:
        return None
    return day, month


def _yy_to_yyyy(yy: str) -> int:
    # Dataset appears to use 2-digit years like 24/25/26.
    return 2000 + int(yy)


def _infer_year1(*, month1: int, day1: int, month2: int, day2: int, year2: int) -> int | None:
    if (month1, day1) <= (month2, day2):
        return year2
    # Cross-year week like 30diciembre_05enero_26 -> start is 2025.
    if month1 == 12 and month2 == 1:
        return year2 - 1
    # If months go backwards, also assume it wrapped the year.
    if month1 > month2:
        return year2 - 1
    return None


def parse_start_date(folder_name: str) -> dt.date | None:
    name = folder_name.strip()
    if not name.startswith("semana_"):
        return None
    rest = name[len("semana_") :]
    parts = rest.split("_")
    if len(parts) == 4:
        a, yy1, b, yy2 = parts
        year1 = _yy_to_yyyy(yy1)
        year2 = _yy_to_yyyy(yy2)
    elif len(parts) == 3:
        a, b, yy2 = parts
        year2 = _yy_to_yyyy(yy2)
        year1 = None
    else:
        return None

    dm1 = _parse_day_month(a)
    dm2 = _parse_day_month(b)
    if not dm1 or not dm2:
        return None
    day1, month1 = dm1
    day2, month2 = dm2

    if year1 is None:
        year1 = _infer_year1(month1=month1, day1=day1, month2=month2, day2=day2, year2=year2)
        if year1 is None:
            return None

    try:
        return dt.date(year1, month1, day1)
    except ValueError:
        return None


def build_plan(root: Path) -> tuple[list[Rename], list[str]]:
    renames: list[Rename] = []
    warnings: list[str] = []

    for entry in sorted(os.listdir(root)):
        old_path = root / entry
        if not old_path.is_dir():
            continue
        if _DATE_PREFIX_RE.match(entry):
            continue

        start_date = parse_start_date(entry)
        if not start_date:
            warnings.append(f"No pude parsear fecha inicio: {entry!r}")
            continue

        cleaned = entry.strip()
        prefix = start_date.strftime("%Y-%m-%d") + "_"
        new_name = prefix + cleaned
        if new_name == entry:
            continue
        renames.append(Rename(old=entry, new=new_name, start_date=start_date))

    # Validate collisions and pre-existing targets
    targets = [r.new for r in renames]
    dupes = {t for t in targets if targets.count(t) > 1}
    if dupes:
        raise SystemExit(f"Colisión de nombres destino (duplicados): {sorted(dupes)!r}")
    for r in renames:
        if (root / r.new).exists():
            raise SystemExit(f"Ya existe el destino: {r.new!r}")

    return renames, warnings


def write_log(root: Path, renames: list[Rename]) -> Path:
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = root / f"rename_semana_prefix_log_{ts}.csv"
    with log_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["old_name", "new_name", "start_date"])
        for r in renames:
            w.writerow([r.old, r.new, r.start_date.isoformat()])
    return log_path


def apply_renames(root: Path, renames: list[Rename]) -> None:
    # Do in chronological order (mostly for human predictability).
    for r in sorted(renames, key=lambda x: (x.start_date, x.old)):
        os.rename(root / r.old, root / r.new)


def main() -> int:
    p = argparse.ArgumentParser(description="Prefija carpetas semana_* con YYYY-MM-DD_ para orden cronológico.")
    p.add_argument(
        "path",
        nargs="?",
        default="Datos_RAdAR",
        help="Directorio donde están las carpetas semanales (default: Datos_RAdAR)",
    )
    p.add_argument("--apply", action="store_true", help="Ejecuta los renombres (sin esto solo hace dry-run).")
    args = p.parse_args()

    root = Path(args.path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Ruta inválida: {str(root)!r}")

    renames, warnings = build_plan(root)
    for w in warnings:
        print("WARN:", w)

    if not renames:
        print("No hay carpetas para renombrar.")
        return 0

    print("Propuesta de renombres:")
    for r in sorted(renames, key=lambda x: (x.start_date, x.old)):
        print(f"  {r.old!r} -> {r.new!r}")

    if not args.apply:
        print("\nDry-run: no se aplicaron cambios. Usa --apply para renombrar.")
        return 0

    log_path = write_log(root, renames)
    apply_renames(root, renames)
    print(f"\nOK: renombradas {len(renames)} carpetas. Log: {str(log_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

