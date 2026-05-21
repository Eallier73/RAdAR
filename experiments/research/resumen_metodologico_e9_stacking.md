# Resumen Metodologico E9 Stacking Clasico Controlado

Fecha de actualizacion: `2026-04-02`

## Estado de la familia

La familia `E9` queda `pausada util`.

Constructo canonico de familia:

- `rama operativa de riesgo-direccion-caidas`

## Corridas auditadas

- `E9_v1_clean`
- `E9_v2_clean`

## Constructos de run

- `E9_v1_clean`: baseline stacking clasico ridge
- `E9_v2_clean`: campeon riesgo-direccion-caidas

## Lectura consolidada

Resultados:

- `E9_v1_clean = 0.268475`
- `E9_v2_clean = 0.227510`

Lectura:

- `E9_v1_clean` fue una apertura sobria y limpia, con mejora parcial localizada.
- `E9_v2_clean` mejoro claramente `H1`, `H2` y `H4`, y quedo como mejor run interno de la familia.
- `E9_v2_clean` no reemplaza a `E1_v5_clean` como referente numerico puro.
- `E9_v2_clean` si se vuelve el mejor referente actual de riesgo, direccion y deteccion de caidas.

## Posicion vigente en el proyecto

- `E9` no se cierra como fallida.
- `E9` tampoco se declara ganadora global unica.
- La familia queda en pausa metodologica porque ya probo una utilidad funcional real distinta de la tarea numerica pura.

## Decision

- mantener `E9_v2_clean` como referente operativo vigente
- no reactivar `E9` inmediatamente sin una pregunta metodologica nueva
- usar su evidencia para justificar la transicion a `E10` y la apertura conceptual de `E11`
