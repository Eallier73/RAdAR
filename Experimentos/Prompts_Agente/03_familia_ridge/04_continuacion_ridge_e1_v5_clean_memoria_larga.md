# Continuacion Ridge E1_v5_clean Memoria Larga

## Objetivo
Evaluar si una memoria mas larga mejora el desempeno de Ridge, especialmente en H3 y H4, sin mezclar cambios metodologicos.

## Experimento
`E1_v5_clean`

Configuracion:
- script: `/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e1_ridge_clean.py`
- reference_run_id: `E1_v4_clean`
- target_mode: `nivel`
- feature_mode: `corr`
- transform_mode: `standard`
- horizons: `1,2,3,4`
- inner_splits: `3`
- alpha_selection_metric: `mae`
- lags: `1,2,3,4,5,6`

Comando:

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e1_ridge_clean.py --run-id E1_v5_clean --reference-run-id E1_v4_clean --target-mode nivel --feature-mode corr --lags 1,2,3,4,5,6 --transform-mode standard --horizons 1,2,3,4 --inner-splits 3 --alpha-selection-metric mae
```

## Instrucciones de analisis
1. Actualizar `grid_experimentos_radar.xlsx`.
2. Comparar `E1_v5_clean` contra `E1_v4_clean` y `E1_v2_clean`.
3. Reportar:
   - `feature_count_prom`
   - `mae_promedio`
   - `rmse_promedio`
   - `direction_accuracy_promedio`
   - `deteccion_caidas_promedio`
   - `L_total_Radar`
4. Desglosar por horizonte `H1-H4`.
5. Concluir explicitamente:
   - si la memoria mas larga mejora `H3/H4`,
   - si sacrifica `H1/H2`,
   - y si `E1_v5_clean` reemplaza o no a `E1_v4_clean` como mejor Ridge limpio.
6. Guardar artifacts habituales y mantener trazabilidad de `features_seleccionadas_h1.csv` a `features_seleccionadas_h4.csv`.

## Criterio de decision
- Si `E1_v5_clean` baja `L_total_Radar` y mejora claramente `H3` o `H4` sin deterioro serio en `H1/H2`, continuar con `E1_v6_clean`.
- Si `E1_v5_clean` no mejora materialmente frente a `E1_v4_clean`, cerrar exploracion principal de Ridge y pasar a otra familia o modelo.
