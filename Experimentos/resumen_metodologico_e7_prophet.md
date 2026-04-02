# Resumen Metodologico E7 Prophet

Fecha de actualizacion: `2026-04-02`

## Estado de la familia

La familia `E7` queda `intermedia`.

Constructo canonico de familia:

- `referencia temporal secundaria`

## Corridas auditadas

- `E7_v1_clean`
- `E7_v2_clean`
- `E7_v3_clean`

## Constructos de run

- `E7_v1_clean`: baseline temporal parsimonioso
- `E7_v2_clean`: variante `all` colapsada
- `E7_v3_clean`: campeon temporal secundario

## Lectura consolidada

Resultados:

- `E7_v1_clean = 0.325502`
- `E7_v2_clean = 0.681992`
- `E7_v3_clean = 0.321328`

Lectura:

- `Prophet` mejora con claridad a `E6`.
- `feature_mode=all` colapsa la familia.
- `E7_v3_clean` mejora un poco a `E7_v1_clean`, sobre todo en `H2/H3`.
- Aun asi la familia no entra al bloque contendiente principal.

## Posicion vigente en el proyecto

- `E7_v3_clean` queda como referencia temporal estructurada secundaria.
- Tiene valor comparativo y puede aportar diversidad metodologica, pero no desplaza a `E1_v5_clean`, `E5_v4_clean` o `E3_v2_clean`.

## Decision

- no abrir una expansion amplia de `E7`
- conservar `E7_v3_clean` como referencia temporal secundaria y posible candidato contextual
