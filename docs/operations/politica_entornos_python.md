# Política de entornos Python por subsistema — RAdAR

## Tabla de verdad actual

| Entorno               | Archivo yml                   | Para qué                                   | Estado          |
|-----------------------|-------------------------------|--------------------------------------------|-----------------|
| `radar-ops-py311`     | `environment.ops.yml`         | Extracción, preprocesamiento, ops          | **Operable ya** |
| `radar-modeling-py311`| `environment.modeling.yml`    | Modelado, experimentación, NLP, evaluación | **Operable ya** |
| `radar-exp-py311`     | `environment.experimentos.yml`| Alias histórico del stack de modelado      | Transitorio     |
| `RadaR_3_11`          | *(sin yml canónico anterior)* | Env ad-hoc de extracción actual            | Reemplazado por ops |
| `environment.nlp.yml` | —                             | NLP separado                               | **No creado — no justificado** |

---

## Cuál entorno usar para qué

### Para correr extractores y check_config

```bash
conda activate radar-ops-py311
# o mientras no se haya creado el nuevo:
conda activate RadaR_3_11
```

Incluye: playwright, trafilatura, cloudscraper, apify-client, googleapiclient, pandas, openpyxl.

### Para correr modelado y experimentos

```bash
conda activate radar-modeling-py311
# o equivalente:
conda activate radar-exp-py311
```

Incluye: scikit-learn, xgboost, catboost, lightgbm, prophet, statsmodels, shap, optuna, numpy, pandas.

### Para correr NLP (clasificación de temas, sentimiento)

Usar el entorno de **modelado** (`radar-modeling-py311` o `radar-exp-py311`).
NLP solo necesita pandas + openpyxl — ambos ya están en ese entorno.
No existe ni es necesario un entorno NLP separado.

### Para preprocesamiento

Cualquier entorno funciona. Preprocesamiento es stdlib puro (csv, datetime, pathlib, re).
En la práctica, usar `radar-ops-py311` para mantener consistencia con el contexto operativo.

---

## Por qué ops NO afecta a modeling

`environment.ops.yml` y `environment.modeling.yml` son **entornos conda independientes**.
Crearlos o actualizarlos no afecta al otro de ninguna forma.

Las dependencias son ortogonales:
- Ops tiene: playwright, trafilatura, cloudscraper, apify-client, googleapiclient.
- Modeling tiene: scikit-learn, xgboost, catboost, prophet, statsmodels, shap, optuna.
- No hay conflicto de versiones entre los dos conjuntos.
- Ops deliberadamente omite el stack de ML para mantener el entorno liviano.

---

## Relación entre environment.experimentos.yml y environment.modeling.yml

`environment.experimentos.yml`:
- Fue el primer env canónico del proyecto, nombrado para experimentación.
- Refleja de facto el stack de modelado completo.
- **No se elimina ni se modifica.** Sigue funcionando con `radar-exp-py311`.

`environment.modeling.yml`:
- Es la forma canónica, explícitamente nombrada, del mismo stack.
- Crea el entorno `radar-modeling-py311`.
- Flujos nuevos deben usar este. Flujos existentes pueden seguir con `radar-exp-py311`.

Son **funcionalmente equivalentes**. La diferencia es solo el nombre del entorno conda.

---

## Por qué no existe environment.nlp.yml

La capa NLP de este repo (`src/nlp/`) hace clasificación de temas basada en diccionarios y
cómputo de ponderaciones de sentimiento. Sus únicos deps externos son:

- `pandas` — manipulación de datos
- `openpyxl` — lectura/escritura de archivos Excel

No usa spacy, nltk, gensim, transformers, ni ninguna librería de NLP especializada.
Ambos paquetes ya están presentes en el entorno de modelado.

Crear `environment.nlp.yml` sería formalismo sin beneficio real.

**Decisión explícita:** NLP corre en el mismo entorno que modelado. Revisitar solo si NLP
incorpora dependencias especializadas que justifiquen la separación.

---

## .env vs entorno conda — diferencia importante

Son dos cosas completamente distintas:

| `.env` (archivo de texto) | Entorno conda (ambiente Python) |
|---|---|
| Contiene credenciales y API keys | Contiene librerías de Python |
| Se carga en runtime por `src/shared/secrets.py` | Se activa con `conda activate` |
| Gitignoreado (secretos, nunca versionar) | El `.yml` sí se versiona |
| Afecta: qué keys tienen los extractores | Afecta: qué paquetes Python están disponibles |
| Ejemplo: `APIFY_TOKEN=xxx` | Ejemplo: `playwright`, `scikit-learn` |

**`.env` no es un entorno Python. Un entorno conda no contiene secretos.**

---

## Estado de secrets y runtime (intervención anterior 2026-04-14)

Ya implementado y operativo:

- `.env` en raíz del repo — gitignoreado, con las keys reales
- `.env.example` — plantilla versionada
- `src/shared/secrets.py` — loader central de `.env` + validación sin exponer valores
- `src/shared/runtime_paths.py` — rutas canónicas de runtime (TWITTER_STATE_PATH, etc.)
- `src/shared/check_config.py` — checker standalone
- `artifacts/state/x_state.json` — state de Playwright para Twitter/X (gitignoreado)

Secretos eliminados de código:
- `SERPER_API_KEY` ya no está hardcodeada en `facebook_extractor_apify_tampico.py`
- `YOUTUBE_API_KEY` ya no está hardcodeada en `youtube_extractor_tampico.py`

---

## Política de artifacts/state/

`artifacts/state/` es la sede canónica de state persistente por sesión:

- `x_state.json` — sesión autenticada de Playwright para Twitter/X
- `*.json` — todos gitignoreados via `.gitignore`
- `*.example.json` — ejemplos de estructura, sí versionados

El state de Twitter/X se reutiliza automáticamente mientras sea válido.
No se regenera salvo que expire o se corrompa (ver `docs/operations/secrets_and_runtime.md`).

---

## Comandos de creación de entornos

### Crear radar-ops-py311

```bash
conda env create -f environment.ops.yml
conda activate radar-ops-py311
playwright install chromium   # requerido para twitter_extractor y medios_extractor
```

### Crear radar-modeling-py311

```bash
conda env create -f environment.modeling.yml
conda activate radar-modeling-py311
python -m ipykernel install --user --name radar-modeling-py311 --display-name "Python (radar-modeling-py311)"
```

### Verificar configuración de secretos (usar env ops)

```bash
conda run -n radar-ops-py311 python -m src.shared.check_config
# o con env existente:
conda run -n RadaR_3_11 python -m src.shared.check_config
```

### Actualizar entorno ops sin afectar modeling

```bash
conda env update -n radar-ops-py311 -f environment.ops.yml --prune
# El entorno de modeling NO se ve afectado.
```

---

## Política de transición

**No hay migración forzosa.** Los flujos existentes que usan `radar-exp-py311` y `RadaR_3_11`
siguen funcionando sin cambios.

La separación es una preparación profesional, no un cierre de la fase actual.

Fases de adopción sugeridas:
1. Crear `radar-ops-py311` y verificar que los extractores funcionan.
2. Usar `radar-ops-py311` para corridas nuevas de extracción.
3. En un momento posterior, retirar `RadaR_3_11` una vez que `radar-ops-py311` esté
   validado en producción.
4. `radar-exp-py311` puede coexistir con `radar-modeling-py311` indefinidamente.

---

## Límites honestos de esta implementación

**Funcional hoy:**
- `environment.ops.yml` — crear con `conda env create` y usar ya
- `environment.modeling.yml` — crear con `conda env create` y usar ya
- Secrets y runtime layer — ya operativo
- check_config — ya operativo

**Preparado para fase posterior:**
- Automatización integral del pipeline end-to-end
- Scheduling periódico
- Integración del orquestador con los entornos separados por subsistema

**No declarado como implementado:**
- Pipeline final cerrado
- Automatización periódica
- Migración forzosa de entornos existentes
