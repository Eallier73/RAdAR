# Operacion Minima Post-W10

Estatus: `integrada_a_entrypoint_y_gui_con_inferencia_predict_only_validada_para_e1_y_e9`

Este documento define la operacion minima controlada del sistema Radar para el tramo posterior al historico validado.

Frontera operativa:
- historico validado: hasta `2026-W10` (`2026-03-02`)
- operacion real controlada: desde `2026-W11` (`2026-03-09`)

## Regla de congelamiento

Esta capa no cambia modelos ni metodologia.

Perfiles congelados reconocidos por artefacto:
- `E1_v5_clean`: campeon numerico vigente
- `E9_v2_clean`: referente de riesgo, direccion y deteccion de caidas

Dependencias congeladas de `E9_v2_clean`:
- `E1_v5_clean`
- `E2_v3_clean`
- `E3_v2_clean`
- `E5_v4_clean`
- `E7_v3_clean`

La base curada oficial de `E9` sigue siendo:
- `experiments/audit/tabla_maestra_experimentos_radar_e9_curada.xlsx`

## Que queda congelado por capa

Recopilacion y texto semanal:
- universo de fuentes: `facebook`, `twitter`, `youtube`, `medios`
- estructura raw: `data/raw/radar_weekly_flat/`
- estructura texto: `data/text/radar_weekly_flat/`
- semana canonica basada en inicio ISO `YYYY-MM-DD`

Preprocesamiento:
- se reutiliza la etapa ya operativa del orquestador canónico

NLP:
- se reutiliza `run_radar_pipeline` por semana sobre la etapa `nlp`
- no se cambia sentimiento, PMI, normalizacion ni reconstruccion del dataset

Dataset maestro:
- dataset operativo: `data/processed/modeling/datos_ml_master_indice_aceptacion_digital.xlsx`

Modelado:
- no se modifica `src/modeling/`
- no se alteran runners existentes
- `post_w10_controlled` ya no refresca runners experimentales
- la operacion usa una ruta `predict-only` separada de la ruta experimental
- hoy esa ruta esta materializada para `E1_v5_clean` y `E9_v2_clean`, con paquetes congelados propios
- `E9_v2_clean` consume ademas paquetes base congelados de `E2_v3_clean`, `E3_v2_clean`, `E5_v4_clean` y `E7_v3_clean`

Registro:
- cada emision se guarda como artefacto separado bajo `artifacts/operations/post_w10/<operation_id>/`

## Punto de entrada

Punto de entrada integrado al launcher operativo existente:

```bash
python3 -m src.operations.run_radar_pipeline \
  --operation-profile post_w10_controlled \
  --from-stage extraction \
  --to-stage modeling \
  --operation-modeling-python /home/emilio/anaconda3/envs/radar-exp-py311/bin/python
```

Tambien puede dispararse desde:
- `python -m src.operations.gui_radar_pipeline`
- preset `Operación mínima post-W10`
- usando `From Stage / To Stage` para elegir el tramo entre `extraction` y `modeling`

El wrapper subyacente sigue existiendo y puede correrse de forma directa:

```bash
python3 -m src.operations.run_operacion_minima_post_w10 --dry-run
```

Corrida real:

```bash
python3 -m src.operations.run_operacion_minima_post_w10
```

Si el `.env` o las variables de entorno tienen rutas stale para Python, se pueden fijar explícitamente:

```bash
python3 -m src.operations.run_operacion_minima_post_w10 \
  --ops-python /home/emilio/anaconda3/envs/radar-ops-py311/bin/python \
  --modeling-python /home/emilio/anaconda3/envs/radar-exp-py311/bin/python
```

Rango explicito:

```bash
python3 -m src.operations.run_operacion_minima_post_w10 --from-week 2026-W11 --to-week 2026-W18
```

## Estado de integracion

Esta capa ya esta expuesta dentro de:
- `src/operations/run_radar_pipeline.py`
- `src/operations/gui_radar_pipeline.py`

El modulo base que implementa la secuencia sigue siendo:
- `src/operations/run_operacion_minima_post_w10.py`

No esta injertada dentro de `pipeline_orchestrator.py` como una etapa adicional del DAG semanal estándar.
La integracion se hace a nivel de entrypoint y UI, pero ya respeta selección de etapas `extraction -> preprocessing -> nlp -> modeling` para el perfil post-W10.

## Secuencia operativa real

La secuencia implementada es:

1. backfill semanal de NLP sobre `2026-W11 -> semana comun mas reciente disponible`
2. actualizacion del dataset maestro operativo
3. carga de paquetes congelados `predict-only` para `E1_v5_clean`, `E2_v3_clean`, `E3_v2_clean`, `E5_v4_clean`, `E7_v3_clean` y `E9_v2_clean`
4. validacion de contratos congelados de entrada y ensamblado
5. ejecucion de `predict()` solamente sobre semanas pendientes
6. construccion del registro formal de emisiones
7. persistencia de snapshots de prediccion por horizonte para `E1` y `E9`

Regla de selección de etapas del perfil integrado:
- `from-stage extraction --to-stage nlp`: corre `extraction -> preprocessing -> nlp` por semana y se detiene antes de modelado
- `from-stage nlp --to-stage modeling`: corre `nlp` por semana y luego inferencia `predict-only` + emisiones
- `from-stage extraction --to-stage modeling`: corre el tramo completo `extraction -> preprocessing -> nlp -> modeling`
- `from-stage modeling --to-stage modeling`: reutiliza el dataset maestro existente y corre solo inferencia `predict-only` + emisiones

Regla operativa de entorno:
- `run_radar_pipeline` se ejecuta con `ops_python`
- el bootstrap de paquetes predict-only y el registro de emisiones se ejecutan con `modeling_python`
- esto evita depender de un entorno operativo sin dependencias de modelado y separa la preparacion del paquete congelado de la operacion semanal

## Archivos nuevos de esta capa

Wrappers externos:
- `src/operations/frozen_profiles.py`
- `src/operations/frozen_inference_assets.py`
- `src/operations/bootstrap_frozen_inference_assets.py`
- `src/operations/frozen_inference.py`
- `src/operations/build_emission_registry_post_w10.py`
- `src/operations/run_operacion_minima_post_w10.py`

Estos archivos no reemplazan ni mueven scripts existentes.

## Registro de emisiones

Salida esperada por corrida:

```text
artifacts/operations/post_w10/<operation_id>/
├── manifest.json
├── summary.json
├── logs/
│   └── operacion.log
├── emisiones/
│   ├── registro_emisiones.csv
│   ├── registro_emisiones.json
│   └── manifest_ultima_actualizacion.json
└── snapshots/
```

Campos clave del registro:
- `operation_id`
- `model_profile_id`
- `role`
- `fecha_inicio_semana`
- `semana_iso`
- `prediccion_h1..h4`
- `actual_h1..h4`
- `prediction_source_h1..h4`
- `estado_emision`
- `estado_evaluacion`
- `dataset_reference`
- `historical_run_dir`

El `manifest.json` de cada corrida tambien fija:
- `canonical_profiles`
- `canonical_run_dir`
- `metadata_path`
- `parameters_path`
- `runner_module`

Los paquetes `predict-only` viven en:

```text
artifacts/operations/frozen_inference_profiles/
├── E1_v5_clean/
├── E2_v3_clean/
├── E3_v2_clean/
├── E5_v4_clean/
├── E7_v3_clean/
└── E9_v2_clean/
```

Cada paquete contiene:
- `manifest.json`
- `horizons/model_h1.pkl .. model_h4.pkl`
- `horizons/spec_h1.json .. spec_h4.json`

## Backfill post-W10

Ventana actualmente detectable en texto canonico comun:
- desde `2024-09-30`
- hasta `2026-04-27`

Ventana operativa post-W10 actualmente lista para procesar:
- `2026-W11` a `2026-W18`

Contrato congelado adicional de `E9_v2_clean`:
- `H1`: `E1_v5_clean`, `E5_v4_clean`, `E3_v2_clean`, `E2_v3_clean`
- `H2`: `E1_v5_clean`, `E5_v4_clean`, `E2_v3_clean`, `E7_v3_clean`
- `H3`: `E1_v5_clean`, `E5_v4_clean`, `E3_v2_clean`, `E7_v3_clean`
- `H4`: `E1_v5_clean`, `E5_v4_clean`, `E3_v2_clean`, `E2_v3_clean`

## Capa posterior pendiente

No bloquea la operacion minima:
- tablero conectado
- refresco del tablero
- interpretacion asistida
- documento
- presentacion

Sigue siendo la siguiente fase natural del sistema.

## Validacion actual

Validado en esta tarea:
- el punto de entrada integrado compila
- `post_w10_controlled` ya no ejecuta refresh experimental de runs en `modeling`
- se materializaron paquetes `predict-only` de `E1_v5_clean`, `E2_v3_clean`, `E3_v2_clean`, `E5_v4_clean`, `E7_v3_clean` y `E9_v2_clean`, todos con corte historico `2026-W10`
- se ejecuto una corrida real `modeling -> emisiones`:
  - `artifacts/operations/post_w10/post_w10_predict_only_e1_e9_validation_20260508_0758/`
  - genero `registro_emisiones.csv/json`
  - emitio predicciones nuevas de `E1_v5_clean` y `E9_v2_clean` para semanas pendientes
  - dejo snapshots por horizonte para ambos perfiles principales
  - mantuvo `operation_mode = predict_only_frozen_inference` y sin refresh experimental de runs

No validado todavia en esta tarea:
- backfill historico completo de emisiones semana por semana desde `2026-W11`
- comparacion numerica contra una referencia externa de emisiones operativas
