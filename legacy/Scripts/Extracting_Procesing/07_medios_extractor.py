"""
=============================================================
 BUSCADOR DE NOTICIAS — SerpAPI Google News + trafilatura
=============================================================
Uso:
    python 07_medios_extractor.py

Dependencias:
    pip install google-search-results trafilatura pandas
=============================================================
"""

# ============================================================
# CONFIGURACIÓN — solo edita esta sección
# ============================================================
API_KEY = "6e223f787885b3a684e1d0b6a1d7c07332107aa78901e3c32705f2d10f5a4760"
MEDIOS = [
    "site:oem.com.mx",
    "site:milenio.com",
    "site:noticiasdetampico.mx",
]

TERMINOS = [
    '"Monica Villarreal"',
    '"gobierno de tampico"',
    '"tampico"',
    
]

ANIO_INICIO = 2025
MES_INICIO = 1
FECHA_INICIO_EXACTA = "2024-10-01"  # None => usa primer_lunes_del_mes(ANIO_INICIO, MES_INICIO)
FECHA_FIN_EXACTA = "2024-10-07"            # None => hoy
MODO_QUERIES = "combinado"          # "compacto" o "combinado" (compatibilidad ML)
USAR_GOOGLE_WEB = True             # False reduce llamadas ~50%
NUM_RESULTADOS_GOOGLE_WEB = 100
OMITIR_SEMANAS_EXISTENTES = True
CONSULTAR_CUOTA_AL_INICIO = False
MIN_SEARCHES_LEFT_PARA_CONTINUAR = 0
MAX_LLAMADAS_SERPAPI_POR_EJECUCION = None
MAX_LLAMADAS_SERPAPI_POR_HORA = 45
SERPAPI_REINTENTOS = 5
SERPAPI_BACKOFF_INICIAL = 4.0
SERPAPI_BACKOFF_MAX = 90.0
SERPAPI_USAR_CACHE_LOCAL = True
NOMBRE_CARPETA_CACHE_SERPAPI = "_cache_serpapi"
CARPETA_BASE_SEMANAL = "/home/emilio/Documentos/Datos_Radar/Medios"
NOMBRE_ARCHIVO_BASE = "noticias_tampico"
PAUSA        = 2.0            # segundos entre requests
# ============================================================

import hashlib
import json
import random
import time
import re
import unicodedata
from collections import deque
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote_plus
from urllib.request import urlopen

import trafilatura
import pandas as pd

# Compatibilidad con ambos SDKs de SerpAPI:
# - google-search-results (GoogleSearch)
# - serpapi oficial nuevo (Client)
SERPAPI_BACKEND = None
try:
    from serpapi import GoogleSearch  # type: ignore
    SERPAPI_BACKEND = "google-search-results"
except ImportError:
    try:
        from serpapi import Client  # type: ignore
        SERPAPI_BACKEND = "serpapi-client"
    except ImportError as exc:
        raise ImportError(
            "No se encontró un cliente compatible de SerpAPI. "
            "Instala 'google-search-results' o 'serpapi'."
        ) from exc

SERPAPI_CALLS_REALES = 0
SERPAPI_RESPUESTAS_CACHE_LOCAL = 0
SERPAPI_TIEMPOS_CALLS = deque()


def _ruta_cache_serpapi():
    return Path(CARPETA_BASE_SEMANAL) / NOMBRE_CARPETA_CACHE_SERPAPI


def _hash_cache_params(params):
    limpios = {k: v for k, v in params.items() if k != "api_key"}
    serializado = json.dumps(limpios, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def _leer_cache_serpapi(params):
    if not SERPAPI_USAR_CACHE_LOCAL:
        return None
    ruta = _ruta_cache_serpapi() / f"{_hash_cache_params(params)}.json"
    if not ruta.exists():
        return None
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _guardar_cache_serpapi(params, resultados):
    if not SERPAPI_USAR_CACHE_LOCAL:
        return
    carpeta = _ruta_cache_serpapi()
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{_hash_cache_params(params)}.json"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False)


def _clasificar_error_serpapi(mensaje):
    texto = (mensaje or "").lower()
    patrones_rate = (
        "429",
        "too many requests",
        "rate limit",
        "throughput limit",
    )
    patrones_cuota = (
        "run out of searches",
        "searches left",
        "not enough credits",
        "plan searches",
    )
    if any(p in texto for p in patrones_rate):
        return "rate"
    if any(p in texto for p in patrones_cuota):
        return "cuota"
    return ""


def _respetar_limite_horario_serpapi():
    """Evita exceder MAX_LLAMADAS_SERPAPI_POR_HORA dentro de ventanas de 60 min."""
    if MAX_LLAMADAS_SERPAPI_POR_HORA is None or MAX_LLAMADAS_SERPAPI_POR_HORA <= 0:
        return

    ventana_segundos = 3600
    ahora = time.time()
    while SERPAPI_TIEMPOS_CALLS and (ahora - SERPAPI_TIEMPOS_CALLS[0]) >= ventana_segundos:
        SERPAPI_TIEMPOS_CALLS.popleft()

    if len(SERPAPI_TIEMPOS_CALLS) < MAX_LLAMADAS_SERPAPI_POR_HORA:
        return

    espera = ventana_segundos - (ahora - SERPAPI_TIEMPOS_CALLS[0]) + random.uniform(0.3, 1.0)
    espera = max(espera, 0.0)
    print(
        f"  ⏸ Límite horario local ({MAX_LLAMADAS_SERPAPI_POR_HORA}/h) alcanzado. "
        f"Esperando {espera/60:.1f} minutos..."
    )
    time.sleep(espera)

    ahora = time.time()
    while SERPAPI_TIEMPOS_CALLS and (ahora - SERPAPI_TIEMPOS_CALLS[0]) >= ventana_segundos:
        SERPAPI_TIEMPOS_CALLS.popleft()


def ejecutar_busqueda_serpapi(params):
    """Ejecuta búsqueda SerpAPI con backend compatible y regresa dict."""
    global SERPAPI_CALLS_REALES, SERPAPI_RESPUESTAS_CACHE_LOCAL

    cacheado = _leer_cache_serpapi(params)
    if cacheado is not None:
        SERPAPI_RESPUESTAS_CACHE_LOCAL += 1
        return cacheado

    if (
        MAX_LLAMADAS_SERPAPI_POR_EJECUCION is not None
        and SERPAPI_CALLS_REALES >= MAX_LLAMADAS_SERPAPI_POR_EJECUCION
    ):
        raise RuntimeError(
            f"Tope local alcanzado: {MAX_LLAMADAS_SERPAPI_POR_EJECUCION} llamadas SerpAPI."
        )

    espera = SERPAPI_BACKOFF_INICIAL
    ultimo_error = None

    for intento in range(1, SERPAPI_REINTENTOS + 1):
        try:
            _respetar_limite_horario_serpapi()
            SERPAPI_CALLS_REALES += 1
            SERPAPI_TIEMPOS_CALLS.append(time.time())
            if SERPAPI_BACKEND == "google-search-results":
                search = GoogleSearch(params)
                results = search.get_dict()
            else:
                # Backend oficial nuevo: serpapi.Client
                request_params = dict(params)
                api_key = request_params.pop("api_key", None)
                client = Client(api_key=api_key)
                results = dict(client.search(request_params))

            tipo_error = _clasificar_error_serpapi(results.get("error", ""))
            if tipo_error == "cuota":
                raise RuntimeError(
                    f"SerpAPI reportó cuota agotada: {results.get('error', 'sin detalle')}"
                )
            if tipo_error == "rate":
                raise RuntimeError(
                    f"SerpAPI rate limit: {results.get('error', 'sin detalle')}"
                )

            _guardar_cache_serpapi(params, results)
            return results

        except Exception as exc:
            ultimo_error = exc
            tipo_error = _clasificar_error_serpapi(str(exc))
            if tipo_error == "cuota":
                raise RuntimeError(f"Cuota SerpAPI agotada: {exc}") from exc

            if intento >= SERPAPI_REINTENTOS:
                break

            pausa = min(espera, SERPAPI_BACKOFF_MAX) + random.uniform(0.4, 1.2)
            print(
                f"  ⚠ Error SerpAPI (intento {intento}/{SERPAPI_REINTENTOS}): {exc}. "
                f"Reintentando en {pausa:.1f}s..."
            )
            time.sleep(pausa)
            espera = min(espera * 2, SERPAPI_BACKOFF_MAX)

    raise RuntimeError(f"Fallo SerpAPI tras {SERPAPI_REINTENTOS} intentos: {ultimo_error}")


def consultar_cuenta_serpapi(api_key):
    """Consulta plan_searches_left en account.json (no consume búsquedas)."""
    url = f"https://serpapi.com/account.json?api_key={quote_plus(api_key)}"
    try:
        with urlopen(url, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as exc:
        print(f"⚠ No se pudo consultar cuenta SerpAPI: {exc}")
    except Exception as exc:
        print(f"⚠ Respuesta inválida de cuenta SerpAPI: {exc}")
    return None


def obtener_plan_searches_left(account_info):
    if not isinstance(account_info, dict):
        return None
    valor = account_info.get("plan_searches_left")
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def generar_queries(medios, terminos, modo="compacto"):
    """Genera queries por medio. Modo compacto usa OR entre términos."""
    if modo == "combinado":
        return [f"{termino} {medio}" for medio in medios for termino in terminos]
    bloque_or = " OR ".join(terminos)
    return [f"({bloque_or}) {medio}" for medio in medios]


def buscar_google_news(query, fecha_ini, fecha_fin, api_key):
    """Busca noticias usando el engine google_news de SerpAPI."""
    print("\nBuscando en Google News via SerpAPI...")
    query_con_fechas = f"{query} after:{fecha_ini} before:{fecha_fin}"

    params = {
        "api_key": api_key,
        "engine":  "google_news",
        "q":       query_con_fechas,
        "hl":      "es",
        "gl":      "mx",
    }

    results = ejecutar_busqueda_serpapi(params)

    noticias = []
    for r in results.get("news_results", []):
        # Algunos resultados traen sub-noticias (stories)
        if "stories" in r:
            for story in r["stories"]:
                noticias.append(extraer_campos(story))
        else:
            noticias.append(extraer_campos(r))

    print(f"  → {len(noticias)} noticias encontradas en Google News")
    return noticias


def buscar_google_web(query, fecha_ini, fecha_fin, api_key):
    """Búsqueda complementaria usando engine google normal con tbm=nws."""
    print("\nBuscando en Google Web News (complemento)...")

    # Convertir fechas a formato MM/DD/YYYY para tbs
    ini = datetime.strptime(fecha_ini, "%Y-%m-%d").strftime("%m/%d/%Y")
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d").strftime("%m/%d/%Y")

    params = {
        "api_key": api_key,
        "engine":  "google",
        "q":       query,
        "tbm":     "nws",
        "tbs":     f"cdr:1,cd_min:{ini},cd_max:{fin}",
        "hl":      "es",
        "gl":      "mx",
        "num":     NUM_RESULTADOS_GOOGLE_WEB,
    }

    results = ejecutar_busqueda_serpapi(params)

    noticias = []
    for r in results.get("news_results", []):
        noticias.append({
            "titulo":  r.get("title", ""),
            "url":     r.get("link", ""),
            "fecha":   r.get("date", ""),
            "iso_date": "",
            "fuente":  r.get("source", ""),
            "autor":   "",
            "thumbnail": r.get("thumbnail", ""),
            "texto":   "",
            "origen":  "GOOGLE_WEB"
        })

    print(f"  → {len(noticias)} noticias encontradas en Google Web")
    return noticias


def extraer_campos(r):
    """Extrae campos estándar de un resultado de google_news."""
    return {
        "titulo":    r.get("title", ""),
        "url":       r.get("link", ""),
        "fecha":     r.get("date", ""),
        "iso_date":  r.get("iso_date", ""),
        "fuente":    r.get("source", {}).get("name", "") if isinstance(r.get("source"), dict) else r.get("source", ""),
        "autor":     ", ".join(r.get("authors", [])) if r.get("authors") else "",
        "thumbnail": r.get("thumbnail", ""),
        "texto":     "",
        "origen":    "GOOGLE_NEWS"
    }


def deduplicar(lista):
    """Elimina duplicados por URL."""
    vistos = set()
    unicos = []
    for r in lista:
        if r["url"] and r["url"] not in vistos:
            vistos.add(r["url"])
            unicos.append(r)
    return unicos


def filtrar_por_fecha(noticias, fecha_ini, fecha_fin):
    """Filtra por fecha usando iso_date cuando está disponible."""
    ini = datetime.strptime(fecha_ini, "%Y-%m-%d")
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d")

    filtradas = []
    sin_fecha = []

    for r in noticias:
        if r.get("iso_date"):
            try:
                fecha = datetime.fromisoformat(r["iso_date"].replace("Z", "+00:00")).replace(tzinfo=None)
                if ini <= fecha <= fin:
                    filtradas.append(r)
                continue
            except Exception:
                pass
        # Si no tiene iso_date confiable, la incluimos igual.
        # Para google_news el query ya incluye after/before.
        sin_fecha.append(r)

    print(f"  Dentro del rango: {len(filtradas)} | Sin fecha parseable: {len(sin_fecha)}")
    return filtradas + sin_fecha


def descargar_textos(noticias):
    """Descarga el texto completo de cada URL con trafilatura."""
    print(f"\n[3/3] Descargando texto completo de {len(noticias)} artículos...")

    for i, r in enumerate(noticias, 1):
        if not r["url"]:
            continue
        print(f"  {i}/{len(noticias)} {r['titulo'][:60]}")
        try:
            html   = trafilatura.fetch_url(r["url"])
            r["texto"] = trafilatura.extract(html, include_comments=False) or ""
        except Exception as e:
            print(f"    ⚠ Error: {e}")
            r["texto"] = ""
        time.sleep(PAUSA)

    return noticias


def limpiar_texto_para_txt(texto):
    """Normaliza texto para salida TXT limpia y ASCII."""
    t = (texto or "").lower()

    # Quitar URLs completas y dominios tipo sitio.com/sitio.mx/etc.
    t = re.sub(r"https?://\S+|www\.\S+", " ", t)
    t = re.sub(r"\b[\w-]+(?:\.[\w-]+)+\b", " ", t)

    # Remplazar acentos/diacríticos y convertir todo a ASCII.
    t = unicodedata.normalize("NFD", t)
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = t.encode("ascii", "ignore").decode("ascii")

    # Quitar números y cualquier caracter no alfabético ASCII.
    t = re.sub(r"\d+", " ", t)
    t = re.sub(r"[^a-z\s]", " ", t)

    # Compactar espacios.
    t = re.sub(r"\s+", " ", t).strip()
    return t


def formatear_en_lineas_de_palabras(texto, palabras_por_linea=30):
    """Divide texto en líneas con N palabras por línea."""
    palabras = texto.split()
    if not palabras:
        return ""
    return "\n".join(
        " ".join(palabras[i:i + palabras_por_linea])
        for i in range(0, len(palabras), palabras_por_linea)
    )


def guardar_txt_noticias(noticias, ruta_txt):
    """Guarda TXT limpio, normalizado y en líneas de 30 palabras."""
    material_limpio = []
    for r in noticias:
        titulo = (r.get("titulo") or "").strip()
        texto = (r.get("texto") or "").strip()
        combinado = f"{titulo} {texto}".strip()
        limpio = limpiar_texto_para_txt(combinado)
        if limpio:
            material_limpio.append(limpio)

    texto_final = formatear_en_lineas_de_palabras(" ".join(material_limpio), palabras_por_linea=30)

    with open(ruta_txt, "w", encoding="utf-8") as f:
        if texto_final:
            f.write(texto_final + "\n")


def primer_lunes_del_mes(anio, mes):
    """Regresa la fecha del primer lunes de un mes."""
    primer_dia = date(anio, mes, 1)
    dias_hasta_lunes = (0 - primer_dia.weekday()) % 7
    return primer_dia + timedelta(days=dias_hasta_lunes)


def iterar_semanas(fecha_inicio, fecha_fin):
    """Genera periodos semanales [lunes-domingo] hasta fecha_fin."""
    inicio = fecha_inicio
    while inicio <= fecha_fin:
        fin = min(inicio + timedelta(days=6), fecha_fin)
        yield inicio, fin
        inicio += timedelta(days=7)


def nombre_carpeta_semana(fecha_inicio, fecha_fin):
    """Nombre de carpeta: semana_DDmes_DDmes_YY."""
    meses = {
        1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
        7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic",
    }
    ini = f"{fecha_inicio.day:02d}{meses[fecha_inicio.month]}"
    fin = f"{fecha_fin.day:02d}{meses[fecha_fin.month]}"
    return f"semana_{ini}_{fin}_{fecha_fin.strftime('%y')}"


def rutas_salida_semana(fecha_inicio_semana, fecha_fin_semana):
    fecha_inicio = fecha_inicio_semana.strftime("%Y-%m-%d")
    fecha_fin = fecha_fin_semana.strftime("%Y-%m-%d")
    carpeta_semana = Path(CARPETA_BASE_SEMANAL) / nombre_carpeta_semana(
        fecha_inicio_semana, fecha_fin_semana
    )
    archivo_salida = carpeta_semana / f"{NOMBRE_ARCHIVO_BASE}_{fecha_inicio}_{fecha_fin}.csv"
    archivo_txt = carpeta_semana / f"{NOMBRE_ARCHIVO_BASE}_{fecha_inicio}_{fecha_fin}.txt"
    return carpeta_semana, archivo_salida, archivo_txt


def procesar_semana(fecha_inicio_semana, fecha_fin_semana):
    """Procesa extracción para una sola semana y guarda su CSV."""
    fecha_inicio = fecha_inicio_semana.strftime("%Y-%m-%d")
    fecha_fin = fecha_fin_semana.strftime("%Y-%m-%d")

    carpeta_semana, archivo_salida, archivo_txt = rutas_salida_semana(
        fecha_inicio_semana, fecha_fin_semana
    )
    carpeta_semana.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"  MEDIOS:       {', '.join(MEDIOS)}")
    print(f"  TERMINOS:     {', '.join(TERMINOS)}")
    print(f"  FECHA INICIO: {fecha_inicio}")
    print(f"  FECHA FIN:    {fecha_fin}")
    print(f"  SERPAPI SDK:  {SERPAPI_BACKEND}")
    print(f"  CARPETA:      {carpeta_semana}")
    print("=" * 60)

    queries = generar_queries(MEDIOS, TERMINOS, modo=MODO_QUERIES)
    print(f"  QUERIES TOTAL: {len(queries)}")
    llamadas_estimadas = len(queries) * (1 + int(USAR_GOOGLE_WEB))
    print(f"  LLAMADAS SERPAPI (estimadas): {llamadas_estimadas}")

    noticias_gn = []
    noticias_web = []

    for i, query in enumerate(queries, 1):
        print("\n" + "-" * 60)
        print(f"Query {i}/{len(queries)}: {query}")
        print("-" * 60)
        noticias_gn.extend(buscar_google_news(query, fecha_inicio, fecha_fin, API_KEY))
        if USAR_GOOGLE_WEB:
            noticias_web.extend(buscar_google_web(query, fecha_inicio, fecha_fin, API_KEY))
        time.sleep(PAUSA)

    # Combinar, deduplicar y filtrar
    todos = deduplicar(noticias_gn + noticias_web)
    todos = filtrar_por_fecha(todos, fecha_inicio, fecha_fin)

    print(f"\n  TOTAL ÚNICO: {len(todos)} noticias")

    # Descargar textos
    todos = descargar_textos(todos)

    # Guardar
    df = pd.DataFrame(todos, columns=[
        "titulo", "fecha", "iso_date", "fuente",
        "autor", "url", "thumbnail", "texto", "origen"
    ])

    # Ordenar por fecha
    try:
        df["_sort"] = pd.to_datetime(df["iso_date"], errors="coerce")
        df = df.sort_values("_sort", ascending=False).drop(columns="_sort")
    except Exception:
        pass

    df.to_csv(archivo_salida, index=False, encoding="utf-8-sig")
    print(f"\n✓ Guardado en: {archivo_salida}")
    guardar_txt_noticias(todos, archivo_txt)
    print(f"✓ TXT guardado en: {archivo_txt}")

    # Resumen
    print("\n--- NOTICIAS ---")
    for i, r in enumerate(todos, 1):
        tiene_texto = "✓" if r["texto"] else "✗"
        print(f"  {i:2}. [{r['fecha'][:10]}] {r['titulo'][:60]}")
        print(f"       {r['fuente']} | texto:{tiene_texto} | {r['origen']}")

    return df


def main():
    if FECHA_INICIO_EXACTA:
        fecha_inicio_global = datetime.strptime(FECHA_INICIO_EXACTA, "%Y-%m-%d").date()
        etiqueta_inicio = f"{fecha_inicio_global} (manual)"
    else:
        fecha_inicio_global = primer_lunes_del_mes(ANIO_INICIO, MES_INICIO)
        etiqueta_inicio = f"{fecha_inicio_global} (primer lunes de {MES_INICIO}/{ANIO_INICIO})"

    if FECHA_FIN_EXACTA:
        fecha_fin_global = datetime.strptime(FECHA_FIN_EXACTA, "%Y-%m-%d").date()
        etiqueta_fin = f"{fecha_fin_global} (manual)"
    else:
        fecha_fin_global = date.today()
        etiqueta_fin = f"{fecha_fin_global} (hoy)"

    plan_left = None
    if CONSULTAR_CUOTA_AL_INICIO:
        account_info = consultar_cuenta_serpapi(API_KEY)
        plan_left = obtener_plan_searches_left(account_info)

    print("\n" + "#" * 60)
    print("  EXTRACCIÓN SEMANAL")
    print(f"  DESDE: {etiqueta_inicio}")
    print(f"  HASTA: {etiqueta_fin}")
    print(f"  BASE:  {CARPETA_BASE_SEMANAL}")
    print(f"  MODO_QUERIES: {MODO_QUERIES}")
    print(f"  USAR_GOOGLE_WEB: {USAR_GOOGLE_WEB}")
    if plan_left is not None:
        print(f"  PLAN_SEARCHES_LEFT (inicio): {plan_left}")
    print("#" * 60)

    semanas = list(iterar_semanas(fecha_inicio_global, fecha_fin_global))
    print(f"Semanas a procesar: {len(semanas)}")

    resultados = []
    errores = []

    for idx, (inicio, fin) in enumerate(semanas, 1):
        print("\n" + "#" * 60)
        print(f"SEMANA {idx}/{len(semanas)}: {inicio} -> {fin}")
        print("#" * 60)
        if (
            plan_left is not None
            and plan_left < MIN_SEARCHES_LEFT_PARA_CONTINUAR
        ):
            print(
                f"⚠ Se detiene ejecución para no agotar cuota. "
                f"plan_searches_left={plan_left} < {MIN_SEARCHES_LEFT_PARA_CONTINUAR}"
            )
            break
        carpeta_semana, archivo_salida, _ = rutas_salida_semana(inicio, fin)
        if OMITIR_SEMANAS_EXISTENTES and archivo_salida.exists():
            print(f"↷ Semana omitida (ya existe CSV): {archivo_salida}")
            continue
        try:
            llamadas_antes = SERPAPI_CALLS_REALES
            df_semana = procesar_semana(inicio, fin)
            resultados.append(df_semana)
            llamadas_semana = SERPAPI_CALLS_REALES - llamadas_antes
            if plan_left is not None:
                plan_left = max(0, plan_left - llamadas_semana)
                print(f"  plan_searches_left estimado tras semana: {plan_left}")
        except Exception as exc:
            errores.append((inicio, fin, str(exc)))
            print(f"⚠ Error en semana {inicio} -> {fin}: {exc}")

    if errores:
        print("\n--- ERRORES ---")
        for inicio, fin, err in errores:
            print(f"  {inicio} -> {fin}: {err}")

    if resultados:
        print(
            f"\nSerpAPI llamadas reales: {SERPAPI_CALLS_REALES} | "
            f"respuestas desde cache local: {SERPAPI_RESPUESTAS_CACHE_LOCAL}"
        )
        return pd.concat(resultados, ignore_index=True)

    print(
        f"\nSerpAPI llamadas reales: {SERPAPI_CALLS_REALES} | "
        f"respuestas desde cache local: {SERPAPI_RESPUESTAS_CACHE_LOCAL}"
    )
    return pd.DataFrame()


if __name__ == "__main__":
    df = main()
