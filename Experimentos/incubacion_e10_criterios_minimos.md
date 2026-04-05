# Incubacion E10: Documento historico superado

Fecha de actualizacion: `2026-04-02`

## Nota de alcance

Este documento conserva la lectura previa en la que `E10` quedaba en incubacion metodologica.

Esa lectura quedo superada por el cierre formal posterior de la familia. El estado canonico vigente debe leerse hoy en:

- [cierre_formal_e10_no_promocionable.md](/home/emilio/Documentos/RAdAR/Experimentos/cierre_formal_e10_no_promocionable.md)
- [consolidacion_operativa_post_produccion_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/consolidacion_operativa_post_produccion_controlada.md)
- [plan_de_experimentacion_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/plan_de_experimentacion_radar.md)

## Texto historico preservado

## Estado vigente en la lectura anterior

En la lectura anterior, `E10` ya existia como familia abierta y con corrida canonica real:

- [E10_v1_clean_20260401_090439](/home/emilio/Documentos/RAdAR/Experimentos/runs/E10_v1_clean_20260401_090439)

Su estado correcto no es:

- premodelado
- familia ganadora
- benchmark promocionado

En esa lectura, su estado correcto era:

- `incubacion metodologica`

## Por que seguia en incubacion en la lectura anterior

En esa lectura, `E10_v1_clean` habia sido metodologicamente limpio, pero no competitivo:

- no supero globalmente al selector fijo;
- no supero globalmente a `E1_v5_clean`;
- no supero globalmente a `E9_v2_clean`;
- la mejora observada fue parcial y fragil por horizonte.

Por tanto, en esa lectura, `E10` seguia siendo una rama seria de investigacion, pero todavia no una salida promocionable.

## Criterios minimos para competir de verdad

Antes de cualquier promocion futura, `E10` debe cumplir simultaneamente:

1. comparabilidad real contra `E1_v5_clean` y `E9_v2_clean` en el mismo marco temporal;
2. evidencia de no leakage en tabla, target selector y variables de entrada;
3. trazabilidad completa de features, columnas excluidas, folds, artefactos y benchmark de comparacion;
4. mejora defendible frente al selector fijo;
5. mejora no cosmetica en el plano funcional que pretende optimizar;
6. lectura estable de `H2` y `H3` sin deterioro severo de `H1` y `H4`;
7. lectura explicita de `direction_accuracy` y `deteccion_caidas`;
8. costo metodologico justificado frente a la ganancia observada;
9. posibilidad de explicar si desplaza un benchmark vigente o si solo convive como experimento;
10. reproducibilidad suficiente como para sostener una segunda corrida confirmatoria limpia.

## Condiciones minimas de paso

En esa lectura, `E10` solo podria salir de incubacion si demostraba una de estas dos cosas:

### Salida 1. Sustitucion funcional

Que desplaza de forma defendible al benchmark operativo vigente `E9_v2_clean`.

### Salida 2. Resolucion dual parcial

Que mejora de forma defendible la seleccion contextual sin degradar el benchmark numerico puro y con ganancia operativa suficientemente clara como para justificar una arquitectura mas compleja.

## Lo que no basta

No basta con:

- una mejora aislada en un solo horizonte;
- una mejora en `L_total_Radar` sin lectura operativa coherente;
- una mejora fragil sobre muy pocas filas;
- una corrida unica no replicada;
- una ventaja pequena que no justifique el costo metodologico agregado.

## Veredicto vigente en la lectura anterior

En la lectura anterior, `E10` permanecia en incubacion hasta nuevo aviso.

La familia puede seguir existiendo como rama seria de investigacion, pero hoy no debe:

- promocionarse,
- sustituir a `E1_v5_clean`,
- sustituir a `E9_v2_clean`,
- ni presentarse como solucion vigente del Radar.
