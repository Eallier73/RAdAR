# Actualizacion metodologica posterior a E9 y continuidad hacia E10 / E11

Fecha: `2026-04-01`

## Proposito

Este documento registra una decision metodologica posterior a la apertura de `E9`, sin reescribir la historia del proyecto ni forzar una lectura simplista de ganador unico.

Nota de alcance:

- Este documento conserva la decision tomada justo despues de `E9_v2_clean`.
- El estado canonico posterior de `E10`, de la clasificacion y de la capa explicativa transversal debe leerse hoy junto con:
  - [plan_de_experimentacion_radar.md](/home/emilio/Documentos/RAdAR/experiments/research/plan_de_experimentacion_radar.md)
  - [bitacora_experimental_radar.md](/home/emilio/Documentos/RAdAR/experiments/research/bitacora_experimental_radar.md)
  - [resumen_saneamiento_documental_radar.md](/home/emilio/Documentos/RAdAR/experiments/research/resumen_saneamiento_documental_radar.md)

La decision parte de la evidencia ya observada en:

- `E1_v5_clean`
- `E9_v1_clean`
- `E9_v2_clean`

## Decision central

`E1_v5_clean` no reemplaza a `E9_v2_clean`, y `E9_v2_clean` no reemplaza a `E1_v5_clean`.

Ambos representan funciones distintas y complementarias dentro del Radar.

- `E1_v5_clean` queda como mejor referente numerico puro.
- `E9_v2_clean` queda como mejor referente actual de riesgo, direccion y caidas.

La arquitectura futura del Radar debe reconocer explicitamente esta dualidad funcional.

## Que aprendimos realmente de E9

1. `E9` no fue una rama fallida.
2. `E9_v1_clean` mostro una mejora puntual, pero insuficiente.
3. `E9_v2_clean` si produjo una mejora operativa real, especialmente en:
   - `deteccion_caidas`
   - `direction_accuracy`
   - trade-off de riesgo en `H1-H2`
4. Esa mejora no debe confundirse con una sustitucion simple del mejor modelo numerico puro.

## Por que E9 no se cierra del todo

`E9` no se cierra porque ya mostro valor real en una dimension importante del problema:

- utilidad operativa de movimiento
- direccion
- deteccion temprana de bajas

Pero tampoco se declara ganadora absoluta porque:

- no resolvio de forma limpia todas las dimensiones a la vez
- no vuelve obsoleta la referencia numerica `E1_v5_clean`
- su interpretacion correcta depende de reconocer que la tarea del Radar no es una sola

Estado formal de `E9`:

- util
- no descartada
- no ganadora absoluta
- pausada metodologicamente
- potencialmente reactivable como componente de arquitectura compuesta o refinamiento controlado

## Dualidad funcional del Radar

La evidencia acumulada obliga a distinguir al menos dos tareas:

### A. Tarea numerica

Pronostico del porcentaje o nivel esperado del indicador.

Benchmark principal:

- `E1_v5_clean`

### B. Tarea categorica / operativa

Pronostico del movimiento:

- sube
- baja
- se mantiene

Y dentro de esta tarea, detectar bajas tiene prioridad operativa superior.

Benchmark operativo actual:

- `E9_v2_clean`

## Por que E10 sigue

`E10` sigue como siguiente familia activa porque la evidencia posterior a `E9` ya no sugiere una sola pregunta del tipo "que modelo promedio mejor".

La pregunta siguiente pasa a ser contextual:

- cuando conviene que tipo de salida
- cuando conviene que familia
- bajo que condiciones una arquitectura mas contextual mejora la utilidad del sistema

Eso corresponde a una familia distinta de `E9`:

- `E9` = stacking clasico controlado
- `E10` = gating, meta-selector o arquitectura contextual con trazabilidad fuerte

## Que problema nuevo justifica E11

`E11` queda justificada por una observacion estructural del proyecto:

el Radar no parece reducirse a una sola tarea predictiva homogenea.

La nueva familia conceptual `E11` queda definida como:

- componente numerico para porcentaje, nivel o cambio esperado
- componente categorico para movimiento:
  - sube
  - baja
  - se mantiene

Y, si mas adelante se justifica, una extension ordinal:

- baja fuerte
- baja moderada
- se mantiene
- sube moderada
- sube fuerte

## Diferencia conceptual entre E10 y E11

- `E10` pregunta como decidir o combinar contextualmente entre salidas o familias dentro del marco de meta-modelado.
- `E11` pregunta si el sistema debe separar explicitamente la prediccion numerica y la prediccion categorica como dos problemas coordinados pero distintos.

`E10` y `E11` no son lo mismo.

`E11` tampoco debe contaminar todavia la evaluacion de `E10`.

## Estado vigente del plan

### Activo ahora

- `E10` como siguiente familia activa

### Pausado pero util

- `E9`

### Solo planificado

- `E11`

## Cierre

El proyecto Radar entra a una etapa donde ya no basta con buscar un unico ganador global.

La evidencia sugiere una estructura funcional dual:

- un mejor referente numerico
- y un mejor referente de riesgo-direccion-caidas

En consecuencia:

- `E9` queda pausada como rama util pero no definitiva
- `E10` continua como siguiente linea activa
- `E11` queda abierta como futura familia explicitamente diseñada para separar la prediccion numerica de la prediccion categorica
