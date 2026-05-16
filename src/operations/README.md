# operations

Estatus: `codigo_activo_canonico`

`src/operations/` implementa la capa operativa controlada del repositorio Radar.
Su función es coordinar el pipeline canónico de punta a punta sin reescribir la lógica metodológica ya existente en extracción, preprocessing, NLP y modelado.

## Qué sí hace

- expone un entrypoint operativo único: `python -m src.operations.run_radar_pipeline`
- integra la operación mínima controlada post-W10 vía `--operation-profile post_w10_controlled`
- distingue `mode=controlled` y `mode=experimental`
- orquesta etapas explícitas: extracción, preprocessing, NLP, modelado, export y reporte
- persiste estado auditable por corrida
- soporta reanudación por `run_id` y por etapa
- deja manifiesto maestro, resumen, logs por etapa y JSON de estado por etapa
- publica salidas estables bajo `artifacts/operations/.../published/`
- expone una GUI mínima de control con `python -m src.operations.gui_radar_pipeline`
- expone en la GUI el preset `Operación mínima post-W10`
- permite acotar ventanas operativas con `--date-from` y `--date-to` dentro de una semana canónica

## Qué no hace

- no reemplaza la metodología canónica de cada capa
- no mezcla outputs operativos `controlled` con publicación experimental
- no incorpora scheduling
- no sustituye el tracker experimental de `src/modeling/tracking/`
- no inventa un generador final de reporte cuando todavía no existe

## Estructura

```text
src/operations/
├── __init__.py
├── README.md
├── config.py
├── contracts.py
├── run_context.py
├── state_store.py
├── pipeline_orchestrator.py
├── run_radar_pipeline.py
├── gui_radar_pipeline.py
└── stages/
    ├── __init__.py
    ├── extraction_stage.py
    ├── preprocessing_stage.py
    ├── nlp_stage.py
    ├── modeling_stage.py
    ├── export_stage.py
    └── report_stage.py
```

## Ejecución

Corrida completa:

```bash
python -m src.operations.run_radar_pipeline --week 2026-W14 --mode controlled
```

Corrida parcial:

```bash
python -m src.operations.run_radar_pipeline --week 2026-W14 --from-stage modeling --to-stage export
```

Reanudación por `run_id`:

```bash
python -m src.operations.run_radar_pipeline --resume-run-id radar_2026W14_001
```

Reanudación desde etapa específica:

```bash
python -m src.operations.run_radar_pipeline --resume-run-id radar_2026W14_001 --from-stage preprocessing
```

Dry-run:

```bash
python -m src.operations.run_radar_pipeline --week 2026-W14 --mode controlled --dry-run
```

Operación mínima post-W10 integrada:

```bash
python -m src.operations.run_radar_pipeline --operation-profile post_w10_controlled --from-stage extraction --to-stage modeling --dry-run --operation-modeling-python /home/emilio/anaconda3/envs/radar-exp-py311/bin/python
```

Corrida experimental:

```bash
python -m src.operations.run_radar_pipeline --week 2026-W14 --mode experimental --model-runner src.modeling.runners.run_e2_huber_clean
```

GUI mínima:

```bash
python -m src.operations.gui_radar_pipeline
```

Corrida acotada por fechas y fuentes:

```bash
python -m src.operations.run_radar_pipeline --week 2026-W14 --date-from 2026-04-01 --date-to 2026-04-03 --from-stage extraction --to-stage nlp --sources twitter youtube
```

## Artefactos de corrida

Cada run deja una carpeta bajo:

```text
artifacts/operations/<YYYY>/<YYYY-Www>/<run_id>/
```

Con esta lógica:

- `manifest.json`: contrato maestro de la corrida
- `run_summary.json`: resumen legible con estado global y por etapa
- `manifest_run.json` y `summary_run.json`: aliases de compatibilidad
- `state.json`: estado persistente para reanudar
- `logs/`: log general y log por etapa
- `stages/`: payload JSON homogéneo por etapa
- `published/powerbi/`: tablas y artefactos operativos cuando `mode=controlled`
- `published/experimental/`: publicación aislada cuando `mode=experimental`
- `published/report_inputs/`: paquete de insumos para reporte

## Reanudación

La reanudación funciona leyendo `state.json` del run previo.

- si se usa solo `--resume-run-id`, el orquestador detecta la primera etapa no terminal y continúa desde ahí
- si además se usa `--from-stage`, las etapas desde esa frontera se resetean a `planned` y se reejecutan
- las etapas ya exitosas no se reprocesan innecesariamente cuando la reanudación no fuerza su repetición

## Modos

- `controlled`: exige runner y dataset canónicos de modelado y publica salidas operativas en `published/powerbi/`.
- `experimental`: permite runner o dataset alternativo y publica resultados separados en `published/experimental/`.

## Relación con `experiments/`

La capa operativa no crea un banco experimental paralelo.
Cuando llega a modelado, invoca runners canónicos de `src/modeling/runners/` y reutiliza el tracker existente en `experiments/runs/` y `experiments/audit/`.

## Limitaciones actuales

- el scheduler externo todavía no forma parte de esta capa
- la GUI es mínima: sirve para disparar/reanudar corridas y ver stdout, no para monitoreo multiusuario
- la GUI ahora organiza presets por capa (`Extractors`, `Preprocessing`, `NLP`, `Modeling`, `Export`, `Reporting`) y un preset integrado `Operación mínima post-W10`, pero sigue siendo un launcher local, no una consola multiusuario
- la etapa de reporte queda como `stubbed` en `controlled` y como `skipped` explícito en `experimental`
- la capa NLP activa ya ejecuta sentimiento, clasificacion PMI, normalizacion, refresco de `ml_ready_monica_villarreal_encuestas_pmi_1.xlsx`, `datos_ml_0.xlsx` y reconstruccion del dataset maestro final
- si la corrida rebasa el horizonte historico del scaffold semanal de encuestas, el refresco de `ml_ready` extiende semanas por carry-forward
- la operación post-W10 está integrada al entrypoint y a la GUI; su ruta `predict-only` ya quedó validada materialmente para `E1_v5_clean` y `E9_v2_clean`
- `E9_v2_clean` opera mediante un paquete meta-modelo congelado que consume paquetes base congelados de `E2_v3_clean`, `E3_v2_clean`, `E5_v4_clean` y `E7_v3_clean`
- la operación post-W10 integrada respeta `From Stage / To Stage` entre `extraction` y `modeling`; fuera de ese rango sigue aplicando el pipeline semanal estándar
