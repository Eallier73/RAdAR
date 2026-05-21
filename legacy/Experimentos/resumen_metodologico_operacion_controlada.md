# Resumen Metodologico Operacion Controlada Radar

Fecha de actualizacion: `2026-04-03`

## Estado de la capa

La operacion controlada del Radar queda:

- formalizada
- reproducible
- auditable
- dual
- no unificada en un modelo final unico

## Benchmarks vigentes

- benchmark numerico puro: `E1_v5_clean`
- benchmark operativo de riesgo-direccion-caidas: `E9_v2_clean`

La capa operativa no promociona `E10` ni `E11`.

## Documentos rectores

- [fase_produccion_controlada_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_radar.md)
- [consolidacion_operativa_post_produccion_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/consolidacion_operativa_post_produccion_controlada.md)
- [politica_promocion_sistemas_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/politica_promocion_sistemas_radar.md)
- [cierre_formal_e10_no_promocionable.md](/home/emilio/Documentos/RAdAR/Experimentos/cierre_formal_e10_no_promocionable.md)

## Lectura metodologica vigente

La evidencia actual obliga a preservar una salida dual honesta:

- `E1_v5_clean` para el plano numerico
- `E9_v2_clean` para el plano operativo

Esa dualidad no debe maquillarse como defecto ni como solucion ya resuelta.

## Estado de las familias criticas

- `E10`: corrida real, hipotesis no confirmada, cerrada para promocion
- `E11`: familia dual ya abierta, evaluada sin promocion
- clasificacion: `C1` y `C2` ejecutadas y pausadas tempranamente; `C3-C4` preparadas

## Decision

La operacion controlada no es un sustituto de la capa experimental.

Su funcion vigente es:

- congelar benchmarks reales
- sostener trazabilidad operativa
- aplicar politica de promocion sin ambiguedad
- preservar la comparabilidad historica del proyecto
