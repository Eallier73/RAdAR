# Resumen Resultados E12 Apertura Controlada

Fecha de actualizacion: `2026-04-03`

## Corridas canonicas

- [E12_v1_clean_20260403_075150](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v1_clean_20260403_075150)
- [E12_v2_clean_20260403_075843](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v2_clean_20260403_075843)
- [E12_v3_clean_20260403_080040](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v3_clean_20260403_080040)

## Tabla comparativa

| run_id | representation_mode | rep_features | source_runs | L_total_Radar | delta vs E1 mismo subset | delta vs E9 mismo subset | lectura breve |
|---|---:|---:|---|---:|---:|---:|---|
| `E1_v5_clean` | n/a | n/a | n/a | `0.243442` | `0.000000` | `-0.001952` | benchmark numerico puro vigente |
| `E9_v2_clean` | n/a | n/a | tabla curada | `0.227510` | `+0.001952` | `0.000000` | benchmark operativo vigente |
| `E12_v1_clean` | `minimal` | `15` | `E1_v5_clean,E5_v4_clean` | `0.253732` | `+0.028174` | `+0.026223` | baseline de representacion minima claramente no ganador |
| `E12_v2_clean` | `expanded` | `25` | `E1_v5_clean,E5_v4_clean,E3_v2_clean,E7_v3_clean` | `0.252948` | `+0.027390` | `+0.025438` | ampliar diversidad mete complejidad sin ganancia |
| `E12_v3_clean` | `disagreement_only` | `10` | `E1_v5_clean,E5_v4_clean,E3_v2_clean,E7_v3_clean` | `0.244120` | `+0.018563` | `+0.016611` | mejor variante interna, pero todavia peor que ambos benchmarks |

## Lectura por horizonte

Hipotesis central de la familia:

- capturar parte de la ventaja de `E9` en `H1` sin perder la robustez de `E1` en `H2-H4`

Resultado:

- ninguna variante mejora `H1` frente a `E1_v5_clean`
- ninguna variante se acerca a `E9_v2_clean` en `H1`
- `E12_v3_clean` mejora marginalmente `H2` frente a `E1` en el mismo subset
- `E12_v1_clean` y `E12_v2_clean` empeoran con claridad `H4`
- `E12_v3_clean` es la tension metodologica mas informativa porque minimiza el dano relativo y deja la mejor deteccion de caidas interna (`0.839286`), pero sigue sin justificar expansion

## Juicio metodologico

La hipotesis sustantiva de `E12` no queda confirmada.

Lo que si deja la familia:

- evidencia de que el desacuerdo entre bases parece aportar mas que el bloque de regimen usado aqui
- evidencia de que ampliar indiscriminadamente la representacion no ayuda
- evidencia de que la ventaja de `E9` en `H1` no se absorbe facilmente con un Ridge enriquecido simple bajo esta formulacion

## Decision

`E12` queda como `hallazgo parcial sin promocion`.

Decision operativa:

- no promocionar
- no expandir por inercia
- reabrir solo si aparece una hipotesis de representacion para `H1` mas precisa, mas defendible y no dependiente de curacion ex post
