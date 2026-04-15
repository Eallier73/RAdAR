#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import unicodedata
from pathlib import Path

from src.preprocessing.normalizar_semanas_canonicas import build_week_folder_name


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

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MAIN_ROOT = Path("/home/emilio/Documentos/RAdAR/Datos_RAdAR")
RAW_WEEKLY_ROOT = REPO_ROOT / "data" / "raw" / "radar_weekly_flat"

SOURCE_DIRS = {
    "facebook": "Facebook",
    "twitter": "Twitter",
    "youtube": "YouTube",
    "medios": "Medios",
}

SOURCE_FILENAME_BUILDERS = {
    "facebook": lambda week_name: f"facebook_institutional_raw_{week_name}.csv",
    "twitter": lambda week_name: f"twitter_data_{week_name}.csv",
    "youtube": lambda week_name: f"youtube_comentarios_{week_name}.csv",
    "medios": lambda week_name: f"media_articles_{week_name}.csv",
}

TARGET_FILENAME_BUILDERS = {
    "facebook": lambda week_name: f"{week_name}_facebook.csv",
    "twitter": lambda week_name: f"{week_name}_twitter.csv",
    "youtube": lambda week_name: f"{week_name}_youtube.csv",
    "medios": lambda week_name: f"{week_name}_medios.txt",
}

WEEK_NAME_RE = re.compile(r"^(?P<start>\d{4}-\d{2}-\d{2})_semana_")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Importa semanas descargadas en el repo principal y las convierte "
            "al raw semanal canonico de esta rama."
        )
    )
    parser.add_argument(
        "--main-root",
        default=str(DEFAULT_MAIN_ROOT),
        help="Raiz del repo principal con Datos_RAdAR.",
    )
    parser.add_argument(
        "--dest-root",
        default=str(RAW_WEEKLY_ROOT),
        help="Directorio raw semanal canonico dentro de esta rama.",
    )
    parser.add_argument(
        "--shift-days",
        type=int,
        default=1,
        help=(
            "Desfase en dias entre la semana de origen del repo principal y "
            "la nomenclatura canonica local. Default: 1."
        ),
    )
    parser.add_argument(
        "--weeks",
        nargs="*",
        help=(
            "Semanas de origen a importar. Si se omite, se importan las semanas "
            "de origen cuyo destino aun no existe."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sobrescribe semanas destino ya existentes.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica los cambios. Sin esta bandera solo hace dry-run.",
    )
    return parser.parse_args()


def parse_source_week_start(week_name: str) -> dt.date:
    match = WEEK_NAME_RE.match(week_name)
    if not match:
        raise ValueError(f"Nombre de semana invalido: {week_name}")
    return dt.date.fromisoformat(match.group("start"))


def build_target_week_name(source_week_name: str, shift_days: int) -> str:
    source_start = parse_source_week_start(source_week_name)
    target_start = source_start + dt.timedelta(days=shift_days)
    return build_week_folder_name(target_start)


def discover_source_weeks(main_root: Path) -> list[str]:
    reference_dir = main_root / SOURCE_DIRS["twitter"]
    weeks: list[str] = []
    for entry in sorted(reference_dir.iterdir()):
        if entry.is_dir() and not entry.name.startswith("_"):
            weeks.append(entry.name)
    return weeks


def iter_requested_mappings(
    main_root: Path,
    dest_root: Path,
    shift_days: int,
    requested_weeks: list[str] | None,
    overwrite: bool,
) -> list[tuple[str, str]]:
    source_weeks = requested_weeks or discover_source_weeks(main_root)
    mappings: list[tuple[str, str]] = []
    for source_week in source_weeks:
        target_week = build_target_week_name(source_week, shift_days)
        target_dir = dest_root / target_week
        if target_dir.exists() and not overwrite:
            continue
        mappings.append((source_week, target_week))
    return mappings


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_utc_timestamp(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if value.endswith("Z"):
        return value
    if value.endswith("+00:00"):
        return value[:-6] + ".000Z"
    return value


def target_nombre_semana(target_week_name: str) -> str:
    return target_week_name


def transform_facebook_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    transformed: list[dict[str, str]] = []
    for row in source_rows:
        record_type = (row.get("record_type") or "").strip()
        if record_type == "post_parent":
            transformed.append(
                {
                    "tipo": "POST",
                    "url": row.get("post_url", ""),
                    "post_url_padre": "",
                    "fecha": normalize_utc_timestamp(row.get("created_time", "")),
                    "texto": row.get("text", "") or row.get("post_text", ""),
                    "num_comentarios": row.get("comment_count_post", ""),
                }
            )
        elif record_type in {"comment", "reply"}:
            transformed.append(
                {
                    "tipo": "COMENTARIO",
                    "url": row.get("comment_url", "") or row.get("post_url", ""),
                    "post_url_padre": row.get("post_url", ""),
                    "fecha": normalize_utc_timestamp(row.get("created_time", "")),
                    "texto": row.get("text", ""),
                    "num_comentarios": "",
                }
            )
    return transformed


def transform_twitter_rows(
    source_rows: list[dict[str, str]],
    *,
    target_week_name: str,
) -> list[dict[str, str]]:
    week_name_value = target_nombre_semana(target_week_name)
    transformed: list[dict[str, str]] = []
    for row in source_rows:
        tweet_datetime = row.get("tweet_published_at", "")
        transformed.append(
            {
                "fecha_semana": "",
                "nombre_semana": week_name_value,
                "author": row.get("tweet_author", ""),
                "datetime": tweet_datetime,
                "datetime_parsed_utc": tweet_datetime.replace("Z", "+00:00"),
                "url": row.get("tweet_url", ""),
                "text": row.get("tweet_text", ""),
                "replies": row.get("reply_count", ""),
                "retweets": row.get("retweet_count", ""),
                "likes": row.get("like_count", ""),
                "bookmarks": "",
                "views": row.get("view_count", ""),
                "query_used": row.get("query", ""),
                "is_reply": row.get("is_reply", ""),
                "in_reply_to_url": row.get("parent_tweet_url", ""),
            }
        )
    return transformed


def transform_youtube_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    transformed: list[dict[str, str]] = []
    for row in source_rows:
        transformed.append(
            {
                "video_id": row.get("video_id", ""),
                "comment_id": row.get("comment_id", ""),
                "author": row.get("author", ""),
                "comment_text": row.get("comment_text", ""),
                "published_at": row.get("published_at", ""),
                "like_count": row.get("like_count", ""),
                "query": row.get("query", ""),
                "video_title": row.get("video_title", ""),
                "channel_title": row.get("channel_title", ""),
                "video_published_at": row.get("video_published_at", ""),
                "fecha_extraccion": row.get("fecha_extraccion", ""),
            }
        )
    return transformed


def limpiar_texto_para_txt(texto: str) -> str:
    value = (texto or "").lower()
    value = re.sub(r"https?://\S+", " ", value)
    value = re.sub(r"www\.\S+", " ", value)
    value = re.sub(r"\b[\w-]+(?:\.[\w-]+)+\b", " ", value)
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"\d+", " ", value)
    value = re.sub(r"[^a-z\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def formatear_en_lineas_de_palabras(texto: str, palabras_por_linea: int = 30) -> str:
    palabras = texto.split()
    if not palabras:
        return ""
    return "\n".join(
        " ".join(palabras[index:index + palabras_por_linea])
        for index in range(0, len(palabras), palabras_por_linea)
    )


def transform_medios_text(source_rows: list[dict[str, str]]) -> str:
    material_limpio: list[str] = []
    for row in source_rows:
        titulo = (row.get("article_title") or "").strip()
        texto = (row.get("article_text") or "").strip()
        combinado = f"{titulo} {texto}".strip()
        limpio = limpiar_texto_para_txt(combinado)
        if limpio:
            material_limpio.append(limpio)
    return formatear_en_lineas_de_palabras(" ".join(material_limpio), palabras_por_linea=30)


def ensure_parent(path: Path, *, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)


def write_csv_rows(
    path: Path,
    *,
    fieldnames: list[str],
    rows: list[dict[str, str]],
    encoding: str,
    dry_run: bool,
) -> None:
    if dry_run:
        return
    ensure_parent(path, dry_run=False)
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, content: str, *, dry_run: bool) -> None:
    if dry_run:
        return
    ensure_parent(path, dry_run=False)
    with path.open("w", encoding="utf-8") as handle:
        if content:
            handle.write(content + "\n")


def import_week(
    main_root: Path,
    dest_root: Path,
    *,
    source_week_name: str,
    target_week_name: str,
    dry_run: bool,
) -> dict[str, int]:
    target_dir = dest_root / target_week_name
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}

    facebook_source = (
        main_root
        / SOURCE_DIRS["facebook"]
        / source_week_name
        / SOURCE_FILENAME_BUILDERS["facebook"](source_week_name)
    )
    facebook_target = target_dir / TARGET_FILENAME_BUILDERS["facebook"](target_week_name)
    facebook_rows = transform_facebook_rows(read_rows(facebook_source))
    write_csv_rows(
        facebook_target,
        fieldnames=["tipo", "url", "post_url_padre", "fecha", "texto", "num_comentarios"],
        rows=facebook_rows,
        encoding="utf-8-sig",
        dry_run=dry_run,
    )
    counts["facebook"] = len(facebook_rows)

    twitter_source = (
        main_root
        / SOURCE_DIRS["twitter"]
        / source_week_name
        / SOURCE_FILENAME_BUILDERS["twitter"](source_week_name)
    )
    twitter_target = target_dir / TARGET_FILENAME_BUILDERS["twitter"](target_week_name)
    twitter_rows = transform_twitter_rows(read_rows(twitter_source), target_week_name=target_week_name)
    write_csv_rows(
        twitter_target,
        fieldnames=[
            "fecha_semana",
            "nombre_semana",
            "author",
            "datetime",
            "datetime_parsed_utc",
            "url",
            "text",
            "replies",
            "retweets",
            "likes",
            "bookmarks",
            "views",
            "query_used",
            "is_reply",
            "in_reply_to_url",
        ],
        rows=twitter_rows,
        encoding="utf-8",
        dry_run=dry_run,
    )
    counts["twitter"] = len(twitter_rows)

    youtube_source = (
        main_root
        / SOURCE_DIRS["youtube"]
        / source_week_name
        / SOURCE_FILENAME_BUILDERS["youtube"](source_week_name)
    )
    youtube_target = target_dir / TARGET_FILENAME_BUILDERS["youtube"](target_week_name)
    youtube_rows = transform_youtube_rows(read_rows(youtube_source))
    write_csv_rows(
        youtube_target,
        fieldnames=[
            "video_id",
            "comment_id",
            "author",
            "comment_text",
            "published_at",
            "like_count",
            "query",
            "video_title",
            "channel_title",
            "video_published_at",
            "fecha_extraccion",
        ],
        rows=youtube_rows,
        encoding="utf-8-sig",
        dry_run=dry_run,
    )
    counts["youtube"] = len(youtube_rows)

    medios_source = (
        main_root
        / SOURCE_DIRS["medios"]
        / source_week_name
        / SOURCE_FILENAME_BUILDERS["medios"](source_week_name)
    )
    medios_target = target_dir / TARGET_FILENAME_BUILDERS["medios"](target_week_name)
    medios_text = transform_medios_text(read_rows(medios_source))
    write_text(medios_target, medios_text, dry_run=dry_run)
    counts["medios_lineas"] = len(medios_text.splitlines()) if medios_text else 0

    return counts


def main() -> int:
    args = parse_args()
    main_root = Path(args.main_root).expanduser().resolve()
    dest_root = Path(args.dest_root).expanduser().resolve()
    if not main_root.exists():
        raise SystemExit(f"Raiz principal no encontrada: {main_root}")
    if not dest_root.exists():
        raise SystemExit(f"Directorio destino no encontrado: {dest_root}")

    mappings = iter_requested_mappings(
        main_root,
        dest_root,
        shift_days=args.shift_days,
        requested_weeks=args.weeks,
        overwrite=args.overwrite,
    )
    if not mappings:
        print("No hay semanas por importar.")
        return 0

    print(f"Semanas a importar: {len(mappings)}")
    for source_week, target_week in mappings:
        print(f"  {source_week} -> {target_week}")

    dry_run = not args.apply
    if dry_run:
        print("\nDry-run: no se escribieron archivos.")
        return 0

    print()
    for source_week, target_week in mappings:
        counts = import_week(
            main_root,
            dest_root,
            source_week_name=source_week,
            target_week_name=target_week,
            dry_run=False,
        )
        print(
            f"OK {target_week} | "
            f"facebook={counts['facebook']} twitter={counts['twitter']} "
            f"youtube={counts['youtube']} medios_lineas={counts['medios_lineas']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
