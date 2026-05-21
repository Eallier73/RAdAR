# Verificacion Reproducibilidad Dual Controlada

Fecha de actualizacion: `2026-04-03`

## Objetivo

Dejar evidencia de reejecucion controlada de los dos benchmarks congelados del sistema dual vigente.

## Benchmarks verificados

### E1 numerico puro

- benchmark oficial: [E1_v5_clean_20260321_105449](/home/emilio/Documentos/RAdAR/Experimentos/runs/E1_v5_clean_20260321_105449)
- rerun controlado: [E1_v5_operativo_rebuild_v2_20260403_092120](/home/emilio/Documentos/RAdAR/Experimentos/runs/E1_v5_operativo_rebuild_v2_20260403_092120)
- runner: [run_e1_ridge_clean.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e1_ridge_clean.py)

### E9 riesgo-direccion-caidas

- benchmark oficial: [E9_v2_clean_20260401_070431](/home/emilio/Documentos/RAdAR/Experimentos/runs/E9_v2_clean_20260401_070431)
- rerun controlado: [E9_v2_operativo_rebuild_20260403_092042](/home/emilio/Documentos/RAdAR/Experimentos/runs/E9_v2_operativo_rebuild_20260403_092042)
- runner: [run_e9_stacking.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e9_stacking.py)

## Comandos ejecutados

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_benchmarks_operativos_vigentes.py --benchmark-id benchmark_operativo_riesgo_vigente --execute --run-id E9_v2_operativo_rebuild
```

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_benchmarks_operativos_vigentes.py --benchmark-id benchmark_numerico_puro_vigente --execute --run-id E1_v5_operativo_rebuild_v2
```

## Incidente menor corregido

- El primer intento de reejecucion numerica fallo porque el dispatcher operativo arrastraba argumentos viejos (`--extra-reference-run-ids`, `--hypothesis-note`) que [run_e1_ridge_clean.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e1_ridge_clean.py) ya no acepta.
- El congelamiento se corrigio en [run_benchmarks_operativos_vigentes.py](/home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_benchmarks_operativos_vigentes.py).
- La reejecucion valida posterior fue `E1_v5_operativo_rebuild_v2`.

## Resultado

La reproducibilidad operativa quedo confirmada.

### Igualdad exacta en RUN_SUMMARY

| benchmark | rerun | delta_L_total | delta_Avg_MAE | delta_Avg_RMSE | delta_Dir_acc_prom | delta_Det_caidas_prom |
|---|---|---:|---:|---:|---:|---:|
| `E1_v5_clean` | `E1_v5_operativo_rebuild_v2` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `E9_v2_clean` | `E9_v2_operativo_rebuild` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

### Igualdad exacta por horizonte

- `E1_v5_clean` vs `E1_v5_operativo_rebuild_v2`
  - `H1-H4`: `Loss_h`, `MAE`, `Direction_accuracy` y `Deteccion_caidas` sin diferencias.
- `E9_v2_clean` vs `E9_v2_operativo_rebuild`
  - `H1-H4`: `Loss_h`, `MAE`, `Direction_accuracy` y `Deteccion_caidas` sin diferencias.

## Lectura metodologica

- `E1_v5_clean` es regenerable de forma controlada con igualdad exacta en el tracker.
- `E9_v2_clean` es regenerable de forma controlada con igualdad exacta en el tracker.
- La reproducibilidad fuerte del sistema dual vigente queda demostrada a nivel de run oficial, rerun controlado y grid.
- Los reruns de verificacion no reemplazan a los benchmarks oficiales congelados; solo prueban reproducibilidad.
