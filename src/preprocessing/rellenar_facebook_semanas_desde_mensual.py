#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import random
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal

from zoneinfo import ZoneInfo


WeekStratum = Literal["post", "photo", "video"]

PHOTO_MAX_RATIO = 0.20
DEFAULT_STRATIFIED_RATIOS: dict[WeekStratum, float] = {"post": 0.4, "photo": 0.3, "video": 0.3}

WEEK_DIR_RE = re.compile(r"^(?P<start>\d{4}-\d{2}-\d{2})_semana_")


@dataclass
class PostGroup:
    object_id: str
    created_dt_local: dt.datetime | None = None
    post_row: dict[str, str] | None = None
    comments_by_path: dict[str, dict[str, str]] = field(default_factory=dict)

    def stratum(self) -> WeekStratum:
        # The monthly source files do not include permalink URLs, so we cannot reliably
        # distinguish photo vs video the same way as `clasificar_url_sampling()` in the
        # unified scraper. As a best-effort heuristic, treat posts without text as
        # "photo" (media-only); everything else as "post".
        msg = ""
        if self.post_row:
            msg = (self.post_row.get("message") or "").strip()
        return "photo" if not msg else "post"

    def rows_in_output_order(self) -> Iterable[dict[str, str]]:
        if self.post_row:
            yield self.post_row
        for row in self.comments_by_path.values():
            yield row


def _parse_created_time_local(value: str, tz: ZoneInfo) -> dt.datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    # 1) ISO 8601 with timezone (most monthly files)
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
        try:
            return dt.datetime.strptime(value, fmt).astimezone(tz)
        except ValueError:
            pass

    # 2) US-style dates without timezone (MV_Datos_Mensual_Enero_25.csv)
    for fmt in ("%m/%d/%y %H:%M", "%m/%d/%Y %H:%M", "%m/%d/%y %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
        try:
            return dt.datetime.strptime(value, fmt).replace(tzinfo=tz)
        except ValueError:
            pass

    return None


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


def _sample_hybrid(
    items: list[PostGroup], *, sample_size: int, seed: int, min_per_stratum: int = 0
) -> list[PostGroup]:
    rng = random.Random(seed)
    groups: dict[WeekStratum, list[PostGroup]] = {"post": [], "photo": [], "video": []}
    for item in items:
        groups[item.stratum()].append(item)
    for k in groups:
        rng.shuffle(groups[k])

    total = len(items)
    available = {k: len(v) for k, v in groups.items()}
    ratios = {k: (available[k] / total) if total else 0.0 for k in groups}

    surplus = max(0.0, ratios["photo"] - PHOTO_MAX_RATIO)
    ratios["photo"] = min(ratios["photo"], PHOTO_MAX_RATIO)
    ratios["post"] += surplus

    allocation: dict[WeekStratum, int] = {
        k: min(round(sample_size * ratios[k]), available[k]) for k in groups
    }
    for k in groups:
        if available[k] > 0:
            allocation[k] = max(allocation[k], min(min_per_stratum, available[k]))

    assigned = sum(allocation.values())
    while assigned > sample_size:
        candidates = [
            k for k in groups if allocation[k] > min(min_per_stratum, available[k])
        ]
        if not candidates:
            break
        k = max(candidates, key=lambda kk: allocation[kk])
        allocation[k] -= 1
        assigned -= 1
    while assigned < sample_size:
        candidates = [k for k in groups if allocation[k] < available[k]]
        if not candidates:
            break
        k = max(candidates, key=lambda kk: available[kk] - allocation[kk])
        allocation[k] += 1
        assigned += 1

    sampled: list[PostGroup] = []
    for k in ("post", "photo", "video"):
        n = allocation.get(k, 0)
        if n > 0:
            sampled.extend(groups[k][:n])
    rng.shuffle(sampled)
    return sampled


def _sample_stratified(
    items: list[PostGroup], *, sample_size: int, seed: int, min_per_stratum: int = 0
) -> list[PostGroup]:
    rng = random.Random(seed)
    groups: dict[WeekStratum, list[PostGroup]] = {"post": [], "photo": [], "video": []}
    for item in items:
        groups[item.stratum()].append(item)
    for k in groups:
        rng.shuffle(groups[k])

    available = {k: len(v) for k, v in groups.items()}
    allocation: dict[WeekStratum, int] = {
        k: min(int(sample_size * DEFAULT_STRATIFIED_RATIOS[k]), available[k]) for k in groups
    }

    min_req: dict[WeekStratum, int] = {}
    for k in groups:
        min_req[k] = min(min_per_stratum, available[k]) if available[k] > 0 else 0
        if allocation[k] < min_req[k]:
            allocation[k] = min_req[k]

    assigned = sum(allocation.values())
    while assigned > sample_size:
        candidates = [k for k in groups if allocation[k] > min_req[k]]
        if not candidates:
            break
        k = max(candidates, key=lambda kk: allocation[kk] - min_req.get(kk, 0))
        allocation[k] -= 1
        assigned -= 1
    while assigned < sample_size:
        candidates = [k for k in groups if allocation[k] < available[k]]
        if not candidates:
            break
        k = max(candidates, key=lambda kk: available[kk] - allocation[kk])
        allocation[k] += 1
        assigned += 1

    sampled: list[PostGroup] = []
    for k in ("post", "photo", "video"):
        n = allocation.get(k, 0)
        if n > 0:
            sampled.extend(groups[k][:n])
    rng.shuffle(sampled)
    return sampled


def aplicar_sampling_posts(
    posts: list[PostGroup],
    *,
    strategy: str,
    size: int,
    seed: int,
    min_per_stratum: int = 0,
) -> list[PostGroup]:
    if not posts or size <= 0 or size >= len(posts):
        return posts
    if min_per_stratum < 0:
        min_per_stratum = 0
    if strategy == "none":
        strategy = "stratified"

    # Stable order going into sampling for reproducibility.
    posts = sorted(posts, key=lambda p: p.object_id)

    if strategy == "random":
        rng = random.Random(seed)
        return rng.sample(posts, size)
    if strategy == "hybrid":
        return _sample_hybrid(posts, sample_size=size, seed=seed, min_per_stratum=min_per_stratum)
    return _sample_stratified(posts, sample_size=size, seed=seed, min_per_stratum=min_per_stratum)


def has_facebook_file(week_dir: Path) -> bool:
    for f in week_dir.iterdir():
        if f.is_file() and f.name.lower().startswith("facebook_"):
            return True
    return False


def output_path_for_week(week_dir: Path) -> Path:
    # Keep consistent naming with earlier renames: Facebook_<semana_part>.csv
    semana_part = week_dir.name.split("_", 1)[1] if "_" in week_dir.name else week_dir.name
    return week_dir / f"Facebook_{semana_part}.csv"


def load_source_groups(src_dir: Path, *, tz: ZoneInfo) -> tuple[list[str], dict[str, PostGroup]]:
    monthly_files = sorted(src_dir.glob("MV_Datos_Mensual_*.csv"))
    if not monthly_files:
        raise SystemExit(f"No encontré archivos MV_Datos_Mensual_*.csv en: {str(src_dir)!r}")

    fieldnames: list[str] | None = None
    groups: dict[str, PostGroup] = {}

    for csv_path in monthly_files:
        with csv_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
            header_line = f.readline()
            delimiter = ";" if header_line.count(";") > header_line.count(",") else ","
            f.seek(0)
            reader = csv.DictReader(f, delimiter=delimiter)
            if not reader.fieldnames:
                continue
            if fieldnames is None:
                fieldnames = list(reader.fieldnames)

            for row in reader:
                if (row.get("object_type") or "").strip() != "data":
                    continue
                object_id = (row.get("object_id") or "").strip()
                if not object_id:
                    continue

                level = (row.get("level") or "").strip()
                qtype = (row.get("query_type") or "").strip()
                is_post = level == "1" and qtype == "Facebook:/<page-id>/posts"
                is_comment = level == "2" and qtype == "Facebook:/<post-id>/comments"
                if not (is_post or is_comment):
                    continue

                group = groups.get(object_id)
                if group is None:
                    group = PostGroup(object_id=object_id)
                    groups[object_id] = group

                if is_post:
                    created_local = _parse_created_time_local(row.get("created_time") or "", tz)
                    if created_local:
                        group.created_dt_local = created_local

                    # Choose the best post row seen (prefer non-empty text).
                    if group.post_row is None:
                        group.post_row = row
                    else:
                        prev_msg = (group.post_row.get("message") or "").strip()
                        new_msg = (row.get("message") or "").strip()
                        if (not prev_msg and new_msg) or (len(new_msg) > len(prev_msg)):
                            group.post_row = row

                if is_comment:
                    path = (row.get("path") or "").strip()
                    if not path:
                        continue
                    if path not in group.comments_by_path:
                        group.comments_by_path[path] = row

    if fieldnames is None:
        raise SystemExit("No pude leer encabezados de los CSV fuente.")
    return fieldnames, groups


def write_week_csv(
    out_path: Path, *, fieldnames: list[str], sampled_posts: list[PostGroup], apply: bool
) -> tuple[int, int]:
    rows_to_write: list[dict[str, str]] = []
    for g in sampled_posts:
        if not g.post_row:
            continue
        rows_to_write.extend(list(g.rows_in_output_order()))

    if not apply:
        return len(sampled_posts), len(rows_to_write)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter=";",
            quotechar='"',
            quoting=csv.QUOTE_ALL,
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows_to_write:
            writer.writerow(row)

    return len(sampled_posts), len(rows_to_write)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Divide CSV mensuales de Facebook en CSV semanales en data/raw/radar_weekly_flat, aplicando sampling por semana."
    )
    p.add_argument(
        "--src",
        default="/home/emilio/Documentos/Lab/tampico_env/Proyectos/IPSEL_Tampico/Ml_Monica_Villarreal/Datos/Facebook_Instituional",
        help="Directorio con MV_Datos_Mensual_*.csv",
    )
    p.add_argument(
        "--dest",
        default="/home/emilio/Documentos/RAdAR/data/raw/radar_weekly_flat",
        help="Directorio con carpetas semanales YYYY-MM-DD_semana_*",
    )
    p.add_argument(
        "--timezone",
        default="America/Mexico_City",
        help="Zona horaria para asignar posts a semana (default: America/Mexico_City)",
    )
    p.add_argument(
        "--sample-strategy",
        choices=["none", "random", "stratified", "hybrid"],
        default="hybrid",
        help="Estrategia de muestreo (como en facebook_scraper_unified.py)",
    )
    p.add_argument("--sample-size", type=int, default=25, help="Tamaño de muestra por semana")
    p.add_argument("--sample-seed", type=int, default=42, help="Semilla para muestreo reproducible")
    p.add_argument(
        "--sample-min-per-stratum",
        type=int,
        default=5,
        help="Mínimo por estrato (si hay suficientes en el estrato)",
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

    fieldnames, groups = load_source_groups(src_dir, tz=tz)
    print(f"Posts únicos (object_id): {len(groups)}")

    by_week: dict[Path, list[PostGroup]] = defaultdict(list)
    unassigned = 0
    without_post_row = 0
    for g in groups.values():
        if not g.post_row:
            without_post_row += 1
            continue
        if not g.created_dt_local:
            unassigned += 1
            continue
        week_dir = week_index.resolve(g.created_dt_local.date())
        if not week_dir:
            unassigned += 1
            continue
        by_week[week_dir].append(g)

    print(f"Semanas destino detectadas: {len(week_index)}")
    print(f"Posts sin semana asignable: {unassigned}")
    print(f"object_id sin fila POST válida: {without_post_row}")

    weeks_missing_fb = [w.path for w in week_index.weeks if not has_facebook_file(w.path)]
    print(f"Semanas sin archivo Facebook_*: {len(weeks_missing_fb)}")

    created = 0
    skipped_existing = 0
    skipped_no_data = 0

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = dest_root / f"fill_facebook_weekly_from_monthly_{ts}.csv"
    with log_path.open("w", newline="", encoding="utf-8") as log_fp:
        log_w = csv.writer(log_fp)
        log_w.writerow(
            [
                "week_folder",
                "output_path",
                "posts_total",
                "posts_sampled",
                "rows_written",
                "action",
            ]
        )

        for week_dir in weeks_missing_fb:
            out_path = output_path_for_week(week_dir)
            if out_path.exists():
                skipped_existing += 1
                log_w.writerow([week_dir.name, str(out_path), "", "", "", "skip_output_exists"])
                continue

            posts = by_week.get(week_dir, [])
            if not posts:
                skipped_no_data += 1
                log_w.writerow([week_dir.name, str(out_path), 0, 0, 0, "skip_no_posts"])
                continue

            sampled = aplicar_sampling_posts(
                posts,
                strategy=args.sample_strategy,
                size=args.sample_size,
                seed=args.sample_seed,
                min_per_stratum=args.sample_min_per_stratum,
            )
            posts_sampled, rows_written = write_week_csv(
                out_path,
                fieldnames=fieldnames,
                sampled_posts=sampled,
                apply=args.apply,
            )

            action = "would_write" if not args.apply else "written"
            if args.apply:
                created += 1
            log_w.writerow(
                [
                    week_dir.name,
                    str(out_path),
                    len(posts),
                    posts_sampled,
                    rows_written,
                    action,
                ]
            )

    print(f"Log: {str(log_path)}")
    if args.apply:
        print(f"Archivos creados: {created}")
    else:
        print("Dry-run: no se escribieron archivos. Usa --apply para escribir.")
    print(f"Saltados (ya existía output): {skipped_existing}")
    print(f"Saltados (sin posts en fuente): {skipped_no_data}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
