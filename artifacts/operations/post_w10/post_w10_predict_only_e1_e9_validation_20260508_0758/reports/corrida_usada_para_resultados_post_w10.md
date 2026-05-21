# Registro De Corrida Usada Para Resultados Post-W10

- `operation_id`: `post_w10_predict_only_e1_e9_validation_20260508_0758`
- `registrado_en`: `2026-05-16T06:01:51-06:00`
- `objetivo`: dejar asentado exactamente que artefactos, dataset, paquetes y comando se usaron para la corrida cuyos resultados post-W10 fueron comentados posteriormente.

## Alcance real de la corrida

- tramo corrido: `2026-W11 -> 2026-W18`
- stages: `modeling -> modeling`
- modo operativo: `predict_only_frozen_inference`
- `ops_python`: `/home/emilio/anaconda3/envs/radar-ops-py311/bin/python`
- `modeling_python`: `/home/emilio/anaconda3/envs/radar-exp-py311/bin/python`

## Comando ejecutado

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python -m src.operations.build_emission_registry_post_w10 --operation-id post_w10_predict_only_e1_e9_validation_20260508_0758 --operation-root /home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/post_w10/post_w10_predict_only_e1_e9_validation_20260508_0758 --from-week 2026-W11 --to-week 2026-W18 --dataset-path /home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/data/processed/modeling/datos_ml_master_indice_aceptacion_digital.xlsx --comment '' --e1-run-dir /home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/runs/E1_v5_clean_20260321_105449 --e9-run-dir /home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/runs/E9_v2_clean_20260401_070431
```

## Dataset e insumos estructurales usados

- dataset maestro operativo:
  - `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/data/processed/modeling/datos_ml_master_indice_aceptacion_digital.xlsx`
- tabla curada de stacking `E9`:
  - `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/audit/tabla_maestra_experimentos_radar_e9_curada.xlsx`

## Corridas canonicas tomadas como base

- `E1_v5_clean`:
  - run dir: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/runs/E1_v5_clean_20260321_105449`
  - metadata: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/runs/E1_v5_clean_20260321_105449/metadata_run.json`
  - parametros: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/runs/E1_v5_clean_20260321_105449/parametros_run.json`
  - runner module: `src.modeling.runners.run_e1_ridge_clean`
- `E2_v3_clean`:
  - run dir: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/runs/E2_v3_clean_20260323_061213`
  - runner module: `src.modeling.runners.run_e2_huber_clean`
- `E3_v2_clean`:
  - run dir: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/runs/E3_v2_clean_20260325_045918`
  - runner module: `src.modeling.runners.run_e3_random_forest`
- `E5_v4_clean`:
  - run dir: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/runs/E5_v4_clean_20260330_091736`
  - runner module: `src.modeling.runners.run_e5_catboost`
- `E7_v3_clean`:
  - run dir: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/runs/E7_v3_clean_20260330_113801`
  - runner module: `src.modeling.runners.run_e7_prophet`
- `E9_v2_clean`:
  - run dir: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/runs/E9_v2_clean_20260401_070431`
  - metadata: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/runs/E9_v2_clean_20260401_070431/metadata_run.json`
  - parametros: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/experiments/runs/E9_v2_clean_20260401_070431/parametros_run.json`
  - runner module: `src.modeling.runners.run_e9_stacking`

## Paquetes predict-only realmente cargados

- `E1_v5_clean`:
  - package root: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/frozen_inference_profiles/E1_v5_clean`
  - manifest: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/frozen_inference_profiles/E1_v5_clean/manifest.json`
  - package kind: `base_model`
  - dataset cutoff: `2026-W10` / `2026-03-02`
- `E2_v3_clean`:
  - package root: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/frozen_inference_profiles/E2_v3_clean`
  - manifest: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/frozen_inference_profiles/E2_v3_clean/manifest.json`
  - package kind: `base_model`
  - dataset cutoff: `2026-W10` / `2026-03-02`
- `E3_v2_clean`:
  - package root: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/frozen_inference_profiles/E3_v2_clean`
  - manifest: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/frozen_inference_profiles/E3_v2_clean/manifest.json`
  - package kind: `base_model`
  - dataset cutoff: `2026-W10` / `2026-03-02`
- `E5_v4_clean`:
  - package root: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/frozen_inference_profiles/E5_v4_clean`
  - manifest: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/frozen_inference_profiles/E5_v4_clean/manifest.json`
  - package kind: `base_model`
  - dataset cutoff: `2026-W10` / `2026-03-02`
- `E7_v3_clean`:
  - package root: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/frozen_inference_profiles/E7_v3_clean`
  - manifest: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/frozen_inference_profiles/E7_v3_clean/manifest.json`
  - package kind: `base_model`
  - dataset cutoff: `2026-W10` / `2026-03-02`
- `E9_v2_clean`:
  - package root: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/frozen_inference_profiles/E9_v2_clean`
  - manifest: `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/frozen_inference_profiles/E9_v2_clean/manifest.json`
  - package kind: `stacking_meta_model`
  - dependencias cargadas: `E1_v5_clean`, `E2_v3_clean`, `E3_v2_clean`, `E5_v4_clean`, `E7_v3_clean`
  - dataset cutoff: `2026-W10` / `2026-03-02`

## Nota metodologica critica

- esta corrida no cargo un `model.pkl` original publicado por la experimentacion historica, porque ese artefacto no existia en `experiments/runs/...`
- esta corrida si cargo paquetes `predict-only` reconstruidos desde corridas canonicas y recortados al corte historico `2026-W10`
- por tanto, este registro sirve para trazabilidad operativa exacta de lo corrido, pero no debe usarse como prueba de equivalencia bit a bit con un artefacto productivo historicamente publicado

## Salidas dejadas por la corrida

- manifest operativo:
  - `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/post_w10/post_w10_predict_only_e1_e9_validation_20260508_0758/manifest.json`
- summary operativo:
  - `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/post_w10/post_w10_predict_only_e1_e9_validation_20260508_0758/summary.json`
- resumen del registro:
  - `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/post_w10/post_w10_predict_only_e1_e9_validation_20260508_0758/emission_registry_summary.json`
- registro de emisiones:
  - `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/post_w10/post_w10_predict_only_e1_e9_validation_20260508_0758/emisiones/registro_emisiones.csv`
  - `/home/emilio/Documentos/RAdAR_worktrees/restructuracion_arquitectonica/artifacts/operations/post_w10/post_w10_predict_only_e1_e9_validation_20260508_0758/emisiones/registro_emisiones.json`
