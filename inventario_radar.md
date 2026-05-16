# RAdAR — Inventario Exhaustivo de Componentes del Repositorio

**Branch:** `feature/restructuracion-arquitectonica-repo`  
**Fecha de generación:** 10 de mayo de 2026

---

## Arquitectura General

El repositorio está organizado en **8 capas funcionales**, cada una con un rol definido en el pipeline de predicción de aprobación política (RAdAR). El flujo general es:

```
GUI/CLI → Pipeline Orchestrator → Stages (preflight → extraction → preprocessing → NLP → modeling → export → report)
```

En modo post-W10, el pipeline usa **frozen inference** en lugar de re-entrenar modelos, generando emisiones (predicciones) a partir de perfiles congelados.

---

## CAPA 1: RAÍZ — Entrada y configuración del sistema

| Archivo | Función | Genera | Conecta con |
|---------|---------|--------|-------------|
| `launch_radar_gui.py` | Punto de entrada gráfico. Lanza la GUI Tkinter del pipeline. | — | `gui_radar_pipeline.py` |
| `environment.ops.yml` | Define el entorno conda `radar-ops-py311` (extracción, preprocessing, NLP, operaciones). | Entorno conda ops | — |
| `environment.modeling.yml` | Define el entorno conda `radar-modeling-py311` (modelado, experimentos). | Entorno conda modeling | — |
| `.env` | Variables de entorno con API keys y secretos (no versionado). | — | `shared/secrets.py` |

---

## CAPA 2: SHARED — Infraestructura transversal

| Archivo | Función | Genera | Conecta con |
|---------|---------|--------|-------------|
| `shared/runtime_paths.py` | Define todas las rutas canónicas dghhhhhhhhhhhhh             |        |                                        |
|                           |                                                              |        |                                        |
|                           |                                                              |        |                                        |
|                           | Logger compartido. Configura formato y niveles de log consistentes en todo el sistema. | — | Extractores, preprocessing, operations |

---

## CAPA 3: EXTRACTION — Recolección de datos crudos

| Archivo | Función | Genera | Conecta con |
|---------|---------|--------|-------------|
| `extraction/runners/facebook_institutional_extractor_core.py` | Extrae publicaciones y comentarios de páginas de Facebook institucionales usando Playwright + Apify. | CSVs raw, manifests en `data/raw/` | `secrets.py`, `runtime_paths.py` |
| `extraction/runners/twitter_extractor_tampico.py` | Extrae tweets de cuentas objetivo usando estado de sesión persistente (`x_state.json`). | CSVs raw | `runtime_paths.py`, `x_state.json` |
| `extraction/runners/youtube_extractor_tampico.py` | Extrae comentarios de videos de YouTube via API. | CSVs raw | `secrets.py` |
| `extraction/runners/medios_extractor.py` | Extrae noticias de medios digitales vía Google News RSS y parsing de contenido. | CSVs raw | `runtime_paths.py` |

---

## CAPA 4: PREPROCESSING — Transformación de datos crudos a texto limpio

| Archivo | Función | Genera | Conecta con |
|---------|---------|--------|-------------|
| `preprocessing/ejecutar_preprocesamiento_base.py` | Orquestador de las 8 subetapas de preprocesamiento. Ejecuta secuencialmente la limpieza, normalización y estructuración del corpus. | Logs, carpetas intermedias | 8 subetapas internas |
| `preprocessing/promover_raw_a_texto.py` | Subetapa: promueve datos crudos (CSVs) al formato texto limpio semanal (`radar_weekly_flat/`). | `data/text/radar_weekly_flat/` | `runtime_paths.py` |
| *Otras 7 subetapas* | Limpieza de texto, normalización, deduplicación, tokenización, etc. Cada una transforma progresivamente el corpus. | Archivos intermedios en `data/text/` | `ejecutar_preprocesamiento_base.py` |

---

## CAPA 5: NLP — Análisis de lenguaje natural y construcción del dataset ML

| Archivo | Función | Genera | Conecta con |
|---------|---------|--------|-------------|
| `nlp/aceptacion_digital_redes_ponderacion_medios.py` | Calcula sentimiento semanal ponderado por fuente (redes vs medios). Aplica diccionarios de sentimiento al corpus procesado. | `sentimiento_semanal.xlsx` | `data/text/`, diccionarios de sentimiento |
| `nlp/clasificacion_temas_pmi_confianza.py` | Clasifica cada texto en temas temáticos usando PMI (Pointwise Mutual Information) con scores de confianza. | Clasificación temática | Corpus procesado |
| `nlp/generar_ml_ready_encuestas_pmi.py` | Fusiona datos de encuestas con clasificación temática PMI para generar el dataset pre-ML. | `datos_ml_0.xlsx` | Sentimiento, PMI, encuestas |
| `nlp/unir_ml_ready_con_sentimiento.py` | Paso final: une el dataset pre-ML con sentimiento semanal para producir el dataset maestro de modelado. | **`datos_ml_master.xlsx`** (artefacto crítico) | `generar_ml_ready`, `aceptacion_digital` |

---

## CAPA 6: MODELING — Experimentación y modelado predictivo

### Core (infraestructura compartida de modelado)

| Archivo | Función | Genera | Conecta con |
|---------|---------|--------|-------------|
| `modeling/core/config.py` | Constantes y configuración central de modelado: horizontes, variables target, parámetros globales. | — | Todos los runners, frozen inference |
| `modeling/core/data_master.py` | Carga y prepara `datos_ml_master.xlsx` como DataFrame estandarizado para todos los modelos. | — | Todos los runners, `frozen_inference_assets.py` |
| `modeling/core/feature_engineering.py` | Pipeline de ingeniería de features: lag features, rolling windows, interacciones, transformaciones temporales. | — | Runners, frozen inference |

### Runners (familias experimentales E1–E10)

| Archivo | Familia | Algoritmo | Genera | Conecta con |
|---------|---------|-----------|--------|-------------|
| `modeling/runners/run_e1_ridge_clean.py` | E1 | Ridge Regression | `experiments/runs/E1_*/` (metadata, params, predicciones por horizonte) | `core/*`, `tracking/`, exporta `build_estimator()` |
| `modeling/runners/run_e2_huber_clean.py` | E2 | Huber Regression | `experiments/runs/E2_*/` | `core/*`, `tracking/`, exporta `build_estimator()` |
| `modeling/runners/run_e3_random_forest.py` | E3 | Random Forest | `experiments/runs/E3_*/` | `core/*`, `tracking/`, exporta `build_estimator()` |
| `modeling/runners/run_e5_catboost.py` | E5 | CatBoost | `experiments/runs/E5_*/` | `core/*`, `tracking/`, exporta `build_estimator()` |
| `modeling/runners/run_e7_prophet.py` | E7 | Prophet (series de tiempo) | `experiments/runs/E7_*/` | `core/*`, `tracking/`, exporta `build_estimator()` |
| `modeling/runners/run_e9_stacking.py` | E9 | Stacking Meta-Model | `experiments/runs/E9_*/` con `predicciones_h*.csv` | `core/*`, `tracking/` |
| `modeling/runners/run_e10_meta_selector.py` | E10 | Meta-Selector (selección automática de modelo) | `experiments/runs/E10_*/` | `core/*`, `tracking/` |

### Tracking y reporting

| Archivo | Función | Genera | Conecta con |
|---------|---------|--------|-------------|
| `modeling/tracking/experiment_logger.py` | Registra metadata de cada run experimental en JSON estandarizado (hiperparámetros, métricas, timestamps). | JSON por run | Todos los runners |
| `modeling/reporting/build_experiments_master_table.py` | Consolida todos los runs en una tabla maestra comparativa de métricas. | Excel maestra en `experiments/audit/` | `experiments/runs/` |

---

## CAPA 7: OPERATIONS — Orquestación del pipeline y frozen inference

### Pipeline principal

| Archivo | Función | Genera | Conecta con |
|---------|---------|--------|-------------|
| `operations/config.py` | Configuración operativa: modos de ejecución, flags, parámetros del pipeline. | — | Todo el módulo operations |
| `operations/contracts.py` | Define contratos (interfaces) entre stages: qué datos espera cada stage y qué produce. | — | `pipeline_orchestrator.py`, stages |
| `operations/run_context.py` | Contexto de ejecución: encapsula el estado de un run (timestamp, modo, rutas, configuración activa). | — | `pipeline_orchestrator.py`, stages, `build_emission_registry` |
| `operations/state_store.py` | Persiste el estado de cada run del pipeline en JSON para trazabilidad y recovery. | `artifacts/operations/run-*/state.json` | `pipeline_orchestrator.py` |
| `operations/pipeline_orchestrator.py` | Orquestador central: ejecuta stages en secuencia, maneja errores, registra estado. Es el cerebro del pipeline. | `artifacts/operations/run-*/stages/*.json` | `run_radar_pipeline.py`, stages |
| `operations/run_radar_pipeline.py` | CLI principal: punto de entrada por línea de comandos. Parsea argumentos y lanza el orchestrator. | — (CLI) | `pipeline_orchestrator.py` |
| `operations/gui_radar_pipeline.py` | GUI Tkinter: interfaz gráfica que invoca el CLI via subprocess. | — (GUI) | `run_radar_pipeline.py` via subprocess |

### Stages (etapas del pipeline)

| Archivo | Stage | Función | Genera | Conecta con |
|---------|-------|---------|--------|-------------|
| `operations/stages/preflight_stage.py` | Preflight | Verifica secretos, rutas y configuración antes de ejecutar. Gate de validación. | — | `secrets.py`, `runtime_paths.py`, `contracts.py` |
| `operations/stages/extraction_stage.py` | Extraction | Invoca los extractores de Facebook, Twitter, YouTube y medios. | Datos en `data/raw/`, artefactos en `artifacts/runs/extraction/` | Runners extraction, `run_context.py`, `contracts.py` |
| `operations/stages/preprocessing_stage.py` | Preprocessing | Invoca el orquestador de preprocesamiento. | Datos en `data/text/`, logs | `ejecutar_preprocesamiento_base.py`, `run_context.py`, `contracts.py` |
| `operations/stages/nlp_stage.py` | NLP | Ejecuta la cadena NLP completa hasta producir el dataset maestro. | `datos_ml_master.xlsx` | Módulos NLP, `run_context.py`, `contracts.py` |
| `operations/stages/modeling_stage.py` | Modeling | Ejecuta modelado (modo normal: E10 meta-selector; modo post-W10: frozen inference). | Artefactos de corrida o registro de emisiones | Runners modeling o `build_emission_registry`, `run_context.py`, `contracts.py` |
| `operations/stages/export_stage.py` | Export | Exporta resultados a formato PowerBI. | `published/powerbi/`, manifest | `run_context.py`, `contracts.py` |
| `operations/stages/report_stage.py` | Report | Stub para futura generación de reportes narrativos. | `published/report_inputs/` (stub) | `run_context.py`, `contracts.py` |

### Post-W10: Sistema de Frozen Inference

| Archivo | Función | Genera | Conecta con |
|---------|---------|--------|-------------|
| `operations/frozen_profiles.py` | Define la estructura de datos de un perfil congelado: qué contiene, cómo se valida, cómo se carga. Registro canónico de los 6 modelos (E1, E2, E3, E5, E7, E9). | — | `frozen_inference_assets.py`, `frozen_inference.py`, `build_emission_registry` |
| `operations/frozen_inference_assets.py` | **Componente crítico.** Serializa los modelos entrenados como perfiles congelados. Para E1/E2/E3/E5/E7: reconstruye cada modelo via `build_estimator()` con hiperparámetros terminales extraídos de `predicciones_h*.csv`. Para E9: carga la tabla maestra curada como frame de entrenamiento del meta-modelo. | `frozen_inference_profiles/*/` (`.pkl` + `spec_hX.json` + `manifest.json`) | `frozen_profiles.py`, runners' `build_estimator`, `modeling/core/*`, `experiments/runs/*/predicciones_h*.csv`, `tabla_maestra_e9_curada.xlsx` |
| `operations/frozen_inference.py` | Motor de inferencia: carga perfiles congelados, aplica feature engineering, genera predicciones por horizonte. Para E9: orquesta la cascada (primero predice con modelos base, luego alimenta al meta-modelo). | `PendingForecastBundle` (en memoria) | `frozen_inference_assets.py`, `frozen_profiles.py`, `modeling/core/feature_engineering.py` |
| `operations/bootstrap_frozen_inference_assets.py` | Script one-shot: ejecuta `frozen_inference_assets.py` para serializar los 6 perfiles (E1, E2, E3, E5, E7, E9) desde los artefactos experimentales existentes. | 6 perfiles serializados en `frozen_inference_profiles/` | `frozen_inference_assets.py` |
| `operations/build_emission_registry_post_w10.py` | Genera el **registro de emisiones**: ejecuta frozen inference sobre datos nuevos y persiste predicciones con trazabilidad completa (CSV, JSON, snapshots). | `emisiones/*.csv`, `emisiones/*.json`, `snapshots/`, `emission_registry_summary.json` | `frozen_inference.py`, `frozen_profiles.py`, `frozen_inference_assets.py`, `run_context.py` |
| `operations/run_operacion_minima_post_w10.py` | Wrapper CLI minimalista para ejecutar el registro de emisiones sin pasar por el pipeline completo. | — (wrapper CLI) | `build_emission_registry_post_w10.py` |

---

## CAPA 8: EXPERIMENTS — Investigación y auditoría histórica

### Subcarpetas

| Ruta | Función | Conecta con |
|------|---------|-------------|
| `experiments/research/` | Documentos metodológicos por familia experimental (E1–E11): resúmenes de enfoque, decisiones de diseño, actualizaciones post-E9. Referencia de contexto, no genera artefactos. | — (solo lectura humana) |
| `experiments/prompts/` | Historial cronológico de prompts de desarrollo (carpetas 01 a 35). Solo referencia histórica. | — (solo lectura humana) |
| `experiments/runs/` | Artefactos de todos los runs ejecutados. Estructura: `{RUN_ID}_{TIMESTAMP}/` con metadata JSON, parameters JSON, y `predicciones_h*.csv` por horizonte. | `frozen_inference_assets.py` (lee specs terminales de E1, E2, E3, E5, E7, E9) |

### Artefactos de auditoría

| Archivo | Función | Conecta con |
|---------|---------|-------------|
| `experiments/audit/resumen_auditoria_experimentos.md` | Ranking curado de los 37 runs maestros con métricas comparativas. Referencia para decisiones de selección de modelo. | — (solo lectura humana) |
| `experiments/audit/tabla_maestra_experimentos_radar_e9_curada.xlsx` | **Artefacto de datos crítico.** Contiene las predicciones aprobadas de los modelos base por horizonte, con control de calidad manual. Es la **única entrada externa** que `frozen_inference_assets.py._load_e9_curated_training_frame()` lee para reconstruir el meta-modelo de E9. | `frozen_inference_assets.py` (input crítico para E9) |

---

## CAPA 9: DOCS — Documentación autoritativa

| Archivo | Función |
|---------|---------|
| `docs/README.md` | Índice de documentación. Declara `docs/` como fuente de verdad arquitectónica (overridea `experiments/`). |
| `docs/architecture/repository_architecture.md` | Estructura física del repo capa por capa, estado de implementación de cada una. |
| `docs/architecture/repository_governance.md` | Gobernanza: criterios para cambios, quién decide qué en cada capa. |
| `docs/architecture/structural_audit.md` | Auditoría y veredicto de la reestructuración. Estatus: **aprobada**. |
| `docs/operations/README.md` | Documentación operativa general del pipeline. |
| `docs/operations/secrets_and_runtime.md` | Configuración de API keys en `.env`, generación de `x_state.json` para Twitter (login manual con Playwright). |
| `docs/operations/politica_entornos_python.md` | Política de entornos: cuándo usar `radar-ops-py311` vs `radar-modeling-py311` y justificación de la separación. |
| `docs/operations/intervencion_envs_ops_modeling.md` | Guía de debugging para problemas con entornos conda. |
| `docs/migration/repository_restructure_migration.md` | Trazabilidad completa de la migración: qué se movió, de dónde, por qué. |

---

## ARTEFACTOS EN DISCO (artifacts/)

| Ruta | Contenido | Generado por |
|------|-----------|--------------|
| `artifacts/operations/run-*/state.json` | Estado persistido de cada run del pipeline | `state_store.py` |
| `artifacts/operations/run-*/stages/*.json` | Resultado de cada stage por run | `pipeline_orchestrator.py` |
| `artifacts/operations/frozen_inference_profiles/E1/` | `manifest.json` + `horizons/model_hX.pkl` + `horizons/spec_hX.json` | `frozen_inference_assets.py` |
| `artifacts/operations/frozen_inference_profiles/E2/` | Ídem E1 | `frozen_inference_assets.py` |
| `artifacts/operations/frozen_inference_profiles/E3/` | Ídem E1 | `frozen_inference_assets.py` |
| `artifacts/operations/frozen_inference_profiles/E5/` | Ídem E1 | `frozen_inference_assets.py` |
| `artifacts/operations/frozen_inference_profiles/E7/` | Ídem E1 | `frozen_inference_assets.py` |
| `artifacts/operations/frozen_inference_profiles/E9_v2_clean/` | `manifest.json` (`package_kind: stacking_meta_model`, `dependencies: [E1,E2,E3,E5,E7]`) + `horizons/model_hX.pkl` (meta-modelo por horizonte) | `frozen_inference_assets.py` |

---

## Mapa de Conexiones: Flujo Principal

```
launch_radar_gui.py
  └→ gui_radar_pipeline.py  [Tkinter, subprocess]
       └→ run_radar_pipeline.py  [CLI principal]
            └→ pipeline_orchestrator.py
                 ├→ preflight_stage.py
                 │    └→ secrets.py, runtime_paths.py
                 ├→ extraction_stage.py
                 │    ├→ facebook_institutional_extractor_core.py
                 │    ├→ twitter_extractor_tampico.py
                 │    ├→ youtube_extractor_tampico.py
                 │    └→ medios_extractor.py
                 ├→ preprocessing_stage.py
                 │    └→ ejecutar_preprocesamiento_base.py
                 │         └→ [8 subetapas]
                 ├→ nlp_stage.py
                 │    ├→ aceptacion_digital_redes_ponderacion_medios.py
                 │    ├→ clasificacion_temas_pmi_confianza.py
                 │    ├→ generar_ml_ready_encuestas_pmi.py
                 │    └→ unir_ml_ready_con_sentimiento.py → datos_ml_master.xlsx
                 ├→ modeling_stage.py
                 │    ├→ [modo normal] run_e10_meta_selector.py
                 │    └→ [modo post-W10] build_emission_registry_post_w10.py
                 │         └→ frozen_inference.py
                 │              └→ frozen_inference_assets.py
                 │                   ├→ frozen_profiles.py
                 │                   ├→ build_estimator() de E1/E2/E3/E5/E7
                 │                   ├→ modeling/core/data_master.py
                 │                   ├→ modeling/core/feature_engineering.py
                 │                   ├→ experiments/runs/*/predicciones_h*.csv
                 │                   └→ experiments/audit/tabla_maestra_e9_curada.xlsx
                 ├→ export_stage.py
                 └→ report_stage.py  [stub]
```

---

## Dependencias Clave entre Capas

1. **Frozen Inference depende de Experiments:** Los perfiles congelados se construyen leyendo `predicciones_h*.csv` de runs históricos y la tabla maestra curada de E9.
2. **NLP produce el artefacto central:** `datos_ml_master.xlsx` es el dataset que alimenta tanto el modelado experimental como frozen inference.
3. **E9 es un meta-modelo:** Depende de las predicciones de E1, E2, E3, E5 y E7 como features de entrada. Su perfil congelado tiene `dependencies: [E1,E2,E3,E5,E7]`.
4. **Dos modos de operación:** El `modeling_stage.py` bifurca entre modo normal (re-entrenamiento via E10) y modo post-W10 (frozen inference + registro de emisiones).
5. **Dos entornos conda separados:** `radar-ops-py311` para todo excepto modelado; `radar-modeling-py311` para runners y experimentación.

# Inventario maestro de arquitectura del repo RAdAR

## Propósito de este documento

Este documento describe los componentes del repositorio **RAdAR** desde una doble lógica:

1. **Técnica**: usando los términos correctos de arquitectura de software, operación de pipelines, trazabilidad, inferencia, artefactos, contratos y capas.
2. **Explicativa**: aclarando cada término como si el lector no tuviera por qué conocer ese vocabulario de antemano.

La idea es que este inventario sirva al mismo tiempo como:

- documento de arquitectura operativa,
- mapa de responsabilidades del repo,
- guía de lectura del árbol,
- y referencia para futuras auditorías o refactors.

**Alcance:**

- se inventarian componentes versionados del repo,
- se excluye el contenido de `data/` como datos,
- pero sí se explica cómo las capas se conectan con `data/` y con `artifacts/`.

------

# 1. Vista general del sistema

## 1.1 Qué es este repo en términos técnicos

El repositorio está organizado como una **arquitectura por capas**.

Eso significa que no todo el código está mezclado en una sola carpeta, sino separado por responsabilidad:

- una capa para **adquirir datos**,
- otra para **normalizarlos y promoverlos**,
- otra para **convertir texto en variables modelables**,
- otra para **modelar o inferir**,
- y otra para **coordinar la ejecución completa**.

### En lenguaje simple

Piensa en una línea de producción:

- una parte baja el material,
- otra lo limpia,
- otra lo convierte en piezas útiles,
- otra aplica el modelo,
- y otra supervisa que todo corra en orden.

------

## 1.2 Taxonomía oficial del repo

El gobierno del repositorio divide todo en seis zonas raíz:

- `src/`: código activo canónico
- `data/`: datos canónicos
- `artifacts/`: runtime técnico
- `docs/`: documentación estructural y operativa
- `experiments/`: evidencia experimental, prompts, auditoría y runs históricos
- `legacy/`: material histórico fuera del flujo canónico

### Traducción simple

- `src/` = donde vive el sistema actual
- `data/` = donde viven los datos del sistema
- `artifacts/` = lo que el sistema va dejando al correr
- `docs/` = las reglas y explicaciones
- `experiments/` = la bitácora experimental
- `legacy/` = lo viejo que no se borra, pero ya no manda

------

## 1.3 Flujo general del sistema

El flujo lógico del proyecto es este:

```
extraction -> preprocessing -> nlp -> modeling -> operations/publicación
```

Más precisamente:

1. `src/extraction/` adquiere datos por fuente.
2. `src/preprocessing/` normaliza, completa faltantes y promueve a texto.
3. `src/nlp/` transforma texto en variables semanales y datasets modelables.
4. `src/modeling/` define dataset maestro, features, validación, familias de modelos y tracking.
5. `src/operations/` coordina corridas operativas, reanudación, publicación y la operación controlada post-W10.

### Traducción simple

El repo no está hecho para que un solo script haga todo. Está dividido en estaciones. Cada estación recibe una salida de la anterior y la convierte en la entrada de la siguiente.

------

# 2. Raíz del repositorio

## 2.1 `README.md`

- **Capa:** documentación raíz / onboarding.
- **Función técnica:** documento de entrada del repositorio; resume estructura, objetivos y estado real de implementación.
- **Conexiones:** apunta conceptualmente a todas las capas.
- **Artefactos que genera:** ninguno.
- **Artefactos que consume:** ninguno.

### Explicación simple

Es la puerta de entrada. Sirve para que alguien entienda qué es el repo y qué partes ya existen o todavía faltan.

------

## 2.2 `.env.example`

- **Capa:** configuración.
- **Función técnica:** plantilla de variables de entorno; define qué secretos o parámetros de entorno necesita el sistema.
- **Conexiones:** `src/shared/secrets.py`, `src/shared/check_config.py`, preflight y operaciones.
- **Artefactos:** no genera runtime; establece el contrato de configuración.

### Explicación simple

Es una lista modelo de “cosas que el sistema necesita para correr”, por ejemplo claves, rutas o nombres de variables.

------

## 2.3 `.gitignore`

- **Capa:** gobierno de versionado.
- **Función técnica:** evitar que se suban al repo archivos que no deben versionarse, como caches, estados, entornos, logs o artefactos de ejecución.
- **Conexiones:** `artifacts/`, sesiones, caches, entornos virtuales.
- **Artefactos:** ninguno.

### Explicación simple

Es la lista de cosas que Git debe ignorar para no llenar el repo de basura técnica o de archivos regenerables.

------

## 2.4 `CONTRIBUTING.md`

- **Capa:** gobernanza colaborativa.
- **Función técnica:** reglas de colaboración y contribución.
- **Conexiones:** mantenimiento del repo.
- **Artefactos:** ninguno.

### Explicación simple

Es el documento que dice cómo se supone que se trabaja aquí sin desordenar el proyecto.

------

## 2.5 `environment.experimentos.yml`

- **Capa:** infraestructura de entorno.
- **Función técnica:** define dependencias del entorno de experimentación.
- **Conexiones:** `experiments/`, runners experimentales, modelado de investigación.
- **Artefactos:** un entorno instalable, no un artefacto de pipeline.

### Explicación simple

Es la receta del entorno donde corren los experimentos.

------

## 2.6 `environment.modeling.yml`

- **Capa:** infraestructura de entorno.
- **Función técnica:** define dependencias del entorno de modelado.
- **Conexiones:** `src/modeling/`, inferencia/modelado desde `src/operations/`.
- **Artefactos:** entorno instalable.

### Explicación simple

Es la receta del entorno que necesita la parte de modelado del sistema.

------

## 2.7 `environment.ops.yml`

- **Capa:** infraestructura de entorno.
- **Función técnica:** define el entorno operativo para extracción, preprocessing, NLP y utilidades operativas.
- **Conexiones:** `src/extraction/`, `src/preprocessing/`, `src/nlp/`, `src/operations/`.
- **Artefactos:** entorno instalable.

### Explicación simple

Es la receta del entorno que necesita la parte operativa del sistema.

------

## 2.8 `launch_radar_gui.py`

- **Capa:** launcher raíz.
- **Función técnica:** punto de arranque simple para lanzar la GUI de control.
- **Conexiones:** `src/operations/gui_radar_pipeline.py`.
- **Artefactos:** no genera propios; dispara corridas que sí generan artefactos.

### Explicación simple

Es un acceso directo para abrir la interfaz gráfica del pipeline.

------

## 2.9 `setup_env_experimentos.sh`

- **Capa:** bootstrap de entorno.
- **Función técnica:** automatiza la preparación del entorno experimental.
- **Conexiones:** `environment.experimentos.yml`.
- **Artefactos:** entorno local preparado.

### Explicación simple

Es un script de instalación para dejar listo el ambiente de experimentación.

------

## 2.10 `setup_env_ops.sh`

- **Capa:** bootstrap de entorno.
- **Función técnica:** automatiza la preparación del entorno operativo.
- **Conexiones:** `environment.ops.yml`.
- **Artefactos:** entorno local preparado.

### Explicación simple

Es un instalador rápido para dejar lista la parte operativa.

------

# 3. `src/`: código activo canónico

## 3.1 `src/README.md`

- **Capa:** documentación de código activo.
- **Función técnica:** define qué es `src/`, qué puede vivir ahí y qué no.
- **Conexiones:** todas las subcapas.
- **Artefactos:** ninguno.

### Explicación simple

Es el reglamento interno del código vivo del sistema.

------

## 3.2 `src/__init__.py`

- **Capa:** paquete Python raíz.
- **Función técnica:** marca `src/` como paquete importable.
- **Conexiones:** todos los submódulos que hacen imports tipo `from src...`.
- **Artefactos:** ninguno.

### Explicación simple

Le dice a Python: “esta carpeta forma parte de una estructura de módulos seria; puedes importarla ordenadamente”.

------

# 4. `src/extraction/`: adquisición por fuente

## 4.1 `src/extraction/README.md`

- **Capa:** extracción.
- **Función técnica:** documenta que esta capa contiene runners de adquisición por fuente y aclara qué scripts escriben dato canónico y cuáles generan artefacto intermedio.
- **Conexiones:** `src/preprocessing/`, `artifacts/state/`, `artifacts/cache/`, `data/raw/...`.
- **Artefactos:** documentación de frontera.

### Explicación simple

Es el mapa de la parte que baja la información desde afuera.

------

## 4.2 `src/extraction/__init__.py`

- **Capa:** extracción.
- **Función técnica:** marca la carpeta como paquete importable.
- **Conexiones:** runners y utilitarios de extracción.
- **Artefactos:** ninguno.

### Explicación simple

Cumple la misma función estructural que otros `__init__.py`: ordenar imports.

------

## 4.3 `src/extraction/runners/`

- **Capa:** extracción.
- **Función técnica:** concentra runners por fuente.
- **Conexiones:** `data/raw/radar_weekly_flat/`, `artifacts/runs/extraction/...`, `artifacts/state/`, `artifacts/cache/`.
- **Artefactos:** archivos semanales canónicos o artefactos intermedios.

### Explicación simple

Aquí están los ejecutables concretos que bajan datos de cada fuente.

------

## 4.4 `src/extraction/runners/twitter_extractor_tampico.py`

- **Capa:** extracción.
- **Función técnica:** runner de adquisición de Twitter/X para Tampico.
- **Conexiones:** raw semanal canónico.
- **Artefactos:** archivos semanales canónicos en `data/raw/radar_weekly_flat/`.

### Explicación simple

Es el script que baja Twitter/X y lo deja en el formato semanal esperado.

------

## 4.5 `src/extraction/runners/youtube_extractor_tampico.py`

- **Capa:** extracción.
- **Función técnica:** runner de adquisición de YouTube.
- **Conexiones:** raw semanal canónico.
- **Artefactos:** archivos semanales canónicos en `data/raw/radar_weekly_flat/`.

### Explicación simple

Hace lo mismo que el de Twitter, pero para YouTube.

------

## 4.6 `src/extraction/runners/medios_extractor.py`

- **Capa:** extracción.
- **Función técnica:** adquisición de medios y emisión del `.txt` canónico ya limpiado y segmentado.
- **Conexiones:** promoción posterior a `data/text/`.
- **Artefactos:** `*_medios.txt` canónico en `data/raw/radar_weekly_flat/`.

### Explicación simple

Este script no solo baja medios: además deja el texto ya cortado en el formato que el pipeline espera después.

------

## 4.7 `src/extraction/runners/facebook_extractor_apify_tampico.py`

- **Capa:** extracción.
- **Función técnica:** adquisición de Facebook institucional mediante Apify.
- **Conexiones:** `src/preprocessing/`.
- **Artefactos:** artefactos intermedios de adquisición en `artifacts/runs/extraction/facebook/`.

### Explicación simple

Facebook está tratado distinto: este script baja material, pero todavía no lo deja en el formato canónico final. Esa promoción ocurre después.

------

# 5. `src/preprocessing/`: promoción y normalización

## 5.1 `src/preprocessing/README.md`

- **Capa:** preprocessing.
- **Función técnica:** define esta capa como responsable de normalizar el raw semanal, completar faltantes y promover a texto.
- **Conexiones:** extracción, `data/raw/`, `data/text/`, logs de preprocessing.
- **Artefactos:** ninguno directo; documenta el stage.

### Explicación simple

Es el mapa de la parte que ordena lo que se bajó y lo deja listo para NLP.

------

## 5.2 `src/preprocessing/__init__.py`

- **Capa:** preprocessing.
- **Función técnica:** marca la carpeta como paquete Python.
- **Conexiones:** wrapper y scripts del stage.
- **Artefactos:** ninguno.

### Explicación simple

Es estructura de paquete, no lógica de negocio.

------

## 5.3 `src/preprocessing/ejecutar_preprocesamiento_base.py`

- **Capa:** preprocessing.
- **Función técnica:** wrapper canónico del stage; coordina la secuencia base de preprocessing.
- **Conexiones:** scripts específicos del stage.
- **Artefactos:** outputs del stage y logs asociados.

### Explicación simple

Es el script que ordena la secuencia básica del preprocesamiento sin que tengas que correr todo a mano uno por uno.

------

## 5.4 `src/preprocessing/prefijar_carpetas_semanales.py`

- **Capa:** preprocessing.
- **Función técnica:** agrega prefijo ISO a carpetas semanales heredadas.
- **Conexiones:** naming semanal histórico.
- **Artefactos:** carpetas renombradas/normalizadas.

### Explicación simple

Sirve para que carpetas viejas queden con el formato correcto de semana.

------

## 5.5 `src/preprocessing/normalizar_semanas_canonicas.py`

- **Capa:** preprocessing.
- **Función técnica:** normaliza naming, crea semanas faltantes y reporta faltantes.
- **Conexiones:** organización semanal canónica.
- **Artefactos:** estructura semanal homogénea.

### Explicación simple

Hace que el sistema tenga semanas ordenadas, nombradas igual y sin huecos silenciosos.

------

## 5.6 `src/preprocessing/distribuir_facebook_semanal.py`

- **Capa:** preprocessing.
- **Función técnica:** asigna archivos Facebook ya cortados por rango semanal.
- **Conexiones:** artefactos intermedios de Facebook.
- **Artefactos:** semana Facebook distribuida.

### Explicación simple

Toma el material de Facebook ya bajado y lo acomoda en la semana correcta.

------

## 5.7 `src/preprocessing/distribuir_medios_semanales.py`

- **Capa:** preprocessing.
- **Función técnica:** asigna TXT o CSV externos de medios a semanas.
- **Conexiones:** ingresos externos / medios.
- **Artefactos:** semanas de medios distribuidas.

### Explicación simple

Sirve para poner material de medios en la semana que le corresponde.

------

## 5.8 `src/preprocessing/completar_facebook_semanal_desde_mensual.py`

- **Capa:** preprocessing.
- **Función técnica:** genera faltantes semanales de Facebook a partir de fuente mensual.
- **Conexiones:** disponibilidad parcial de datos.
- **Artefactos:** semanas Facebook completadas.

### Explicación simple

Si no tienes semanas separadas pero sí tienes un bloque mensual, este script ayuda a reconstruir lo semanal.

------

## 5.9 `src/preprocessing/completar_twitter_semanal_desde_mensual.py`

- **Capa:** preprocessing.
- **Función técnica:** completa semanas de Twitter desde fuente mensual.
- **Conexiones:** mismo patrón que Facebook.
- **Artefactos:** semanas Twitter completadas.

### Explicación simple

Hace para Twitter lo que el anterior hace para Facebook.

------

## 5.10 `src/preprocessing/completar_youtube_semanal_desde_mensual.py`

- **Capa:** preprocessing.
- **Función técnica:** completa semanas de YouTube desde fuente mensual.
- **Conexiones:** mismo patrón de completado semanal.
- **Artefactos:** semanas YouTube completadas.

### Explicación simple

Reconstruye semanas de YouTube cuando la fuente original viene agregada de otro modo.

------

## 5.11 `src/preprocessing/promover_raw_a_texto.py`

- **Capa:** preprocessing.
- **Función técnica:** promueve `data/raw/` semanal hacia `data/text/`.
- **Conexiones:** salida de preprocessing, entrada de NLP.
- **Artefactos:** corpus textual semanal en `data/text/`.

### Explicación simple

Convierte o copia el material semanal al lugar donde NLP espera encontrar texto listo para trabajar.

------

## 5.12 `src/preprocessing/importar_semanas_main_a_raw.py`

- **Capa:** preprocessing.
- **Función técnica:** helper de importación hacia raw canónico.
- **Conexiones:** `data/raw/`.
- **Artefactos:** semanas incorporadas a raw.

### Explicación simple

Parece ser una utilidad para meter semanas externas al flujo raw ordenado del sistema.

------

# 6. `src/nlp/`: variables textuales y premodelado

## 6.1 `src/nlp/README.md`

- **Capa:** NLP.
- **Función técnica:** documenta que esta capa sigue siendo activa pero todavía bastante “script-oriented”, con piezas canónicas, de soporte e históricas conviviendo.
- **Conexiones:** preprocessing, modelado, tracking.
- **Artefactos:** ninguno.

### Explicación simple

Es una capa viva, útil y operativa, pero aún no totalmente refinada en submódulos elegantes. Todavía tiene algo de historia encima.

------

## 6.2 `src/nlp/__init__.py`

- **Capa:** NLP.
- **Función técnica:** marca la carpeta como paquete.
- **Conexiones:** scripts NLP y imports desde otras capas.
- **Artefactos:** ninguno.

### Explicación simple

Otra pieza estructural para que Python trate la carpeta como módulo.

------

## 6.3 `src/nlp/aceptacion_digital_redes_ponderacion_medios.py`

- **Capa:** NLP.
- **Función técnica:** construir o ponderar señal semanal de aceptación digital a partir de redes y medios.
- **Conexiones:** texto semanal, sentimiento, unión con encuestas.
- **Artefactos:** señales agregadas semanales.

### Explicación simple

Es una pieza que parece participar en la construcción de la señal final que el modelo usa como insumo o referencia.

------

## 6.4 `src/nlp/clasificacion_temas.py`

- **Capa:** NLP.
- **Función técnica:** clasificación temática general.
- **Conexiones:** diccionarios temáticos y normalización posterior.
- **Artefactos:** resultados de clasificación temática.

### Explicación simple

Toma texto y lo traduce a temas reconocibles por el sistema.

------

## 6.5 `src/nlp/clasificacion_temas_pmi_confianza.py`

- **Capa:** NLP.
- **Función técnica:** clasificación temática basada en PMI+Confianza.
- **Conexiones:** `diccionario_temas_pmi.py`, `diccionario_temas_pmi_confianza.py`, normalización de resultados.
- **Artefactos:** clasificación temática PMI+Confianza.

### Explicación simple

Es una variante más específica de clasificación temática, apoyada en reglas o pesos léxicos y en un criterio adicional de confianza.

------

## 6.6 `src/nlp/diccionario_temas_pmi.py`

- **Capa:** NLP.
- **Función técnica:** construir o alojar el diccionario de temas basado en PMI.
- **Conexiones:** `clasificacion_temas_pmi_confianza.py` y clasificación temática relacionada.
- **Artefactos:** recurso léxico/temático.

### Explicación simple

Es una tabla o recurso que ayuda al sistema a decidir qué palabras o señales apuntan a qué tema.

------

## 6.7 `src/nlp/diccionario_temas_pmi_confianza.py`

- **Capa:** NLP.
- **Función técnica:** diccionario o recurso temático para la lógica PMI+Confianza.
- **Conexiones:** `clasificacion_temas_pmi_confianza.py`.
- **Artefactos:** recurso temático.

### Explicación simple

Es el apoyo léxico o estructural específico para esa versión de clasificación temática.

------

## 6.8 `src/nlp/diccionario_temas_wpmi.py`

- **Capa:** NLP.
- **Función técnica:** recurso temático basado en WPMI.
- **Conexiones:** scripts de clasificación temática que lo usen.
- **Artefactos:** diccionario o tabla temática.

### Explicación simple

Es otra variante de recurso léxico para clasificación, probablemente basada en una variante ponderada de PMI.

------

## 6.9 `src/nlp/experiment_logger.py`

- **Capa:** NLP / compatibilidad.
- **Función técnica:** wrapper explícito hacia `src/modeling/tracking/experiment_logger.py`.
- **Conexiones:** tracking canónico de modelado.
- **Artefactos:** no propios; delega en el tracker.

### Explicación simple

Existe para no romper compatibilidad con código que todavía espera encontrar un logger aquí, pero en realidad redirige a la implementación canónica.

------

## 6.10 `src/nlp/generar_lags_datos_ml.py`

- **Capa:** NLP hacia modelado.
- **Función técnica:** generación de lags para datasets de modelado.
- **Conexiones:** `ml_ready`, datasets intermedios y dataset maestro.
- **Artefactos:** tablas con lags listas para modelado.

### Explicación simple

Ayuda a preparar el dataset con memoria temporal, es decir, con valores de semanas previas.

------

## 6.11 `src/nlp/resultados_clasificacion_temas_pmi_confianza_normalizado.py`

- **Capa:** NLP.
- **Función técnica:** normalización de resultados de clasificación temática PMI+Confianza.
- **Conexiones:** clasificación temática, refresco de tablas modelables.
- **Artefactos:** resultados temáticos normalizados.

### Explicación simple

Toma la salida temática cruda y la deja en un formato más uniforme y usable para lo que sigue.

------

## 6.12 `src/nlp/unificar_encuestas_sentimiento.py`

- **Capa:** NLP.
- **Función técnica:** unión de encuestas y sentimiento.
- **Conexiones:** variables de sentimiento, series de encuestas.
- **Artefactos:** tabla unificada de insumo.

### Explicación simple

Junta dos fuentes importantes del sistema en una sola estructura para que puedan usarse juntas.

------

## 6.13 `src/nlp/unir_ml_ready_con_sentimiento.py`

- **Capa:** NLP / premodelado.
- **Función técnica:** refresco de `ml_ready` y unión con sentimiento normalizado.
- **Conexiones:** dataset maestro final de modelado.
- **Artefactos:** tablas listas para modelado.

### Explicación simple

Es una pieza de ensamblado final antes de que el modelado tome el relevo.

------

## 6.14 `src/nlp/README_pipeline_nlp_modelado.md`

- **Capa:** documentación operativa NLP->modelado.
- **Función técnica:** mapa real del pipeline entre NLP y modelado.
- **Conexiones:** decisiones operativas sobre scripts activos.
- **Artefactos:** ninguno.

### Explicación simple

Es la guía más confiable para entender qué scripts de NLP sí importan hoy para producir el dataset de modelado.

------

## 6.15 `src/nlp/CHANGELOG_NLP_MODELADO.md`

- **Capa:** documentación / changelog.
- **Función técnica:** bitácora de intervención sobre la capa NLP->modelado.
- **Conexiones:** mantenimiento del subárbol.
- **Artefactos:** ninguno.

### Explicación simple

Sirve para saber qué se movió o endureció en esa parte del pipeline.

------

# 7. `src/shared/`: utilitarios transversales mínimos

## 7.1 `src/shared/README.md`

- **Capa:** shared.
- **Función técnica:** fija la regla de frontera para que `shared` contenga solo utilitarios transversales mínimos y estables.
- **Conexiones:** todas las capas activas, pero con frontera dura.
- **Artefactos:** ninguno.

### Explicación simple

Es un freno disciplinario: evita que la carpeta se convierta en un “cajón de sastre” donde todo acaba mal colocado.

------

## 7.2 `src/shared/__init__.py`

- **Capa:** shared.
- **Función técnica:** marca la carpeta como paquete.
- **Conexiones:** módulos shared y consumidores en otras capas.
- **Artefactos:** ninguno.

### Explicación simple

Hace que `shared` sea importable como parte ordenada del sistema.

------

## 7.3 `src/shared/check_config.py`

- **Capa:** shared / configuración.
- **Función técnica:** checker standalone de configuración y secretos.
- **Conexiones:** `.env`, `secrets.py`, rutas de runtime, preflight.
- **Artefactos:** validación de configuración.

### Explicación simple

Es una pieza para verificar antes de correr si el sistema tiene lo que necesita.

------

## 7.4 `src/shared/common_runtime_logging.py`

- **Capa:** shared / observabilidad.
- **Función técnica:** logging transversal mediante `log_event(...)`.
- **Conexiones:** modelado y potencialmente otras capas activas.
- **Artefactos:** logs o eventos de logging.

### Explicación simple

Es la forma común de dejar rastro ordenado de lo que está haciendo el sistema.

------

## 7.5 `src/shared/runtime_paths.py`

- **Capa:** shared / runtime.
- **Función técnica:** centraliza rutas canónicas de runtime.
- **Conexiones:** operaciones, extractores, validación de configuración.
- **Artefactos:** no genera; normaliza rutas.

### Explicación simple

Evita que cada script invente sus propias rutas para estado, logs o caches.

------

## 7.6 `src/shared/secrets.py`

- **Capa:** shared / configuración sensible.
- **Función técnica:** carga y valida secretos desde `.env`.
- **Conexiones:** extractores, operaciones, preflight.
- **Artefactos:** ninguno; resuelve secretos en tiempo de ejecución.

### Explicación simple

Es el módulo que evita que cada script tenga que resolver por su cuenta claves y variables sensibles.

------

# 8. `src/modeling/`: núcleo técnico de modelado

## 8.1 `src/modeling/README.md`

- **Capa:** modelado.
- **Función técnica:** declara la estructura canónica física de `core/`, `runners/`, `reporting/` y `tracking/`.
- **Conexiones:** NLP, operaciones, experiments.
- **Artefactos:** ninguno.

### Explicación simple

Es el documento que dice: aquí ya no hay una bolsa de scripts mezclados; ya existe una arquitectura interna de modelado.

------

## 8.2 `src/modeling/__init__.py`

- **Capa:** modelado.
- **Función técnica:** paquete raíz de modelado.
- **Conexiones:** todas las subcapas de modelado.
- **Artefactos:** ninguno.

### Explicación simple

Otra pieza estructural para imports ordenados.

------

## 8.3 `src/modeling/core/`

Subcapa reusable donde vive la lógica base del modelado.

### Explicación simple

Aquí está el “motor común” que varias familias de modelos necesitan compartir.

------

## 8.3.1 `src/modeling/core/config.py`

- **Capa:** core / configuración.
- **Función técnica:** define constantes maestras del modelado: dataset maestro, columnas, targets, features base, lags, horizontes, tolerancias, modos de target, modos de features y transformaciones.
- **Conexiones:** casi todo el subárbol `core/` y `runners/`.
- **Artefactos:** ninguno; define contratos de trabajo.

### Explicación simple

Es el archivo que le dice al sistema qué nombres de columnas existen, qué horizontes se predicen y cuáles son las reglas básicas del modelado.

------

## 8.3.2 `src/modeling/core/data_master.py`

- **Capa:** core / carga de datos.
- **Función técnica:** cargar, ordenar y validar el dataset maestro.
- **Conexiones:** `config.py`, `shared.common_runtime_logging`, runners, inferencia congelada.
- **Artefactos:** produce un `DataFrame` validado en memoria; registra eventos de carga.

### Explicación simple

Es el guardia de entrada del dataset maestro: lo carga y se asegura de que tenga lo necesario.

------

## 8.3.3 `src/modeling/core/feature_engineering.py`

- **Capa:** core / features.
- **Función técnica:** construir datasets laggeados y model frames por horizonte y `target_mode`.
- **Conexiones:** `data_master.py`, `evaluation.py`, runners, inferencia.
- **Artefactos:** frames modelables en memoria; logs de reducción por `dropna`.

### Explicación simple

Es la pieza que transforma el dataset en la forma que un modelo realmente puede usar.

------

## 8.3.4 `src/modeling/core/evaluation.py`

- **Capa:** core / evaluación.
- **Función técnica:** validación temporal, selección de features, tuning temporal interno y métricas Radar.
- **Conexiones:** `feature_engineering.py`, `pipeline_common.py`, tracking.
- **Artefactos:** predicciones, trazas de tuning, métricas por horizonte y pérdida total Radar.

### Explicación simple

Es una de las piezas metodológicas más importantes del repo: aquí vive buena parte de la lógica que decide cómo se prueba un modelo correctamente en el tiempo.

------

## 8.3.5 `src/modeling/core/preprocessing.py`

- **Capa:** core / transformaciones.
- **Función técnica:** construir transformadores de features como `StandardScaler`, `RobustScaler` y winsorización.
- **Conexiones:** runners tabulares.
- **Artefactos:** transformadores en memoria.

### Explicación simple

Aquí se decide cómo se escalan o recortan ciertos valores numéricos antes de alimentar al modelo.

------

## 8.3.6 `src/modeling/core/custom_estimators.py`

- **Capa:** core / estimadores personalizados.
- **Función técnica:** wrappers para SARIMAX, Prophet con exógenas, híbridos residuales y stacking temporal.
- **Conexiones:** familias E6, E7, E8, E9.
- **Artefactos:** estimadores ajustables y predictivos en memoria.

### Explicación simple

Es donde se guardan modelos que no vienen “listos” en una sola línea estándar de scikit-learn y por eso necesitan envoltura propia.

------

## 8.4 `src/modeling/runners/`

Subcapa de entrypoints por familia.

### Explicación simple

Aquí no vive toda la lógica del modelado; viven los scripts que la activan para una familia concreta.

------

## 8.4.1 `src/modeling/runners/pipeline_common.py`

- **Capa:** runners / utilitario común.
- **Función técnica:** infraestructura común de ejecución de experimentos: parsing de CLI, armado de parámetros, guardado de salidas, comparaciones, notas de config y `run_tabular_experiment(...)`.
- **Conexiones:** `core/`, `tracking/experiment_logger.py`.
- **Artefactos:** predicciones por horizonte, resúmenes, comparaciones, tablas de selección de features y paquete de run vía tracker.

### Explicación simple

Es la pieza que evita reescribir la misma lógica de corrida para cada familia de modelo.

------

## 8.4.2 Runners por familia

Familias documentadas como canónicas:

- `run_e1_ridge.py`
- `run_e2_huber.py`
- `run_e3_random_forest.py`
- `run_e4_xgboost.py`
- `run_e5_catboost.py`
- `run_e6_arimax.py`
- `run_e7_prophet.py`
- `run_e8_hibrido_residuales.py`
- `run_e9_stacking.py`

Además, el README documenta también runners de clasificación como `run_c1_random_forest_classifier`.

- **Capa:** runners.
- **Función técnica:** entrypoints por familia; delegan a `core/` y a `pipeline_common.py`.
- **Conexiones:** `core/`, tracking, reporting, experiments.
- **Artefactos:** el paquete completo del experimento, siempre persistido vía tracker.

### Explicación simple

Cada uno es la puerta de entrada para correr una familia concreta de modelos sin mezclarlo todo en un solo script gigante.

------

## 8.5 `src/modeling/tracking/`

Subcapa de trazabilidad experimental.

### Explicación simple

Es la parte que asegura que un experimento no solo corrió, sino que quedó registrado, comparable y reproducible.

------

## 8.5.1 `src/modeling/tracking/experiment_logger.py`

- **Capa:** tracking.
- **Función técnica:** bitácora automática de experimentos; registra runs, snapshots, parámetros, métricas, artefactos y refresca auditoría maestra.
- **Conexiones:** runners, `experiments/runs/`, `experiments/audit/`, `src/modeling/reporting/build_experiments_master_table.py`.
- **Artefactos:**
  - `experiments/runs/<run_id>_<timestamp>/`
  - `parametros_run.json`
  - `metricas_horizonte.json`
  - `metadata_run.json`
  - snapshots del script
  - tablas, JSON y otros artefactos del run
  - actualización del workbook maestro.

### Explicación simple

Es el notario del sistema experimental.

------

## 8.6 `src/modeling/reporting/`

Subcapa de reporting y auditoría experimental.

### Explicación simple

Toma los runs ya hechos y los convierte en tablas maestras, inventarios y resúmenes de alto nivel.

------

## 8.6.1 `src/modeling/reporting/build_experiments_master_table.py`

- **Capa:** reporting / auditoría experimental.
- **Función técnica:** reconstruir la tabla maestra de experimentos y auditorías derivadas a partir de `experiments/runs/` y del workbook.
- **Conexiones:** tracker, runs históricos, auditoría metodológica.
- **Artefactos:** CSV, XLSX, JSON y Markdown de auditoría maestra; además soporta curaduría de E9 y lectura de familias/runs.

### Explicación simple

Es el script que convierte un montón de runs dispersos en una visión maestra organizada del estado experimental.

------

# 9. `src/operations/`: orquestación operativa controlada

## 9.1 `src/operations/README.md`

- **Capa:** operations.
- **Función técnica:** documento rector de la capa operativa controlada.
- **Conexiones:** extracción, preprocessing, NLP, modelado, export, reporte, artifacts.
- **Artefactos:** define el contrato de corrida y publicación.

### Explicación simple

Es el mapa de la capa que convierte todas las capas anteriores en un sistema que se puede correr de forma coordinada.

------

## 9.2 `src/operations/__init__.py`

- **Capa:** operations.
- **Función técnica:** paquete Python de operaciones.
- **Conexiones:** submódulos operativos.
- **Artefactos:** ninguno.

### Explicación simple

Otra pieza estructural de empaquetado.

------

## 9.3 `src/operations/config.py`

- **Capa:** operations / configuración.
- **Función técnica:** configuración de la capa operativa.
- **Conexiones:** orchestrator, state, stages, launcher.
- **Artefactos:** contratos y defaults de operación.

### Explicación simple

Es el archivo donde se centralizan decisiones de configuración de la capa operativa.

------

## 9.4 `src/operations/contracts.py`

- **Capa:** operations / contratos.
- **Función técnica:** definir estructuras homogéneas para payloads, estados y etapas.
- **Conexiones:** `run_context.py`, `state_store.py`, `pipeline_orchestrator.py`.
- **Artefactos:** contratos lógicos, no runtime final.

### Explicación simple

Sirve para que la capa operativa hable con estructuras previsibles y no con diccionarios improvisados por todos lados.

------

## 9.5 `src/operations/run_context.py`

- **Capa:** operations / runtime.
- **Función técnica:** contexto de ejecución del run operativo.
- **Conexiones:** state store, stages, orchestrator.
- **Artefactos:** contexto serializable del run.

### Explicación simple

Mantiene juntas las piezas clave de una corrida: quién es, en qué semana va, qué etapas tiene, qué estado lleva.

------

## 9.6 `src/operations/state_store.py`

- **Capa:** operations / estado.
- **Función técnica:** persistencia del estado para reanudar corridas.
- **Conexiones:** `run_context.py`, `pipeline_orchestrator.py`, `state.json`.
- **Artefactos:** archivos de estado.

### Explicación simple

Es lo que permite pausar o retomar una corrida sin perder la memoria de por dónde iba.

------

## 9.7 `src/operations/pipeline_orchestrator.py`

- **Capa:** operations / orquestación.
- **Función técnica:** coordinar etapas explícitas del pipeline operativo.
- **Conexiones:** context, state, stages, launcher.
- **Artefactos:** corridas operativas estructuradas, reanudables y auditables.

### Explicación simple

Es el director de orquesta del pipeline operativo.

------

## 9.8 `src/operations/run_radar_pipeline.py`

- **Capa:** operations / entrypoint.
- **Función técnica:** entrypoint único de la capa operativa.
- **Conexiones:** orchestrator, perfiles, modos de corrida.
- **Artefactos:** dispara corridas bajo `artifacts/operations/...`.

### Explicación simple

Es la forma oficial de lanzar el pipeline.

------

## 9.9 `src/operations/gui_radar_pipeline.py`

- **Capa:** operations / GUI.
- **Función técnica:** GUI mínima de control, presets y reanudación.
- **Conexiones:** `run_radar_pipeline.py`.
- **Artefactos:** no propios; dispara corridas y muestra estado.

### Explicación simple

Es una interfaz sencilla para no tener que correr todo por consola cada vez.

------

## 9.10 `src/operations/stages/`

- **Capa:** operations / etapas.
- **Función técnica:** implementar etapas explícitas del pipeline:
  - `extraction_stage.py`
  - `preprocessing_stage.py`
  - `nlp_stage.py`
  - `modeling_stage.py`
  - `export_stage.py`
  - `report_stage.py`
- **Conexiones:** respectivas capas funcionales.
- **Artefactos:** payloads homogéneos por etapa bajo `artifacts/operations/.../stages/`.

### Explicación simple

Es la traducción de las estaciones del pipeline en piezas operativas concretas.

------

## 9.11 `src/operations/README_operacion_minima_post_w10.md`

- **Capa:** operations / documentación específica.
- **Función técnica:** documentar la operación mínima controlada post-W10.
- **Conexiones:** frozen profiles, inferencia congelada, emisiones.
- **Artefactos:** ninguno.

### Explicación simple

Explica la lógica específica de la operación post-W10.

------

## 9.12 `src/operations/CHANGELOG_OPERACION_POST_W10.md`

- **Capa:** operations / changelog.
- **Función técnica:** bitácora de la evolución de la operación post-W10.
- **Conexiones:** mantenimiento de esa subcapa.
- **Artefactos:** ninguno.

### Explicación simple

Sirve para no perder la historia de cómo se fue endureciendo esa operación.

------

## 9.13 `src/operations/frozen_profiles.py`

- **Capa:** operations / perfiles congelados.
- **Función técnica:** resolver cuáles corridas canónicas son los perfiles congelados de operación.
- **Conexiones:** inferencia congelada y wrappers post-W10.
- **Artefactos:** perfiles en memoria y referencias a runs canónicos.

### Explicación simple

Es el módulo que responde: “cuando dices benchmark congelado, ¿exactamente a qué run te refieres?”.

------

## 9.14 `src/operations/frozen_inference_assets.py`

- **Capa:** operations / assets predict-only.
- **Función técnica:** gestionar contratos, manifiestos y carga de paquetes predict-only congelados.
- **Conexiones:** `frozen_inference.py`, bootstrap de assets, operación post-W10.
- **Artefactos:** paquetes predict-only serializados y sus manifiestos.

### Explicación simple

Es la pieza que convierte un benchmark congelado en algo cargable de verdad para solo predecir.

------

## 9.15 `src/operations/frozen_inference.py`

- **Capa:** operations / inferencia congelada.
- **Función técnica:** ejecutar la ruta predict-only real sobre artefactos congelados.
- **Conexiones:** `frozen_inference_assets.py`, `frozen_profiles.py`, `src/modeling/core/*`, dataset maestro.
- **Artefactos:** bundles de pronósticos pendientes por perfil/horizonte; predicciones con fuente explícita.

### Explicación simple

Esta pieza es crucial porque hace que el sistema use semanas nuevas como entrada sin volver a entrenar el modelo.

------

## 9.16 `src/operations/bootstrap_frozen_inference_assets.py`

- **Capa:** operations / bootstrap.
- **Función técnica:** publicar o regenerar paquetes de inferencia congelada a partir del histórico validado.
- **Conexiones:** frozen profiles, frozen assets.
- **Artefactos:** paquetes congelados publicados bajo runtime operativo.

### Explicación simple

Es la herramienta que construye el “paquete de solo predicción” que luego la operación usa.

------

## 9.17 `src/operations/build_emission_registry_post_w10.py`

- **Capa:** operations / emisiones.
- **Función técnica:** construir el registro formal de emisiones post-W10.
- **Conexiones:** inferencia congelada, perfiles congelados, runtime de operaciones.
- **Artefactos:** `registro_emisiones.csv`, `registro_emisiones.json`, resúmenes de emisiones.

### Explicación simple

Es la pieza que deja por escrito qué se predijo, cuándo y con qué benchmark.

------

## 9.18 `src/operations/run_operacion_minima_post_w10.py`

- **Capa:** operations / wrapper especializado.
- **Función técnica:** coordinar la operación mínima controlada post-W10.
- **Conexiones:** launcher, frozen profiles, inferencia, registro de emisiones.
- **Artefactos:** corrida post-W10 y sus salidas asociadas.

### Explicación simple

Es el wrapper específico para la operación con semanas nuevas del mundo real sin reentrenamiento.

------

# 10. `docs/`: documentación estructural y operativa

## 10.1 `docs/README.md`

- **Capa:** documentación raíz.
- **Función técnica:** índice de documentación.
- **Conexiones:** arquitectura, operación y migración.
- **Artefactos:** ninguno.

### Explicación simple

Es la puerta de entrada a la documentación formal del repo.

------

## 10.2 `docs/architecture/repository_governance.md`

- **Capa:** gobernanza arquitectónica.
- **Función técnica:** documento autoritativo que fija taxonomía, fronteras duras y reglas de naming/runtime/versionado.
- **Conexiones:** todas las capas.
- **Artefactos:** ninguno.

### Explicación simple

Es la constitución arquitectónica del repo.

------

## 10.3 `docs/architecture/repository_architecture.md`

- **Capa:** arquitectura.
- **Función técnica:** describir estructura y relaciones del repo.
- **Conexiones:** organización física del árbol.
- **Artefactos:** ninguno.

### Explicación simple

Es el documento que explica cómo está armado el edificio.

------

## 10.4 `docs/architecture/structural_audit.md`

- **Capa:** auditoría arquitectónica.
- **Función técnica:** revisar conformidad estructural del repo.
- **Conexiones:** gobierno y migración.
- **Artefactos:** ninguno.

### Explicación simple

Sirve para verificar si el repo realmente se parece a la arquitectura que dice tener.

------

## 10.5 `docs/operations/README.md`

- **Capa:** documentación operativa.
- **Función técnica:** índice de operación.
- **Conexiones:** entornos, secrets, runtime, preflight.
- **Artefactos:** ninguno.

### Explicación simple

Es la entrada a la parte documental que explica cómo operar el sistema.

------

## 10.6 `docs/operations/intervencion_envs_ops_modeling.md`

- **Capa:** documentación operativa.
- **Función técnica:** explicar la separación entre entornos `ops` y `modeling`.
- **Conexiones:** `environment.ops.yml`, `environment.modeling.yml`, capa operativa.
- **Artefactos:** ninguno.

### Explicación simple

Explica por qué no todo corre en el mismo entorno de Python.

------

## 10.7 `docs/operations/intervencion_secrets_runtime_preflight.md`

- **Capa:** documentación operativa.
- **Función técnica:** documentar secretos, runtime y preflight.
- **Conexiones:** shared, operations.
- **Artefactos:** ninguno.

### Explicación simple

Es la bitácora de cómo se ordenó la parte sensible de configuración y validación previa.

------

## 10.8 `docs/operations/politica_entornos_python.md`

- **Capa:** documentación operativa.
- **Función técnica:** política oficial de entornos Python por capa.
- **Conexiones:** envs del repo.
- **Artefactos:** ninguno.

### Explicación simple

Dice qué corre en qué entorno y por qué.

------

## 10.9 `docs/operations/secrets_and_runtime.md`

- **Capa:** documentación operativa.
- **Función técnica:** explicar manejo de secretos y runtime.
- **Conexiones:** `src/shared/`, `src/operations/`.
- **Artefactos:** ninguno.

### Explicación simple

Es la guía práctica de configuración sensible y runtime.

------

## 10.10 `docs/migration/`

- **Capa:** migración.
- **Función técnica:** documentar transición desde la estructura anterior.
- **Conexiones:** `legacy/`, naming histórico, limpieza estructural.
- **Artefactos:** tablas o ledger de migración.

### Explicación simple

Sirve para no perder memoria de de dónde vino cada cosa al reorganizar el repo.

------

# 11. `experiments/`: evidencia experimental y prompts

## 11.1 `experiments/README.md`

- **Capa:** experimentación.
- **Función técnica:** definir que esta raíz contiene evidencia experimental, no código activo.
- **Conexiones:** tracking, reporting, prompts.
- **Artefactos:** ninguno.

### Explicación simple

Es el reglamento de la zona experimental del repo.

------

## 11.2 `experiments/audit/`

- **Capa:** auditoría experimental.
- **Función técnica:** conservar el workbook maestro y backups.
- **Conexiones:** `src/modeling/tracking/experiment_logger.py`.
- **Artefactos:** workbook Excel maestro, backups y tablas de auditoría.

### Explicación simple

Es la bóveda donde queda el índice maestro de experimentos.

------

## 11.3 `experiments/prompts/`

- **Capa:** prompts / evidencia metodológica.
- **Función técnica:** conservar prompts experimentales y operativos del proyecto.
- **Conexiones:** auditoría metodológica y diseño experimental.
- **Artefactos:** documentos `.md` de prompts.

### Explicación simple

Es el archivo histórico de instrucciones importantes que guiaron etapas del proyecto.

------

## 11.4 `experiments/research/`

- **Capa:** investigación.
- **Función técnica:** alojar material de investigación metodológica.
- **Conexiones:** decisiones experimentales y análisis.
- **Artefactos:** documentos de research.

### Explicación simple

Es la zona de pensamiento experimental más libre, pero separada del flujo canónico.

------

## 11.5 `experiments/runs/`

- **Capa:** evidencia histórica de runs.
- **Función técnica:** guardar paquetes de ejecución experimental por run.
- **Conexiones:** tracker y reporting.
- **Artefactos típicos:** `metadata_run.json`, `parametros_run.json`, `metricas_horizonte.json`, `predicciones_h*.csv`, snapshots, comparaciones.

### Explicación simple

Es la carpeta donde cada corrida experimental deja su expediente completo.

------

# 12. `artifacts/`: runtime técnico

## 12.1 `artifacts/README.md`

- **Capa:** runtime técnico.
- **Función técnica:** documentar que esta raíz almacena runtime técnico, no datos canónicos ni código fuente.
- **Conexiones:** extracción, preprocessing, operations.
- **Artefactos:** ninguno; describe artefactos.

### Explicación simple

Es la explicación de la zona donde el sistema deja su huella de ejecución.

------

## 12.2 `artifacts/cache/`

- **Capa:** runtime técnico / cache.
- **Función técnica:** almacenar caches técnicos regenerables.
- **Conexiones:** extracción y quizá otras capas con costo de repetición.
- **Artefactos:** caches técnicos.

### Explicación simple

Guarda cosas que conviene no recalcular o volver a bajar si no hace falta.

------

## 12.3 `artifacts/logs/`

- **Capa:** runtime técnico / logs.
- **Función técnica:** almacenar logs técnicos por capa o corrida.
- **Conexiones:** preprocessing y potencialmente otras capas.
- **Artefactos:** logs de ejecución.

### Explicación simple

Es la zona de rastro textual del sistema cuando corre.

------

## 12.4 `artifacts/runs/`

- **Capa:** runtime técnico / corridas.
- **Función técnica:** guardar corridas o artefactos técnicos no experimentales, como extracción intermedia.
- **Conexiones:** extracción y otras piezas operativas.
- **Artefactos:** workdirs y paquetes runtime por ejecución.

### Explicación simple

Es una zona de trabajo técnico donde ciertas partes del sistema guardan sus resultados operativos intermedios.

------

## 12.5 `artifacts/state/`

- **Capa:** runtime técnico / estado.
- **Función técnica:** tokens, sesiones, cursores y estado persistente.
- **Conexiones:** extractores, operaciones, reanudación.
- **Artefactos:** archivos de estado y sesión.

### Explicación simple

Es la memoria técnica del sistema entre una corrida y otra.

------

## 12.6 `artifacts/operations/`

- **Capa:** runtime técnico / operaciones.
- **Función técnica:** almacenar corridas operativas controladas y sus publicaciones.
- **Conexiones:** `src/operations/`.
- **Artefactos:** `manifest.json`, `run_summary.json`, `state.json`, logs, payloads por etapa, publicación a powerbi, report inputs y artefactos post-W10.

### Explicación simple

Es el archivo técnico central de la capa operativa.

------

# 13. `legacy/`: histórico preservado

## 13.1 `legacy/README.md`

- **Capa:** legado.
- **Función técnica:** explicar la función de esta raíz como histórico fuera del flujo canónico.
- **Conexiones:** migración, trazabilidad histórica.
- **Artefactos:** ninguno.

### Explicación simple

Es la zona donde se guarda el pasado sin dejar que mande sobre el presente.

------

## 13.2 `legacy/code/extraction_variants/`

- **Capa:** legado técnico.
- **Función técnica:** conservar variantes históricas de extracción.
- **Conexiones:** auditoría histórica.
- **Artefactos:** scripts históricos.

### Explicación simple

Guarda versiones viejas o alternativas que ya no forman parte del flujo canónico.

------

## 13.3 `legacy/data/...`

- **Capa:** legado de datos.
- **Función técnica:** preservar materiales históricos fuera del flujo vivo.
- **Conexiones:** migración y referencia histórica.
- **Artefactos:** histórico preservado.

### Explicación simple

Es la bodega histórica del proyecto.

------

# 14. Conexión entre capas

## 14.1 Cadena canónica

### `src/extraction/`

Produce insumos semanales por fuente.

### `src/preprocessing/`

Normaliza semanas, completa faltantes y promueve a texto.

### `src/nlp/`

Transforma texto en variables, une con encuestas y refresca datasets para modelado.

### `src/modeling/`

Carga dataset maestro, arma features, valida modelos, registra runs y construye auditoría experimental.

### `src/operations/`

Coordina el pipeline operativo de punta a punta y, en post-W10, usa inferencia congelada y registro formal de emisiones.

### Explicación simple

Cada capa toma la salida útil de la anterior, la transforma y la deja lista para la siguiente.

------

# 15. Componentes más críticos del repo

## 15.1 `docs/architecture/repository_governance.md`

Porque fija las fronteras y evita que el repo vuelva al caos estructural.

## 15.2 `src/modeling/core/evaluation.py`

Porque concentra gran parte de la lógica metodológica temporal del proyecto.

## 15.3 `src/modeling/runners/pipeline_common.py`

Porque estandariza ejecución y evita duplicación de lógica entre familias.

## 15.4 `src/modeling/tracking/experiment_logger.py`

Porque convierte los runs en evidencia trazable y comparable.

## 15.5 `src/operations/pipeline_orchestrator.py` y `run_radar_pipeline.py`

Porque convierten las capas en sistema operable.

## 15.6 `src/operations/frozen_inference.py`

Porque resuelve la separación crítica entre entrenamiento e inferencia en la operación post-W10.

------

# 16. Resumen ejecutivo

- `src/` es el código vivo.
- `src/extraction/` baja datos por fuente.
- `src/preprocessing/` normaliza y promueve a texto.
- `src/nlp/` convierte texto en variables y prepara datasets modelables.
- `src/modeling/core/` define dataset, features, validación y métricas.
- `src/modeling/runners/` ejecuta familias.
- `src/modeling/tracking/` registra runs y artefactos.
- `src/modeling/reporting/` construye tablas maestras y auditorías.
- `src/shared/` contiene utilitarios transversales mínimos.
- `src/operations/` coordina el sistema operativo y la inferencia congelada post-W10.
- `docs/` gobierna.
- `experiments/` conserva evidencia metodológica.
- `artifacts/` guarda runtime técnico.
- `legacy/` preserva el pasado sin contaminar el flujo canónico.

------

# 17. Capa adicional de auditoría operativa

Lo que sigue no sustituye al inventario anterior. Lo endurece.

La idea aquí es pasar de una descripción arquitectónica general a una lectura más útil para operación, auditoría y mantenimiento. Para cada componente o familia de componentes se aclara ahora no solo **qué es**, sino también **qué recibe**, **qué entrega**, **de qué depende**, **en qué entorno debería correr**, **qué tan canónico es hoy** y **si deja o no persistencia material**.

En términos técnicos, esto equivale a documentar:

- **inputs**: entradas esperadas
- **outputs**: salidas producidas
- **dependencies**: dependencias directas
- **execution environment**: entorno Python o capa donde corre
- **status**: canónico, transicional, experimental, legado o wrapper de compatibilidad
- **persistence mode**: si deja artefacto persistente, si solo transforma en memoria o si ambas cosas

En lenguaje llano, significa responder mejor preguntas como estas:

- ¿qué necesita este archivo para poder correr?
- ¿qué deja después de correr?
- ¿qué se rompe si falla?
- ¿en qué parte del sistema vive realmente?
- ¿es una pieza central o una pieza puente?

------

# 18. Inventario operativo endurecido por capa

## 18.1 Raíz del repo

### `README.md`

Este archivo no participa en el pipeline como código ejecutable. Su **entrada** real es el estado del proyecto y su **salida** es orientación documental. Depende de que la documentación no esté desfasada respecto al árbol real. Corre en ningún entorno particular porque no se ejecuta; se consulta. Su **estatus** es canónico como documento raíz. Su modo de persistencia es puramente documental: no produce artefactos runtime ni transforma datos en memoria.

### `.env.example`

Su entrada es el contrato esperado de variables de entorno. Su salida es una plantilla de configuración para humanos o para bootstrap manual del sistema. Depende de que `src/shared/secrets.py`, `src/shared/check_config.py` y la documentación operativa sigan alineados con las variables declaradas aquí. Está en la frontera entre documentación y operación. No corre como pipeline, pero condiciona el entorno donde sí correrán extractores y operaciones. Su estatus es canónico como plantilla. Su persistencia también es documental.

### `environment.experimentos.yml`, `environment.modeling.yml`, `environment.ops.yml`

Estos archivos reciben como entrada la definición de dependencias de cada subdominio técnico. Su salida no es un artefacto del pipeline, sino un entorno instalable. Dependen de que los imports reales del repo no se hayan movido sin actualizar la receta. El primero corresponde al trabajo experimental, el segundo al modelado e inferencia, y el tercero a extracción, preprocessing, NLP y operación. Su estatus es canónico-operativo. Producen persistencia indirecta, porque al materializarse crean un entorno local reproducible, pero no dejan un artefacto del sistema dentro del repo.

### `launch_radar_gui.py`

Su entrada es una intención de lanzamiento. Su salida es abrir la GUI o delegar a la capa operativa que sí produce artefactos. Depende directamente de `src/operations/gui_radar_pipeline.py`. Su entorno natural es el entorno operativo. Su estatus es canónico como launcher de conveniencia. No deja persistencia propia; la persistencia la deja la corrida que dispara.

### `setup_env_experimentos.sh` y `setup_env_ops.sh`

Reciben como entrada las recetas de entorno y un sistema local donde instalar. Entregan entornos preparados. Dependen de los archivos `environment.*.yml` y del gestor de entorno usado. Su estatus es utilitario canónico. No generan artefactos del pipeline, pero sí infraestructura local reproducible.

------

## 18.2 `src/` como capa de código activo

### `src/__init__.py`

Su entrada no es un dato de negocio, sino la necesidad de que Python trate `src` como paquete. Su salida es habilitar imports limpios del tipo `from src...`. Depende del empaquetado lógico del repositorio. Su entorno es cualquiera donde corra el proyecto. Su estatus es estructural canónico. No deja persistencia ni salida de negocio.

### `src/README.md`

Recibe como entrada el estado arquitectónico del código vivo. Entrega una explicación normativa de qué puede o no vivir en `src/`. Depende del gobierno del repo y del árbol real. Su estatus es canónico-documental.

------

## 18.3 `src/extraction/`

La capa de extracción recibe como entrada credenciales, parámetros de consulta, ventanas temporales y, según la fuente, estados previos como cursores o sesiones. Su salida puede ser de dos tipos. A veces deja ya un **dato canónico semanal** en `data/raw/...`; otras veces deja un **artefacto intermedio de adquisición** que todavía no puede considerarse dato listo para el pipeline. Esa distinción es central para no confundir adquisición con dato final.

En términos de dependencia, esta capa mira hacia afuera del repo: APIs, HTML, plataformas y autenticación. Hacia adentro se conecta con `artifacts/state/`, `artifacts/cache/` y `src/preprocessing/`. Su entorno natural es `environment.ops.yml`. Su estatus general es canónico, pero todavía fuente-específico. Deja persistencia fuerte porque escribe archivos y estados técnicos.

### `src/extraction/README.md`

Su función endurecida es servir como contrato de frontera: aclarar si un runner escribe dato canónico o artefacto intermedio. Eso tiene valor operativo porque evita asumir falsamente que todo lo extraído ya está listo para NLP.

### `src/extraction/runners/twitter_extractor_tampico.py`

Su entrada típica son criterios de consulta, fechas, configuración y autenticación. Su salida es raw semanal canónico de Twitter/X. Depende de la disponibilidad de la fuente y del estado técnico persistido. Corre en entorno ops. Su estatus es canónico. Produce persistencia fuerte en datos y posiblemente en logs/estado.

### `src/extraction/runners/youtube_extractor_tampico.py`

Su lógica operativa es análoga a la de Twitter. Recibe configuración y ventana temporal. Entrega archivos semanales canónicos de YouTube. Depende de credenciales, accesibilidad de fuente y estructura esperada del destino raw. Corre en entorno ops. Es canónico. Deja persistencia fuerte.

### `src/extraction/runners/medios_extractor.py`

Aquí la entrada sigue siendo una consulta o una lista de medios/fuentes, pero la salida es más avanzada porque ya deja el `.txt` de medios limpio y segmentado. Eso significa que parte de la transformación semántica que en otras fuentes ocurre después, aquí ya sucede en extracción. Depende de scraping, parsing y lógica de limpieza incorporada. Corre en entorno ops. Su estatus es canónico. Deja persistencia fuerte en raw y en texto ya preparado para la promoción posterior.

### `src/extraction/runners/facebook_extractor_apify_tampico.py`

Este caso es especial. Su entrada son parámetros de adquisición y acceso vía Apify. Su salida no es el CSV canónico final, sino artefacto intermedio de adquisición. Depende de Apify, configuración de actor, sesión y de la etapa de preprocessing que hará la promoción posterior. Corre en entorno ops. Su estatus es canónico, pero con salida intermedia. Deja persistencia fuerte en `artifacts/runs/extraction/facebook/`.

------

## 18.4 `src/preprocessing/`

Esta capa recibe como entrada raw semanal, ingresos externos, fuentes mensuales y estructuras heredadas con naming inconsistente. Entrega semanas normalizadas y, sobre todo, texto promovido hacia `data/text/`. Su dependencia principal es que extracción haya dejado archivos suficientemente consistentes para poder ubicarlos y transformarlos. También depende del convenio semanal ISO y del layout esperado de carpetas.

Su entorno natural es ops. Su estatus general es canónico, aunque contiene piezas transicionales. Su persistencia es fuerte porque escribe semanas normalizadas, textos promovidos y logs técnicos.

### `src/preprocessing/README.md`

No solo documenta scripts: también define una **secuencia base recomendada**. Eso es valioso porque transforma una colección de utilitarios en un stage reconocible.

### `ejecutar_preprocesamiento_base.py`

Recibe como entrada una semana o conjunto de semanas y coordina la secuencia base del stage. Entrega la ejecución ordenada del preprocessing y los outputs que de ella derivan. Depende de los scripts específicos del stage. Corre en entorno ops. Su estatus es canónico como wrapper. Deja persistencia indirecta a través de los scripts que orquesta.

### `prefijar_carpetas_semanales.py`

Recibe una estructura heredada de carpetas. Entrega una estructura con prefijo ISO correcto. Depende del naming histórico previo. Corre en ops. Su estatus es transicional. Deja persistencia fuerte porque modifica estructura física.

### `normalizar_semanas_canonicas.py`

Recibe una estructura semanal posiblemente heterogénea. Entrega una estructura homogénea, detecta faltantes y reporta huecos. Depende del convenio canónico de semana. Corre en ops. Es canónico. Deja persistencia física y probablemente reportes/logs.

### `distribuir_facebook_semanal.py` y `distribuir_medios_semanales.py`

Ambos reciben ingresos ya existentes pero todavía mal ubicados temporalmente. Entregan una asignación correcta por semana. Dependen del calendario semanal y de los nombres/rangos de los archivos. Corren en ops. Su estatus es transicional. Dejan persistencia física.

### `completar_facebook_semanal_desde_mensual.py`, `completar_twitter_semanal_desde_mensual.py`, `completar_youtube_semanal_desde_mensual.py`

Reciben fuentes mensuales y reglas de desagregación semanal. Entregan semanas faltantes reconstruidas. Dependen de que exista una lógica metodológicamente aceptada para pasar de mensual a semanal. Corren en ops. Su estatus es canónico. Dejan persistencia física en raw semanal.

### `promover_raw_a_texto.py`

Recibe raw semanal ya suficientemente ordenado. Entrega corpus textual en `data/text/`. Depende del layout raw y de reglas de promoción. Corre en ops. Su estatus es canónico. Deja persistencia fuerte en texto promovido y en logs/auditoría cuando corresponde.

### `importar_semanas_main_a_raw.py`

Recibe semanas o materiales externos. Entrega inserción dentro del raw canónico. Depende del formato de entrada. Corre en ops. Su estatus parece auxiliar/canónico de soporte. Deja persistencia física.

------

## 18.5 `src/nlp/`

Esta capa es la más híbrida del repo actual. Recibe como entrada el texto semanal promovido, diccionarios temáticos, resultados intermedios y tablas auxiliares como encuestas. Entrega variables textuales agregadas, sentimiento, temas, normalizaciones, uniones con encuestas, tablas `ml_ready`, lags y finalmente reconstrucción del dataset que modelado consumirá.

Su dependencia principal es doble. Hacia atrás depende de que preprocessing haya dejado el texto correcto. Hacia adelante depende de que modelado espere exactamente las columnas o estructuras que aquí se producen. Su entorno natural es ops cuando participa en operación canónica. Su estatus general es canónico pero todavía script-oriented. Deja persistencia fuerte, porque muchas de sus salidas son archivos o tablas intermedias/semifinales, no solo transformaciones en memoria.

### `src/nlp/README.md`

Recibe como entrada el estado real del subárbol y entrega una advertencia metodológica importante: esta capa todavía no está completamente limpiada en términos de separación física entre activo y legado. Su dependencia documental más fuerte es `README_pipeline_nlp_modelado.md`.

### `aceptacion_digital_redes_ponderacion_medios.py`

Recibe texto o señales ya agregadas y produce una medida o transformación relacionada con aceptación digital y ponderación por medios. Depende de insumos textuales y posiblemente de reglas de agregación. Corre en ops. Su estatus parece canónico. Deja persistencia probablemente en tablas intermedias o finales.

### `clasificacion_temas.py`

Recibe texto y un recurso temático. Entrega asignación temática. Depende de los diccionarios y de la lógica de clasificación. Corre en ops. Su estatus es canónico. Deja persistencia en resultados de clasificación.

### `clasificacion_temas_pmi_confianza.py`

Recibe texto y recursos léxicos basados en PMI/Confianza. Entrega clasificación temática con ese enfoque. Depende de `diccionario_temas_pmi.py`, `diccionario_temas_pmi_confianza.py` y de la normalización posterior. Corre en ops. Su estatus es canónico. Deja persistencia en tablas/resultados clasificados.

### `diccionario_temas_pmi.py`

Su entrada suele ser un conjunto de términos, asociaciones o definición temática. Su salida es un recurso léxico estructurado que la clasificación puede consumir. No es tanto un ejecutable final como un soporte de conocimiento o una pieza de preparación de recursos. Corre donde se necesite dentro de NLP. Su estatus es canónico como recurso/script de soporte. Puede dejar persistencia si genera archivos de diccionario.

### `diccionario_temas_pmi_confianza.py`

Recibe la definición de la variante PMI+Confianza y entrega el recurso específico para esa lógica. Depende de la convención temática adoptada. Su estatus es canónico. Deja persistencia si materializa ese recurso.

### `diccionario_temas_wpmi.py`

Mismo patrón general: recibe lógica temática, entrega recurso léxico-estructural para otra variante metodológica. Su estatus es canónico como soporte.

### `experiment_logger.py`

Aquí la lectura endurecida es importante: no debe entenderse como un tracker autónomo de NLP, sino como una **capa de compatibilidad**. Su entrada es una llamada heredada desde código que todavía apunta a NLP. Su salida es delegar al tracker canónico de modelado. Corre donde corra el código que lo invoque. Su estatus es wrapper explícito, no implementación primaria.

### `generar_lags_datos_ml.py`

Recibe tablas modelables previas. Entrega tablas con memoria temporal incorporada. Depende de la estructura de `ml_ready` o de la tabla previa. Corre en ops o en flujo NLP->modelado. Su estatus es canónico. Deja persistencia si escribe tabla.

### `resultados_clasificacion_temas_pmi_confianza_normalizado.py`

Recibe clasificación temática cruda. Entrega salida normalizada. Depende del archivo de clasificación PMI+Confianza. Corre en ops. Es canónico. Deja persistencia.

### `unificar_encuestas_sentimiento.py`

Recibe resultados de sentimiento y tablas de encuestas. Entrega una tabla unificada. Depende de que ambas fuentes tengan llaves temporales o estructura conciliable. Corre en ops. Es canónico. Deja persistencia.

### `unir_ml_ready_con_sentimiento.py`

Recibe `ml_ready` y señales de sentimiento/PMI normalizado. Entrega una tabla más cercana al dataset maestro de modelado. Depende de formatos compatibles. Corre en ops. Es canónico. Deja persistencia.

### `README_pipeline_nlp_modelado.md`

Su entrada es el estado real del pipeline NLP->modelado. Su salida es un mapa operativo usable. Su dependencia crítica es que se mantenga actualizado. Su estatus es canónico-documental.

### `CHANGELOG_NLP_MODELADO.md`

Cumple el rol de bitácora de endurecimiento. No ejecuta nada, pero reduce ambigüedad histórica.

------

## 18.6 `src/shared/`

Esta capa no recibe datos de negocio ni entrega producto sustantivo del pipeline. Recibe necesidades transversales del sistema —logging, secrets, paths, checks— y entrega servicios comunes a más de una capa. Su gran dependencia no es un archivo concreto, sino la disciplina arquitectónica: si aquí empieza a entrar lógica de negocio, se degrada la claridad del repo. Su entorno es transversal. Su estatus es canónico. Su persistencia depende del módulo: logging sí deja artefactos; secrets y paths normalmente no.

### `src/shared/README.md`

Su entrada es la necesidad de frontera arquitectónica. Su salida es una regla clara: `shared` no debe convertirse en cajón de sastre.

### `check_config.py`

Recibe configuración esperada y entorno actual. Entrega validación o errores de configuración. Depende de `.env`, `secrets.py`, `runtime_paths.py`. Corre en ops. Su estatus es canónico. Puede dejar persistencia leve si loguea resultados.

### `common_runtime_logging.py`

Recibe eventos estructurados desde múltiples módulos. Entrega logging homogéneo. Depende de una convención común de logging. Corre transversalmente. Es canónico. Deja persistencia cuando el backend de logs escribe.

### `runtime_paths.py`

Recibe como entrada la necesidad de ubicar runtime de forma consistente. Entrega rutas canónicas. Depende del layout aprobado del repo. Su estatus es canónico. No deja persistencia propia.

### `secrets.py`

Recibe variables de entorno o `.env`. Entrega acceso validado a secretos. Depende del contrato de variables esperadas. Corre transversalmente. Es canónico. No deja persistencia de negocio.

------

## 18.7 `src/modeling/core/`

Esta subcapa recibe tablas listas para modelado y devuelve estructuras, transformaciones, predicciones y métricas reutilizables. Su entorno natural es `environment.modeling.yml`, aunque parte de su lógica también es consumida por operaciones en post-W10. Su estatus es canónico y muy estable. Su persistencia es baja a moderada: por sí sola muchas veces trabaja en memoria, pero sus consumidores sí persisten salidas.

### `config.py`

Recibe la decisión metodológica ya tomada y la cristaliza como constantes. Entrega contratos para el resto del modelado. Depende de que dataset y columnas sigan siendo las correctas. No deja persistencia.

### `data_master.py`

Recibe la ruta del dataset maestro. Entrega un `DataFrame` ordenado y validado. Depende del archivo Excel y de los nombres de columnas. Corre en modeling y también sirve a inferencia congelada. No deja artefacto sustantivo, pero sí puede loguear.

### `feature_engineering.py`

Recibe un dataset y una lista de features/targets/lag config. Entrega model frames. Depende de `config.py` y de un dataset ya correcto. Corre en modeling e inferencia. No suele dejar persistencia propia; produce objetos en memoria y logs.

### `evaluation.py`

Recibe estimadores, frames modelables y configuración metodológica. Entrega predicciones walk-forward, tuning temporal y métricas Radar. Depende de scikit-learn, de la estructura temporal correcta y del contrato de columnas. Corre en modeling experimental. Su persistencia es indirecta: produce en memoria lo que luego runners y tracker guardan.

### `preprocessing.py`

Recibe matrices/features numéricas y configuración de transformación. Entrega transformadores. Depende de scikit-learn y numpy. Corre en modeling. Su persistencia es indirecta, salvo cuando el pipeline los serializa.

### `custom_estimators.py`

Recibe datasets/parametrización de modelos especiales. Entrega estimadores utilizables dentro del pipeline general. Depende de `statsmodels`, `prophet`, scikit-learn y del contrato temporal del sistema. Corre en modeling. Su persistencia es indirecta cuando el modelo entrenado se serializa.

------

## 18.8 `src/modeling/runners/`

Esta subcapa recibe una configuración experimental concreta y entrega una corrida completa de una familia. Depende fuertemente de `core/` y del tracker. Corre en `environment.modeling.yml`. Su estatus es canónico como entrypoint de investigación/modelado. Deja persistencia fuerte porque normalmente toda corrida registrada termina en `experiments/runs/` y en el workbook maestro.

### `pipeline_common.py`

Recibe argumentos CLI y configuración de experimento. Entrega la mecánica común de corrida, métricas, comparación, guardado y cierre. Depende de `core/*` y de `tracking/experiment_logger.py`. Es canónico. Deja persistencia indirecta a través del tracker.

### Runners de familia

Cada `run_e*.py` o `run_c*.py` recibe la configuración de una familia concreta. Entrega una corrida completa con métricas por horizonte y artefactos. Depende de `pipeline_common.py`, de `core/` y del estimador o familia correspondiente. Corre en modeling. Su estatus es canónico si la familia está vigente; puede ser histórico vigente, referencia secundaria o línea preparada según la familia. Deja persistencia fuerte.

------

## 18.9 `src/modeling/tracking/`

Esta subcapa recibe resultados ya producidos por runners. Entrega trazabilidad duradera. Depende del workbook maestro, del filesystem y del layout de `experiments/`. Corre en modeling. Su estatus es canónico. Deja persistencia muy fuerte.

### `experiment_logger.py`

Su entrada son parámetros, resultados, artefactos y metadatos del run. Su salida es el expediente formal del experimento: run dir, JSONs, snapshots, workbook y eventualmente refresh de auditoría maestra. Es una pieza crítica porque si falla, el sistema puede haber modelado algo pero no haberlo convertido todavía en evidencia trazable.

------

## 18.10 `src/modeling/reporting/`

Recibe los expedientes de `experiments/runs/` y el workbook maestro. Entrega tablas maestras y auditorías derivadas. Depende fuertemente de que tracking haya sido consistente. Corre en modeling. Su estatus es canónico. Deja persistencia fuerte en CSV/XLSX/JSON/Markdown.

### `build_experiments_master_table.py`

Su entrada es el universo de runs y sus archivos estructurados. Su salida es una visión consolidada del estado experimental. Si tracking es el notario, reporting es el archivista mayor.

------

## 18.11 `src/operations/`

La capa de operaciones recibe como entrada una intención de corrida: semana, rango de fechas, stages, perfil operativo, modo controlado o experimental, y eventualmente un `resume_run_id`. Su salida es una corrida auditada, reanudable y publicada en `artifacts/operations/...`. Depende de todas las capas funcionales previas y de que el runtime esté bien resuelto. Corre principalmente en entorno ops, aunque en ciertos tramos invoca el entorno modeling. Su estatus es canónico como capa operativa controlada. Deja persistencia muy fuerte.

### `config.py`

Centraliza decisiones operativas. Recibe parámetros y entrega defaults/contratos para el resto de operaciones.

### `contracts.py`

Da forma estable a los objetos de etapa, manifests, estados o payloads. Su entrada es la necesidad de homogeneidad; su salida es estructura disciplinada.

### `run_context.py`

Recibe los metadatos de una corrida. Entrega una representación estable del contexto operativo. Es la memoria estructurada del run actual.

### `state_store.py`

Recibe actualizaciones de estado. Entrega persistencia para reanudación. Si esta pieza falla, se debilita la capacidad de recuperar corridas.

### `pipeline_orchestrator.py`

Recibe plan de corrida y contexto. Entrega coordinación secuencial o controlada entre stages. Es una pieza crítica de continuidad del sistema.

### `run_radar_pipeline.py`

Recibe argumentos del usuario. Entrega una corrida operativa disparada conforme al contrato oficial. Es el entrypoint de operación.

### `gui_radar_pipeline.py`

Recibe interacción del usuario. Entrega construcción y disparo de comandos operativos. No produce artefactos por sí misma; los produce la corrida que invoca.

### `stages/*`

Cada stage recibe el contexto más los outputs de la etapa anterior. Entrega payloads homogéneos y/o side effects reales del stage. En conjunto, representan el pipeline operativo materializado.

### `frozen_profiles.py`

Recibe la necesidad de operar con benchmarks congelados. Entrega perfiles resueltos contra corridas canónicas concretas.

### `frozen_inference_assets.py`

Recibe la necesidad de un contrato predict-only. Entrega paquetes congelados cargables, con manifiesto, modelo serializado y contrato de input.

### `frozen_inference.py`

Recibe el dataset maestro actualizado más un perfil congelado. Entrega predicciones nuevas usando solo `predict()`. Depende de que el paquete frozen exista y de que el contrato de features sea satisfecho. Es la pieza central de la separación fit/predict.

### `bootstrap_frozen_inference_assets.py`

Recibe el histórico validado y la referencia a los benchmarks canónicos. Entrega el paquete frozen que luego consumirá inferencia. Es un puente entre experimento cerrado e inferencia operativa.

### `build_emission_registry_post_w10.py`

Recibe predicciones emitidas y metadatos operativos. Entrega el registro formal de emisiones. Es la pieza que vuelve auditable la inferencia post-W10.

### `run_operacion_minima_post_w10.py`

Recibe la intención de ejecutar la operación mínima post-W10. Entrega la coordinación especializada de ese flujo. Su valor es encapsular un perfil operativo distinto del pipeline semanal estándar.

------

# 19. Lectura transversal de estatus

Una forma útil de leer el repo es preguntarse qué tipo de pieza es cada archivo en términos de madurez.

Un archivo **canónico** es uno que forma parte del flujo vigente y cuya existencia está respaldada por la documentación de capa o por la gobernanza del repo.

Un archivo **transicional** es uno que todavía resuelve una necesidad real, pero ligado a una etapa de migración, compatibilidad o normalización histórica. No está “mal”, pero idealmente no define el estado final del sistema.

Un archivo **wrapper de compatibilidad** no implementa la lógica principal, sino que redirige o protege compatibilidad con rutas anteriores. `src/nlp/experiment_logger.py` es el ejemplo más claro.

Un archivo **documental canónico** no ejecuta el pipeline, pero sí gobierna su lectura correcta. `repository_governance.md` es el caso más fuerte.

Un archivo **de legado** preserva historia útil, pero no debe reaparecer como dependencia activa del sistema.

------

# 20. Qué se gana con esta arquitectura y qué cuesta

Se gana separación de responsabilidades, trazabilidad, capacidad de auditoría, posibilidad de correr por etapas, y una distinción mucho más limpia entre experimento, operación y runtime. También se gana una frontera mucho más sana entre el benchmark congelado y la inferencia operativa post-W10.

Pero se paga un costo: el repo deja de ser visualmente simple. Hay más archivos, más puntos de entrada y más necesidad de documentación. Cuando esa documentación existe y es veraz, la fragmentación deja de ser caos y se vuelve especialización. Cuando no existe o se atrasa, la misma fragmentación se vuelve confusión.

La lectura correcta de RAdAR hoy no es “demasiados scripts porque sí”, sino “múltiples piezas especializadas que necesitan un mapa de alto nivel para no sentirse arbitrarias”. Por eso este inventario no debe verse como lujo documental, sino como parte del sistema mismo.

------

# 21. Nota final

Este inventario describe la arquitectura visible y versionada del repositorio. Los artefactos runtime generados dinámicamente dentro de `artifacts/` y `experiments/runs/` deben entenderse como familias de salidas gobernadas por los módulos aquí descritos, no como una lista cerrada de archivos permanentes.
