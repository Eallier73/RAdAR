#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


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

EXPECTED_TYPES = ("medios", "facebook", "twitter", "youtube")
EXPECTED_EXTENSIONS = {
    "medios": ".txt",
    "facebook": ".csv",
    "twitter": ".csv",
    "youtube": ".csv",
}


@dataclass(frozen=True)
class RenameOp:
    source: Path
    target: Path
    kind: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Normaliza nombres dentro de carpetas semanales del raw semanal del Radar, "
            "crea semanas faltantes y genera un reporte de faltantes."
        )
    )
    parser.add_argument(
        "--root",
        default="/home/emilio/Documentos/RAdAR/data/raw/radar_weekly_flat",
        help="Directorio raíz con carpetas semanales.",
    )
    parser.add_argument(
        "--report",
        default="/home/emilio/Documentos/RAdAR/artifacts/logs/preprocessing/reporte_semanas_incompletas.txt",
        help="Ruta del reporte de semanas incompletas.",
    )
    parser.add_argument(
        "--create-missing-month",
        default="2026-03",
        help="Mes (YYYY-MM) sobre el cual crear semanas faltantes.",
    )
    parser.add_argument(
        "--through-date",
        default="2026-03-16",
        help="Fecha final inclusiva para crear semanas faltantes (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo reporta cambios, sin renombrar ni crear carpetas.",
    )
    return parser.parse_args()


def parse_iso_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"Fecha inválida: {value!r}") from exc


def parse_year_month(value: str) -> tuple[int, int]:
    parts = value.split("-")
    if len(parts) != 2:
        raise SystemExit(f"Mes inválido: {value!r}. Usa YYYY-MM.")
    year, month = parts
    try:
        year_i = int(year)
        month_i = int(month)
        dt.date(year_i, month_i, 1)
    except ValueError as exc:
        raise SystemExit(f"Mes inválido: {value!r}. Usa YYYY-MM.") from exc
    return year_i, month_i


def iter_week_dirs(root: Path) -> Iterable[Path]:
    for entry in sorted(root.iterdir()):
        if entry.is_dir():
            yield entry


def build_week_folder_name(start: dt.date) -> str:
    end = start + dt.timedelta(days=6)
    start_part = f"{start.day:02d}{MONTHS_ES[start.month]}"
    end_part = f"{end.day:02d}{MONTHS_ES[end.month]}"
    yy = f"{end.year % 100:02d}"
    return f"{start.isoformat()}_semana_{start_part}_{end_part}_{yy}"


def detect_kind(file_path: Path) -> str | None:
    lower_name = file_path.name.lower()
    if "facebook" in lower_name:
        return "facebook"
    if "twitter" in lower_name:
        return "twitter"
    if "youtube" in lower_name:
        return "youtube"
    if lower_name.startswith("noticias_tampico_") or "_medios" in lower_name:
        return "medios"
    return None


def expected_name(folder: Path, kind: str) -> str:
    return f"{folder.name}_{kind}{EXPECTED_EXTENSIONS[kind]}"


def collect_rename_ops(root: Path) -> tuple[list[RenameOp], list[str]]:
    ops: list[RenameOp] = []
    warnings: list[str] = []

    for folder in iter_week_dirs(root):
        seen: dict[str, Path] = {}
        unknown_files: list[Path] = []
        for file_path in sorted(p for p in folder.iterdir() if p.is_file()):
            kind = detect_kind(file_path)
            if kind is None:
                unknown_files.append(file_path)
                continue
            if kind in seen:
                warnings.append(
                    f"{folder.name}: múltiples archivos detectados para {kind}: "
                    f"{seen[kind].name} y {file_path.name}"
                )
                continue
            seen[kind] = file_path

        for file_path in unknown_files:
            warnings.append(f"{folder.name}: archivo no reconocido {file_path.name}")

        for kind, file_path in seen.items():
            target = folder / expected_name(folder, kind)
            if file_path == target:
                continue
            if target.exists() and target != file_path:
                warnings.append(
                    f"{folder.name}: no se renombró {file_path.name} porque ya existe {target.name}"
                )
                continue
            ops.append(RenameOp(source=file_path, target=target, kind=kind))

    return ops, warnings


def apply_rename_ops(ops: list[RenameOp], *, dry_run: bool) -> None:
    if dry_run:
        return
    for op in ops:
        op.source.rename(op.target)


def create_missing_week_dirs(
    root: Path,
    *,
    month_year: tuple[int, int],
    through_date: dt.date,
    dry_run: bool,
) -> list[Path]:
    year, month = month_year
    existing_names = {folder.name for folder in iter_week_dirs(root)}
    created: list[Path] = []

    cursor = dt.date(year, month, 1)
    while cursor.weekday() != 1:
        cursor += dt.timedelta(days=1)

    while cursor <= through_date:
        folder_name = build_week_folder_name(cursor)
        target = root / folder_name
        if folder_name not in existing_names and cursor.month == month:
            created.append(target)
            if not dry_run:
                target.mkdir(parents=True, exist_ok=True)
            existing_names.add(folder_name)
        cursor += dt.timedelta(days=7)

    return created


def assess_folder(folder: Path) -> tuple[dict[str, Path], list[str]]:
    recognized: dict[str, Path] = {}
    warnings: list[str] = []

    for file_path in sorted(p for p in folder.iterdir() if p.is_file()):
        kind = detect_kind(file_path)
        if kind is None:
            warnings.append(f"archivo no reconocido: {file_path.name}")
            continue
        if kind in recognized:
            warnings.append(f"archivo duplicado para {kind}: {file_path.name}")
            continue
        recognized[kind] = file_path

    return recognized, warnings


def build_report(
    root: Path,
    *,
    rename_ops: list[RenameOp],
    created_dirs: list[Path],
    warnings: list[str],
) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = []
    lines.append("Reporte de semanas incompletas del raw semanal del Radar")
    lines.append(f"Generado: {now}")
    lines.append("")
    lines.append(f"Renombres aplicados/propuestos: {len(rename_ops)}")
    lines.append(f"Carpetas faltantes creadas/propuestas: {len(created_dirs)}")
    for path in created_dirs:
        lines.append(f"- {path.name}")
    lines.append("")

    if warnings:
        lines.append("Advertencias")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    incomplete_sections: list[str] = []
    for folder in iter_week_dirs(root):
        recognized, folder_warnings = assess_folder(folder)
        missing = [kind for kind in EXPECTED_TYPES if kind not in recognized]
        if not missing and not folder_warnings:
            continue

        present = [kind for kind in EXPECTED_TYPES if kind in recognized]
        incomplete_sections.append(f"{folder.name}")
        incomplete_sections.append(f"  presentes: {', '.join(present) if present else 'ninguno'}")
        incomplete_sections.append(
            "  faltan: "
            + ", ".join(f"{folder.name}_{kind}{EXPECTED_EXTENSIONS[kind]}" for kind in missing)
        )
        for warning in folder_warnings:
            incomplete_sections.append(f"  nota: {warning}")
        incomplete_sections.append("")

    if incomplete_sections:
        lines.append("Semanas incompletas")
        lines.extend(incomplete_sections)
    else:
        lines.append("Semanas incompletas")
        lines.append("No se detectaron semanas incompletas.")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    month_year = parse_year_month(args.create_missing_month)
    through_date = parse_iso_date(args.through_date)

    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Ruta inválida para --root: {str(root)!r}")
    if through_date.weekday() != 0:
        raise SystemExit(f"--through-date debe ser lunes: {through_date.isoformat()}")

    rename_ops, warnings = collect_rename_ops(root)
    created_dirs = create_missing_week_dirs(
        root,
        month_year=month_year,
        through_date=through_date,
        dry_run=args.dry_run,
    )
    apply_rename_ops(rename_ops, dry_run=args.dry_run)

    report = build_report(root, rename_ops=rename_ops, created_dirs=created_dirs, warnings=warnings)
    if not args.dry_run:
        report_path.write_text(report, encoding="utf-8")

    print(f"Renombres {'propuestos' if args.dry_run else 'aplicados'}: {len(rename_ops)}")
    print(f"Carpetas {'propuestas' if args.dry_run else 'creadas'}: {len(created_dirs)}")
    print(f"Reporte: {report_path}")
    if args.dry_run:
        print("")
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
