# Intervención: Política de entornos Python por subsistema

**Fecha:** 2026-04-14
**Tipo:** Intervención quirúrgica — separación de entornos
**Estado:** Implementado

---

## Primera regla

NO inventar una arquitectura distinta a la que ya declara el repo.

- El repo se declara como base canónica pre-automatización.
- `src/operations/` es namespace reservado para fase posterior — no debe inflarse.
- Las capas activas hoy son: extracción, preprocesamiento, NLP, modelado.
- `artifacts/` es el lugar canónico para runtime técnico.
- La tarea es profesionalizar entornos y secretos, NO cerrar automatización integral.

---

## Objetivo

Dejar definida e implementada una política profesional de entornos separados por subsistema,
SIN romper el entorno actual de modelado y SIN vender que la automatización ya está terminada.

---

## Diagnóstico de estado actual

| Subsistema      | Deps externas reales                                              | Entorno hoy       |
|-----------------|-------------------------------------------------------------------|-------------------|
| Extracción      | playwright, trafilatura, cloudscraper, apify-client, googleapiclient, requests, pandas | RadaR_3_11 (ad-hoc) |
| Preprocesamiento| ninguna (stdlib puro)                                            | RadaR_3_11 (ad-hoc) |
| NLP             | pandas, openpyxl (solo)                                          | radar-exp-py311   |
| Modelado        | numpy, pandas, scipy, sklearn, xgboost, lgbm, catboost, prophet, statsmodels, shap, optuna | radar-exp-py311 |
| Shared          | ninguna (stdlib puro)                                            | cualquiera        |

**Problema**: extracción usa un env no versionado (`RadaR_3_11`) con deps de scraping que
no pertenecen al stack de modelado. No hay archivo `.yml` que lo formalice.

**No hay problema** en modelado/NLP: ambos conviven bien en `environment.experimentos.yml`.

---

## Decisiones de separación

### `environment.ops.yml` — SÍ, creado y operable

Justificación: extracción necesita playwright, trafilatura, apify-client, cloudscraper,
googleapiclient — deps pesadas de scraping que NO pertenecen en el entorno de modelado.

Preprocesamiento es stdlib puro pero corre en el mismo contexto operativo que extracción.
Lo incluimos para que `environment.ops.yml` sea el entorno único para la capa operativa.

### `environment.modeling.yml` — SÍ, creado como forma canónica

`environment.experimentos.yml` sigue intacto. `environment.modeling.yml` es su nombre
canónico claro para uso futuro. Son funcionalmente equivalentes.

### `environment.nlp.yml` — NO, no justificado

NLP usa solo pandas + openpyxl. Ambos ya están en el entorno de modelado.
No hay librería especializada (no spacy, no nltk, no transformers, no gensim).
Crear un env separado sería puro formalismo sin beneficio real.
Decisión explícitamente documentada y diferida.

---

## Qué se implementó

- `environment.ops.yml`: nuevo, operable
- `environment.modeling.yml`: nuevo, equivalente a `environment.experimentos.yml`
- `environment.experimentos.yml`: conservado intacto
- `docs/operations/politica_entornos_python.md`: documentación autoritativa
- `environment.nlp.yml`: NO creado (decisión documentada)

---

## Qué NO se tocó

- `environment.experimentos.yml` — intacto
- `src/modeling/` — intacto
- Contratos metodológicos de modelado — intactos
- Estructura de `src/operations/` — no se infló más allá de la intervención anterior
- Ningún runner activo de extracción o modelado

---

## Límites honestos

- `environment.ops.yml` está definido para `conda env create`. Requiere `playwright install chromium` posterior.
- `environment.modeling.yml` replica el stack de `environment.experimentos.yml`. No hay migración de flujos existentes requerida.
- La separación de envs es una preparación profesional, no un cierre de automatización.
