"""
Extractor automatizado de YouTube - Compatible con estructura de semanas
========================================================================

Este script extrae comentarios de YouTube y los guarda en la estructura:
/home/emilio/Documentos/Radar_Politico/Datos/semana_24noviembre_01diciembre_25/

Fechas configurables dentro del script.
"""

import os
import googleapiclient.discovery
import pandas as pd
from datetime import datetime, timedelta
import time
import sys

# =========================
# CONFIGURACIÓN DEL RANGO
# =========================
# Usa formato YYYY-MM-DD. Si ambos quedan como None, se usan los últimos 15 días
# (incluyendo hoy). Configuración actual: 24/11/2025 al 01/12/2025.
CONFIG_START_DATE_STR = "2026-03-03"
CONFIG_END_DATE_STR = "2026-03-09"
DEFAULT_RANGE_DAYS = 15

SEARCH_QUERIES = [
    "presidenta municipal de Tampico",
    "Presidenta municipal de Tampico",
    "Gobierno de Tampico",
    "gobierno de Tampico",
]

OUTPUT_BASE_DIR = "/home/emilio/Documentos/RAdAR/data/raw/radar_weekly_flat"

def convertir_fecha_a_espanol(fecha):
    """Convierte fecha a formato español DDmes_AA (ejemplo: 08octubre_24)"""
    meses = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }

    dia = fecha.strftime('%d')
    mes = meses[fecha.month]
    anio = fecha.strftime('%y')
    return f"{dia}{mes}_{anio}"

def calcular_nombre_semana(fecha_inicio, fecha_fin):
    """Calcula el nombre de la carpeta de semana usando las fechas exactas
    Formato: semana_08octubre_24_14octubre_24
    """
    # Usar las fechas exactas sin ajustar al lunes
    fecha_inicio_real = fecha_inicio
    fecha_fin_real = fecha_fin

    # Convertir a formato español (ya incluye el año)
    fecha_inicio_esp = convertir_fecha_a_espanol(fecha_inicio_real)
    fecha_fin_esp = convertir_fecha_a_espanol(fecha_fin_real)

    return f"semana_{fecha_inicio_esp}_{fecha_fin_esp}"

def setup_youtube_api():
    """Set up and return a YouTube API client."""
    api_service_name = "youtube"
    api_version = "v3"
    api_key = "AIzaSyADmTxdJGJN9_wwahbt-qD0OtaqlEmTKEM"

    return googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key)

def search_videos(youtube, query, start_date, end_date):
    """Search for videos based on query and date range."""
    start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    search_response = youtube.search().list(
        q=query,
        part="id,snippet",
        maxResults=50,
        type="video",
        publishedAfter=start_date_str,
        publishedBefore=end_date_str
    ).execute()

    video_ids = []
    for item in search_response.get("items", []):
        if item["id"]["kind"] == "youtube#video":
            video_ids.append(item["id"]["videoId"])

    return video_ids

def get_video_comments(youtube, video_id, query, video_title="", channel_title="", published_at=""):
    """Get all comments for a specific video."""
    comments = []
    next_page_token = None

    while True:
        try:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "video_id": video_id,
                    "comment_id": item["id"],
                    "author": comment["authorDisplayName"],
                    "comment_text": comment["textDisplay"],
                    "published_at": comment["publishedAt"],
                    "like_count": comment["likeCount"],
                    "query": query,
                    "video_title": video_title,
                    "channel_title": channel_title,
                    "video_published_at": published_at
                })

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

            time.sleep(0.1)

        except Exception as e:
            print(f"Error obteniendo comentarios para video {video_id}: {e}")
            break

    return comments

def get_video_details(youtube, video_ids):
    """Get video details for a list of video IDs."""
    video_details = {}

    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]

        try:
            request = youtube.videos().list(
                part="snippet",
                id=",".join(batch_ids)
            )
            response = request.execute()

            for item in response["items"]:
                video_id = item["id"]
                snippet = item["snippet"]
                video_details[video_id] = {
                    "title": snippet["title"],
                    "channel_title": snippet["channelTitle"],
                    "published_at": snippet["publishedAt"]
                }

        except Exception as e:
            print(f"Error obteniendo detalles de videos: {e}")

    return video_details

def resolver_rango_fechas():
    """Resuelve el rango de fechas desde configuración o por defecto."""
    if (CONFIG_START_DATE_STR and not CONFIG_END_DATE_STR) or (CONFIG_END_DATE_STR and not CONFIG_START_DATE_STR):
        print("❌ Configuración de fechas incompleta. Define ambas fechas o ninguna.")
        sys.exit(1)

    if CONFIG_START_DATE_STR and CONFIG_END_DATE_STR:
        try:
            start_date = datetime.strptime(CONFIG_START_DATE_STR, "%Y-%m-%d")
            end_date = datetime.strptime(CONFIG_END_DATE_STR, "%Y-%m-%d")
        except ValueError:
            print("❌ Formato de fecha inválido en la configuración. Usar YYYY-MM-DD")
            sys.exit(1)
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=DEFAULT_RANGE_DAYS)

    end_date = end_date.replace(hour=23, minute=59, second=59)
    return start_date, end_date

def main():
    start_date, end_date = resolver_rango_fechas()

    print("🚀 Iniciando extracción de YouTube...")
    print(f"📅 Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")

    # Calcular nombre de carpeta de semana
    nombre_semana = calcular_nombre_semana(start_date, end_date)

    # Crear directorio en la estructura correcta
    output_dir = os.path.join(OUTPUT_BASE_DIR, nombre_semana)

    # Crear el directorio si no existe
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Carpeta creada: {output_dir}")
    else:
        print(f"📁 Usando carpeta existente: {output_dir}")

    print(f"📂 Directorio de salida: {output_dir}")
    print()

    # Inicializar cliente de YouTube API
    try:
        youtube = setup_youtube_api()
    except Exception as e:
        print(f"❌ Error configurando YouTube API: {e}")
        sys.exit(1)

    columnas_base = [
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
    ]

    all_comments = []
    total_videos = 0

    for i, query in enumerate(SEARCH_QUERIES, 1):
        print(f"🔍 Query {i}/{len(SEARCH_QUERIES)}: {query}")

        try:
            # Buscar videos
            video_ids = search_videos(youtube, query, start_date, end_date)
            print(f"   📺 Encontrados {len(video_ids)} videos")

            if video_ids:
                # Obtener detalles de los videos
                video_details = get_video_details(youtube, video_ids)

                # Obtener comentarios de cada video
                query_comments = 0
                for j, video_id in enumerate(video_ids, 1):
                    details = video_details.get(video_id, {})
                    print(f"   📄 Video {j}/{len(video_ids)}: {video_id}")

                    comments = get_video_comments(
                        youtube,
                        video_id,
                        query,
                        details.get("title", ""),
                        details.get("channel_title", ""),
                        details.get("published_at", "")
                    )

                    all_comments.extend(comments)
                    query_comments += len(comments)
                    print(f"      💬 {len(comments)} comentarios")

                    # Pausa para evitar límites de API
                    time.sleep(0.5)

                print(f"   ✅ Total query: {query_comments} comentarios")

            total_videos += len(video_ids)

        except Exception as e:
            print(f"   ❌ Error procesando query '{query}': {e}")
            continue

        print()

    if all_comments:
        comments_df = pd.DataFrame(all_comments)
        comments_df["fecha_extraccion"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        print("⚠️  Sin comentarios, se generará CSV vacío con columnas.")
        comments_df = pd.DataFrame(columns=columnas_base)

    filename = f"youtube_comentarios_{nombre_semana}.csv"
    filepath = os.path.join(output_dir, filename)

    try:
        comments_df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print("✅ EXTRACCIÓN COMPLETADA")
        print("=" * 50)
        print(f"📊 Total videos procesados: {total_videos}")
        print(f"💬 Total comentarios: {len(all_comments)}")
        print(f"📁 Carpeta: {nombre_semana}")
        print(f"📄 Archivo: {filename}")
        print(f"📂 Ruta: {filepath}")
        print(f"📋 Columnas: {list(comments_df.columns)}")
        print()
    except Exception as e:
        print(f"❌ Error guardando archivo CSV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
