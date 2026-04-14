# Endurecimiento Estructural de promover_raw_a_texto.py

**Fecha:** 2026-04-13
**Rama destino:** feature/restructuracion-arquitectonica-repo
**Tipo:** Endurecimiento estructural — preservación canónica estricta
**Script intervenido:** `src/preprocessing/promover_raw_a_texto.py`

---

## Contexto metodológico obligatorio

Este script no es un script cualquiera de limpieza. Es el script histórico que produjo el material textual con el que se entrenó el modelo vigente. Por tanto, su lógica de transformación forma parte del contrato metodológico del sistema ya validado. En esta tarea NO se va a reexperimentar el modelo, NO se va a abrir una rama alternativa de preprocesamiento, NO se va a corregir la lógica lingüística, NO se va a "aprovechar" la refactorización para hacer mejoras semánticas. Cualquier modificación que altere el contenido efectivo del corpus canónico, aunque parezca una mejora técnica, será considerada un error.

## Naturaleza exacta de la tarea

La tarea es exclusivamente esta:

> hacer endurecimiento estructural, trazabilidad, auditoría, logging, validación operativa y robustez de ejecución, preservando compatibilidad funcional estricta con la salida histórica canónica.

Dicho de otro modo:

- sí puedes cambiar la envoltura
- no puedes cambiar la sustancia

## Regla suprema de esta intervención

La salida canónica `.txt` debe seguir siendo la misma que produce el script actual cuando se ejecuta sobre los mismos insumos.

No quiero equivalencia "aproximada".
No quiero equivalencia "conceptual".
No quiero equivalencia "metodológica".
Quiero equivalencia funcional efectiva de outputs canónicos.

Si una decisión de refactorización pone en riesgo esa equivalencia, no la tomes.

## Marco de restricción absoluta

Tienes prohibido reinterpretar esta tarea como cualquiera de las siguientes cosas:

- rediseño del pipeline
- mejora de limpieza textual
- optimización lingüística
- modernización metodológica
- corrección de sesgos del corpus
- unificación de criterios entre plataformas
- ampliación de columnas aceptadas
- corrección del formato histórico de líneas
- consolidación inteligente de medios
- normalización nueva
- refactorización "libre"

Nada de eso está autorizado.

## Lo que debes preservar exactamente

Debes preservar, sin alteración material de comportamiento, toda la lógica que define el contenido del corpus.

No basta con "parecerte" al script. Debes conservar el comportamiento histórico puntual.

### Se conserva exactamente la configuración base funcional

Debes mantener como configuración base funcional:

```python
SOURCE_BASE = Path("/home/emilio/Documentos/RAdAR/Datos_RAdAR")
TARGET_BASE = Path("/home/emilio/Documentos/RAdAR/Datos_RadaR_Texto")

TARGET_DIRS = {
    "facebook": TARGET_BASE / "Facebook_Semana_Texto",
    "twitter": TARGET_BASE / "Twitter_Semana_Texto",
    "youtube": TARGET_BASE / "Youtube_Semanas_Texto",
    "medios": TARGET_BASE / "Medios_Semana_Texto",
}
```

Si agregas configuración auxiliar, debe ser no invasiva y separada. No cambies estas rutas base ni la semántica de estas salidas canónicas.

### Se conserva exactamente el mapping de reemplazo de caracteres

Debes mantener exactamente este mapping:

```python
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
```

No agregues caracteres. No quites caracteres. No sustituyas este mecanismo por `unicodedata.normalize`. No introduzcas una alternativa "equivalente". Debe seguir siendo sustitución literal con este mapping.

### La función `_replace_accents(text)` debe seguir comportándose igual

Debe seguir aplicando el reemplazo carácter por carácter con el mapping anterior. No la sustituyas por otra estrategia de transliteración. No uses bibliotecas externas para este paso. No metas excepciones especiales. No cambies el resultado.

### Normalización de Facebook: preservar exactamente el comportamiento histórico

La función `normalize_facebook(text)` debe seguir haciendo, en sustancia y orden efectivo, lo siguiente:

1. `_replace_accents`
2. `lower()`
3. remover menciones `@\w+`
4. transformar hashtags con: `#(\w+) -> " \1 "`
5. remover URLs con estos patrones históricos: `https?:\/\/\S*`, `www\.\S+`, `\S+\.com\b`, `\S+\.mx\b`
6. remover tokens literales: `http`, `https`, `com`, `facebook`, `fb`, `me gusta`, `compartir`
7. remover puntuación y dígitos con esta lógica: `re.sub(r"[" + re.escape(string.punctuation + string.digits) + "]", " ", text)`
8. eliminar caracteres no ASCII dejando solo `ord(char) < 128`
9. colapsar espacios con: `re.sub(r"\s+", " ", text)`
10. `strip()`

No cambies regex. No cambies orden. No cambies criterios. No preserves emojis. No preserves acentos. No preserves ñ. No agregues limpieza de tokens "parecidos". No unifiques esta lógica con otras plataformas.

### Normalización de Twitter: preservar exactamente el comportamiento histórico

La función `normalize_twitter(text)` debe seguir haciendo exactamente, en términos de resultado:

1. `_replace_accents`
2. `lower()`
3. remover menciones
4. transformar hashtags como hoy
5. remover URLs con los mismos patrones históricos
6. remover tokens: `http`, `https`, `com`, `rt`, `via`
7. remover puntuación y dígitos
8. eliminar no ASCII
9. colapsar espacios
10. `strip()`

No inventes limpieza especial para Twitter. No cambies `rt`. No cambies `via`. No agregues otras stopwords. No quites lo que hoy se quita.

### Normalización de YouTube: preservar exactamente el comportamiento histórico

La función `normalize_youtube(text)` debe seguir haciendo exactamente:

1. `_replace_accents`
2. `lower()`
3. remover `https?:\/\/\S*`
4. remover token `http`
5. remover token `https`
6. remover token `com`
7. remover `\.\s*com\b`
8. remover puntuación y dígitos
9. eliminar no ASCII
10. colapsar espacios
11. `strip()`

No le metas menciones si hoy no las mete. No la hagas "consistente" con Facebook/Twitter. No cambies criterios de inclusión.

### Detección de dialecto CSV: preservar comportamiento

`detect_dialect(path)` debe seguir leyendo muestra con:

```python
sample = handle.read(8192)
```

y debe seguir intentando:

```python
csv.Sniffer().sniff(sample, delimiters=",;")
```

con fallback a:

```python
csv.get_dialect("excel")
```

No cambies tamaño de muestra salvo razón de encapsulación sin efecto. No cambies delimitadores. No cambies el fallback.

### Lectura de filas tipo diccionario: preservar comportamiento

`read_dict_rows(path)` debe seguir:

- abriendo con `encoding="utf-8-sig"`
- `errors="ignore"`
- `newline=""`
- usando `csv.DictReader`
- normalizando fieldnames con `strip().lower()`
- normalizando claves a `strip().lower()`
- normalizando valores con: `(value or "").strip().strip('"')`

No conviertas esto a pandas. No metas inferencia automática distinta. No cambies esta limpieza de columnas/valores.

### Deduplicación: preservar exact match y orden

`dedupe_keep_order(items)` debe seguir:

- eliminando duplicados por coincidencia exacta
- preservando orden de primera aparición

No implementes fuzzy dedupe. No normalices adicionalmente antes de deduplicar. No dedupes por hash semántico. No cambies el criterio.

### Segmentación en líneas: absolutamente intocable

`words_to_lines(items, words_per_line)` debe seguir operando conceptualmente así:

```python
words = " ".join(items).split()
return [
    " ".join(words[index:index + words_per_line])
    for index in range(0, len(words), words_per_line)
    if words[index:index + words_per_line]
]
```

Esto es crítico. No segmentes por comentario. No segmentes por documento. No segmentes por oración. No segmentes por párrafo. No intentes "respetar límites discursivos". No metas sliding windows. No metas solapamiento. No metas padding. No cambies nada aquí. Este comportamiento histórico debe permanecer intacto porque forma parte de la forma efectiva del material con que se alimentó el modelo.

### Escritura de líneas: preservar comportamiento

`write_lines(path, lines)` debe seguir:

- creando padres con `mkdir(parents=True, exist_ok=True)`
- escribiendo en UTF-8
- una línea por renglón
- agregando salto final si hay contenido

No cambies el formato. No agregues encabezados. No agregues metadatos en el `.txt`. No mezcles auditoría con salida canónica.

### Procesamiento Facebook: preservar comportamiento exacto

`process_facebook(files, output_path)` debe seguir:

- recorriendo archivos detectados
- buscando columna de texto en este orden estricto: `"texto"`, `"message"`
- si no existe ninguna, continuar sin reinterpretar
- aplicar `normalize_facebook`
- incluir solo si: `if cleaned and len(cleaned.split()) >= 2:`
- incrementar `extracted` por cada entrada aceptada antes de deduplicar
- deduplicar con `dedupe_keep_order`
- escribir con: `write_lines(output_path, words_to_lines(unique, 35))`
- retornar: `return extracted, len(unique)`

No cambies el umbral mínimo. No agregues nuevas columnas. No uses otra métrica de longitud. No escribas por comentario. No cambies 35.

### Procesamiento Twitter: preservar comportamiento exacto

`process_twitter(files, output_path)` debe seguir:

- buscando columnas en este orden: `"text"`, `"tweet_content"`
- si encuentra columna válida, leer CSV y procesar filas
- si no la encuentra, activar el fallback histórico leyendo el archivo como texto plano línea por línea
- limpiar con `normalize_twitter`
- incluir solo si: `if cleaned and len(cleaned.split()) >= 3:`
- deduplicar igual
- escribir con: `write_lines(output_path, words_to_lines(unique, 25))`
- retornar conteos equivalentes

No cambies el fallback. No cambies el threshold. No agregues otras columnas. No cambies 25.

### Procesamiento YouTube: preservar comportamiento exacto

`process_youtube(files, output_path)` debe seguir:

- si `"comment_text"` está en los fieldnames, procesar como CSV
- si no, usar fallback leyendo línea por línea como texto
- limpiar con `normalize_youtube`
- incluir solo si `cleaned`
- deduplicar igual
- escribir con: `write_lines(output_path, words_to_lines(unique, 30))`
- retornar conteos equivalentes

No cambies 30. No cambies criterio de inclusión. No agregues columnas nuevas. No cambies el fallback histórico.

### Procesamiento medios: preservar exactamente la copia histórica

`process_medios(files, output_path)` debe seguir copiando exactamente el primer archivo:

```python
shutil.copy2(files[0], output_path)
```

No concatenes. No selecciones el "mejor". No combines. No reordenes. No detectes encoding y recompongas. No cambies el artefacto canónico.

Sí puedes auditar si hay más de un archivo, pero el output canónico debe seguir saliendo de `files[0]`.

### Prefijo por semana: preservar exactamente

`source_prefix(week_dir)` debe seguir siendo:

```python
return week_dir.name.split("_semana_", 1)[0]
```

No cambies la estrategia. No metas parsing más sofisticado. No sustituyas esto por regex nueva. No alteres el naming canónico.

### Descubrimiento de archivos: preservar patrones y orden

`find_type_files(week_dir, media_type)` debe seguir usando estos patrones:

```python
patterns = {
    "facebook": ["*_facebook.csv", "*facebook*.csv"],
    "twitter": ["*_twitter.csv", "*twitter*.csv"],
    "youtube": ["*_youtube.csv", "*youtube*.csv"],
    "medios": ["*_medios.txt", "*medios*.txt"],
}
```

Y debe seguir:

- iterando patrones en ese orden
- usando `sorted`
- evitando duplicados con `seen`
- aceptando solo `path.is_file()`

No cambies patrones. No agregues nuevos. No expandas extensiones. No priorices de otra forma.

### Orquestación principal: preservar salida canónica

En `main()` debes preservar la lógica funcional actual:

- crear directorios destino
- listar semanas como subdirectorios de `SOURCE_BASE`
- para cada semana: calcular prefix, encontrar archivos por tipo, procesar
- conservar el naming canónico actual:
  - `f"{prefix}_facebook.txt"`
  - `f"{prefix}_twitter.txt"`
  - `f"{prefix}_youtube.txt"`
  - `f"{prefix}_medios.txt"`

No cambies nombres de archivo. No metas sufijos nuevos en la salida canónica. No cambies carpetas destino canónicas. No metas timestamps al nombre canónico. Todo lo adicional debe ir por fuera, como artefacto auxiliar.

## Qué sí debes hacer

### Reorganización estructural

Ordena el código en secciones claras:
- configuración
- utilidades generales
- logging/auditoría
- funciones históricas de limpieza
- procesamiento por fuente
- orquestación

### Type hints

Agrega tipado consistente sin cambiar comportamiento.

### Docstrings

Documenta con precisión qué hace cada función y, muy importante, señala explícitamente cuando una función está congelada por compatibilidad histórica.

### Logging a archivo

Agrega logging persistente. Debe registrar:
- inicio de ejecución
- rutas base
- semanas detectadas
- archivos encontrados por semana/fuente
- conteos de salida
- faltantes
- warnings
- errores
- resumen final

Puedes conservar print, pero el log en archivo debe existir.

### Carpeta de auditoría separada

Crea una carpeta auxiliar dentro de `TARGET_BASE`, por ejemplo `_auditoria_preprocessing`. Todo artefacto nuevo debe vivir ahí o en una estructura equivalente claramente auxiliar.

### Manifest por corrida

Genera un JSON por corrida con al menos:
- timestamp de ejecución
- script name
- source_base
- target_base
- total_weeks_detected
- total_weeks_processed
- total_outputs_generated
- total_missing_by_media
- errores detectados
- ruta del log
- versión o firma de la corrida si lo consideras útil

### Tabla de auditoría por semana y fuente

Genera CSV con columnas como mínimo:
- `run_timestamp`
- `week_dir`
- `prefix`
- `media_type`
- `n_files_detected`
- `input_files`
- `output_path`
- `status`
- `extracted_count`
- `unique_count`
- `missing_flag`
- `error_message`
- `notes`

Si para medios ciertos campos no aplican, déjalos nulos, pero mantén consistencia estructural.

### Validaciones operativas

Agrega validaciones claras para:
- inexistencia de `SOURCE_BASE`
- problemas de permisos
- errores al crear directorios
- archivos vacíos
- CSV ilegibles
- encabezados ausentes
- múltiple archivo en medios
- errores de lectura por archivo

Ojo: validar no significa cambiar el comportamiento canónico. Significa volverlo auditable y robusto.

### Manejo de errores por unidad de trabajo

Cada combinación semana/fuente debe poder:
- fallar
- registrar el error
- seguir con el resto cuando sea posible

No hagas fallos silenciosos. No abortes todo salvo que el error sea estructural y realmente lo justifique.

### Trazabilidad de insumos y salidas

Para cada archivo detectado registra, si es razonable:
- ruta absoluta
- tamaño en bytes
- timestamp de modificación
- hash opcional

Para cada salida:
- ruta
- existencia
- tamaño
- hash opcional

Esto es deseable especialmente para auditoría, no para alterar la salida.

### Compatibilidad hacia atrás explícita

Dentro del código y del resumen final deja explícito que:
- la lógica textual histórica se preservó
- la intervención fue estructural
- la salida canónica no fue rediseñada

## Prohibiciones absolutas

Está estrictamente prohibido:

- cambiar cualquier regex histórica si eso puede alterar el texto resultante
- reordenar pasos de limpieza si el resultado puede variar
- conservar acentos, ñ o ü
- usar transliteración distinta
- usar pandas para reemplazar lectura histórica si el comportamiento cambia
- aceptar columnas nuevas en el flujo canónico
- cambiar thresholds de inclusión
- cambiar deduplicación
- cambiar palabras por línea
- reemplazar `words_to_lines`
- escribir salidas por comentario en vez de por bolsa de palabras
- unir medios
- corregir naming histórico
- corregir criterios "raros" del script
- introducir supuestas mejores prácticas que modifiquen el corpus
- reinterpretar silenciosamente archivos
- optimizar semánticamente el contenido
- cambiar la lógica canónica porque "parece mejor"

## Prueba obligatoria de no regresión

Debes hacer una verificación explícita de equivalencia funcional. Haz una prueba controlada comparando la versión original y la versión refactorizada sobre un subconjunto representativo o muestra suficiente. Luego compara los `.txt` canónicos resultantes.

Necesito que reportes explícitamente si:
- son idénticos byte a byte, o
- no lo son

Si no son idénticos, eso no se maquilla. Se reporta como incompatibilidad y se corrige antes de dar por cerrada la tarea.

## Entregables obligatorios

1. Script refactorizado final.
2. Resumen técnico de refactorización estructural.
3. Lista explícita de elementos históricos preservados.
4. Descripción de logs y artefactos de auditoría agregados.
5. Resultado de la prueba de no regresión de outputs canónicos.
6. Riesgos residuales detectados que no se tocaron por preservar compatibilidad histórica.
7. Confirmación expresa de que no se alteró la lógica que afecta el corpus canónico.

## Criterio de aceptación

El trabajo solo se acepta si se cumplen simultáneamente estas condiciones:

- el script queda más sólido y profesional
- la trazabilidad mejora de forma clara
- la auditoría queda persistida en artefactos
- la robustez operativa aumenta
- la compatibilidad histórica se conserva
- la salida canónica `.txt` no cambia
- hay evidencia explícita de no regresión

## Regla final de decisión

Si en algún punto dudas entre hacer algo más elegante o preservar el comportamiento histórico, debes preservar el comportamiento histórico. No improvises. No optimices. No modernices el contenido. No corrijas la metodología. Solo endurece la estructura alrededor del comportamiento histórico congelado.
