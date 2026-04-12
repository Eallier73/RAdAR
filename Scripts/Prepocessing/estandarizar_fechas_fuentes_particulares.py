#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from dataclasses import dataclass
from pathlib import Path


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

SOURCE_DATE_KEYS = {
    "Facebook": ("since", "until"),
    "Twitter": ("since", "until"),
    "YouTube": ("start_date", "end_date"),
    "Medios": ("since", "before"),
}

TEXT_EXTENSIONS = {
    ".csv",
    ".json",
    ".jsonl",
    ".log",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class WeekPlan:
    source: str
    old_dir: Path
    new_dir: Path
    aliases: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Estandariza carpetas semanales dentro de contenedores por fuente "
            "usando la fecha real de inicio/fin registrada en summary.json."
        )
    )
    parser.add_argument(
        "--root",
        default="/home/emilio/Documentos/RAdAR/Datos_RAdAR",
        help="Raíz de Datos_RAdAR.",
    )
    parser.add_argument(
        "--sources",
        nargs="*",
        default=["Facebook", "Twitter", "YouTube", "Medios"],
        help="Contenedores por fuente a revisar.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica renombres y reescritura de referencias. Sin esto solo hace dry-run.",
    )
    return parser.parse_args()


def parse_iso_date(value: str | None, *, field: str, file_path: Path) -> dt.date:
    if not value:
        raise ValueError(f"Falta campo {field!r} en {file_path}")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Fecha inválida en {file_path}: {field}={value!r}") from exc


def build_week_name(start: dt.date, end: dt.date) -> str:
    start_part = f"{start.day:02d}{MONTHS_ES[start.month]}"
    end_part = f"{end.day:02d}{MONTHS_ES[end.month]}"
    yy = f"{end.year % 100:02d}"
    return f"{start.isoformat()}_semana_{start_part}_{end_part}_{yy}"


def load_json(path: Path) -> dict:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def collect_aliases(week_dir: Path) -> tuple[str, ...]:
    aliases: set[str] = {week_dir.name}
    for json_name in ("summary.json", "metadata_run.json", "parametros_run.json"):
        file_path = week_dir / json_name
        if not file_path.exists():
            continue
        try:
            data = load_json(file_path)
        except Exception:
            continue
        if isinstance(data, dict):
            week_name = data.get("week_name")
            if isinstance(week_name, str) and week_name.strip():
                aliases.add(week_name.strip())
    return tuple(sorted(aliases, key=len, reverse=True))


def replace_aliases(text: str, aliases: tuple[str, ...], new_name: str) -> str:
    out = text
    for alias in aliases:
        out = out.replace(alias, new_name)
    return out


def discover_plan(root: Path, sources: list[str]) -> tuple[list[WeekPlan], list[str]]:
    plans: list[WeekPlan] = []
    warnings: list[str] = []

    for source in sources:
        source_dir = root / source
        if not source_dir.exists():
            warnings.append(f"No existe contenedor: {source_dir}")
            continue
        if source not in SOURCE_DATE_KEYS:
            warnings.append(f"Fuente no soportada: {source}")
            continue

        start_key, end_key = SOURCE_DATE_KEYS[source]
        for week_dir in sorted(p for p in source_dir.iterdir() if p.is_dir() and not p.name.startswith("_")):
            summary_path = week_dir / "summary.json"
            if not summary_path.exists():
                warnings.append(f"{week_dir}: falta summary.json")
                continue
            try:
                summary = load_json(summary_path)
                start = parse_iso_date(summary.get(start_key), field=start_key, file_path=summary_path)
                end = parse_iso_date(summary.get(end_key), field=end_key, file_path=summary_path)
            except Exception as exc:
                warnings.append(str(exc))
                continue

            new_name = build_week_name(start, end)
            if week_dir.name == new_name:
                continue

            aliases = collect_aliases(week_dir)
            plans.append(
                WeekPlan(
                    source=source,
                    old_dir=week_dir,
                    new_dir=week_dir.parent / new_name,
                    aliases=aliases,
                )
            )

    seen_targets: dict[Path, Path] = {}
    for plan in plans:
        existing = seen_targets.get(plan.new_dir)
        if existing is not None:
            raise SystemExit(
                f"Colisión: {plan.old_dir} y {existing} quieren renombrarse a {plan.new_dir}"
            )
        if plan.new_dir.exists() and plan.new_dir != plan.old_dir:
            raise SystemExit(f"Ya existe el destino {plan.new_dir}")
        seen_targets[plan.new_dir] = plan.old_dir

    return plans, warnings


def rename_nested_entries(plan: WeekPlan, *, dry_run: bool) -> list[tuple[Path, Path]]:
    ops: list[tuple[Path, Path]] = []
    for path in sorted(plan.old_dir.rglob("*"), key=lambda p: (len(p.parts), str(p)), reverse=True):
        new_name = replace_aliases(path.name, plan.aliases, plan.new_dir.name)
        if new_name == path.name:
            continue
        target = path.with_name(new_name)
        ops.append((path, target))

    for old_path, new_path in ops:
        if new_path.exists():
            raise SystemExit(f"No puedo renombrar {old_path} -> {new_path}: el destino ya existe.")

    if dry_run:
        return ops

    for old_path, new_path in ops:
        old_path.rename(new_path)
    return ops


def rewrite_text_references(plan: WeekPlan, *, dry_run: bool) -> list[Path]:
    changed: list[Path] = []
    for file_path in sorted(p for p in plan.old_dir.rglob("*") if p.is_file()):
        if file_path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = replace_aliases(content, plan.aliases, plan.new_dir.name)
        if updated == content:
            continue
        changed.append(file_path)
        if not dry_run:
            file_path.write_text(updated, encoding="utf-8")
    return changed


def apply_plan(plans: list[WeekPlan], *, dry_run: bool) -> tuple[int, int, int]:
    renamed_dirs = 0
    renamed_nested = 0
    rewritten_files = 0

    for plan in plans:
        nested_ops = rename_nested_entries(plan, dry_run=dry_run)
        rewritten = rewrite_text_references(plan, dry_run=dry_run)

        renamed_nested += len(nested_ops)
        rewritten_files += len(rewritten)

        if not dry_run:
            plan.old_dir.rename(plan.new_dir)
        renamed_dirs += 1

    return renamed_dirs, renamed_nested, rewritten_files


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Ruta inválida: {root}")

    plans, warnings = discover_plan(root, args.sources)

    if warnings:
        print("Advertencias:")
        for warning in warnings:
            print(f"  - {warning}")
        print("")

    if not plans:
        print("No hay carpetas por fuente que requieran estandarización.")
        return 0

    print("Criterio: fecha_inicio_real_semana_<inicio>_<fin>_<yy_fin>")
    print("Cambios detectados:")
    for plan in plans:
        print(f"  - [{plan.source}] {plan.old_dir.name} -> {plan.new_dir.name}")
        print(f"    aliases detectados: {', '.join(plan.aliases)}")

    renamed_dirs, renamed_nested, rewritten_files = apply_plan(plans, dry_run=not args.apply)

    mode = "aplicados" if args.apply else "propuestos"
    print("")
    print(f"Directorios {mode}: {renamed_dirs}")
    print(f"Entradas internas {mode}: {renamed_nested}")
    print(f"Archivos de texto reescritos {mode}: {rewritten_files}")
    if not args.apply:
        print("Dry-run: usa --apply para ejecutar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
