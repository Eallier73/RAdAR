# Resumen Metodologico E1.1 Bayesian

Fecha de actualizacion: `2026-04-03`

## Estado de la micro-rama

`E1.1` no es una familia principal nueva.

Queda registrada como:

- micro-rama tactica de verificacion lineal bayesiana
- evaluada una vez
- no preferible
- cerrada sin expansion

## Corrida auditada

- [E1_1_v1_bayesian_base_20260402_063714](/home/emilio/Documentos/RAdAR/Experimentos/runs/E1_1_v1_bayesian_base_20260402_063714)

Documento de cierre complementario:

- [resumen_micro_rama_e1_1_bayesian.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_micro_rama_e1_1_bayesian.md)

## Hipotesis probada

La micro-rama pregunto si `BayesianRidge` podia extraer una señal lineal util adicional frente a `Ridge` bajo el mismo marco limpio temporal del proyecto.

Comparacion exigida:

- `E1_v5_clean`
- `E1_v4_clean`
- y, como control historico, `E1_v2_clean`

## Resultado consolidado

Resultado principal:

- `E1_1_v1_bayesian_base = 0.264946`

Comparacion:

- `E1_v5_clean = 0.243442`
- `E1_v4_clean = 0.253277`
- `E1_v2_clean = 0.261239`

Lectura:

- no mejora el benchmark Ridge vigente
- no mejora la referencia parsimoniosa
- no deja una ventaja estable por horizontes
- solo muestra una mejora parcial en `H3`, insuficiente para justificar continuidad

## Decision

`E1.1` queda:

- util como verificacion metodologica
- no preferible
- cerrada sin segunda corrida de control

No procede tratar esta micro-rama como nueva familia ni como continuidad estrategica de la via lineal.
