# Decision Formal Siguiente Paso Post-E11

Fecha de actualizacion: `2026-04-03`

> Nota de actualizacion:
> Esta decision ya fue ejecutada mediante la apertura controlada de `E12` el `2026-04-03`.
> El documento conserva valor historico porque explica por que se abrio una familia de representacion; el estado vigente posterior queda fijado en [resumen_metodologico_e12_representacion.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e12_representacion.md) y [resumen_resultados_e12_apertura_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_resultados_e12_apertura_controlada.md).

## 1. Que se hizo

Se ejecuto una fase corta posterior a `E11` con cinco componentes:

1. autopsia comparativa `E1_v5_clean` vs `E9_v2_clean`;
2. recombinacion ex post por horizonte entre ambos benchmarks;
3. analisis de distribucion del delta real para recalibrar thresholds categoricos;
4. verificacion tactica de `E2` usando sus corridas canonicas ya existentes;
5. cierre documental de la decision sobre el siguiente paso correcto.

Artefactos rectores de esta fase:

- [autopsia_e1_v5_vs_e9_v2.md](/home/emilio/Documentos/RAdAR/Experimentos/autopsia_e1_v5_vs_e9_v2.md)
- [analisis_recombinacion_ex_post_horizontes_e1_e9.md](/home/emilio/Documentos/RAdAR/Experimentos/analisis_recombinacion_ex_post_horizontes_e1_e9.md)
- [analisis_distribucion_delta_iad.md](/home/emilio/Documentos/RAdAR/Experimentos/analisis_distribucion_delta_iad.md)
- [resumen_resultados_e2_verificacion_tactica.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_resultados_e2_verificacion_tactica.md)

## 2. Que evidencia nueva aparecio

- `E9_v2_clean` no domina a `E1_v5_clean` en el subset comun de evaluacion; su ventaja operativa se concentra sobre todo en `H1`.
- En `H1`, `E9_v2_clean` mejora claramente `loss_h`, `direction_accuracy` y `deteccion_caidas`, reduciendo falsos negativos de caida.
- La pauta observada es mas consistente con una ventaja de representacion que con una ventaja puramente arquitectonica: en el `66.0%` del subset comun la mejor base por fila no es `E1_v5_clean`, y entre las victorias claras de `E9_v2_clean` una base no `E1` ya era la mejor en el `87.5%` de los casos.
- La mejor recombinacion ex post por horizonte es `9111`, es decir:
  - `H1 = E9`
  - `H2-H4 = E1`
  - `L_total_Radar = 0.207397`
- Esa recombinacion ex post supera a ambos benchmarks sobre el subset comun, pero no es promocionable ni prospectiva.
- El threshold `+-0.5` usado en `E11_v1_clean` es claramente excesivo para la escala real del problema.
- La evidencia empirica deja `+-0.15` como threshold preferente para una futura reapertura ternaria prudente.
- `E2` no requiere nuevas corridas para responder su pregunta: sus tres runs canónicos ya la dejaron cerrada.

## 3. Que quedo refutado

- Queda refutada la lectura de que `E9_v2_clean` gane operativamente por dominancia global homogenea en todos los horizontes.
- Queda refutada la idea de que `+-0.5` sea un threshold razonable para la formulacion ternaria del movimiento.
- Queda refutada la posibilidad de mantener `E2` viva como familia prometedora a la espera de una simple robustificacion adicional.
- Queda refutada la idea de que la siguiente pregunta deba ser “probar otro algoritmo” sin antes trabajar representacion o definicion de tarea.

## 4. Que quedo plausible

- Queda plausible una futura linea centrada en representacion de features y no en algoritmo.
- Queda plausible una futura pregunta por horizonte, pero no como selector ex post promocionable ni como reactivacion automatica de `E10`.
- Queda plausible una reapertura futura de la clasificacion ternaria con thresholds recalibrados, porque el colapso de `E11_v1_clean` fue en buena medida un problema de umbral.
- Queda plausible que la ventaja operativa de `E9_v2_clean` provenga de una representacion funcional mas rica de regimen, heterogeneidad y bases que del stacking por si solo.

## 5. Que no debe hacerse todavia

- No abrir `E12` por inercia sin definir primero una hipotesis de representacion muy precisa.
- No promocionar la recombinacion por horizonte como si fuera evidencia prospectiva.
- No reabrir `E10` con un parche menor.
- No reabrir la clasificacion ternaria solo porque `+-0.5` fue malo.
- No re-correr `E2`.
- No buscar “otro algoritmo” como siguiente movimiento principal.

## 6. Que siguiente paso recomiendas

La recomendacion disciplinada y unica es esta:

- **Siguiente paso recomendado: Opcion C**, es decir, preparar una futura familia centrada en representacion de features, no en algoritmo.

Justificacion:

- la autopsia sugiere que la ventaja de `E9_v2_clean` es mas consistente con representacion enriquecida que con arquitectura;
- la mejor recombinacion ex post concentra la ganancia en `H1`, lo que sugiere estructura funcional por horizonte;
- la clasificacion ternaria no murio de forma estructural total, pero su problema inmediato fue de threshold y no justifica una reapertura aislada todavia;
- `E2` ya quedo suficientemente cerrada y no merece expansion.

Lectura operativa:

- no recomiendo abrir todavia un selector por horizonte;
- no recomiendo abrir todavia una reapertura categorica aislada;
- si se abre una familia posterior, debe ser una familia de **representacion** con constructos de segundo orden, probablemente sensibles a horizonte y regimen, y no un simple cambio de algoritmo.

## 7. Que archivos cree

- [autopsia_e1_v5_vs_e9_v2.md](/home/emilio/Documentos/RAdAR/Experimentos/autopsia_e1_v5_vs_e9_v2.md)
- [autopsia_e1_v5_vs_e9_v2.xlsx](/home/emilio/Documentos/RAdAR/Experimentos/autopsia_e1_v5_vs_e9_v2.xlsx)
- [resumen_ejecutivo_autopsia_e1_vs_e9.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_ejecutivo_autopsia_e1_vs_e9.md)
- [inventario_fuentes_autopsia_e1_vs_e9.md](/home/emilio/Documentos/RAdAR/Experimentos/inventario_fuentes_autopsia_e1_vs_e9.md)
- [analyze_post_e11_decision_phase.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/analyze_post_e11_decision_phase.py)
- [analisis_recombinacion_ex_post_horizontes_e1_e9.md](/home/emilio/Documentos/RAdAR/Experimentos/analisis_recombinacion_ex_post_horizontes_e1_e9.md)
- [recombinacion_horizontes_e1_e9.csv](/home/emilio/Documentos/RAdAR/Experimentos/recombinacion_horizontes_e1_e9.csv)
- [resumen_viabilidad_selector_por_horizonte.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_viabilidad_selector_por_horizonte.md)
- [analisis_distribucion_delta_iad.md](/home/emilio/Documentos/RAdAR/Experimentos/analisis_distribucion_delta_iad.md)
- [sensibilidad_thresholds_clasificacion.csv](/home/emilio/Documentos/RAdAR/Experimentos/sensibilidad_thresholds_clasificacion.csv)
- [recomendacion_thresholds_e11_o_futura_clasificacion.md](/home/emilio/Documentos/RAdAR/Experimentos/recomendacion_thresholds_e11_o_futura_clasificacion.md)
- [resumen_resultados_e2_verificacion_tactica.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_resultados_e2_verificacion_tactica.md)
- [01_autopsia_e1_vs_e9_recombinacion_thresholds_e2.md](/home/emilio/Documentos/RAdAR/Experimentos/Prompts_Agente/25_autopsia_post_e11/01_autopsia_e1_vs_e9_recombinacion_thresholds_e2.md)
- [01_apertura_e2_verificacion_tactica.md](/home/emilio/Documentos/RAdAR/Experimentos/Prompts_Agente/26_verificacion_tactica_e2/01_apertura_e2_verificacion_tactica.md)

## 8. Que archivos actualice

- [plan_de_experimentacion_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/plan_de_experimentacion_radar.md)
- [bitacora_experimental_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/bitacora_experimental_radar.md)
- [resumen_metodologico_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e11_dual.md)
- [consolidacion_operativa_post_produccion_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/consolidacion_operativa_post_produccion_controlada.md)
- [politica_promocion_sistemas_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/politica_promocion_sistemas_radar.md)
- [politica_promocion_sistemas_radar.json](/home/emilio/Documentos/RAdAR/Experimentos/politica_promocion_sistemas_radar.json)
- [README.md](/home/emilio/Documentos/RAdAR/Scripts/Modeling/README.md)
- [README.md](/home/emilio/Documentos/RAdAR/Experimentos/Prompts_Agente/README.md)

## 9. Que artefactos regenere

Ninguno.

No hubo nuevos runs en esta fase y no hizo falta regenerar `grid`, tabla maestra ni inventarios para sostener la decision metodologica.

## 10. Que partes, si alguna, quedan explicitamente no promocionables

- `E10`, ya cerrada para promocion.
- La recombinacion ex post por horizonte `E1/E9`, aunque sea analiticamente valiosa.
- La sensibilidad de thresholds por si sola, sin nueva corrida temporal limpia.
- `E2`, ratificada como rama cerrada.
- `E11_v1_clean`, `E11_v2_clean` y `E11_v3_clean`, que siguen sin promocion.
