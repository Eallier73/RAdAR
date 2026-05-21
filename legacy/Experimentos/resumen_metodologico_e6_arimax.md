# Resumen Metodologico E6 ARIMAX

Fecha de actualizacion: `2026-04-02`

## Estado de la familia

La familia `E6` queda `debilitada`.

Constructo canonico de familia:

- `referencia temporal debilitada`

## Corridas auditadas

- `E6_v1_clean`
- `E6_v2_clean`

## Constructos de run

- `E6_v1_clean`: campeon interno debilitado
- `E6_v2_clean`: control de amplitud exogena descartado

## Lectura consolidada

Resultados:

- `E6_v1_clean = 0.370318`
- `E6_v2_clean = 0.445769`

Lectura:

- `ARIMAX` no fue competitivo frente a `E1_v5_clean`, `E1_v4_clean`, `E5_v4_clean`, `E3_v2_clean` ni `E4_v1_clean`.
- `feature_mode=corr` fue menos malo que `feature_mode=all`.
- La familia mostro warnings de convergencia y no justifico continuidad inmediata.

## Posicion vigente en el proyecto

- `E6` no queda como linea principal.
- Su valor residual es solo conceptual:
  - referencia temporal estructurada debil
  - posible insumo futuro para hibridos si reapareciera una hipotesis muy acotada

## Decision

- no abrir `E6_v3` en esta etapa
- mantener `E6_v1_clean` solo como referencia historica interna de la familia
