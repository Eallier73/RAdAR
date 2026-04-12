#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import shutil
import string
from pathlib import Path

SOURCE_BASE = Path("/home/emilio/Documentos/RAdAR/data/raw/radar_weekly_flat")
TARGET_BASE = Path("/home/emilio/Documentos/RAdAR/data/text/radar_weekly_flat")

TARGET_DIRS = {
    "facebook": TARGET_BASE / "Facebook_Semana_Texto",
    "twitter": TARGET_BASE / "Twitter_Semana_Texto",
    "youtube": TARGET_BASE / "Youtube_Semana_Texto",
    "medios": TARGET_BASE / "Medios_Semana_Texto",
}

ACCENT_REPLACEMENTS = {
    "á": "a",
    "é": "e",
    "í": "i",
    "ó": "o",
    "ú": "u",
    "Á": "a",
    "É": "e",
    "Í": "i",
    "Ó": "o",
    "Ú": "u",
    "ñ": "n",
    "Ñ": "n",
    "ü": "u",
    "Ü": "u",
}


def _replace_accents(text: str) -> str:
    for original, replacement in ACCENT_REPLACEMENTS.items():
        text = text.replace(original, replacement)
    return text


def normalize_facebook(text: str) -> str:
    text = _replace_accents(text or "")
    text = text.lower()
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"#(\w+)", r" \1 ", text)
    text = re.sub(r"https?:\/\/\S*", " ", text)
    text = re.sub(r"www\.\S+", " ", text)
    text = re.sub(r"\S+\.com\b", " ", text)
    text = re.sub(r"\S+\.mx\b", " ", text)
    text = re.sub(r"\bhttp\b", " ", text)
    text = re.sub(r"\bhttps\b", " ", text)
    text = re.sub(r"\bcom\b", " ", text)
    text = re.sub(r"\bfacebook\b", " ", text)
    text = re.sub(r"\bfb\b", " ", text)
    text = re.sub(r"\bme gusta\b", " ", text)
    text = re.sub(r"\bcompartir\b", " ", text)
    text = re.sub(r"[" + re.escape(string.punctuation + string.digits) + "]", " ", text)
    text = "".join(char for char in text if ord(char) < 128)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_twitter(text: str) -> str:
    text = _replace_accents(text or "")
    text = text.lower()
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"#(\w+)", r" \1 ", text)
    text = re.sub(r"https?:\/\/\S*", " ", text)
    text = re.sub(r"www\.\S+", " ", text)
    text = re.sub(r"\S+\.com\b", " ", text)
    text = re.sub(r"\S+\.mx\b", " ", text)
    text = re.sub(r"\bhttp\b", " ", text)
    text = re.sub(r"\bhttps\b", " ", text)
    text = re.sub(r"\bcom\b", " ", text)
    text = re.sub(r"\brt\b", " ", text)
    text = re.sub(r"\bvia\b", " ", text)
    text = re.sub(r"[" + re.escape(string.punctuation + string.digits) + "]", " ", text)
    text = "".join(char for char in text if ord(char) < 128)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_youtube(text: str) -> str:
    text = _replace_accents(text or "")
    text = text.lower()
    text = re.sub(r"https?:\/\/\S*", " ", text)
    text = re.sub(r"\bhttp\b", " ", text)
    text = re.sub(r"\bhttps\b", " ", text)
    text = re.sub(r"\bcom\b", " ", text)
    text = re.sub(r"\.\s*com\b", " ", text)
    text = re.sub(r"[" + re.escape(string.punctuation + string.digits) + "]", " ", text)
    text = "".join(char for char in text if ord(char) < 128)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_dialect(path: Path) -> csv.Dialect:
    with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
        sample = handle.read(8192)
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;")
    except csv.Error:
        return csv.get_dialect("excel")


def read_dict_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    dialect = detect_dialect(path)
    with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        fieldnames = [field.strip().lower() for field in (reader.fieldnames or [])]
        rows = []
        for row in reader:
            normalized_row = {}
            for key, value in (row or {}).items():
                if key is None:
                    continue
                normalized_row[key.strip().lower()] = (value or "").strip().strip('"')
            rows.append(normalized_row)
    return rows, fieldnames


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set()
    unique = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def words_to_lines(items: list[str], words_per_line: int) -> list[str]:
    words = " ".join(items).split()
    return [
        " ".join(words[index:index + words_per_line])
        for index in range(0, len(words), words_per_line)
        if words[index:index + words_per_line]
    ]


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        if lines:
            handle.write("\n".join(lines) + "\n")


def process_facebook(files: list[Path], output_path: Path) -> tuple[int, int]:
    texts = []
    extracted = 0
    for path in files:
        rows, fieldnames = read_dict_rows(path)
        column = None
        for candidate in ("texto", "message"):
            if candidate in fieldnames:
                column = candidate
                break
        if not column:
            continue
        for row in rows:
            cleaned = normalize_facebook(row.get(column, ""))
            if cleaned and len(cleaned.split()) >= 2:
                texts.append(cleaned)
                extracted += 1
    unique = dedupe_keep_order(texts)
    write_lines(output_path, words_to_lines(unique, 35))
    return extracted, len(unique)


def process_twitter(files: list[Path], output_path: Path) -> tuple[int, int]:
    texts = []
    extracted = 0
    for path in files:
        rows, fieldnames = read_dict_rows(path)
        column = None
        for candidate in ("text", "tweet_content"):
            if candidate in fieldnames:
                column = candidate
                break

        if column:
            for row in rows:
                cleaned = normalize_twitter(row.get(column, ""))
                if cleaned and len(cleaned.split()) >= 3:
                    texts.append(cleaned)
                    extracted += 1
            continue

        # Algunas semanas viejas traen un .csv que en realidad ya es texto plano.
        with open(path, "r", encoding="utf-8-sig", errors="ignore") as handle:
            for raw_line in handle:
                cleaned = normalize_twitter(raw_line.strip())
                if cleaned and len(cleaned.split()) >= 3:
                    texts.append(cleaned)
                    extracted += 1
    unique = dedupe_keep_order(texts)
    write_lines(output_path, words_to_lines(unique, 25))
    return extracted, len(unique)


def process_youtube(files: list[Path], output_path: Path) -> tuple[int, int]:
    texts = []
    extracted = 0
    for path in files:
        rows, fieldnames = read_dict_rows(path)
        if "comment_text" in fieldnames:
            for row in rows:
                cleaned = normalize_youtube(row.get("comment_text", ""))
                if cleaned:
                    texts.append(cleaned)
                    extracted += 1
            continue

        # Algunas semanas traen texto ya procesado pero con extensión .csv.
        with open(path, "r", encoding="utf-8-sig", errors="ignore") as handle:
            for raw_line in handle:
                cleaned = normalize_youtube(raw_line.strip())
                if cleaned:
                    texts.append(cleaned)
                    extracted += 1
    unique = dedupe_keep_order(texts)
    write_lines(output_path, words_to_lines(unique, 30))
    return extracted, len(unique)


def process_medios(files: list[Path], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(files[0], output_path)


def source_prefix(week_dir: Path) -> str:
    return week_dir.name.split("_semana_", 1)[0]


def find_type_files(week_dir: Path, media_type: str) -> list[Path]:
    patterns = {
        "facebook": ["*_facebook.csv", "*facebook*.csv"],
        "twitter": ["*_twitter.csv", "*twitter*.csv"],
        "youtube": ["*_youtube.csv", "*youtube*.csv"],
        "medios": ["*_medios.txt", "*medios*.txt"],
    }
    matches = []
    seen = set()
    for pattern in patterns[media_type]:
        for path in sorted(week_dir.glob(pattern)):
            if path not in seen and path.is_file():
                seen.add(path)
                matches.append(path)
    return matches


def main() -> None:
    for target_dir in TARGET_DIRS.values():
        target_dir.mkdir(parents=True, exist_ok=True)

    weeks = sorted(path for path in SOURCE_BASE.iterdir() if path.is_dir())
    summary = {"facebook": 0, "twitter": 0, "youtube": 0, "medios": 0}
    missing = []

    for week_dir in weeks:
        prefix = source_prefix(week_dir)
        print(f"\n[{prefix}] {week_dir.name}")

        facebook_files = find_type_files(week_dir, "facebook")
        if facebook_files:
            output = TARGET_DIRS["facebook"] / f"{prefix}_facebook.txt"
            extracted, unique = process_facebook(facebook_files, output)
            print(f"  facebook -> {output.name} | extraidos:{extracted} unicos:{unique}")
            summary["facebook"] += 1
        else:
            missing.append((week_dir.name, "facebook"))
            print("  facebook -> faltante")

        twitter_files = find_type_files(week_dir, "twitter")
        if twitter_files:
            output = TARGET_DIRS["twitter"] / f"{prefix}_twitter.txt"
            extracted, unique = process_twitter(twitter_files, output)
            print(f"  twitter -> {output.name} | extraidos:{extracted} unicos:{unique}")
            summary["twitter"] += 1
        else:
            missing.append((week_dir.name, "twitter"))
            print("  twitter -> faltante")

        youtube_files = find_type_files(week_dir, "youtube")
        if youtube_files:
            output = TARGET_DIRS["youtube"] / f"{prefix}_youtube.txt"
            extracted, unique = process_youtube(youtube_files, output)
            print(f"  youtube -> {output.name} | extraidos:{extracted} unicos:{unique}")
            summary["youtube"] += 1
        else:
            missing.append((week_dir.name, "youtube"))
            print("  youtube -> faltante")

        medios_files = find_type_files(week_dir, "medios")
        if medios_files:
            output = TARGET_DIRS["medios"] / f"{prefix}_medios.txt"
            process_medios(medios_files, output)
            print(f"  medios -> {output.name} | copiado")
            summary["medios"] += 1
        else:
            missing.append((week_dir.name, "medios"))
            print("  medios -> faltante")

    print("\nResumen")
    for media_type in ("facebook", "twitter", "youtube", "medios"):
        print(f"  {media_type}: {summary[media_type]}")
    if missing:
        print(f"  faltantes: {len(missing)}")
        for week_name, media_type in missing:
            print(f"    {week_name}: {media_type}")
    else:
        print("  faltantes: 0")


if __name__ == "__main__":
    main()
