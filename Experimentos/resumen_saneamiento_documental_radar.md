# Resumen de saneamiento documental Radar

Fecha de cierre: `2026-04-02`

Nota de alcance posterior:

- Este saneamiento fijo el estado vigente hasta el momento en que `E10` ya habia sido corrido, pero antes del cierre formal de promocion de esa rama.
- El estado canonico posterior de `E10` debe leerse hoy junto con [cierre_formal_e10_no_promocionable.md](/home/emilio/Documentos/RAdAR/Experimentos/cierre_formal_e10_no_promocionable.md) y [consolidacion_operativa_post_produccion_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/consolidacion_operativa_post_produccion_controlada.md).
- El estado canonico posterior de `E11` debe leerse hoy junto con [resumen_metodologico_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e11_dual.md), porque la primera apertura dual controlada ocurrio despues de este saneamiento.

## 1. Resumen ejecutivo del saneamiento realizado

Se ejecutó un saneamiento canónico integral para alinear la lectura metodológica del proyecto Radar con el estado real de los artefactos y runs existentes.

El saneamiento corrigió tres divergencias principales:

- `E10` ya no podía seguir descrito como premodelado porque ya existe una corrida canónica real: [E10_v1_clean_20260401_090439](/home/emilio/Documentos/RAdAR/Experimentos/runs/E10_v1_clean_20260401_090439).
- La clasificación ya no podía seguir descrita como solo planificada porque `C1` sí tuvo tres corridas canónicas: [C1_v1_clean_20260330_085747](/home/emilio/Documentos/RAdAR/Experimentos/runs/C1_v1_clean_20260330_085747), [C1_v2_clean_20260330_085846](/home/emilio/Documentos/RAdAR/Experimentos/runs/C1_v2_clean_20260330_085846), [C1_v3_clean_20260330_085854](/home/emilio/Documentos/RAdAR/Experimentos/runs/C1_v3_clean_20260330_085854).
- La capa explicativa transversal ya no podía quedar como una nota difusa; quedó clasificada explícitamente como `parcial intra-familia`.

El resultado es una sola lectura canónica y consistente entre plan, bitácora, inventario, tabla maestra, README técnico y resumen de auditoría.

## 2. Discrepancias detectadas

1. `E10` aparecía en documentos vivos como `activa premodelado` o como familia todavía sin corrida, mientras que el inventario real ya contenía `E10_v1_clean`.
2. La rama de clasificación aparecía como `sin corridas ejecutadas`, pero el inventario y la tabla maestra ya registraban `C1_v1_clean`, `C1_v2_clean` y `C1_v3_clean`.
3. La capa explicativa transversal se mencionaba como pendiente, pero no estaba fijada con una taxonomía canónica única ni con evidencia cuantificada.
4. Documentos históricos de transición (`post E9`, `construcción tabla E10`) podían leerse como estado vigente si no se les añadía una nota explícita de alcance histórico.
5. La tabla/JSON de `estado_familias_vigente` omitía a `C1-C4` y mantenía a `E10` en un estado anterior al estado real.

## 3. Correcciones aplicadas por archivo

- [plan_de_experimentacion_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/plan_de_experimentacion_radar.md)
  - Se actualizó la fecha.
  - Se corrigió el estado de `E10` al estado vigente en ese momento: `modelado inicial fragil`.
  - Se corrigió la rama de clasificación: `C1` evaluada y pausada tempranamente; `C2-C4` con infraestructura preparada.
  - Se dejó explícita la clasificación de la capa explicativa transversal como `parcial intra-familia`.
  - Mejora trazabilidad porque el plan ya no contradice runs reales ni el inventario.

- [bitacora_experimental_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/bitacora_experimental_radar.md)
  - Se actualizó la fecha y la rama actual a `main`.
  - Se agregó una entrada canónica para `E10_v1_clean`.
  - Se añadieron notas de actualización al bloque histórico de clasificación y al bloque de construcción de tabla E10.
  - Mejora trazabilidad porque preserva historia y aclara qué entradas quedaron superadas.

- [README.md](/home/emilio/Documentos/RAdAR/Scripts/Modeling/README.md)
  - Se corrigió el estado de `E10`.
  - Se corrigió el estado de clasificación (`C1` sí ejecutada; `C2-C4` sin corrida).
  - Se añadió una lectura precisa de la capa explicativa transversal.
  - Mejora trazabilidad porque el README técnico ya no propaga estados obsoletos.

- [actualizacion_metodologica_post_e9_e10_e11.md](/home/emilio/Documentos/RAdAR/Experimentos/actualizacion_metodologica_post_e9_e10_e11.md)
  - Se añadió una nota de alcance histórico.
  - Mejora trazabilidad porque distingue decisión post-`E9` de estado vigente posterior a `E10`.

- [resumen_construccion_tabla_e10.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_construccion_tabla_e10.md)
  - Se añadió una nota de alcance histórico.
  - Mejora trazabilidad porque evita leer un documento de infraestructura como si fuera el estado actual de la familia.

- [build_experiments_master_table.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/build_experiments_master_table.py)
  - Se corrigió la fuente de verdad de `estado_familias_vigente`.
  - Se añadieron `C1-C4` al estado de familias.
  - Se incorporó una síntesis explícita de `estado_capa_explicativa_transversal`.
  - Se ajustó el resumen de auditoría y el documento de stacking para reflejar el alcance real de `E10` y clasificación.
  - Mejora trazabilidad porque la narrativa derivada sale ya corregida desde el generador maestro.

- [README.md](/home/emilio/Documentos/RAdAR/Experimentos/Prompts_Agente/README.md)
  - Se registró el prompt de saneamiento canónico.
  - Mejora trazabilidad porque la intervención queda documentada en el índice de prompts.

## 4. Estado canónico actualizado del proyecto

- `E1`: cerrada. `E1_v5_clean` es el referente numérico puro principal.
- `E2`: cerrada. `E2_v3_clean` queda como referencia robusta histórica.
- `E3`: cerrada en rama base. `E3_v2_clean` conserva valor como referencia de bagging.
- `E4`: cerrada. `E4_v1_clean` queda como boosting histórico secundario.
- `E5`: abierta madura. `E5_v4_clean` sigue como mejor no lineal tabular.
- `E6`: debilitada. Sin continuidad inmediata.
- `E7`: intermedia. Referencia temporal secundaria.
- `E8`: intermedia. Híbrido residual auditable, sin mejora suficiente frente a su base.
- `E9`: pausada útil. `E9_v2_clean` es el referente operativo de riesgo-dirección-caídas.
- `E10`: cerrada para promoción. Ya fue abierta, corrida y evaluada; la lectura `modelado inicial fragil` quedó superada por el cierre posterior de promoción.
- `E11`: evaluada sin promocion. Arquitectura dual numerica + categorica ya abierta en una primera tanda controlada, sin desplazamiento de `E1_v5_clean` ni de `E9_v2_clean`.
- `C1`: evaluada y pausada tempranamente.
- `C2`, `C3`, `C4`: infraestructura preparada, sin corrida real.

Lectura funcional vigente:

- `E1_v5_clean` = referente numérico puro.
- `E9_v2_clean` = referente operativo de riesgo-dirección-caídas.
- `E10` = familia contextual ya abierta, pero aún frágil.
- `E11` = familia dual ya abierta, con evidencia util pero no promocionable en su primera apertura.

## 5. Situación específica de E10

- Apertura formal: sí.
- Corrida canónica real: sí, [E10_v1_clean_20260401_090439](/home/emilio/Documentos/RAdAR/Experimentos/runs/E10_v1_clean_20260401_090439).
- Alcance real: meta-selector duro lineal, trazable y sin leakage.
- Resultado real: metodológicamente limpio, pero sin superar al selector fijo ni a `E1_v5_clean` ni a `E9_v2_clean` en el global.
- Estado canónico: `cerrada para promocion`.
- Lectura correcta: familia operativa en sentido técnico e históricamente útil, pero no competitiva ni promocionable bajo la formulación probada.

## 6. Situación específica de clasificación

- La clasificación no está “sin iniciar”.
- Existe una rama real `C1-C4` con prompts y runners preparados.
- `C1` sí se ejecutó con tres corridas canónicas:
  - [C1_v1_clean_20260330_085747](/home/emilio/Documentos/RAdAR/Experimentos/runs/C1_v1_clean_20260330_085747)
  - [C1_v2_clean_20260330_085846](/home/emilio/Documentos/RAdAR/Experimentos/runs/C1_v2_clean_20260330_085846)
  - [C1_v3_clean_20260330_085854](/home/emilio/Documentos/RAdAR/Experimentos/runs/C1_v3_clean_20260330_085854)
- Las tres corridas colapsaron a clase única y no dejaron señal discriminativa útil.
- Estado canónico de `C1`: `evaluada y pausada tempranamente`.
- Estado canónico de `C2-C4`: `infraestructura preparada`, sin corrida real.

## 7. Estado de la capa explicativa transversal

Clasificación principal fijada:

- `parcial intra-familia`

Evidencia que sustenta esa clasificación:

- `13` de `36` runs maestros tienen `features_seleccionadas_h*.csv`.
- `0` runs maestros tienen coeficientes exportados de forma sistemática.
- `0` runs maestros tienen importancias exportadas de forma sistemática.
- `0` runs maestros tienen SHAP o equivalente exportado de forma sistemática.
- `0` runs pueden tratarse como parte de una capa explicativa transversal canónica.

Lectura canónica:

- Sí existen insumos interpretativos parciales en algunos runs y en algunos horizontes.
- Eso no equivale a interpretabilidad comparable entre familias.
- La selección de modelos sigue descansando principalmente en performance, dirección y detección de caídas, no en una explicación transversal resuelta del porqué.

## 8. Archivos generados o regenerados

Archivos regenerados por el builder maestro:

- [tabla_maestra_experimentos_radar.csv](/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar.csv)
- [tabla_maestra_experimentos_radar.xlsx](/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar.xlsx)
- [tabla_maestra_experimentos_radar_e9_curada.xlsx](/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar_e9_curada.xlsx)
- [inventario_experimentos_radar.json](/home/emilio/Documentos/RAdAR/Experimentos/inventario_experimentos_radar.json)
- [resumen_auditoria_experimentos.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_auditoria_experimentos.md)
- [documentacion_stacking_readiness_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/documentacion_stacking_readiness_radar.md)
- [preparacion_tabla_e9_stacking_controlado.md](/home/emilio/Documentos/RAdAR/Experimentos/preparacion_tabla_e9_stacking_controlado.md)
- [diccionario_constructos_canonicos_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/diccionario_constructos_canonicos_radar.md)
- [registro_constructos_runs_radar.csv](/home/emilio/Documentos/RAdAR/Experimentos/registro_constructos_runs_radar.csv)

Documentos canonicos ampliados durante el saneamiento extendido:

- [resumen_metodologico_e5_catboost.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e5_catboost.md)
- [resumen_metodologico_e6_arimax.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e6_arimax.md)
- [resumen_metodologico_e7_prophet.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e7_prophet.md)
- [resumen_metodologico_e8_hibrido_residual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e8_hibrido_residual.md)
- [resumen_metodologico_e9_stacking.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e9_stacking.md)
- [resumen_metodologico_e10_gating_contextual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e10_gating_contextual.md)
- [resumen_metodologico_clasificacion_c1_c4.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_clasificacion_c1_c4.md)

Comandos ejecutados para regeneración y validación:

```bash
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python -m py_compile /home/emilio/Documentos/RAdAR/Scripts/Modeling/build_experiments_master_table.py
/home/emilio/anaconda3/envs/radar-exp-py311/bin/python /home/emilio/Documentos/RAdAR/Scripts/Modeling/build_experiments_master_table.py
```

## 9. Riesgos residuales o pendientes menores

- `E10_v1_clean` sigue no siendo un modelo base mergeable para stacking; eso es correcto, pero conviene no confundirlo con un run reutilizable dentro de `E9`.
- `C1` sí existe como evidencia real, pero no deja todavía una rama de clasificación consolidada ni competitiva.
- La clasificación de la capa explicativa transversal ya quedó fijada, pero eso no resuelve todavía la carencia de artefactos homogéneos por familia y horizonte.
- Existen documentos históricos que conservan estados previos por diseño; ahora todos llevan o heredan una lectura canónica posterior, pero deben seguir leyéndose con su alcance temporal correcto.
