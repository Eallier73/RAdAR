#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


PREPROCESSING_DIR = Path(__file__).resolve().parent
REPO_ROOT = PREPROCESSING_DIR.parents[1]
RAW_WEEKLY_ROOT = REPO_ROOT / "data" / "raw" / "radar_weekly_flat"
DEFAULT_REPORT_PATH = REPO_ROOT / "artifacts" / "logs" / "preprocessing" / "reporte_semanas_incompletas.txt"


def run_script(label: str, script_name: str, script_args: list[str]) -> None:
    command = [sys.executable, str(PREPROCESSING_DIR / script_name), *script_args]
    print(f"\n[{label}]")
    print(shlex.join(command))
    subprocess.run(command, check=True)


def run_normalize_stage(args: argparse.Namespace) -> None:
    prefijar_args = [str(Path(args.raw_root).expanduser().resolve())]
    if args.apply:
        prefijar_args.append("--apply")
    run_script("prefijar_carpetas_semanales", "prefijar_carpetas_semanales.py", prefijar_args)

    normalizar_args = [
        "--root",
        str(Path(args.raw_root).expanduser().resolve()),
        "--report",
        str(Path(args.report).expanduser().resolve()),
        "--create-missing-month",
        args.create_missing_month,
        "--through-date",
        args.through_date,
    ]
    if not args.apply:
        normalizar_args.append("--dry-run")
    run_script("normalizar_semanas_canonicas", "normalizar_semanas_canonicas.py", normalizar_args)


def run_distribute_facebook(args: argparse.Namespace) -> None:
    command = [
        "--src",
        str(Path(args.src).expanduser().resolve()),
        "--dest",
        str(Path(args.dest).expanduser().resolve()),
        "--max-span-days",
        str(args.max_span_days),
    ]
    if args.apply:
        command.append("--apply")
    run_script("distribuir_facebook_semanal", "distribuir_facebook_semanal.py", command)


def run_distribute_medios(args: argparse.Namespace) -> None:
    command = [
        "--src",
        str(Path(args.src).expanduser().resolve()),
        "--dest",
        str(Path(args.dest).expanduser().resolve()),
        "--extensions",
        *args.extensions,
    ]
    if args.include_cache:
        command.append("--include-cache")
    if args.keep_empty_dirs:
        command.append("--keep-empty-dirs")
    if args.apply:
        command.append("--apply")
    run_script("distribuir_medios_semanales", "distribuir_medios_semanales.py", command)


def run_fill_facebook(args: argparse.Namespace) -> None:
    command = [
        "--src",
        str(Path(args.src).expanduser().resolve()),
        "--dest",
        str(Path(args.dest).expanduser().resolve()),
        "--timezone",
        args.timezone,
        "--sample-strategy",
        args.sample_strategy,
        "--sample-size",
        str(args.sample_size),
        "--sample-seed",
        str(args.sample_seed),
        "--sample-min-per-stratum",
        str(args.sample_min_per_stratum),
    ]
    if args.apply:
        command.append("--apply")
    run_script(
        "completar_facebook_semanal_desde_mensual",
        "completar_facebook_semanal_desde_mensual.py",
        command,
    )


def run_fill_twitter(args: argparse.Namespace) -> None:
    command = [
        "--src",
        str(Path(args.src).expanduser().resolve()),
        "--dest",
        str(Path(args.dest).expanduser().resolve()),
        "--timezone",
        args.timezone,
        "--date-column",
        args.date_column,
    ]
    if args.apply:
        command.append("--apply")
    run_script(
        "completar_twitter_semanal_desde_mensual",
        "completar_twitter_semanal_desde_mensual.py",
        command,
    )


def run_fill_youtube(args: argparse.Namespace) -> None:
    command = [
        "--src",
        str(Path(args.src).expanduser().resolve()),
        "--dest",
        str(Path(args.dest).expanduser().resolve()),
        "--timezone",
        args.timezone,
        "--date-column",
        args.date_column,
    ]
    if args.apply:
        command.append("--apply")
    run_script(
        "completar_youtube_semanal_desde_mensual",
        "completar_youtube_semanal_desde_mensual.py",
        command,
    )


def run_promote_text() -> None:
    run_script("promover_raw_a_texto", "promover_raw_a_texto.py", [])


def add_apply_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--apply", action="store_true", help="Ejecuta cambios. Sin esto solo se hace dry-run cuando el script lo soporta.")


def add_dest_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--dest",
        default=str(RAW_WEEKLY_ROOT),
        help=f"Directorio canónico semanal. Default: {RAW_WEEKLY_ROOT}",
    )


def add_normalize_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--raw-root",
        default=str(RAW_WEEKLY_ROOT),
        help=f"Directorio semanal canónico a normalizar. Default: {RAW_WEEKLY_ROOT}",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help=f"Ruta del reporte estructural. Default: {DEFAULT_REPORT_PATH}",
    )
    parser.add_argument(
        "--create-missing-month",
        default="2026-03",
        help="Mes YYYY-MM sobre el que se crean semanas faltantes.",
    )
    parser.add_argument(
        "--through-date",
        default="2026-03-16",
        help="Fecha final inclusiva para creación de semanas faltantes.",
    )
    add_apply_argument(parser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Orquesta automatización parcial del stage de preprocessing. "
            "No es la automatización integral del repositorio."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    normalize = subparsers.add_parser(
        "normalizar-semanas",
        help="Ejecuta prefijado cronológico y normalización canónica del raw semanal.",
    )
    add_normalize_arguments(normalize)

    distribute_facebook = subparsers.add_parser(
        "distribuir-facebook",
        help="Asigna archivos Facebook con rango de fechas a su carpeta semanal.",
    )
    distribute_facebook.add_argument("--src", required=True, help="Directorio fuente con archivos externos de Facebook.")
    add_dest_argument(distribute_facebook)
    distribute_facebook.add_argument(
        "--max-span-days",
        type=int,
        default=7,
        help="Máximo tamaño del rango en días aceptado para un archivo.",
    )
    add_apply_argument(distribute_facebook)

    distribute_medios = subparsers.add_parser(
        "distribuir-medios",
        help="Asigna archivos externos de medios a la semana correspondiente.",
    )
    distribute_medios.add_argument("--src", required=True, help="Directorio fuente con TXT o CSV de medios.")
    add_dest_argument(distribute_medios)
    distribute_medios.add_argument(
        "--extensions",
        nargs="+",
        default=[".txt"],
        help="Extensiones permitidas en la fuente. Default: .txt",
    )
    distribute_medios.add_argument(
        "--include-cache",
        action="store_true",
        help="Incluye archivos ubicados dentro de _cache_rss.",
    )
    distribute_medios.add_argument(
        "--keep-empty-dirs",
        action="store_true",
        help="Conserva carpetas semana_* vacías después del movimiento.",
    )
    add_apply_argument(distribute_medios)

    fill_facebook = subparsers.add_parser(
        "completar-facebook",
        help="Completa semanas faltantes de Facebook a partir de exportaciones mensuales.",
    )
    fill_facebook.add_argument("--src", required=True, help="Directorio fuente con MV_Datos_Mensual_*.csv.")
    add_dest_argument(fill_facebook)
    fill_facebook.add_argument("--timezone", default="America/Mexico_City", help="Zona horaria de asignación semanal.")
    fill_facebook.add_argument(
        "--sample-strategy",
        choices=["none", "random", "stratified", "hybrid"],
        default="hybrid",
        help="Estrategia de muestreo semanal.",
    )
    fill_facebook.add_argument("--sample-size", type=int, default=25, help="Tamaño de muestra por semana.")
    fill_facebook.add_argument("--sample-seed", type=int, default=42, help="Semilla reproducible del muestreo.")
    fill_facebook.add_argument(
        "--sample-min-per-stratum",
        type=int,
        default=5,
        help="Mínimo por estrato cuando hay suficiente disponibilidad.",
    )
    add_apply_argument(fill_facebook)

    fill_twitter = subparsers.add_parser(
        "completar-twitter",
        help="Completa semanas faltantes de Twitter/X desde exportaciones mensuales.",
    )
    fill_twitter.add_argument("--src", required=True, help="Directorio fuente con Tweets_MV_GT_*.csv.")
    add_dest_argument(fill_twitter)
    fill_twitter.add_argument("--timezone", default="America/Mexico_City", help="Zona horaria de asignación semanal.")
    fill_twitter.add_argument("--date-column", default="UTC_Time", help="Columna temporal en la exportación fuente.")
    add_apply_argument(fill_twitter)

    fill_youtube = subparsers.add_parser(
        "completar-youtube",
        help="Completa semanas faltantes de YouTube desde exportaciones mensuales.",
    )
    fill_youtube.add_argument("--src", required=True, help="Directorio fuente con Youtube_MV_*.csv.")
    add_dest_argument(fill_youtube)
    fill_youtube.add_argument("--timezone", default="America/Mexico_City", help="Zona horaria de asignación semanal.")
    fill_youtube.add_argument(
        "--date-column",
        default="published_at",
        help="Columna temporal en la exportación fuente.",
    )
    add_apply_argument(fill_youtube)

    promote_text = subparsers.add_parser(
        "promover-texto",
        help="Promueve data/raw semanal a data/text semanal.",
    )
    promote_text.add_argument(
        "--apply",
        action="store_true",
        required=True,
        help="Confirmación explícita. Este subcomando escribe salidas y no expone dry-run.",
    )

    pipeline = subparsers.add_parser(
        "pipeline-base",
        help="Ejecuta una secuencia base de preprocessing sin pretender automatización end-to-end.",
    )
    add_normalize_arguments(pipeline)
    pipeline.add_argument("--facebook-weekly-src", help="Directorio con archivos externos Facebook ya cortados por rango semanal.")
    pipeline.add_argument("--facebook-monthly-src", help="Directorio con exportaciones mensuales de Facebook.")
    pipeline.add_argument("--twitter-monthly-src", help="Directorio con exportaciones mensuales de Twitter/X.")
    pipeline.add_argument("--youtube-monthly-src", help="Directorio con exportaciones mensuales de YouTube.")
    pipeline.add_argument("--medios-src", help="Directorio con TXT o CSV externos de medios.")
    pipeline.add_argument(
        "--facebook-max-span-days",
        type=int,
        default=7,
        help="Máximo rango permitido para archivos Facebook ya cortados.",
    )
    pipeline.add_argument(
        "--facebook-sample-strategy",
        choices=["none", "random", "stratified", "hybrid"],
        default="hybrid",
        help="Estrategia de muestreo para completado de Facebook.",
    )
    pipeline.add_argument("--facebook-sample-size", type=int, default=25, help="Tamaño de muestra por semana para Facebook.")
    pipeline.add_argument("--facebook-sample-seed", type=int, default=42, help="Semilla de muestreo para Facebook.")
    pipeline.add_argument(
        "--facebook-sample-min-per-stratum",
        type=int,
        default=5,
        help="Mínimo por estrato para Facebook cuando hay suficientes casos.",
    )
    pipeline.add_argument("--timezone", default="America/Mexico_City", help="Zona horaria para fuentes mensuales.")
    pipeline.add_argument("--twitter-date-column", default="UTC_Time", help="Columna temporal para Twitter/X.")
    pipeline.add_argument("--youtube-date-column", default="published_at", help="Columna temporal para YouTube.")
    pipeline.add_argument(
        "--medios-extensions",
        nargs="+",
        default=[".txt"],
        help="Extensiones permitidas para medios externos.",
    )
    pipeline.add_argument("--include-cache", action="store_true", help="Incluye archivos dentro de _cache_rss para medios.")
    pipeline.add_argument("--keep-empty-dirs", action="store_true", help="Conserva carpetas vacías de medios.")
    pipeline.add_argument(
        "--promover-texto",
        action="store_true",
        help="Ejecuta la promoción raw -> text al final de la secuencia.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "normalizar-semanas":
        run_normalize_stage(args)
        return 0

    if args.command == "distribuir-facebook":
        run_distribute_facebook(args)
        return 0

    if args.command == "distribuir-medios":
        run_distribute_medios(args)
        return 0

    if args.command == "completar-facebook":
        run_fill_facebook(args)
        return 0

    if args.command == "completar-twitter":
        run_fill_twitter(args)
        return 0

    if args.command == "completar-youtube":
        run_fill_youtube(args)
        return 0

    if args.command == "promover-texto":
        run_promote_text()
        return 0

    if args.command == "pipeline-base":
        run_normalize_stage(args)

        if args.facebook_weekly_src:
            run_distribute_facebook(
                argparse.Namespace(
                    src=args.facebook_weekly_src,
                    dest=args.raw_root,
                    max_span_days=args.facebook_max_span_days,
                    apply=args.apply,
                )
            )

        if args.medios_src:
            run_distribute_medios(
                argparse.Namespace(
                    src=args.medios_src,
                    dest=args.raw_root,
                    extensions=args.medios_extensions,
                    include_cache=args.include_cache,
                    keep_empty_dirs=args.keep_empty_dirs,
                    apply=args.apply,
                )
            )

        if args.facebook_monthly_src:
            run_fill_facebook(
                argparse.Namespace(
                    src=args.facebook_monthly_src,
                    dest=args.raw_root,
                    timezone=args.timezone,
                    sample_strategy=args.facebook_sample_strategy,
                    sample_size=args.facebook_sample_size,
                    sample_seed=args.facebook_sample_seed,
                    sample_min_per_stratum=args.facebook_sample_min_per_stratum,
                    apply=args.apply,
                )
            )

        if args.twitter_monthly_src:
            run_fill_twitter(
                argparse.Namespace(
                    src=args.twitter_monthly_src,
                    dest=args.raw_root,
                    timezone=args.timezone,
                    date_column=args.twitter_date_column,
                    apply=args.apply,
                )
            )

        if args.youtube_monthly_src:
            run_fill_youtube(
                argparse.Namespace(
                    src=args.youtube_monthly_src,
                    dest=args.raw_root,
                    timezone=args.timezone,
                    date_column=args.youtube_date_column,
                    apply=args.apply,
                )
            )

        if args.promover_texto:
            if not args.apply:
                print(
                    "\n[promover_raw_a_texto]\n"
                    "Se omite en dry-run porque este script todavía no expone modo sin escritura."
                )
            else:
                run_promote_text()

        return 0

    parser.error(f"Comando no soportado: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
