# Fase de Produccion Controlada Dual Radar

Fecha de actualizacion: `2026-04-03`

## Proposito

Este documento cierra temporalmente la expansion experimental del proyecto Radar y abre formalmente una fase operativa dual.

No define un modelo final unico.
No promociona combinaciones ex post.
No reabre familias cerradas.

Su funcion es fijar que corre, como se interpreta, que artefactos son oficiales y bajo que reglas debe prepararse la futura automatizacion.

## Decision ejecutiva

El sistema operativo vigente del Radar queda congelado asi:

- salida numerica principal: `E1_v5_clean`
- deteccion de caidas: `E9_v2_clean`
- politica direccional fija por horizonte: `9-1-9-1`
  - `H1 = E9_v2_clean`
  - `H2 = E1_v5_clean`
  - `H3 = E9_v2_clean`
  - `H4 = E1_v5_clean`

Esto constituye un sistema operativo compuesto / dual con asignacion funcional por salida.

No constituye una mezcla dinamica online.
No constituye un selector por fila.
No constituye un modelo unificado ganador.

## Por que se congela ahora

La evidencia acumulada ya dejo una frontera clara:

- `E1_v5_clean` sigue siendo la referencia numerica mas solida.
- `E9_v2_clean` sigue siendo la referencia mas util para caidas y parte de la lectura direccional.
- `E12` ya fue ejecutada y no justifico promocion ni expansion inmediata.
- el rendimiento marginal esperado de seguir experimentando de inmediato ya no compensa la necesidad de consolidacion operativa.

## Tabla funcional canonica

| Horizonte | Medida | E1_v5_clean | E9_v2_clean | Ganador |
|---|---|---:|---:|---|
| H1 | MAE | 0.121907 | 0.123894 | E1_v5_clean |
| H1 | RMSE | 0.160550 | 0.166878 | E1_v5_clean |
| H1 | Direction accuracy | 0.846154 | 0.857143 | E9_v2_clean |
| H1 | Deteccion de caidas | 0.833333 | 1.000000 | E9_v2_clean |
| H1 | Loss_h | 0.064860 | 0.051557 | E9_v2_clean |
| H2 | MAE | 0.118495 | 0.136777 | E1_v5_clean |
| H2 | RMSE | 0.153470 | 0.178276 | E1_v5_clean |
| H2 | Direction accuracy | 0.760000 | 0.720000 | E1_v5_clean |
| H2 | Deteccion de caidas | 0.700000 | 0.833333 | E9_v2_clean |
| H2 | Loss_h | 0.071501 | 0.063405 | E9_v2_clean |
| H3 | MAE | 0.092137 | 0.129780 | E1_v5_clean |
| H3 | RMSE | 0.123798 | 0.172374 | E1_v5_clean |
| H3 | Direction accuracy | 0.666667 | 0.708333 | E9_v2_clean |
| H3 | Deteccion de caidas | 0.818182 | 1.000000 | E9_v2_clean |
| H3 | Loss_h | 0.068181 | 0.073641 | E1_v5_clean |
| H4 | MAE | 0.077511 | 0.115178 | E1_v5_clean |
| H4 | RMSE | 0.108231 | 0.157989 | E1_v5_clean |
| H4 | Direction accuracy | 0.702703 | 0.658824 | E1_v5_clean |
| H4 | Deteccion de caidas | 0.777778 | 0.833333 | E9_v2_clean |
| H4 | Loss_h | 0.038900 | 0.038906 | E1_v5_clean |

## Politica funcional canonica

| Capa | Politica operativa |
|---|---|
| Salida numerica principal | Siempre `E1_v5_clean` |
| Deteccion de caidas | Siempre `E9_v2_clean` |
| Direction accuracy H1 | `E9_v2_clean` |
| Direction accuracy H2 | `E1_v5_clean` |
| Direction accuracy H3 | `E9_v2_clean` |
| Direction accuracy H4 | `E1_v5_clean` |

## Alcances y limites

### Salida principal

- corresponde al forecast numerico oficial del sistema;
- se deriva exclusivamente de `E1_v5_clean`;
- es la referencia primaria para lectura de nivel / valor / porcentaje.

### Salida complementaria

- corresponde a la alerta de caida y a la lectura direccional funcional;
- usa `E9_v2_clean` para alertas de caida en todos los horizontes;
- usa politica fija `9-1-9-1` para direction accuracy por horizonte.

### Lo que no debe inferirse

- no existe una mezcla adaptativa online entre `E1` y `E9`;
- no existe seleccion por observacion;
- no existe un sistema unificado que haya desplazado a ambos benchmarks;
- no debe usarse la recombinacion ex post `9111` como politica de produccion.

## Reproducibilidad y empaquetado

La capa operativa dual se apoya en:

- [registro_operacion_controlada_radar.json](/home/emilio/Documentos/RAdAR/Experimentos/registro_operacion_controlada_radar.json)
- [run_benchmarks_operativos_vigentes.py](/home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_benchmarks_operativos_vigentes.py)
- [run_sistema_dual_operativo_radar.py](/home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_sistema_dual_operativo_radar.py)
- [verificacion_reproducibilidad_dual_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/verificacion_reproducibilidad_dual_controlada.md)
- [politica_operativa_sistema_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/politica_operativa_sistema_dual_radar.md)
- [preparacion_automatizacion_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/preparacion_automatizacion_radar.md)

## Que queda fuera de esta etapa

- nuevas familias experimentales
- reoptimizacion de `E12`
- reapertura de `E10`
- promocion de una mezcla ex post como modelo final
- automatizacion operativa plena

## Condicion futura de reapertura experimental

Solo podria reabrirse investigacion si aparece una hipotesis nueva, acotada y defendible que:

- no rompa comparabilidad historica;
- no dependa de leakage o logica ex post;
- compita explicitamente contra el sistema dual vigente;
- y justifique su costo metodologico frente a un sistema ya congelado.
