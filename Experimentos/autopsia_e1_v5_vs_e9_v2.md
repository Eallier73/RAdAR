# Autopsia E1_v5_clean vs E9_v2_clean

## Alcance

La comparacion se hizo sobre el subset comun evaluable por horizonte, es decir, las filas donde `E1_v5_clean` y `E9_v2_clean` tienen prediccion alineable por fecha, `y_current` y `y_true`.

- `E1_v5_clean` run_dir: /home/emilio/Documentos/RAdAR/Experimentos/runs/E1_v5_clean_20260321_105449
- `E9_v2_clean` run_dir: /home/emilio/Documentos/RAdAR/Experimentos/runs/E9_v2_clean_20260401_070431
- `autopsia_e1_v5_vs_e9_v2.xlsx`: /home/emilio/Documentos/RAdAR/Experimentos/autopsia_e1_v5_vs_e9_v2.xlsx

## Hallazgos principales

- En el subset comun, `E1_v5_clean` queda con `L_total_Radar=0.225558` y `E9_v2_clean` con `L_total_Radar=0.227510`.
- Por tanto, la superioridad de `E9_v2_clean` no debe leerse como dominancia global en el mismo subset, sino como ventaja operativa concentrada.
- La mejora mas clara de `E9_v2_clean` aparece en `H1`: `loss_h` pasa de `0.069718` a `0.051557`, con `direction_accuracy` y `deteccion_caidas` mas altas.
- En `H2`, `E9_v2_clean` baja `MAE`, pero pierde por `loss_h` frente a `E1_v5_clean` por deterioro direccional.
- En `H3` y `H4`, `E1_v5_clean` mantiene mejor balance global en el subset comun.
- En `H1`, `E9_v2_clean` elimina falsos negativos de caida: `recall_caida` pasa de `0.857143` a `1.000000`.

## Juicio tecnico sobre representacion vs arquitectura

- En el subset comun, la mejor base por fila no es `E1_v5_clean` en el `66.0%` de los casos.
- Entre las victorias claras de `E9_v2_clean`, una base no `E1` ya era la mejor en el `87.5%` de los casos.
- La pauta observada es consistente con que la ventaja operativa de `E9_v2_clean` proviene en buena medida de la representacion contenida en la tabla curada, es decir, de la diversidad funcional de bases no lineales y temporales disponibles para el meta-modelo.
- La arquitectura de stacking si importa, pero la hipotesis mas parsimoniosa no es que el meta-modelo Huber invente señal nueva por si solo, sino que explota mejor una representacion ya enriquecida por bases heterogeneas.

## Lectura operativa

- `E9_v2_clean` gana sobre todo por mejor lectura de caidas y de cambios de signo en el arranque de horizonte.
- La mejora no aparece como simple compensacion promedio del error en todos los horizontes.
- La mejora se parece mas a una reduccion de falsos negativos de caida y a una sensibilidad mayor en episodios criticos que a una superioridad numerica homogenea.