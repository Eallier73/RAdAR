# Resumen Metodologico E8 Hibrido Residual

Fecha de actualizacion: `2026-04-02`

## Estado de la familia

La familia `E8` queda `intermedia`.

Constructo canonico de familia:

- `hibrido residual auditable`

## Corridas auditadas

- `E8_v1_clean`
- `E8_v2_clean`
- `E8_v3_clean`

## Constructos de run

- `E8_v1_clean`: hibrido residual inicial
- `E8_v2_clean`: campeon hibrido residual
- `E8_v3_clean`: variante Prophet residual colapsada

## Lectura consolidada

Resultados:

- `E8_v1_clean = 0.336482`
- `E8_v2_clean = 0.285721`
- `E8_v3_clean = 0.627755`

Lectura:

- La familia fue metodologicamente valida: residuales OOF limpios y trazables.
- `E8_v2_clean` fue la unica variante con senal util.
- Ninguna variante supero de forma defendible a sus mejores referencias base.
- `E8_v3_clean` mostro que `Prophet` como residual learner no fue una direccion util.

## Posicion vigente en el proyecto

- `E8` no es una linea principal competitiva.
- `E8_v2_clean` conserva valor como referencia hibrida residual y como antecedente metodologico de sistemas compuestos.

## Decision

- no abrir una expansion amplia de `E8`
- mantener `E8_v2_clean` solo como referencia secundaria o reserva metodologica
