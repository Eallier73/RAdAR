# Resumen Resultados E2 Verificacion Tactica

Fecha de actualizacion: `2026-04-03`

## Alcance

La verificacion tactica de `E2` no requirio nuevas corridas en esta fase porque la familia ya tenia tres runs canónicos, comparables y completos:

- [E2_v1_clean_20260323_050029](/home/emilio/Documentos/RAdAR/Experimentos/runs/E2_v1_clean_20260323_050029)
- [E2_v2_clean_20260323_054101](/home/emilio/Documentos/RAdAR/Experimentos/runs/E2_v2_clean_20260323_054101)
- [E2_v3_clean_20260323_061213](/home/emilio/Documentos/RAdAR/Experimentos/runs/E2_v3_clean_20260323_061213)

La lectura se hizo con:

- mismos horizontes `H1-H4`
- validacion `walk-forward expanding`
- `target_mode=nivel`
- `feature_mode=corr`
- trazabilidad completa en `RUN_SUMMARY`, `RESULTADOS_GRID`, `RUN_ARTEFACTOS` y artefactos por run

## Verificacion de integridad

- `E2_v1_clean`: `RUN_SUMMARY=1`, `RESULTADOS_GRID=4`, `RUN_ARTEFACTOS=15`
- `E2_v2_clean`: `RUN_SUMMARY=1`, `RESULTADOS_GRID=4`, `RUN_ARTEFACTOS=16`
- `E2_v3_clean`: `RUN_SUMMARY=1`, `RESULTADOS_GRID=4`, `RUN_ARTEFACTOS=16`

Todos los runs tienen:

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `predicciones_h1.csv` a `predicciones_h4.csv`

## Tabla tactica consolidada

| run_id | modelo | feature_mode | lags | mae_promedio | rmse_promedio | direction_accuracy_promedio | deteccion_caidas_promedio | L_total_Radar | lectura |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| E1_v5_clean | ridge_tscv | corr | 1,2,3,4,5,6 | 0.102512 | 0.136512 | 0.743753 | 0.782323 | 0.243442 | benchmark numerico puro vigente |
| E2_v1_clean | huber_tscv | corr | 1,2,3,4,5,6 | 0.146700 | 0.191300 | 0.629800 | 0.726800 | 0.301907 | baseline Huber claramente inferior |
| E2_v2_clean | huber_tscv | corr | 1,2,3,4,5,6 | 0.146700 | 0.191200 | 0.629800 | 0.726800 | 0.301920 | control de convergencia sin mejora material |
| E2_v3_clean | huber_tscv | corr | 1,2,3,4 | 0.129700 | 0.157100 | 0.707600 | 0.769900 | 0.286465 | mejor run interno, aun por debajo de Ridge |

## Juicio tactico

- `E2_v2_clean` ya descarto que el problema principal fuera convergencia.
- `E2_v3_clean` ya mostro que la memoria corta ayuda a `Huber`, pero no lo vuelve competitivo.
- La familia no ofrece una mejora defendible frente a `E1_v5_clean`.
- Por tanto, re-correr `E2` en esta fase solo duplicaria evidencia ya suficiente.

## Decision formal

- `E2` no merece expansion posterior en esta etapa.
- `E2` queda ratificada como `rama cerrada` y no como familia en observacion.
- El resultado tactico util ya fue obtenido: `Huber` no cambia de forma creible el balance global del Radar.
