# Resumen Metodologico E5 CatBoost

Fecha de actualizacion: `2026-04-02`

## Estado de la familia

La familia `E5` queda `abierta madura`.

Constructo canonico de familia:

- `campeon no lineal tabular vigente`

## Corridas auditadas

- `E5_v1_clean`
- `E5_v2_clean`
- `E5_v3_clean`
- `E5_v4_clean`
- `E5_v5_clean`

## Constructos de run

- `E5_v1_clean`: baseline CatBoost
- `E5_v2_clean`: control `corr` vs `all`
- `E5_v3_clean`: control de profundidad
- `E5_v4_clean`: campeon no lineal tabular vigente
- `E5_v5_clean`: tuning focal dominado

## Lectura consolidada

Resultados clave:

- `E5_v1_clean = 0.255259`
- `E5_v2_clean = 0.261819`
- `E5_v3_clean = 0.261319`
- `E5_v4_clean = 0.247788`
- `E5_v5_clean = 0.264427`

Lectura:

- `E5_v4_clean` es el mejor run interno de la familia.
- Supera a `E1_v4_clean`, `E3_v2_clean` y `E4_v1_clean`.
- No supera a `E1_v5_clean`.
- Las variantes locales de `E5_v2`, `E5_v3` y `E5_v5` no justifican expansion incremental adicional.

## Posicion vigente en el proyecto

- `E5_v4_clean` es la mejor referencia no lineal tabular del Radar.
- La familia conserva valor central para comparaciones y arquitecturas compuestas.
- La familia no esta cerrada por completo, pero ya no se justifica abrir micro-variantes sin una hipotesis realmente distinta.

## Decision

- mantener `E5_v4_clean` como campeon interno
- no reabrir tuning local rutinario
- conservar `E5` como referencia competitiva principal frente a arquitecturas compuestas, `E9` y `E10`
