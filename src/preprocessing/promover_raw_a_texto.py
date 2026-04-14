#!/usr/bin/env python3
"""
promover_raw_a_texto.py — Producción de corpus textual semanal por fuente.

ADVERTENCIA METODOLÓGICA — LEER ANTES DE MODIFICAR
====================================================
Este script produce el material textual semanal consumido por NLP y modelado.
Su lógica de transformación forma parte del contrato metodológico del sistema.
Las funciones marcadas con [CONGELADO] no deben modificarse sin documentar
impacto sobre el corpus canónico.

Intervenciones vigentes:
  - v2.0.0-structural: logging persistente, artefactos de auditoría,
    validaciones operativas y manejo de errores por unidad de trabajo.
"""
from __future__ import annotations

# ── Sección 1: Imports ────────────────────────────────────────────────────────
import csv
import hashlib
import json
import logging
import re
import shutil
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Sección 2: Configuración canónica ────────────────────────────────────────
# CONTRATO CANÓNICO: estas rutas y directorios definen la topología de salida
# del sistema validado. No modificar sin documentar impacto en el corpus.
REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_BASE = REPO_ROOT / "data" / "raw" / "radar_weekly_flat"
TARGET_BASE = REPO_ROOT / "data" / "text" / "radar_weekly_flat"

TARGET_DIRS: dict[str, Path] = {
    "facebook": TARGET_BASE / "facebook_semana_texto",
    "twitter":  TARGET_BASE / "twitter_semana_texto",
    "youtube":  TARGET_BASE / "youtube_semana_texto",
    "medios":   TARGET_BASE / "medios_semana_texto",
}

# Directorio auxiliar de auditoría — NO forma parte de la salida canónica.
AUDIT_DIR = TARGET_BASE / "_auditoria_preprocessing"

SCRIPT_NAME = Path(__file__).name
SCRIPT_VERSION = "2.0.0-structural"

# ── Sección 3: Configuración histórica de limpieza textual ───────────────────
# [CONGELADO: COMPATIBILIDAD HISTÓRICA]
# Mapping de sustitución literal de acentos y caracteres especiales.
# Forma parte del contrato metodológico del corpus canónico.
# Prohibido agregar, eliminar o sustituir por unicodedata.normalize.
ACCENT_REPLACEMENTS: dict[str, str] = {
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

# ── Sección 4: Logging y auditoría ───────────────────────────────────────────

logger = logging.getLogger(__name__)


def setup_logging(audit_dir: Path) -> Path:
    """Configura logging dual: consola e archivo persistente en audit_dir.

    Devuelve la ruta al archivo de log creado.
    """
    audit_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = audit_dir / f"run_{timestamp}.log"

    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%Y-%m-%dT%H:%M:%S"

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    return log_path


def _file_meta(path: Path) -> dict[str, Any]:
    """Recopila metadatos básicos de un archivo: tamaño, mtime y hash MD5."""
    try:
        stat = path.stat()
        md5 = hashlib.md5(path.read_bytes()).hexdigest()
        return {
            "path": str(path),
            "size_bytes": stat.st_size,
            "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "md5": md5,
        }
    except OSError as exc:
        return {"path": str(path), "error": str(exc)}


def write_manifest(audit_dir: Path, manifest: dict[str, Any]) -> None:
    """Persiste el manifest JSON de la corrida en audit_dir."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    ts = manifest.get("run_timestamp", "unknown").replace(":", "").replace("-", "")
    manifest_path = audit_dir / f"manifest_{ts}.json"
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    logger.info("Manifest escrito: %s", manifest_path)


def write_audit_csv(audit_dir: Path, rows: list[dict[str, Any]], run_ts: str) -> None:
    """Persiste la tabla de auditoría por semana/fuente como CSV."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    ts_slug = run_ts.replace(":", "").replace("-", "")
    csv_path = audit_dir / f"auditoria_{ts_slug}.csv"
    fieldnames = [
        "run_timestamp",
        "week_dir",
        "prefix",
        "media_type",
        "n_files_detected",
        "input_files",
        "output_path",
        "status",
        "extracted_count",
        "unique_count",
        "missing_flag",
        "error_message",
        "notes",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Tabla de auditoría escrita: %s", csv_path)


# ── Sección 5: Funciones históricas de limpieza [CONGELADO] ──────────────────
# ADVERTENCIA: las funciones de esta sección no pueden modificarse.
# Su comportamiento define el contenido efectivo del corpus canónico.
# Cualquier cambio invalida la reproducibilidad histórica del modelo vigente.

def _replace_accents(text: str) -> str:
    """[CONGELADO] Sustituye literalmente acentos y caracteres especiales.

    Usa ACCENT_REPLACEMENTS carácter por carácter. No usar unicodedata ni
    ninguna otra estrategia de transliteración como sustituto.
    """
    for original, replacement in ACCENT_REPLACEMENTS.items():
        text = text.replace(original, replacement)
    return text


def normalize_facebook(text: str) -> str:
    """[CONGELADO] Normalización histórica para textos de Facebook.

    Pipeline exacto (orden y regex no negociables):
    1. Sustitución de acentos con _replace_accents
    2. lower()
    3. Remoción de menciones @\\w+
    4. Transformación de hashtags #(\\w+) -> " \\1 "
    5. Remoción de URLs (https?://, www., .com, .mx)
    6. Remoción de tokens literales: http, https, com, facebook, fb,
       me gusta, compartir
    7. Remoción de puntuación y dígitos vía string.punctuation+string.digits
    8. Eliminación de caracteres no ASCII (ord(char) >= 128)
    9. Colapso de espacios múltiples
    10. strip()
    """
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
    """[CONGELADO] Normalización histórica para textos de Twitter.

    Pipeline exacto (orden y regex no negociables):
    1. Sustitución de acentos con _replace_accents
    2. lower()
    3. Remoción de menciones @\\w+
    4. Transformación de hashtags #(\\w+) -> " \\1 "
    5. Remoción de URLs (https?://, www., .com, .mx)
    6. Remoción de tokens literales: http, https, com, rt, via
    7. Remoción de puntuación y dígitos
    8. Eliminación de caracteres no ASCII
    9. Colapso de espacios múltiples
    10. strip()

    Nota: Twitter conserva rt y via como tokens a remover (distintos de Facebook).
    """
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
    """[CONGELADO] Normalización histórica para comentarios de YouTube.

    Pipeline exacto (orden y regex no negociables):
    1. Sustitución de acentos con _replace_accents
    2. lower()
    3. Remoción de URLs https?://
    4. Remoción de token http
    5. Remoción de token https
    6. Remoción de token com
    7. Remoción de patrón \\.\\s*com\\b
    8. Remoción de puntuación y dígitos
    9. Eliminación de caracteres no ASCII
    10. Colapso de espacios múltiples
    11. strip()

    Nota: YouTube no remueve menciones ni hashtags (comportamiento histórico).
    No "corregir" esta asimetría respecto a Facebook/Twitter.
    """
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


# ── Sección 6: Utilidades generales de CSV [CONGELADO] ───────────────────────

def detect_dialect(path: Path) -> csv.Dialect:
    """[CONGELADO] Detecta el dialecto CSV leyendo los primeros 8 192 bytes.

    Usa csv.Sniffer con delimitadores ',' y ';'. Fallback a dialecto 'excel'.
    No cambiar tamaño de muestra, delimitadores ni fallback.
    """
    with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
        sample = handle.read(8192)
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;")
    except csv.Error:
        return csv.get_dialect("excel")


def read_dict_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """[CONGELADO] Lee un CSV como lista de dicts con claves y valores normalizados.

    Normalización de claves: strip().lower()
    Normalización de valores: (value or "").strip().strip('"')
    Encoding: utf-8-sig con errors=ignore.
    No sustituir por pandas ni cambiar esta normalización.
    """
    dialect = detect_dialect(path)
    with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        fieldnames = [field.strip().lower() for field in (reader.fieldnames or [])]
        rows = []
        for row in reader:
            normalized_row: dict[str, str] = {}
            for key, value in (row or {}).items():
                if key is None:
                    continue
                normalized_row[key.strip().lower()] = (value or "").strip().strip('"')
            rows.append(normalized_row)
    return rows, fieldnames


def dedupe_keep_order(items: list[str]) -> list[str]:
    """[CONGELADO] Elimina duplicados exactos preservando orden de primera aparición.

    No usar fuzzy matching, normalización adicional ni hash semántico.
    """
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def words_to_lines(items: list[str], words_per_line: int) -> list[str]:
    """[CONGELADO] Segmenta en bolsa de palabras de longitud fija.

    Toma todos los ítems, los une, los tokeniza por espacio y produce líneas
    de exactamente words_per_line palabras (la última puede ser más corta).

    CRÍTICO: Esta función define la forma efectiva del corpus canónico.
    No segmentar por oración, comentario, párrafo ni documento.
    No agregar sliding window, solapamiento ni padding.
    """
    words = " ".join(items).split()
    return [
        " ".join(words[index:index + words_per_line])
        for index in range(0, len(words), words_per_line)
        if words[index:index + words_per_line]
    ]


def write_lines(path: Path, lines: list[str]) -> None:
    """[CONGELADO] Escribe líneas en UTF-8, una por renglón, con salto final.

    No agregar encabezados, metadatos ni marcadores de auditoría al .txt.
    La salida canónica debe permanecer limpia.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        if lines:
            handle.write("\n".join(lines) + "\n")


# ── Sección 7: Descubrimiento de archivos [CONGELADO] ────────────────────────

def source_prefix(week_dir: Path) -> str:
    """[CONGELADO] Extrae el prefijo de semana dividiendo por '_semana_'.

    Comportamiento histórico: week_dir.name.split('_semana_', 1)[0].
    No usar parsing más sofisticado ni regex distinta.
    """
    return week_dir.name.split("_semana_", 1)[0]


def find_type_files(week_dir: Path, media_type: str) -> list[Path]:
    """[CONGELADO] Descubre archivos del tipo indicado dentro del directorio de semana.

    Patrones exactos por tipo (no modificar ni expandir):
      facebook: ['*_facebook.csv', '*facebook*.csv']
      twitter:  ['*_twitter.csv',  '*twitter*.csv']
      youtube:  ['*_youtube.csv',  '*youtube*.csv']
      medios:   ['*_medios.txt',   '*medios*.txt']

    Itera patrones en ese orden. Usa sorted por patrón. Evita duplicados con seen.
    """
    patterns: dict[str, list[str]] = {
        "facebook": ["*_facebook.csv", "*facebook*.csv"],
        "twitter":  ["*_twitter.csv",  "*twitter*.csv"],
        "youtube":  ["*_youtube.csv",  "*youtube*.csv"],
        "medios":   ["*_medios.txt",   "*medios*.txt"],
    }
    matches: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns[media_type]:
        for path in sorted(week_dir.glob(pattern)):
            if path not in seen and path.is_file():
                seen.add(path)
                matches.append(path)
    return matches


# ── Sección 8: Procesamiento por fuente [CONGELADO EN LÓGICA CANÓNICA] ───────

def process_facebook(files: list[Path], output_path: Path) -> tuple[int, int]:
    """[CONGELADO] Procesa archivos CSV de Facebook y escribe corpus canónico.

    Columna de texto buscada en este orden: 'texto', 'message'.
    Si no existe ninguna, el archivo se omite sin error.
    Umbral de inclusión: len(cleaned.split()) >= 2
    Palabras por línea: 35 (no modificar).
    Retorna (extracted, unique_count).
    """
    texts: list[str] = []
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
    """[CONGELADO] Procesa archivos CSV/texto de Twitter y escribe corpus canónico.

    Columna de texto buscada en este orden: 'text', 'tweet_content'.
    Si no existe columna válida, activa fallback: leer archivo línea por línea.
    Umbral de inclusión: len(cleaned.split()) >= 3
    Palabras por línea: 25 (no modificar).
    Retorna (extracted, unique_count).
    """
    texts: list[str] = []
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
    """[CONGELADO] Procesa archivos CSV/texto de YouTube y escribe corpus canónico.

    Columna de texto: 'comment_text'.
    Si no existe, activa fallback: leer archivo línea por línea.
    Umbral de inclusión: if cleaned (sin mínimo de palabras, diferente a fb/tw).
    Palabras por línea: 30 (no modificar).
    Retorna (extracted, unique_count).
    """
    texts: list[str] = []
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
    """[CONGELADO] Copia el primer archivo de medios como corpus canónico.

    Comportamiento histórico: shutil.copy2(files[0], output_path).
    No concatenar, seleccionar el "mejor", combinar ni reordenar.
    Si hay más de un archivo, los adicionales se ignoran en la salida canónica
    (el audit los registra como nota).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(files[0], output_path)


# ── Sección 9: Orquestación principal ────────────────────────────────────────

def _process_media_type(
    media_type: str,
    files: list[Path],
    output: Path,
    run_ts: str,
    week_dir: Path,
    prefix: str,
    audit_rows: list[dict[str, Any]],
) -> None:
    """Ejecuta el procesamiento de un tipo de medio con manejo de errores y auditoría.

    Preserva el comportamiento canónico de las funciones process_*. Cualquier
    excepción es capturada, registrada y anotada en audit_rows sin abortar el
    procesamiento de otras semanas/fuentes.
    """
    input_meta = [_file_meta(f) for f in files]
    audit_row: dict[str, Any] = {
        "run_timestamp": run_ts,
        "week_dir": str(week_dir),
        "prefix": prefix,
        "media_type": media_type,
        "n_files_detected": len(files),
        "input_files": "; ".join(str(f) for f in files),
        "output_path": str(output),
        "status": "",
        "extracted_count": None,
        "unique_count": None,
        "missing_flag": False,
        "error_message": "",
        "notes": "",
    }

    try:
        if media_type == "facebook":
            extracted, unique = process_facebook(files, output)
            audit_row["extracted_count"] = extracted
            audit_row["unique_count"] = unique
            audit_row["status"] = "ok"
            logger.info(
                "  facebook -> %s | extraidos:%d unicos:%d",
                output.name, extracted, unique,
            )
            print(f"  facebook -> {output.name} | extraidos:{extracted} unicos:{unique}")

        elif media_type == "twitter":
            extracted, unique = process_twitter(files, output)
            audit_row["extracted_count"] = extracted
            audit_row["unique_count"] = unique
            audit_row["status"] = "ok"
            logger.info(
                "  twitter -> %s | extraidos:%d unicos:%d",
                output.name, extracted, unique,
            )
            print(f"  twitter -> {output.name} | extraidos:{extracted} unicos:{unique}")

        elif media_type == "youtube":
            extracted, unique = process_youtube(files, output)
            audit_row["extracted_count"] = extracted
            audit_row["unique_count"] = unique
            audit_row["status"] = "ok"
            logger.info(
                "  youtube -> %s | extraidos:%d unicos:%d",
                output.name, extracted, unique,
            )
            print(f"  youtube -> {output.name} | extraidos:{extracted} unicos:{unique}")

        elif media_type == "medios":
            if len(files) > 1:
                audit_row["notes"] = (
                    f"Multiples archivos detectados ({len(files)}); "
                    f"se copia solo files[0]: {files[0].name}"
                )
                logger.warning(
                    "  medios: %d archivos detectados; se copia solo files[0]: %s",
                    len(files), files[0].name,
                )
            process_medios(files, output)
            audit_row["status"] = "ok"
            logger.info("  medios -> %s | copiado", output.name)
            print(f"  medios -> {output.name} | copiado")

        # Metadatos de salida (auditoría, no afecta corpus)
        if output.exists():
            out_meta = _file_meta(output)
            audit_row["notes"] = (
                (audit_row.get("notes") or "")
                + f" | output_md5={out_meta.get('md5', '?')} "
                  f"size={out_meta.get('size_bytes', '?')}"
            ).strip(" | ")

    except Exception as exc:  # noqa: BLE001
        audit_row["status"] = "error"
        audit_row["error_message"] = str(exc)
        logger.exception("  ERROR procesando %s/%s: %s", week_dir.name, media_type, exc)
        print(f"  ERROR procesando {week_dir.name}/{media_type}: {exc}")

    audit_rows.append(audit_row)


def main() -> None:
    """Orquesta la producción semanal del corpus textual por fuente.

    Flujo:
    1. Valida SOURCE_BASE
    2. Crea directorios canónicos y de auditoría
    3. Descubre semanas
    4. Procesa cada semana/fuente con manejo de errores
    5. Persiste manifest JSON y tabla CSV de auditoría
    6. Imprime resumen

    La lógica canónica de cada fuente está encapsulada en process_*.
    Esta función solo orquesta, valida y audita.
    """
    run_ts = datetime.now(timezone.utc).isoformat()

    # Validación estructural: SOURCE_BASE debe existir antes de proceder
    if not SOURCE_BASE.exists():
        print(f"ERROR: SOURCE_BASE no existe: {SOURCE_BASE}")
        raise SystemExit(1)
    if not SOURCE_BASE.is_dir():
        print(f"ERROR: SOURCE_BASE no es un directorio: {SOURCE_BASE}")
        raise SystemExit(1)

    # Setup logging (requiere AUDIT_DIR, que se crea aquí)
    try:
        log_path = setup_logging(AUDIT_DIR)
    except OSError as exc:
        print(f"ADVERTENCIA: no se pudo configurar logging a archivo: {exc}")
        log_path = None
        logging.basicConfig(level=logging.DEBUG)

    logger.info("=" * 70)
    logger.info("Inicio de corrida — %s v%s", SCRIPT_NAME, SCRIPT_VERSION)
    logger.info("run_timestamp: %s", run_ts)
    logger.info("SOURCE_BASE:   %s", SOURCE_BASE)
    logger.info("TARGET_BASE:   %s", TARGET_BASE)
    logger.info("AUDIT_DIR:     %s", AUDIT_DIR)

    # Crear directorios canónicos de salida
    for media_type, target_dir in TARGET_DIRS.items():
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error("No se pudo crear TARGET_DIR para %s: %s", media_type, exc)
            raise SystemExit(1) from exc

    # Descubrir semanas
    try:
        weeks = sorted(path for path in SOURCE_BASE.iterdir() if path.is_dir())
    except OSError as exc:
        logger.error("No se pudo listar SOURCE_BASE: %s", exc)
        raise SystemExit(1) from exc

    logger.info("Semanas detectadas: %d", len(weeks))

    summary: dict[str, int] = {"facebook": 0, "twitter": 0, "youtube": 0, "medios": 0}
    missing: list[tuple[str, str]] = []
    audit_rows: list[dict[str, Any]] = []
    error_count = 0

    for week_dir in weeks:
        prefix = source_prefix(week_dir)
        logger.info("\n[%s] %s", prefix, week_dir.name)
        print(f"\n[{prefix}] {week_dir.name}")

        for media_type in ("facebook", "twitter", "youtube", "medios"):
            files = find_type_files(week_dir, media_type)
            logger.debug(
                "  %s: %d archivo(s) encontrado(s): %s",
                media_type,
                len(files),
                [f.name for f in files],
            )

            if files:
                output = TARGET_DIRS[media_type] / f"{prefix}_{media_type}.txt"
                _process_media_type(
                    media_type, files, output, run_ts, week_dir, prefix, audit_rows
                )
                # Contar solo si el status en el último audit_row es ok
                if audit_rows and audit_rows[-1].get("status") == "ok":
                    summary[media_type] += 1
                else:
                    error_count += 1
            else:
                missing.append((week_dir.name, media_type))
                logger.warning("  %s -> faltante", media_type)
                print(f"  {media_type} -> faltante")
                audit_rows.append({
                    "run_timestamp": run_ts,
                    "week_dir": str(week_dir),
                    "prefix": prefix,
                    "media_type": media_type,
                    "n_files_detected": 0,
                    "input_files": "",
                    "output_path": "",
                    "status": "missing",
                    "extracted_count": None,
                    "unique_count": None,
                    "missing_flag": True,
                    "error_message": "",
                    "notes": "",
                })

    # Resumen (preserva comportamiento histórico de print)
    print("\nResumen")
    logger.info("\nResumen")
    for media_type in ("facebook", "twitter", "youtube", "medios"):
        print(f"  {media_type}: {summary[media_type]}")
        logger.info("  %s: %d", media_type, summary[media_type])
    if missing:
        print(f"  faltantes: {len(missing)}")
        logger.info("  faltantes: %d", len(missing))
        for week_name, media_type in missing:
            print(f"    {week_name}: {media_type}")
            logger.info("    %s: %s", week_name, media_type)
    else:
        print("  faltantes: 0")
        logger.info("  faltantes: 0")

    # ── Persistencia de artefactos de auditoría ───────────────────────────────
    missing_by_media: dict[str, int] = {
        mt: sum(1 for _, m in missing if m == mt)
        for mt in ("facebook", "twitter", "youtube", "medios")
    }
    total_outputs = sum(summary.values())
    total_weeks_processed = len(weeks)

    manifest: dict[str, Any] = {
        "run_timestamp": run_ts,
        "script_name": SCRIPT_NAME,
        "script_version": SCRIPT_VERSION,
        "source_base": str(SOURCE_BASE),
        "target_base": str(TARGET_BASE),
        "log_path": str(log_path) if log_path else None,
        "total_weeks_detected": len(weeks),
        "total_weeks_processed": len(weeks),
        "total_outputs_generated": total_outputs,
        "total_missing_by_media": missing_by_media,
        "total_errors": error_count,
        "compatibility_statement": (
            "Lógica textual histórica preservada sin alteración. "
            "Intervención exclusivamente estructural (v2.0.0-structural). "
            "Salida canónica no rediseñada."
        ),
    }

    try:
        write_manifest(AUDIT_DIR, manifest)
        write_audit_csv(AUDIT_DIR, audit_rows, run_ts)
    except OSError as exc:
        logger.error("No se pudieron escribir artefactos de auditoría: %s", exc)

    logger.info("=" * 70)
    logger.info("Corrida completada — outputs: %d | faltantes: %d | errores: %d",
                total_outputs, len(missing), error_count)


if __name__ == "__main__":
    main()
