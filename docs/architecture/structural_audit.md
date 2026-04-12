# Structural Audit

## Objetivo

Auditoria estructural del repositorio previa a la reestructuracion arquitectonica conservadora.

## Inventario inicial de raiz

| Ruta original | Clasificacion | Diagnostico |
| --- | --- | --- |
| `Scripts/` | `operativa_vigente` | Mezclaba codigo activo, wrappers, runtime y arrastre historico. |
| `Datos_RAdAR/` | `canonica_vigente` | Dato bruto operativo valioso, pero mezclado con agregados y legado. |
| `Datos_RadaR_Texto/` | `canonica_vigente` | Corpus canonico util, pero nombrado de forma inconsistente y sin separacion de runtime. |
| `Datos_Modelo_ML/` | `canonica_vigente` | Dataset maestro y derivados de modelado. |
| `Diccionarios_NLP/` | `canonica_vigente` | Recursos de referencia y resultados de clasificacion tematica. |
| `Encuestas/` | `canonica_vigente` | Insumo externo canonico. |
| `Experimentos/` | `experimental` | Mezclaba prompts, runs, auditorias, reportes y piezas casi operativas. |

## Subarboles relevantes y clasificacion

| Ruta original | Clasificacion | Resolucion |
| --- | --- | --- |
| `Scripts/Modeling` | `canonica_vigente` | Movido a `src/modeling/`. |
| `Scripts/NLP_Data_Procesing` | `canonica_vigente` | Movido a `src/nlp/`. |
| `Scripts/Prepocessing` | `operativa_vigente` | Movido a `src/preprocessing/`. |
| `Scripts/state` | `runtime` | Movido a `artifacts/state/`. |
| `Scripts/Extracting_Procesing` | `operativa_vigente` hibrida | Separado entre `src/extraction/runners/`, `src/preprocessing/` y `legacy/code/extraction_variants/`. |
| `Datos_RAdAR/<semanas>` | `canonica_vigente` | Movido a `data/raw/radar_weekly_flat/` para preservar el flujo real existente. |
| `Datos_RAdAR/PPPP_*` | `legacy` | Movido a `legacy/data/pppp/raw/`. |
| `Datos_RadaR_Texto/*_Semana_Texto` | `canonica_vigente` | Movido a `data/text/radar_weekly_flat/`. |
| `Datos_RadaR_Texto/PPPP_*` | `legacy` | Movido a `legacy/data/pppp/text/`. |
| `Experimentos/runs` | `experimental` | Movido a `experiments/runs/`. |
| `Experimentos/Prompts_Agente` | `experimental` | Movido a `experiments/prompts/`. |
| `Experimentos/*.xlsx`, `*.csv`, `*.json` de auditoria | `experimental` | Reagrupados en `experiments/audit/`. |
| `Experimentos/*.md`, `*.docx` metodologicos | `experimental` | Reagrupados en `experiments/research/`. |

## Problemas arquitectonicos detectados

1. Mezcla de codigo, datos, runtime y documentacion al mismo nivel logico.
2. `Scripts/` funcionaba como repositorio paralelo de todo, sin frontera entre activo e historico.
3. `Experimentos/` funcionaba como cajon de sastre documental y operativo.
4. Los datos canonicos convivian con legado y material agregado sin encapsulamiento.
5. Habia naming inconsistente y con errores historicos: `Extracting_Procesing`, `Prepocessing`, `Datos_RadaR_Texto`.
6. Varios scripts activos dependian de rutas absolutas viejas, lo que hacia tacita la arquitectura.

## Ambiguedades y decisiones conservadoras

1. `Scripts/Extracting_Procesing` no se borro: se separo por responsabilidad entre `src/extraction/runners/`, `src/preprocessing/` y `legacy/code/extraction_variants/`.
2. `Datos_RAdAR` no se rediseño por fuente porque el flujo real vigente seguia siendo semanal plano; se encapsulo como `data/raw/radar_weekly_flat/`.
3. Los nombres de varios archivos historicos se preservaron para no romper llamadas existentes; la normalizacion fuerte se aplico sobre carpetas canonicas. En Fase 3 se completó la normalización de nombres activos en `src/`.
4. Los aliases de raiz fueron retirados en Fase 2. Desde entonces, el arbol canónico no contiene aliases transicionales.
