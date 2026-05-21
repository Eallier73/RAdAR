# Consolidacion Operativa Post-Produccion Controlada

Fecha de actualizacion: `2026-04-03`

## Proposito

Este documento cierra la transicion desde la fase de produccion controlada hacia una operacion comparativa realmente gobernable.

Nota de alcance posterior:

- Este documento formalizo la consolidacion operativa justo antes de la primera apertura dual real de `E11`.
- Tambien queda historicamente antes del cierre temporal de expansion experimental y de la congelacion formal del sistema dual vigente.
- El estado canonico posterior de `E11` debe leerse hoy junto con:
  - [resumen_metodologico_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e11_dual.md)
  - [plan_de_experimentacion_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/plan_de_experimentacion_radar.md)
  - [bitacora_experimental_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/bitacora_experimental_radar.md)
- La formalizacion vigente del sistema compuesto debe leerse hoy junto con:
  - [fase_produccion_controlada_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_dual_radar.md)
  - [politica_operativa_sistema_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/politica_operativa_sistema_dual_radar.md)

No abre familias nuevas.
No declara un modelo final unico.
No reabre `E10`.
No promociona `E11`.

Su funcion es:

- congelar los benchmarks operativos vigentes con trazabilidad verificable;
- convertir la operacion de benchmarks en una rutina reproducible y auditable;
- volver aplicable la politica de promocion, permanencia y sustitucion;
- cerrar formalmente a `E10` como rama no promocionable bajo su formulacion actual;
- y dejar a `E11` como arquitectura dual rigurosamente especificada, cuya primera apertura posterior ya fue ejecutada sin promocion.

## Benchmarks operativos congelados

### Benchmark numerico puro vigente

- `benchmark_id`: `benchmark_numerico_puro_vigente`
- `run_id`: `E1_v5_clean`
- `runner canonico`: [run_e1_ridge_clean.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e1_ridge_clean.py)
- `run_dir`: [E1_v5_clean_20260321_105449](/home/emilio/Documentos/RAdAR/Experimentos/runs/E1_v5_clean_20260321_105449)
- `rol`: referente numerico puro del Radar

### Benchmark operativo de riesgo-direccion-caidas vigente

- `benchmark_id`: `benchmark_operativo_riesgo_vigente`
- `run_id`: `E9_v2_clean`
- `runner canonico`: [run_e9_stacking.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e9_stacking.py)
- `run_dir`: [E9_v2_clean_20260401_070431](/home/emilio/Documentos/RAdAR/Experimentos/runs/E9_v2_clean_20260401_070431)
- `rol`: referente operativo de direccion, riesgo y deteccion de caidas

## Rutina operativa reproducible

Fuente canonica de congelamiento:

- [registro_operacion_controlada_radar.json](/home/emilio/Documentos/RAdAR/Experimentos/registro_operacion_controlada_radar.json)

Dispatcher operativo:

- [run_benchmarks_operativos_vigentes.py](/home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_benchmarks_operativos_vigentes.py)

Comandos de referencia:

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_benchmarks_operativos_vigentes.py
```

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_benchmarks_operativos_vigentes.py --validate --strict
```

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_benchmarks_operativos_vigentes.py --benchmark-id benchmark_numerico_puro_vigente
```

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_benchmarks_operativos_vigentes.py --benchmark-id benchmark_operativo_riesgo_vigente
```

La rutina queda definida asi:

1. validar integridad operativa de los benchmarks congelados;
2. inspeccionar el comando congelado del benchmark deseado;
3. ejecutar solo si la auditoria no reporta gaps;
4. registrar cualquier nueva corrida operativa como corrida canonica comparable, no como atajo operativo.

## Auditoria operativa vigente

Reporte canonico:

- [auditoria_benchmarks_operativos_controlados.json](/home/emilio/Documentos/RAdAR/Experimentos/auditoria_benchmarks_operativos_controlados.json)
- [auditoria_benchmarks_operativos_controlados.md](/home/emilio/Documentos/RAdAR/Experimentos/auditoria_benchmarks_operativos_controlados.md)

Resultado actual:

- estado global: `ok`
- benchmarks auditados: `2`
- gaps detectados: `0`

Cobertura auditada actual:

- `E1_v5_clean`: `H1=26`, `H2=25`, `H3=24`, `H4=23`
- `E9_v2_clean`: `H1=14`, `H2=13`, `H3=12`, `H4=11`

Integridad verificada para ambos benchmarks:

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `predicciones_h1..h4.csv`
- snapshot de script
- registro en `RUN_SUMMARY`
- registro en `RESULTADOS_GRID`
- registro en `RUN_ARTEFACTOS`
- consistencia con `inventario_experimentos_radar.json`
- consistencia con `benchmarks_operativos_vigentes` y `capas_radar_vigentes`

## Politica operable de promocion y sustitucion

Documento rector:

- [politica_promocion_sistemas_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/politica_promocion_sistemas_radar.md)

Version estructurada:

- [politica_promocion_sistemas_radar.json](/home/emilio/Documentos/RAdAR/Experimentos/politica_promocion_sistemas_radar.json)

La politica deja cinco estados de decision:

- `promocion`
- `observacion`
- `no_promocion`
- `cierre_rama`
- `despromocion`
- `sustitucion_benchmark`

Y exige, como minimo:

- mejora defendible en `L_total_Radar` o en el plano funcional que pretende reemplazar;
- lectura por horizonte con enfasis en `H2` y `H3`;
- estabilidad de `H1` y `H4`;
- lectura de `direction_accuracy` y `deteccion_caidas`;
- trazabilidad completa;
- ausencia de leakage;
- reproducibilidad de la corrida;
- comparabilidad fuerte contra benchmark vigente;
- y costo metodologico proporcionado frente a la mejora obtenida.

## Cierre formal de E10

Documento rector:

- [cierre_formal_e10_no_promocionable.md](/home/emilio/Documentos/RAdAR/Experimentos/cierre_formal_e10_no_promocionable.md)

Lectura vigente:

- `E10` ya fue abierto y corrido.
- `E10_v1_clean` es evidencia limpia de meta-seleccion contextual.
- `E10` no es promocionable y queda cerrada para promocion bajo su formulacion actual.

Motivo:

- no supera de forma defendible a `E1_v5_clean`;
- no supera de forma defendible a `E9_v2_clean`;
- no supera globalmente al selector fijo;
- el selector mostro accuracies bajas por horizonte;
- y la senal observada no justifica continuidad por inercia.

## Estado posterior de E11

Documento rector:

- [especificacion_futura_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/especificacion_futura_e11_dual.md)
- [resumen_metodologico_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e11_dual.md)

Lectura vigente:

- `E11` ya fue abierta con tres variantes duales controladas.
- la mejor apertura interna fue `E11_v2_clean`.
- ninguna variante desplazo a `E1_v5_clean` ni a `E9_v2_clean`.
- `E11` no queda promocionable todavia y no debe confundirse con una extension de `E10`.
- solo podria reabrirse como candidata seria si una nueva hipotesis dual supera de forma defendible la dualidad vigente.
- la autopsia posterior a `E11` mostro ademas que la version ternaria simple quedo afectada por un threshold excesivo (`+-0.5`), por lo que cualquier reapertura futura deberia partir de umbrales recalibrados y no de retuning narrativo.

## Lectura posterior a la autopsia E1 vs E9

Documentos rectores:

- [autopsia_e1_v5_vs_e9_v2.md](/home/emilio/Documentos/RAdAR/Experimentos/autopsia_e1_v5_vs_e9_v2.md)
- [analisis_recombinacion_ex_post_horizontes_e1_e9.md](/home/emilio/Documentos/RAdAR/Experimentos/analisis_recombinacion_ex_post_horizontes_e1_e9.md)
- [decision_formal_siguiente_paso_post_e11.md](/home/emilio/Documentos/RAdAR/Experimentos/decision_formal_siguiente_paso_post_e11.md)

Lectura vigente despues de esa autopsia:

- la ventaja operativa de `E9_v2_clean` se concentra sobre todo en `H1` y en deteccion de caidas;
- la evidencia observada es mas consistente con una ventaja de representacion que con una ventaja puramente arquitectonica;
- la mejor recombinacion ex post usa `E9` en `H1` y `E1` en `H2-H4`, pero no es promocionable;
- esa lectura ya fue ejecutada en la apertura controlada de `E12`, sin alterar los benchmarks operativos vigentes;
- el siguiente paso serio del proyecto ya no debe ser “otro algoritmo”, sino solo una futura hipotesis de representacion mas precisa si `E12` llegara a reabrirse.

## Cierre

La produccion controlada del Radar queda operativamente consolidada cuando la ejecucion de benchmarks deja de depender de memoria informal y pasa a depender de:

- benchmarks congelados,
- dispatcher reproducible,
- auditoria automatizada,
- politica aplicable,
- cierre formal de ramas no promocionables,
- y especificacion futura sin promocion prematura.
