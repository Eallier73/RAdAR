# Resumen Metodologico Clasificacion Radar C1-C4

Fecha de actualizacion: `2026-04-02`

## Estado de la rama

La clasificacion existe como rama real del proyecto, pero no esta consolidada ni es prioritaria.

Constructos canonicos de rama:

- `C1`: clasificacion base evaluada
- `C2-C4`: clasificacion boosting preparada

## Estado por familia

- `C1`: evaluada y pausada tempranamente
- `C2`: infraestructura preparada, sin corrida real
- `C3`: infraestructura preparada, sin corrida real
- `C4`: infraestructura preparada, sin corrida real

## Corridas auditadas

Corridas reales de `C1`:

- `C1_v1_clean`
- `C1_v2_clean`
- `C1_v3_clean`

## Constructos de run en `C1`

- `C1_v1_clean`: baseline prudente de clasificacion
- `C1_v2_clean`: control parsimonioso de clasificacion
- `C1_v3_clean`: control flexible de clasificacion

## Lectura consolidada

- `C1` si fue ejecutada realmente.
- Las tres corridas colapsaron a clase unica o a una diversidad de clases insuficiente para dejar senal discriminativa util.
- El problema principal no fue solo el clasificador, sino la formulacion del target de clasificacion.

## Posicion vigente en el proyecto

- La clasificacion no debe describirse como “no iniciada”.
- Tampoco debe leerse como una rama competitiva consolidada.
- Queda como antecedente real, ya evaluado, que sugiere que cualquier reactivacion futura exige redefinir primero el target.

## Decision

- no continuar con `C2-C4` por inercia
- mantener la infraestructura preparada
- reactivar clasificacion solo si la agenda metodologica vuelve a priorizar un target categorico mejor formulado
