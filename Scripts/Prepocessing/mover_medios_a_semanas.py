#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


WEEK_DIR_RE = re.compile(r"^(?P<start>\d{4}-\d{2}-\d{2})_semana_")
DATE_RANGE_RE = re.compile(r"_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})(?P<ext>\.[^./]+)$")


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


def parse_date_range(name: str) -> tuple[dt.date, dt.date] | None:
    m = DATE_RANGE_RE.search(name)
    if not m:
        return None
    try:
        start = dt.date.fromisoformat(m.group(1))
        end = dt.date.fromisoformat(m.group(2))
    except ValueError:
        return None
    return start, end


def with_dup_suffix(path: Path) -> Path:
    if not path.exists():
        return path
    suffixes = "".join(path.suffixes)
    stem = path.name[: -len(suffixes)] if suffixes else path.name
    i = 1
    while True:
        candidate = path.with_name(f"{stem}_dup{i}{suffixes}")
        if not candidate.exists():
            return candidate
        i += 1


def main() -> int:
    p = argparse.ArgumentParser(
        description="Mueve archivos de Medios (con rango de fechas en nombre) a la carpeta semanal correspondiente."
    )
    p.add_argument(
        "--src",
        default="/home/emilio/Documentos/Datos_Radar/Medios",
        help="Directorio origen (default: /home/emilio/Documentos/Datos_Radar/Medios)",
    )
    p.add_argument(
        "--dest",
        default="/home/emilio/Documentos/RAdAR/Datos_RAdAR",
        help="Directorio destino con carpetas semanales (default: /home/emilio/Documentos/RAdAR/Datos_RAdAR)",
    )
    p.add_argument(
        "--skip-cache",
        action="store_true",
        default=True,
        help="Omite archivos dentro de _cache_rss (default: true).",
    )
    p.add_argument(
        "--extensions",
        nargs="+",
        default=[".txt"],
        help="Extensiones a mover (default: .txt). Ej: --extensions .txt .csv",
    )
    p.add_argument("--apply", action="store_true", help="Aplica los movimientos (sin esto solo dry-run).")
    p.add_argument(
        "--cleanup-empty-dirs",
        action="store_true",
        default=True,
        help="Borra carpetas semana_* vacías al final (default: true).",
    )
    args = p.parse_args()

    src_root = Path(args.src).expanduser().resolve()
    dest_root = Path(args.dest).expanduser().resolve()
    if not src_root.exists() or not src_root.is_dir():
        raise SystemExit(f"Ruta --src inválida: {str(src_root)!r}")
    if not dest_root.exists() or not dest_root.is_dir():
        raise SystemExit(f"Ruta --dest inválida: {str(dest_root)!r}")

    week_index = WeekIndex(dest_root)
    if len(week_index) == 0:
        raise SystemExit(f"No encontré carpetas semanales en: {str(dest_root)!r}")

    ops: list[tuple[Path, Path, dt.date, dt.date, str]] = []
    skipped: list[tuple[Path, str]] = []
    allowed_exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in args.extensions}

    for src in sorted(src_root.rglob("*")):
        if not src.is_file():
            continue
        if args.skip_cache and "_cache_rss" in src.parts:
            skipped.append((src, "skip_cache"))
            continue
        if src.suffix.lower() not in allowed_exts:
            skipped.append((src, "skip_ext"))
            continue

        rng = parse_date_range(src.name)
        if not rng:
            skipped.append((src, "skip_no_date_range"))
            continue
        start, end = rng
        dest_dir = week_index.resolve(end)
        if not dest_dir:
            skipped.append((src, "skip_no_week_folder"))
            continue

        dest = with_dup_suffix(dest_dir / src.name)
        ops.append((src, dest, start, end, dest_dir.name))

    if not ops:
        print("No encontré archivos que mover.")
        return 0

    print(f"Archivos a mover: {len(ops)}")
    for src, dest, start, end, week in ops[:20]:
        print(f"  {src.relative_to(src_root)} -> {week}/{dest.name} ({start}..{end})")
    if len(ops) > 20:
        print(f"  ... +{len(ops) - 20} más")

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = dest_root / f"move_medios_log_{ts}.csv"
    with log_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["src", "dest", "week_folder", "start", "end", "action"])
        for src, dest, start, end, week in ops:
            w.writerow([str(src), str(dest), week, start.isoformat(), end.isoformat(), "move"])
        for src, reason in skipped:
            w.writerow([str(src), "", "", "", "", reason])

    if not args.apply:
        print(f"\nDry-run: no se aplicaron cambios. Log: {str(log_path)}")
        return 0

    moved = 0
    for src, dest, _start, _end, _week in ops:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        moved += 1

    removed_dirs = 0
    if args.cleanup_empty_dirs:
        for d in sorted(src_root.iterdir()):
            if not d.is_dir() or not d.name.startswith("semana_"):
                continue
            # Remove if empty.
            if any(d.iterdir()):
                continue
            d.rmdir()
            removed_dirs += 1

    print(f"\nOK: movidos {moved} archivos. Log: {str(log_path)}")
    if args.cleanup_empty_dirs:
        print(f"Carpetas semana_* eliminadas (vacías): {removed_dirs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
