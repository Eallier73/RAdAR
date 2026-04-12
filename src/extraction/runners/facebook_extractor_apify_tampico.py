#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   📘 FACEBOOK: URLs (SERPER) + COMENTARIOS (APIFY)                       ║
║                                                                           ║
║   Fase 1: Busca URLs de posts vía Google (Serper.dev)                    ║
║   Fase 2: Baja comentarios de esos posts vía Apify                       ║
║                                                                           ║
║  Ejemplos:                                                                ║
║                                                                           ║
║  # Pipeline completo (URLs + comentarios):                                ║
║  python apify_comentarios.py \                                           ║
║    --since 2026-03-01 --before 2026-03-12                                 ║
║                                                                           ║
║  # Solo URLs (sin comentarios):                                           ║
║  python apify_comentarios.py --solo-urls \                               ║
║    --since 2026-03-01 --before 2026-03-12                                 ║
║                                                                           ║
║  # Solo comentarios (con CSV de URLs existente):                          ║
║  python apify_comentarios.py --solo-comentarios \                        ║
║    --input-csv /ruta/al/urls_TampicoGob_monicavtampico_...csv            ║
║                                                                           ║
║  # Con otras páginas:                                                     ║
║  python apify_comentarios.py \                                           ║
║    --pages GobiernoCDMX ClaraBrugadaM \                                  ║
║    --since 2026-03-01 --before 2026-03-12                                 ║
║                                                                           ║
║  Requisitos:                                                              ║
║    pip install apify-client pandas requests                               ║
║                                                                           ║
║  Config:                                                                  ║
║    export APIFY_TOKEN="tu_token"  (o --token)                             ║
║    Token en: https://console.apify.com/settings/integrations              ║
║                                                                           ║
║  👨‍💻 Autor: Emilio                                                        ║
║  📅 Fecha: Marzo 2026                                                     ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import csv
import getpass
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Set
from urllib.parse import parse_qs, unquote, urlencode, urlparse, urlunparse

import pandas as pd
import requests
from apify_client import ApifyClient


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

SERPER_API_KEY       = "755d127f6d9ac1ff41a7cb9244699509c75fd70c"
SERPER_ENDPOINT      = "https://google.serper.dev/search"
PAUSA_ENTRE_REQUESTS = 1.0

ACTOR_COMMENTS = "apify/facebook-comments-scraper"

DEFAULT_PAGES = ["TampicoGob", "monicavtampico"]
DEFAULT_OUTPUT_BASE_DIR = "/home/emilio/Documentos/Datos_Radar/Facebook"

POST_PATH_MARKERS = (
    "/posts/", "/permalink/", "/photos/", "/videos/",
    "/reel/", "/reels/", "/watch/",
)
MEDIA_PATH_MARKERS = ("/photos/", "/videos/", "/reel/", "/reels/", "/watch/")
PHOTO_MAX_RATIO = 0.20
DEFAULT_STRATIFIED_RATIOS = {"post": 0.4, "photo": 0.3, "video": 0.3}


# ============================================================================
# NORMALIZACIÓN DE URLs (de tu scraper unificado)
# ============================================================================

def unwrap_facebook_redirect(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host in {"l.facebook.com", "lm.facebook.com"}:
        target = parse_qs(parsed.query).get("u", [None])[0]
        if target:
            return unquote(target)
    return url


def normalize_url(url: str) -> str:
    url = unwrap_facebook_redirect(url)
    parsed = urlparse(url.strip())
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    if netloc.startswith("m."):
        netloc = netloc[2:]

    path = parsed.path.rstrip("/")
    path_l = path.lower()
    kept_query = {}
    parsed_query = parse_qs(parsed.query)

    if path_l == "/watch":
        if parsed_query.get("v"):
            kept_query["v"] = parsed_query["v"][0]
    elif path_l == "/story.php":
        if parsed_query.get("story_fbid"):
            kept_query["story_fbid"] = parsed_query["story_fbid"][0]
        if parsed_query.get("id"):
            kept_query["id"] = parsed_query["id"][0]
    elif path_l == "/photo.php":
        if parsed_query.get("fbid"):
            kept_query["fbid"] = parsed_query["fbid"][0]

    query = urlencode(kept_query, doseq=False)
    return urlunparse(("https", netloc, path, "", query, ""))


def is_post_url(url: str, page_handle: str) -> bool:
    parsed = urlparse(url)
    if "facebook.com" not in parsed.netloc.lower():
        return False
    path_l = parsed.path.lower()
    handle_l = page_handle.lower()
    query = parse_qs(parsed.query)

    if f"/{handle_l}/" not in path_l and not (path_l == "/watch" and "v" in query):
        return False
    if any(marker in path_l for marker in POST_PATH_MARKERS):
        return True
    if path_l == "/watch" and "v" in query:
        return True
    if path_l == "/story.php" and "story_fbid" in query and "id" in query:
        return True
    return False


def clasificar_url_sampling(url: str) -> str:
    path_l = urlparse(url).path.lower()
    if "/photos/" in path_l or path_l == "/photo.php":
        return "photo"
    if any(marker in path_l for marker in MEDIA_PATH_MARKERS) or path_l == "/watch":
        return "video"
    return "post"


def contar_urls_por_tipo(urls: List[str]) -> dict[str, int]:
    conteo = {"post": 0, "photo": 0, "video": 0}
    for url in urls:
        conteo[clasificar_url_sampling(url)] += 1
    return conteo


def _sample_hybrid(urls: List[str], sample_size: int, seed: int, min_per_stratum: int = 0) -> List[str]:
    rng = random.Random(seed)
    grupos = {"post": [], "photo": [], "video": []}
    for url in urls:
        grupos[clasificar_url_sampling(url)].append(url)
    for key in grupos:
        rng.shuffle(grupos[key])

    total = len(urls)
    disponibles = {key: len(values) for key, values in grupos.items()}
    ratios = {key: disponibles[key] / total for key in grupos}

    excedente = max(0.0, ratios["photo"] - PHOTO_MAX_RATIO)
    ratios["photo"] = min(ratios["photo"], PHOTO_MAX_RATIO)
    ratios["post"] += excedente

    asignacion = {
        key: min(round(sample_size * ratios[key]), disponibles[key])
        for key in grupos
    }
    for key in grupos:
        if disponibles[key] > 0:
            asignacion[key] = max(asignacion[key], min(min_per_stratum, disponibles[key]))

    total_asignado = sum(asignacion.values())
    while total_asignado > sample_size:
        candidatos = [
            key for key in grupos
            if asignacion[key] > min(min_per_stratum, disponibles[key])
        ]
        if not candidatos:
            break
        key = max(candidatos, key=lambda item: asignacion[item])
        asignacion[key] -= 1
        total_asignado -= 1

    while total_asignado < sample_size:
        candidatos = [key for key in grupos if asignacion[key] < disponibles[key]]
        if not candidatos:
            break
        key = max(candidatos, key=lambda item: disponibles[item] - asignacion[item])
        asignacion[key] += 1
        total_asignado += 1

    sampled = []
    for key in ("post", "photo", "video"):
        n = asignacion.get(key, 0)
        if n > 0:
            sampled.extend(grupos[key][:n])
    rng.shuffle(sampled)
    return sampled


def _sample_stratified(urls: List[str], sample_size: int, seed: int, min_per_stratum: int = 0) -> List[str]:
    rng = random.Random(seed)
    grupos = {"post": [], "photo": [], "video": []}
    for url in urls:
        grupos[clasificar_url_sampling(url)].append(url)
    for key in grupos:
        rng.shuffle(grupos[key])

    disponibles = {key: len(values) for key, values in grupos.items()}
    asignacion = {
        key: min(int(sample_size * DEFAULT_STRATIFIED_RATIOS[key]), disponibles[key])
        for key in grupos
    }

    min_req = {}
    for key in grupos:
        min_req[key] = min(min_per_stratum, disponibles[key]) if disponibles[key] > 0 else 0
        if asignacion[key] < min_req[key]:
            asignacion[key] = min_req[key]

    total_asignado = sum(asignacion.values())
    while total_asignado > sample_size:
        candidatos = [key for key in grupos if asignacion[key] > min_req[key]]
        if not candidatos:
            break
        key = max(candidatos, key=lambda item: asignacion[item] - min_req.get(item, 0))
        asignacion[key] -= 1
        total_asignado -= 1

    while total_asignado < sample_size:
        candidatos = [key for key in grupos if asignacion[key] < disponibles[key]]
        if not candidatos:
            break
        key = max(candidatos, key=lambda item: disponibles[item] - asignacion[item])
        asignacion[key] += 1
        total_asignado += 1

    sampled = []
    for key in ("post", "photo", "video"):
        n = asignacion.get(key, 0)
        if n > 0:
            sampled.extend(grupos[key][:n])
    rng.shuffle(sampled)
    return sampled


def aplicar_sampling_urls(
    urls: List[str],
    strategy: str,
    size: int | None,
    seed: int,
    min_per_stratum: int = 0,
) -> List[str]:
    if not urls or size is None or size <= 0 or size >= len(urls):
        return urls
    if min_per_stratum < 0:
        min_per_stratum = 0
    if strategy == "none":
        return urls
    if strategy == "random":
        rng = random.Random(seed)
        return rng.sample(urls, size)
    if strategy == "hybrid":
        return _sample_hybrid(urls, size, seed, min_per_stratum)
    return _sample_stratified(urls, size, seed, min_per_stratum)


# ============================================================================
# FASE 1: BÚSQUEDA DE URLs VÍA SERPER.DEV
# ============================================================================

@dataclass
class SearchResultRow:
    page_handle: str
    query: str
    google_page: int
    url: str


def build_query(page_handle: str, since: str, before: str) -> str:
    return f"site:facebook.com/{page_handle} after:{since} before:{before}"


def search_page_serper(query: str, page: int) -> list:
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "hl": "es", "gl": "mx", "num": 10, "page": page}
    resp = requests.post(SERPER_ENDPOINT, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json().get("organic", [])


def run_url_search(page_handle: str, since: str, before: str, max_pages: int) -> List[SearchResultRow]:
    query = build_query(page_handle, since, before)
    print(f"\n  Query: {query}")

    rows: List[SearchResultRow] = []
    seen: Set[str] = set()
    empty_pages = 0

    for i in range(max_pages):
        page_num = i + 1
        print(f"    Google page {page_num}/{max_pages}", end=" → ")

        try:
            items = search_page_serper(query, page_num)
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                print("⚠ Límite alcanzado.")
            else:
                print(f"⚠ HTTP {e}")
            break
        except Exception as e:
            print(f"⚠ Error: {e}")
            break

        if not items:
            print("sin resultados")
            empty_pages += 1
            if empty_pages >= 2:
                break
            continue

        found = 0
        for item in items:
            raw_url = item.get("link", "")
            if not raw_url:
                continue
            normalized = normalize_url(raw_url)
            if not is_post_url(normalized, page_handle):
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            rows.append(SearchResultRow(page_handle, query, page_num, normalized))
            found += 1

        print(f"{found} URLs nuevas")
        empty_pages = 0 if found > 0 else empty_pages + 1
        if empty_pages >= 2:
            break
        time.sleep(PAUSA_ENTRE_REQUESTS)

    print(f"  Total URLs para {page_handle}: {len(rows)}")
    return rows


def fase1_buscar_urls(pages: List[str], since: str, before: str,
                      max_pages: int, output_dir: str) -> str:
    """Busca URLs y guarda CSV. Retorna path del CSV generado."""
    print("\n" + "=" * 70)
    print("🔍 FASE 1: BÚSQUEDA DE URLs VÍA GOOGLE (SERPER.DEV)")
    print("=" * 70)

    all_rows: List[SearchResultRow] = []
    for handle in pages:
        all_rows.extend(run_url_search(handle.strip(), since, before, max_pages))

    safe_pages = "_".join(p.strip() for p in pages).replace("/", "_")
    prefix = f"urls_{safe_pages}_{since}_{before}"
    csv_path = os.path.join(output_dir, f"{prefix}.csv")
    txt_path = os.path.join(output_dir, f"{prefix}.txt")

    os.makedirs(output_dir, exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["page_handle", "query", "google_page", "url"])
        writer.writeheader()
        for row in all_rows:
            writer.writerow({
                "page_handle": row.page_handle, "query": row.query,
                "google_page": row.google_page, "url": row.url,
            })

    with open(txt_path, "w", encoding="utf-8") as f:
        for row in all_rows:
            f.write(f"{row.url}\n")

    print(f"\n  ✅ CSV URLs: {csv_path}")
    print(f"  ✅ TXT URLs: {txt_path}")
    print(f"  📊 Total URLs: {len(all_rows)}")
    return csv_path


# ============================================================================
# LECTURA DE URLs (para --solo-comentarios)
# ============================================================================

def leer_urls_csv(input_csv: str) -> List[str]:
    """Lee URLs del CSV generado por Fase 1."""
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"No existe: {input_csv}")

    urls = []
    vistas = set()

    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        campos = reader.fieldnames or []

        col_url = None
        for candidato in ["url", "post_url", "URL", "link"]:
            if candidato in campos:
                col_url = candidato
                break

        if col_url is None:
            raise ValueError(
                f"CSV sin columna de URL reconocida. Columnas: {campos}"
            )

        for row in reader:
            raw = (row.get(col_url) or "").strip()
            if not raw or raw in vistas:
                continue
            if "facebook.com" not in raw.lower():
                continue
            vistas.add(raw)
            urls.append(raw)

    return urls


# ============================================================================
# FASE 2: COMENTARIOS VÍA APIFY
# ============================================================================

def obtener_comentarios_batch(
    client: ApifyClient,
    post_urls: List[str],
    max_comments: int,
    since: Optional[str] = None,
) -> list:
    """Corre facebook-comments-scraper para un batch de URLs."""
    start_urls = [{"url": url} for url in post_urls]

    run_input = {
        "startUrls": start_urls,
        "resultsPerPost": max_comments,
        "includeReplies": True,
    }
    if since:
        run_input["onlyCommentsNewerThan"] = since

    try:
        run = client.actor(ACTOR_COMMENTS).call(run_input=run_input)
    except Exception as e:
        print(f"     ❌ Error al correr actor: {e}")
        return []

    if run is None:
        print("     ❌ El actor no retornó resultado.")
        return []

    status = run.get("status", "UNKNOWN")
    costo = run.get("usageTotalUsd", 0)
    print(f"     Status: {status} | Costo: ${costo:.4f} USD")

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        print("     ❌ Sin dataset.")
        return []

    items = list(client.dataset(dataset_id).iterate_items())
    print(f"     ✅ {len(items)} comentarios")
    return items


def procesar_items_comentarios(items: list) -> List[dict]:
    """Extrae campos relevantes de los items del actor."""
    filas = []
    vistos = set()

    for item in items:
        texto = (
            item.get("text")
            or item.get("commentText")
            or item.get("body")
            or ""
        ).strip()

        if not texto or len(texto) < 5:
            continue

        post_url = item.get("postUrl") or item.get("facebookUrl") or ""
        clave = (post_url, texto[:150])
        if clave in vistos:
            continue
        vistos.add(clave)

        fila = {
            "post_url": post_url,
            "comentario_texto": texto,
            "autor": (
                item.get("profileName")
                or item.get("authorName")
                or item.get("userName")
                or ""
            ),
            "fecha_comentario": (
                item.get("date")
                or item.get("timestamp")
                or item.get("commentDate")
                or ""
            ),
            "likes_comentario": (
                item.get("likesCount")
                or item.get("likes")
                or item.get("reactionsCount")
                or 0
            ),
            "es_respuesta": item.get("isReply", False),
            "url_comentario": item.get("url") or item.get("commentUrl") or "",
        }
        filas.append(fila)

    return filas


def fase2_comentarios(
    client: ApifyClient,
    urls: List[str],
    max_comments: int,
    since: Optional[str],
    output_dir: str,
    input_csv: str,
    batch_size: int,
):
    """Fase 2: baja comentarios vía Apify y guarda CSVs."""
    print("\n" + "=" * 70)
    print("💬 FASE 2: COMENTARIOS VÍA APIFY")
    print("=" * 70)

    print(f"\n  📥 URLs cargadas: {len(urls)}")
    print(f"  💬 Máx comentarios por post: {max_comments}")
    print(f"  📦 Batch size: {batch_size}")
    print(f"  📅 Desde: {since or 'sin filtro'}")

    todas_las_filas = []
    total_batches = (len(urls) + batch_size - 1) // batch_size

    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]
        batch_num = (i // batch_size) + 1

        print(f"\n  ─── Batch {batch_num}/{total_batches} "
              f"({len(batch)} posts) ───")

        items = obtener_comentarios_batch(client, batch, max_comments, since)
        filas = procesar_items_comentarios(items)
        todas_las_filas.extend(filas)

        print(f"     📊 Acumulado: {len(todas_las_filas)} comentarios")

        if i + batch_size < len(urls):
            pausa = 5
            print(f"     ⏸️  Pausa {pausa}s...")
            time.sleep(pausa)

    # ── Guardar CSVs ──
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(input_csv))[0]
    base_name = base_name.replace("urls_", "").replace("posts_", "")

    # CSV de comentarios
    csv_comentarios = os.path.join(output_dir, f"comentarios_{base_name}.csv")
    df_comments = pd.DataFrame(todas_las_filas)
    df_comments.to_csv(csv_comentarios, index=False, encoding="utf-8-sig")

    # CSV mixto (formato compatible con scraper unificado)
    filas_mixtas = []
    for url in urls:
        filas_mixtas.append({
            "tipo": "POST",
            "url": url,
            "post_url_padre": "",
            "fecha": "",
            "texto": "",
            "num_comentarios": "",
        })
    for _, row in df_comments.iterrows():
        filas_mixtas.append({
            "tipo": "COMENTARIO",
            "url": row.get("url_comentario", ""),
            "post_url_padre": row.get("post_url", ""),
            "fecha": row.get("fecha_comentario", ""),
            "texto": row.get("comentario_texto", ""),
            "num_comentarios": "",
        })

    csv_mixto = os.path.join(output_dir, f"posts_comentarios_{base_name}.csv")
    pd.DataFrame(filas_mixtas).to_csv(csv_mixto, index=False, encoding="utf-8-sig")

    # ── Resumen ──
    print("\n" + "=" * 70)
    print("✅ DESCARGA COMPLETADA")
    print("=" * 70)
    print(f"  📊 Posts procesados:  {len(urls)}")
    print(f"  💬 Comentarios:       {len(df_comments)}")
    print(f"  📁 Comentarios:       {csv_comentarios}")
    print(f"  📁 Mixto (post+com):  {csv_mixto}")

    if not df_comments.empty:
        por_post = df_comments.groupby("post_url").size()
        print(f"  📈 Promedio por post: {por_post.mean():.1f}")
        print(f"  📈 Máximo en un post: {por_post.max()}")


# ============================================================================
# CLI
# ============================================================================

def valid_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Fecha inválida '{value}', usa YYYY-MM-DD")
    return value


def _mask_secret(value: str) -> str:
    if not value:
        return "sin configurar"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _prompt_texto(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    valor = input(f"{prompt}{suffix}: ").strip()
    return valor or default


def _prompt_fecha(prompt: str, default: str) -> str:
    while True:
        valor = _prompt_texto(prompt, default)
        try:
            return valid_date(valor)
        except argparse.ArgumentTypeError as exc:
            print(f"❌ {exc}")


def _prompt_entero(prompt: str, default: int, minimo: int | None = None) -> int:
    while True:
        valor = _prompt_texto(prompt, str(default))
        try:
            numero = int(valor)
        except ValueError:
            print("❌ Debe ser un entero.")
            continue
        if minimo is not None and numero < minimo:
            print(f"❌ Debe ser mayor o igual a {minimo}.")
            continue
        return numero


def _default_since() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _default_before() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def configurar_interactivo(args: argparse.Namespace, run_fase2: bool) -> argparse.Namespace:
    if not sys.stdin.isatty() or args.no_prompt:
        return args

    print("\n" + "=" * 70)
    print("⚙️ CONFIGURACIÓN INTERACTIVA")
    print("=" * 70)

    args.since = _prompt_fecha("📅 Fecha inicio (since)", args.since or _default_since())
    args.before = _prompt_fecha("📅 Fecha fin (before)", args.before or _default_before())

    if run_fase2:
        actual = _mask_secret(args.token or os.environ.get("APIFY_TOKEN", ""))
        token = getpass.getpass(
            f"🔑 Token de Apify [ENTER para usar actual {actual}]: "
        ).strip()
        if token:
            args.token = token

        default_mode = "s" if args.sample_size and args.sample_size > 0 else "t"
        while True:
            modo = input(
                "📦 ¿Quieres bajar todo o usar sampling? [t=todo / s=sampling]"
                f" [{default_mode}]: "
            ).strip().lower()
            if not modo:
                modo = default_mode

            if modo in {"t", "todo"}:
                args.sample_strategy = "none"
                args.sample_size = 0
                break

            if modo in {"s", "sampling", "muestra"}:
                estrategia_default = args.sample_strategy if args.sample_strategy != "none" else "hybrid"
                while True:
                    estrategia = _prompt_texto(
                        "🧪 Estrategia de sampling (random/stratified/hybrid)",
                        estrategia_default,
                    ).lower()
                    if estrategia in {"random", "stratified", "hybrid"}:
                        args.sample_strategy = estrategia
                        break
                    print("❌ Estrategia inválida. Usa random, stratified o hybrid.")

                args.sample_size = _prompt_entero("🔢 Tamaño de muestra", args.sample_size or 25, minimo=1)
                args.sample_seed = _prompt_entero("🎲 Semilla", args.sample_seed, minimo=0)
                args.sample_min_per_stratum = _prompt_entero(
                    "📚 Mínimo por estrato",
                    args.sample_min_per_stratum,
                    minimo=0,
                )
                break

            print("❌ Responde 't' para todo o 's' para sampling.")

    print("\n📋 Resumen de configuración")
    print(f"  📅 Rango: {args.since} → {args.before}")
    if run_fase2:
        print(f"  🔑 Apify: {_mask_secret(args.token or os.environ.get('APIFY_TOKEN', ''))}")
        if args.sample_size and args.sample_size > 0:
            print(
                f"  🧪 Sampling: {args.sample_strategy} | size={args.sample_size} | "
                f"seed={args.sample_seed} | min/estrato={args.sample_min_per_stratum}"
            )
        else:
            print("  📦 Descarga: todo lo encontrado")

    return args


def parse_args():
    parser = argparse.ArgumentParser(
        description="Facebook: URLs (Serper) + Comentarios (Apify)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Pipeline completo (URLs + comentarios):
  python apify_comentarios.py \\
    --since 2026-03-01 --before 2026-03-12

  # Con otras páginas:
  python apify_comentarios.py \\
    --pages GobiernoCDMX ClaraBrugadaM \\
    --since 2026-03-01 --before 2026-03-12

  # Solo buscar URLs (sin comentarios):
  python apify_comentarios.py --solo-urls \\
    --since 2026-03-01 --before 2026-03-12

  # Solo comentarios (con CSV existente):
  python apify_comentarios.py --solo-comentarios \\
    --input-csv /ruta/al/urls_TampicoGob_monicavtampico_2026-03-01_2026-03-12.csv
        """,
    )

    # Modo
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--solo-urls", action="store_true",
                      help="Solo Fase 1: buscar URLs y guardar CSV")
    mode.add_argument("--solo-comentarios", action="store_true",
                      help="Solo Fase 2: bajar comentarios de CSV existente")

    # Fase 1
    parser.add_argument("--pages", nargs="+", default=DEFAULT_PAGES,
                        help=f"Handles de páginas (default: {' '.join(DEFAULT_PAGES)})")
    parser.add_argument("--since", type=valid_date, default=None,
                        help="Fecha inicio YYYY-MM-DD")
    parser.add_argument("--before", type=valid_date, default=None,
                        help="Fecha fin YYYY-MM-DD")
    parser.add_argument("--max-google-pages", type=int, default=8,
                        help="Páginas de Google por handle (default: 8)")

    # Fase 2
    parser.add_argument("--input-csv", default=None,
                        help="CSV con URLs (para --solo-comentarios)")
    parser.add_argument("--max-comments", type=int, default=200,
                        help="Máx comentarios por post (default: 200)")
    parser.add_argument("--max-urls", type=int, default=None,
                        help="Limitar número de URLs a procesar")
    parser.add_argument("--batch-size", type=int, default=25,
                        help="URLs por batch en Apify (default: 25)")
    parser.add_argument("--sample-strategy", choices=["none", "random", "stratified", "hybrid"],
                        default="hybrid", help="Estrategia de sampling para URLs")
    parser.add_argument("--sample-size", type=int, default=25,
                        help="Tamaño de muestra para URLs")
    parser.add_argument("--sample-seed", type=int, default=42,
                        help="Semilla para muestreo reproducible")
    parser.add_argument("--sample-min-per-stratum", type=int, default=5,
                        help="Mínimo por estrato")

    # General
    parser.add_argument("--token", default=None,
                        help="Apify API token (o variable APIFY_TOKEN)")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_BASE_DIR,
                        help=f"Directorio base de salida (default: {DEFAULT_OUTPUT_BASE_DIR})")
    parser.add_argument("--no-prompt", action="store_true",
                        help="No abrir configuración interactiva al inicio")

    return parser.parse_args()


def main():
    args = parse_args()

    run_fase1 = not args.solo_comentarios
    run_fase2 = not args.solo_urls
    args = configurar_interactivo(args, run_fase2)

    if not args.since or not args.before:
        print("❌ Debes definir --since y --before.")
        sys.exit(1)
    if datetime.strptime(args.since, "%Y-%m-%d") > datetime.strptime(args.before, "%Y-%m-%d"):
        print("❌ --since no puede ser mayor que --before.")
        sys.exit(1)

    # Token (solo necesario para Fase 2)
    token = args.token or os.environ.get("APIFY_TOKEN")
    if run_fase2 and not token:
        print("❌ Necesitas tu API token de Apify para bajar comentarios.")
        print("   export APIFY_TOKEN='tu_token'")
        print("   o --token tu_token")
        print("   → https://console.apify.com/settings/integrations")
        sys.exit(1)

    client = ApifyClient(token) if token else None

    # Output dir con carpeta semanal
    output_dir = os.path.join(args.output_dir, f"semana_{args.since}_{args.before}")
    os.makedirs(output_dir, exist_ok=True)

    urls_csv = args.input_csv

    # ── FASE 1: URLs vía Serper ──
    if run_fase1:
        urls_csv = fase1_buscar_urls(
            pages=args.pages,
            since=args.since,
            before=args.before,
            max_pages=args.max_google_pages,
            output_dir=output_dir,
        )

    # ── FASE 2: Comentarios vía Apify ──
    if run_fase2:
        if not urls_csv:
            print("❌ No hay CSV de URLs. Usa --input-csv o corre sin --solo-comentarios.")
            sys.exit(1)

        try:
            urls = leer_urls_csv(urls_csv)
        except (FileNotFoundError, ValueError) as e:
            print(f"❌ {e}")
            sys.exit(1)

        if not urls:
            print("❌ No se encontraron URLs válidas en el CSV.")
            sys.exit(1)

        total_csv = len(urls)
        conteo_csv = contar_urls_por_tipo(urls)
        urls = aplicar_sampling_urls(
            urls,
            args.sample_strategy,
            args.sample_size,
            args.sample_seed,
            args.sample_min_per_stratum,
        )
        conteo_muestra = contar_urls_por_tipo(urls)

        print(
            f"  📚 URLs en CSV: {total_csv} "
            f"(post:{conteo_csv['post']} photo:{conteo_csv['photo']} video:{conteo_csv['video']})"
        )
        print(
            f"  🧪 URLs a procesar: {len(urls)} "
            f"(post:{conteo_muestra['post']} photo:{conteo_muestra['photo']} video:{conteo_muestra['video']})"
        )

        if args.max_urls and len(urls) > args.max_urls:
            urls = urls[:args.max_urls]
            print(f"  ✂️  Limitado a {args.max_urls} URLs")

        fase2_comentarios(
            client=client,
            urls=urls,
            max_comments=args.max_comments,
            since=args.since,
            output_dir=output_dir,
            input_csv=urls_csv,
            batch_size=args.batch_size,
        )

    print("\n🏁 Proceso finalizado.")


if __name__ == "__main__":
    print("\n" + "═" * 70)
    print("🚀 FACEBOOK: URLs (SERPER) + COMENTARIOS (APIFY)")
    print("═" * 70)
    main()
