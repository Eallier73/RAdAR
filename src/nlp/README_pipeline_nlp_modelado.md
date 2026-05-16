# Pipeline NLP -> Modelado

## Objetivo

Dejar trazada la ruta real de la etapa NLP previa a modelado, desde los corpus semanales en texto plano hasta el dataset maestro final usado por la capa de modelado.

Este documento no inventa rutas ni scripts nuevos. Mapea la logica funcional esperada contra el estado real del repo en la rama `feature/restructuracion-arquitectonica-repo`.

## Diagnostico ejecutivo

- La ruta operativa hoy ya esta cerrada como: `data/text/` -> sentimiento semanal -> clasificacion PMI -> normalizacion PMI -> `ml_ready_monica_villarreal_encuestas_pmi_1.xlsx` -> `datos_ml_0.xlsx` -> `datos_ml_master_indice_aceptacion_digital.xlsx`.
- La clasificacion tematica PMI ya esta cableada al orquestador operativo actual.
- La normalizacion tematica ya esta cableada al orquestador operativo actual.
- El puente `PMI normalizado -> ml_ready_monica_villarreal_encuestas_pmi_1.xlsx` ya quedo formalizado en `src/nlp/generar_ml_ready_encuestas_pmi.py`.
- El dataset maestro final `datos_ml_master_indice_aceptacion_digital.xlsx` existe y es compatible con `src/modeling/core/config.py` y `src/modeling/core/data_master.py`.
- Ya se reincorporo `src/nlp/reconstruir_dataset_aceptacion_digital.py` y reproduce la cadena `datos_ml_0.xlsx` -> `datos_ml_master_indice_aceptacion_digital.xlsx` con la misma estructura de los artefactos historicos del repo.
- Cuando la corrida semanal rebasa el horizonte historico del scaffold semanal de encuestas, el generador de `ml_ready` extiende la grilla por carry-forward antes de injertar el PMI.

## Rutas reales resueltas

| Concepto | Ruta real |
| --- | --- |
| Corpus semanales en texto | `data/text/radar_weekly_flat/` |
| Raw semanal aguas arriba | `data/raw/radar_weekly_flat/` |
| Diccionarios congelados | `data/reference/dictionaries_nlp/diccionarios_finales/` |
| Resultados de clasificacion tematica | `data/reference/dictionaries_nlp/resultados_clasificacion_temas/` |
| Artefactos de modelado pre-NLP final | `data/processed/modeling/` |
| Config canonica de modelado | `src/modeling/core/config.py` |
| Loader canonico del dataset maestro | `src/modeling/core/data_master.py` |
| Orquestador operativo | `src/operations/run_radar_pipeline.py` |

## Dependencia previa

La etapa NLP arranca despues de preprocessing, no despues de raw.

Equivalentes reales de la frontera previa:

- orquestador operativo: `python -m src.operations.run_radar_pipeline --from-stage preprocessing --to-stage preprocessing ...`
- wrapper de preprocessing: `python -m src.preprocessing pipeline-base ...`
- subpaso minimo que deja la entrada lista para NLP: `python -m src.preprocessing promover-texto`

`src/operations/stages/preprocessing_stage.py` deja la salida canonica en:

- `data/text/radar_weekly_flat/facebook_semana_texto/`
- `data/text/radar_weekly_flat/twitter_semana_texto/`
- `data/text/radar_weekly_flat/youtube_semana_texto/`
- `data/text/radar_weekly_flat/medios_semana_texto/`

## Entrada formal de NLP

### Carpeta real de entrada

`data/text/radar_weekly_flat/`

### Organizacion real por fuente

- `facebook_semana_texto/`
- `twitter_semana_texto/`
- `youtube_semana_texto/`
- `medios_semana_texto/`

### Convencion real de nombres

Conviven dos convenciones:

- canonica actual: `YYYY-MM-DD_fuente.txt`
- heredada: `YY_WW_fuente.txt`

Estado observado:

- `facebook_semana_texto`: 83 archivos canonicos + 76 heredados
- `twitter_semana_texto`: 83 archivos canonicos + 75 heredados
- `youtube_semana_texto`: 83 archivos canonicos + 75 heredados
- `medios_semana_texto`: 83 archivos canonicos + 75 heredados

Para las semanas de interes del 2 de marzo al 12 de abril de 2026, los corpus canonicos presentes llegan hasta:

- `2026-03-02_*`
- `2026-03-09_*`
- `2026-03-16_*`
- `2026-03-23_*`
- `2026-03-30_*`
- `2026-04-06_*`

### Precondiciones minimas

- un `.txt` por fuente y semana en `data/text/radar_weekly_flat/<fuente>_semana_texto/`
- naming canonico preferido `YYYY-MM-DD_fuente.txt`
- la resolucion operativa ya no depende del naming heredado: los scripts NLP resuelven por semana ISO y priorizan el archivo canonico `YYYY-MM-DD_fuente.txt`
- textos ya promovidos desde `data/raw/`
- para sentimiento semanal se esperan las 4 fuentes
- para clasificacion tematica solo se usan Twitter, YouTube y Medios; Facebook queda fuera por diseno

## Ruta operativa real de la etapa

### 1. Sentimiento semanal

**Script:** `src/nlp/aceptacion_digital_redes_ponderacion_medios.py`  
**Estatus:** `canonico`  
**Cableado al orquestador operativo:** `si`

Entradas reales:

- `data/text/radar_weekly_flat/facebook_semana_texto/*.txt`
- `data/text/radar_weekly_flat/twitter_semana_texto/*.txt`
- `data/text/radar_weekly_flat/youtube_semana_texto/*.txt`
- `data/text/radar_weekly_flat/medios_semana_texto/*.txt`
- `data/reference/dictionaries_nlp/diccionarios_polaridad/stop_list_espanol_limpia.txt`
- `data/reference/dictionaries_nlp/diccionarios_polaridad/diccionario_palabras_positivas.txt`
- `data/reference/dictionaries_nlp/diccionarios_polaridad/diccionario_palabras_negativas.txt`

Salida real:

- `data/processed/modeling/aceptacion_digital_redes_medios_sentimiento_semanal.xlsx`
- hoja: `sentimiento_semanal`

Columnas observadas:

- `anio_iso`
- `semana_iso`
- `periodo_iso`
- `sentimiento_facebook`
- `sentimiento_twitter`
- `sentimiento_youtube`
- `sentimiento_redes_ponderado`
- `sentimiento_medios`
- `promedio_redes_medios`

Observaciones:

- las columnas esperadas siguen existiendo con esos nombres exactos
- el script soporta naming heredado `YY_WW` y naming canonico `YYYY-MM-DD`
- cuando detecta ambas convenciones para la misma semana, prioriza el archivo canonico
- el artefacto real llega hoy hasta `2026-W14`

### 2. Diccionarios tematicos congelados

**Artefactos canonicos reales:**

- `data/reference/dictionaries_nlp/diccionarios_finales/diccionario_pmi_confianza_v5.xlsx`
- `data/reference/dictionaries_nlp/diccionarios_finales/diccionario_pmi_confianza_v10.xlsx`

Hojas observadas:

- `Diccionario_V5`
- `Diccionario_V10`

Columnas observadas:

- `Categoria`
- `Palabra`
- `Delta_PMI`
- `Confianza`

Script historico de generacion:

- `src/nlp/diccionario_temas_pmi_confianza.py`

Clasificacion de ese script:

- `historico`
- util para regenerar diccionario si hay una decision metodologica explicita
- no debe formar parte del rerun normal de NLP

Observaciones:

- tambien existe `data/reference/dictionaries_nlp/produccion_diccionarios/pmi_confianza_run1.xlsx`, pero hoy el consumo mas claro y estable esta en los archivos congelados de `diccionarios_finales/`
- no se detecto una version congelada mas nueva que `v5` y `v10`

### 3. Clasificacion semanal de temas

**Script:** `src/nlp/clasificacion_temas_pmi_confianza.py`  
**Estatus:** `canonico`  
**Cableado al orquestador operativo:** `si`

Regla metodologica implementada:

- `score = Delta_PMI * hits * Confianza`

Exclusion de Facebook:

- confirmada en codigo
- `CORPUS_DIRS` solo incluye `twitter`, `medios` y `youtube`

Entradas logicas reales:

- `data/text/radar_weekly_flat/twitter_semana_texto/*.txt`
- `data/text/radar_weekly_flat/medios_semana_texto/*.txt`
- `data/text/radar_weekly_flat/youtube_semana_texto/*.txt`
- diccionarios congelados `v5` y `v10`

Salidas reales localizadas:

- `data/reference/dictionaries_nlp/resultados_clasificacion_temas/pmi_confianza_corpus_unido_twitter.xlsx`
- `data/reference/dictionaries_nlp/resultados_clasificacion_temas/pmi_confianza_corpus_unido_medios.xlsx`
- `data/reference/dictionaries_nlp/resultados_clasificacion_temas/pmi_confianza_corpus_unido_youtube.xlsx`
- `data/reference/dictionaries_nlp/resultados_clasificacion_temas/pmi_confianza_corpus_unido_consolidado.xlsx`

Forma del consolidado real:

- hojas `Consolidado_V5` y `Consolidado_V10`
- 31 columnas por hoja
- categorias en tripletas `Positivo / Negativo / Neto`
- los artefactos historicos observados cubren de `24_40` a `26_10`, y la nueva salida canonica del clasificador ya fue validada sobre el bloque `2026-03-02` a `2026-04-06`

Observaciones criticas:

- el script existe y la metodologia coincide con la especificacion funcional
- sus defaults ya apuntan a `diccionarios_finales/` y al directorio real de resultados
- la seleccion de archivos ya deduplica `YY_WW` vs `YYYY-MM-DD` por semana ISO y prioriza la convencion canonica
- el naming de semana en la salida consolidada ya queda en `YYYY-MM-DD`
- el orquestador le pasa `--through-date` para rerun acumulativo semana por semana

### 4. Normalizacion de temas

**Script:** `src/nlp/resultados_clasificacion_temas_pmi_confianza_normalizado.py`  
**Estatus:** `canonico`  
**Cableado al orquestador operativo:** `si`

Entrada real localizada:

- `data/reference/dictionaries_nlp/resultados_clasificacion_temas/pmi_confianza_corpus_unido_consolidado.xlsx`

Salida real localizada:

- `data/reference/dictionaries_nlp/resultados_clasificacion_temas/pmi_confianza_corpus_unido_consolidado_normalizado.xlsx`

Regla de normalizacion implementada:

- transformacion celda a celda: `signo(x) * log_base(1 + |x|)`
- base por default: `2`
- preserva signo y orden relativo
- comprime outliers

Alcance real de la normalizacion:

- se aplica sobre el consolidado semanal ya unido
- no es una normalizacion por corpus individual
- la normalizacion por volumen de texto ocurre antes, dentro de `clasificacion_temas_pmi_confianza.py`, donde cada corpus se escala por 1000 tokens antes del consolidado

Observaciones criticas:

- los defaults del script ya quedaron alineados con los nombres reales de esta rama
- el orquestador sigue pasandole `--input` y `--output` explicitos para no depender de defaults

### 5. Generacion de ML-ready y fusion hacia ML

**Script puente PMI -> ML-ready:** `src/nlp/generar_ml_ready_encuestas_pmi.py`  
**Estatus:** `canonico`  
**Cableado al orquestador operativo:** `si`

Insumos reales que usa:

- `data/processed/modeling/ml_ready_monica_villarreal_encuestas_pmi_1.xlsx` como scaffold semanal de encuestas/proyecciones
- `data/reference/dictionaries_nlp/resultados_clasificacion_temas/pmi_confianza_corpus_unido_consolidado_normalizado.xlsx`

Salida real:

- `data/processed/modeling/ml_ready_monica_villarreal_encuestas_pmi_1.xlsx`

Lo que hace:

- injerta columnas `v5_*` y `v10_*` desde el PMI normalizado sobre `ML_Ready_AllWeeks`
- recompone `has_full_pmi_features`
- reconstruye `ML_Ready_Train` como subconjunto con PMI completo y targets presentes
- si el `through-date` rebasa el scaffold historico, extiende semanas faltantes por carry-forward de la ultima fila disponible antes de injertar el PMI

Observacion metodologica:

- este puente ya cierra operativamente la regeneracion del `ml_ready` en la rama actual
- la parte que sigue apoyandose en scaffold congelado es la grilla semanal de encuestas/proyecciones, no el injerto PMI

**Script:** `src/nlp/unir_ml_ready_con_sentimiento.py`  
**Estatus:** `canonico`  
**Cableado al orquestador operativo:** `si`

Insumos reales que usa:

- `data/processed/modeling/ml_ready_monica_villarreal_encuestas_pmi_1.xlsx`
- `data/processed/modeling/aceptacion_digital_redes_medios_sentimiento_semanal.xlsx`

Salida real:

- `data/processed/modeling/datos_ml_0.xlsx`

Columnas nuevas que agrega:

- `flag_missing_sentimiento_digital`
- `sentimiento_facebook`
- `sentimiento_twitter`
- `sentimiento_youtube`
- `sentimiento_redes_ponderado`
- `sentimiento_medios`
- `promedio_redes_medios`

Material legacy que arrastra:

- encuestas mensuales y sus variantes `*_locf`
- `flag_missing_*`
- consensos mensuales
- features PMI `v5_*` y `v10_*`

Observacion estructural critica:

- la ruta `PMI normalizado -> ml_ready -> datos_ml_0.xlsx` ya esta cerrada en codigo operativo
- `unir_ml_ready_con_sentimiento.py` sigue sin consumir el consolidado normalizado de forma directa
- consume el `ml_ready_monica_villarreal_encuestas_pmi_1.xlsx` ya regenerado por `generar_ml_ready_encuestas_pmi.py`

Script relacionado de soporte:

- `src/nlp/unificar_encuestas_sentimiento.py`

Rol real de soporte:

- genera `data/processed/modeling/encuestas_y_sentimiento_mensual_unificado.xlsx`
- es un artefacto mensual util para trazabilidad
- no es la entrada directa de `unir_ml_ready_con_sentimiento.py`

### 6. Reconstruccion del dataset final

**Script:** `src/nlp/reconstruir_dataset_aceptacion_digital.py`  
**Estatus:** `canonico`  
**Cableado al orquestador operativo:** `si`

Artefactos reales presentes:

- `data/processed/modeling/datos_ml_0.xlsx`
- `data/processed/modeling/datos_ml_1.xlsx`
- `data/processed/modeling/datos_ml_2.xlsx`
- `data/processed/modeling/datos_ml_3.xlsx`
- `data/processed/modeling/datos_ml_4.xlsx`
- `data/processed/modeling/datos_ml_5.xlsx`
- `data/processed/modeling/datos_ml_master.xlsx`
- `data/processed/modeling/datos_ml_master_1.xlsx`
- `data/processed/modeling/datos_ml_master_2.xlsx`
- `data/processed/modeling/datos_ml_master_3.xlsx`
- `data/processed/modeling/datos_ml_master_4.xlsx`
- `data/processed/modeling/datos_ml_master_indice_aceptacion_digital.xlsx`

Lo que si pudo verificarse:

- `datos_ml_3.xlsx` existe y ya refleja una poda fuerte:
  - conserva `target_serie_3e`, `target_serie_4e`
  - conserva `sentimiento_redes_ponderado`, `sentimiento_medios`
  - conserva `v5_*_neto` y `v10_*_neto`
  - elimina encuestas, variantes `locf`, banderas y columnas PMI positivo/negativo
- `src/nlp/generar_lags_datos_ml.py` sigue siendo el helper de lageado reutilizado por el reconstructor
- `datos_ml_5.xlsx` existe y ya no contiene `target_serie_3e` ni `v10_*_neto`
- `datos_ml_master.xlsx` existe y ya reduce la tabla a:
  - `sentimiento_redes_ponderado`
  - `sentimiento_medios`
  - `v5_*_neto`
  - `target_serie_4e_lag1..lag4`
- `datos_ml_master_1.xlsx` a `datos_ml_master_4.xlsx` existen y el reconstructor los reproduce en la misma secuencia legacy, incluyendo la snapshot transicional corregida despues en `datos_ml_master_2.xlsx`
- `datos_ml_master_indice_aceptacion_digital.xlsx` existe y renombra el target final a la convencion hoy usada por modelado

Validacion ejecutada sobre el script reincorporado:

- salida comparada contra `data/processed/modeling/`
- misma cantidad de filas y columnas en:
  - `datos_ml_3.xlsx`
  - `datos_ml_4.xlsx`
  - `datos_ml_5.xlsx`
  - `datos_ml_master.xlsx`
  - `datos_ml_master_1.xlsx`
  - `datos_ml_master_2.xlsx`
  - `datos_ml_master_3.xlsx`
  - `datos_ml_master_4.xlsx`
  - `datos_ml_master_indice_aceptacion_digital.xlsx`
- diferencias solo de precision flotante residual, sin diferencias de estructura

Conclusion operativa de esta seccion:

- la reconstruccion `datos_ml_0.xlsx` -> dataset maestro final ya sobrevive como pipeline reproducible dentro de `src/nlp/`
- la cadena NLP -> dataset maestro final ya quedo cerrada en esta rama
- la deuda residual ya no esta en el injerto PMI, sino en que el scaffold semanal de encuestas/proyecciones sigue derivando de un workbook congelado y no de una reconstruccion de novo desde encuestas mensuales

### 7. Dataset maestro final de modelado

**Archivo real:** `data/processed/modeling/datos_ml_master_indice_aceptacion_digital.xlsx`

Columnas observadas:

- `fecha_inicio_semana`
- `semana_iso`
- `y_t_aceptacion_digital`
- `target_1w_aceptacion_digital`
- `target_2w_aceptacion_digital`
- `target_3w_aceptacion_digital`
- `target_4w_aceptacion_digital`
- `sentimiento_medios`
- `v5_agua_neto`
- `v5_alumbrado_neto`
- `v5_americo_neto`
- `v5_basura_neto`
- `v5_corrupcion_neto`
- `v5_delitos_neto`
- `v5_morena_neto`
- `v5_obras_neto`
- `v5_prevencion_neto`
- `v5_vialidad_neto`

Compatibilidad con modelado:

- `src/modeling/core/config.py` apunta exactamente a este archivo
- `src/modeling/core/config.py` exige exactamente esas columnas target y esas `BASE_FEATURE_COLUMNS`
- `src/modeling/core/data_master.py` valida esas columnas al cargar el dataset
- los runners `run_e1_bayesian_ridge.py`, `run_e1_ridge_clean.py`, `run_e2_huber_clean.py`, `run_e5_catboost.py`, `run_e8_hibrido_residuales.py`, `run_e9_stacking.py` y `classification_pipeline_common.py` importan `load_master_dataset`

Divergencia importante:

- el runner operativo por default del orquestador es `src.modeling.runners.run_e10_meta_selector`
- `src/operations/stages/modeling_stage.py` trata a E10 como `dataset optional`
- por eso el modo `controlled` del orquestador no ejerce este dataset maestro en su runner por default
- conclusion: el dataset maestro si esta alineado con la capa base de modelado, pero no es el insumo central del runner E10 por default

## Mapa de scripts y estatus

| Item | Ruta real | Funcion | Estatus | Observacion |
| --- | --- | --- | --- | --- |
| `aceptacion_digital_redes_ponderacion_medios.py` | `src/nlp/aceptacion_digital_redes_ponderacion_medios.py` | calcula sentimiento semanal por fuente y ponderado | `canonico` | cableado al orquestador `nlp_stage.py` |
| `clasificacion_temas_pmi_confianza.py` | `src/nlp/clasificacion_temas_pmi_confianza.py` | clasifica temas con `Delta_PMI * hits * Confianza` | `canonico` | cableado; deduplica naming legacy/canonico por semana ISO y expone `--through-date` |
| `resultados_clasificacion_temas_pmi_confianza_normalizado.py` | `src/nlp/resultados_clasificacion_temas_pmi_confianza_normalizado.py` | comprime outliers del consolidado tematico | `canonico` | cableado; defaults alineados a rutas reales |
| `generar_ml_ready_encuestas_pmi.py` | `src/nlp/generar_ml_ready_encuestas_pmi.py` | injerta PMI normalizado sobre el scaffold semanal y recompone `ML_Ready_Train` / `ML_Ready_AllWeeks` | `canonico` | cableado; extiende semanas faltantes por carry-forward si hace falta |
| `unir_ml_ready_con_sentimiento.py` | `src/nlp/unir_ml_ready_con_sentimiento.py` | agrega sentimiento semanal a un dataset ML ya unido con PMI | `canonico` | consume el `ml_ready` regenerado por el script puente |
| `unificar_encuestas_sentimiento.py` | `src/nlp/unificar_encuestas_sentimiento.py` | unifica encuestas mensuales con sentimiento mensual | `soporte` | produce trazabilidad mensual; no alimenta directo `datos_ml_0.xlsx` |
| `generar_lags_datos_ml.py` | `src/nlp/generar_lags_datos_ml.py` | genera lags de `datos_ml_3.xlsx` hacia `datos_ml_4.xlsx` | `soporte` | helper reutilizado por el reconstructor canonico |
| `diccionario_temas_pmi_confianza.py` | `src/nlp/diccionario_temas_pmi_confianza.py` | genera diccionarios PMI+Confianza | `historico` | no debe entrar al rerun normal |
| `diccionario_temas_pmi.py` | `src/nlp/diccionario_temas_pmi.py` | genera diccionarios PMI clasico | `fuera_de_ruta` | metodologia reemplazada por PMI+Confianza |
| `diccionario_temas_wpmi.py` | `src/nlp/diccionario_temas_wpmi.py` | genera WPMI | `fuera_de_ruta` | no participa en el pipeline actual hacia modelado |
| `clasificacion_temas.py` | `src/nlp/clasificacion_temas.py` | clasifica usando PMI sin confianza e incluye Facebook | `fuera_de_ruta` | contradice la metodologia activa |
| `reconstruir_dataset_aceptacion_digital.py` | `src/nlp/reconstruir_dataset_aceptacion_digital.py` | recompone `datos_ml_3.xlsx` a `datos_ml_master_indice_aceptacion_digital.xlsx` desde `datos_ml_0.xlsx` | `canonico` | validado contra los artefactos historicos y cableado al orquestador |
## Scripts historicos o fuera de ruta confirmados

Historico:

- `src/nlp/diccionario_temas_pmi_confianza.py`

Fuera de ruta:

- `src/nlp/diccionario_temas_pmi.py`
- `src/nlp/diccionario_temas_wpmi.py`
- `src/nlp/clasificacion_temas.py`

## Punto de entrada operativo recomendado

### Orquestacion con manejo explicito de interpretes por etapa

Los unicos entry points que hoy activan interpretes diferenciados por etapa son:

- `python -m src.operations.run_radar_pipeline`
- `python -m src.operations.gui_radar_pipeline`

Motivo:

- `src/operations/config.py` resuelve `RADAR_OPS_PYTHON` y `RADAR_MODELING_PYTHON`
- `src/operations/stages/*.py` usan `STAGE_PYTHON[...]`

Lo que no hace cambio de entorno por etapa:

- `python -m src.preprocessing ...`
- `python -m src.nlp....`
- wrappers locales que usan `sys.executable`

### Recomendacion operativa real hoy

No conviene inventar un orquestador nuevo todavia.

La recomendacion real es:

1. usar el orquestador de `src/operations/` para correr la etapa NLP completa
2. correr semana por semana con `--week YYYY-Www` o con la fecha canonica de inicio de semana
3. usar rerun manual script por script solo cuando se quiera depurar un tramo especifico

Secuencia recomendada hoy:

```bash
# 1) etapa NLP completa via orquestador, una semana por corrida
python -m src.operations.run_radar_pipeline --week 2026-W10 --from-stage nlp --to-stage nlp
python -m src.operations.run_radar_pipeline --week 2026-W11 --from-stage nlp --to-stage nlp
python -m src.operations.run_radar_pipeline --week 2026-W12 --from-stage nlp --to-stage nlp
python -m src.operations.run_radar_pipeline --week 2026-W13 --from-stage nlp --to-stage nlp
python -m src.operations.run_radar_pipeline --week 2026-W14 --from-stage nlp --to-stage nlp
python -m src.operations.run_radar_pipeline --week 2026-W15 --from-stage nlp --to-stage nlp

# 2) si se requiere depuracion manual, la secuencia real hoy es:
$RADAR_OPS_PYTHON -m src.nlp.aceptacion_digital_redes_ponderacion_medios --week 2026-W10

# 3) opcional, trazabilidad mensual
$RADAR_OPS_PYTHON -m src.nlp.unificar_encuestas_sentimiento

# 4) clasificacion tematica acumulativa hasta la semana objetivo
$RADAR_OPS_PYTHON -m src.nlp.clasificacion_temas_pmi_confianza \
  --dict_v5 data/reference/dictionaries_nlp/diccionarios_finales/diccionario_pmi_confianza_v5.xlsx \
  --dict_v10 data/reference/dictionaries_nlp/diccionarios_finales/diccionario_pmi_confianza_v10.xlsx \
  --output data/reference/dictionaries_nlp/resultados_clasificacion_temas \
  --nombre pmi_confianza_corpus_unido \
  --through-date 2026-04-12

# 5) normalizacion del consolidado
$RADAR_OPS_PYTHON -m src.nlp.resultados_clasificacion_temas_pmi_confianza_normalizado \
  --input data/reference/dictionaries_nlp/resultados_clasificacion_temas/pmi_confianza_corpus_unido_consolidado.xlsx \
  --output data/reference/dictionaries_nlp/resultados_clasificacion_temas/pmi_confianza_corpus_unido_consolidado_normalizado.xlsx

# 6) refresco de ML-ready desde PMI normalizado
$RADAR_OPS_PYTHON -m src.nlp.generar_ml_ready_encuestas_pmi \
  --scaffold data/processed/modeling/ml_ready_monica_villarreal_encuestas_pmi_1.xlsx \
  --pmi-normalized data/reference/dictionaries_nlp/resultados_clasificacion_temas/pmi_confianza_corpus_unido_consolidado_normalizado.xlsx \
  --output data/processed/modeling/ml_ready_monica_villarreal_encuestas_pmi_1.xlsx \
  --through-date 2026-04-12

# 7) fusion del ML-ready regenerado con sentimiento digital
$RADAR_OPS_PYTHON -m src.nlp.unir_ml_ready_con_sentimiento

# 8) reconstruccion reproducible del dataset maestro final
$RADAR_OPS_PYTHON -m src.nlp.reconstruir_dataset_aceptacion_digital \
  --input-ml0 data/processed/modeling/datos_ml_0.xlsx \
  --output-dir data/processed/modeling
```

## Observaciones de rutas corregidas

- el alias historico `Datos_Modelo_ML/` ya no es ruta canonica; hoy es `data/processed/modeling/`
- la capa historica `Scripts/Modeling/` hoy vive en `src/modeling/`
- el script historico `src/nlp/aceptacion_digital_redes_ponderacion_medios.py` ya fue normalizado a ASCII; no se usa version con acento
- los diccionarios congelados vigentes no estan en `produccion_diccionarios/`; estan en `diccionarios_finales/`
- los resultados consolidados reales localizados no se llaman `consolidado.xlsx` / `consolidado_norm.xlsx`; se llaman:
  - `pmi_confianza_corpus_unido_consolidado.xlsx`
  - `pmi_confianza_corpus_unido_consolidado_normalizado.xlsx`

## Riesgos y huecos abiertos

- la coexistencia fisica de `YYYY-MM-DD_fuente.txt` y `YY_WW_fuente.txt` sigue existiendo en `data/text/`, aunque la resolucion operativa ya prioriza la convencion canonica por semana ISO
- el scaffold semanal de encuestas/proyecciones que alimenta `ml_ready` sigue partiendo de un workbook congelado y no de una reconstruccion de novo desde la fuente mensual
- cuando se rebasa el horizonte historico del scaffold, la extension semanal se hace por carry-forward; eso cierra la operacion, pero debe asumirse como una decision operativa explicita
- el runner default E10 del orquestador sigue tratando el dataset maestro como optional, asi que la alineacion mas fuerte continua estando en la capa base de `src/modeling/core/`

## Validacion final

Estado final de la validacion:

- la etapa NLP real si termina hoy en un dataset usado por modelado: `data/processed/modeling/datos_ml_master_indice_aceptacion_digital.xlsx`
- ese dataset esta alineado con `src/modeling/core/config.py`
- ese dataset esta alineado con `src/modeling/core/data_master.py`
- no hay una ruptura de columnas entre ese dataset y los runners clasicos basados en `load_master_dataset`
- la reconstruccion `datos_ml_0.xlsx` -> dataset maestro final ya es reproducible en `src/nlp/reconstruir_dataset_aceptacion_digital.py`
- la clasificacion tematica, la normalizacion y el refresco de `ml_ready` ya quedaron cableados al orquestador operativo
- la deuda que sigue abierta ya no es de cableado, sino de estrategia de scaffold para encuestas/proyecciones mas alla del horizonte historico disponible
