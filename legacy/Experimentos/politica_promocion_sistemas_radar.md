# Politica de Promocion Futura de Sistemas Radar

Fecha de actualizacion: `2026-04-03`

## Proposito

Esta politica fija la regla de promocion futura para cualquier sistema que aspire a desplazar a los benchmarks vigentes del Radar.

No define un ganador actual unico. Define el criterio minimo para una promocion defendible.

Version estructurada y aplicable:

- [politica_promocion_sistemas_radar.json](/home/emilio/Documentos/RAdAR/Experimentos/politica_promocion_sistemas_radar.json)

## Benchmarks vigentes

- benchmark numerico puro: `E1_v5_clean`
- benchmark operativo de riesgo-direccion-caidas: `E9_v2_clean`

Sistema operativo vigente:

- salida numerica principal: `E1_v5_clean`
- deteccion de caidas: `E9_v2_clean`
- politica direccional por horizonte: `H1=E9`, `H2=E1`, `H3=E9`, `H4=E1`

La promocion futura puede reemplazar:

- una capa funcional puntual;
- o el sistema dual completo;

pero no debe fingirse una sustitucion integral si solo mejora una parte aislada.

## Regla general

Ningun sistema futuro debe considerarse promovible solo por una mejora aislada en una metrica agregada o en un horizonte puntual.

La promocion futura debe leerse sobre dos planos:

### Plano numerico

Variables minimas a revisar:

- `MAE`
- `RMSE`
- `loss_h` por horizonte
- `L_total_Radar`

### Plano operativo

Variables minimas a revisar:

- `direction_accuracy`
- `deteccion_caidas`
- lectura de cambios
- robustez en la anticipacion operativa de bajas

## Regla de superioridad defendible

Un sistema futuro solo puede considerarse superior si:

- mejora de forma defendible el plano numerico frente a `E1_v5_clean`
- y/o mejora de forma defendible el plano operativo frente a `E9_v2_clean`
- sin degradar severamente el otro plano funcional
- y con evidencia temporal limpia, comparable y libre de leakage

## Estados de decision

La politica operativa usa cinco estados canonicos:

### Promocion

Aplica solo si:

- hay mejora defendible frente al benchmark funcional correspondiente;
- la lectura por `H2` y `H3` es favorable;
- `H1` y `H4` no sufren deterioro severo;
- `direction_accuracy` y `deteccion_caidas` siguen una lectura coherente con el plano funcional;
- la corrida es trazable, reproducible y libre de leakage;
- y el costo metodologico agregado esta justificado.

### Observacion

Aplica cuando:

- existe señal util,
- pero todavia no hay evidencia suficiente para promocion o sustitucion formal.

### No promocion

Aplica cuando:

- no existe superioridad defendible,
- la mejora es cosmetica,
- o la evidencia es demasiado fragil para sostener una decision de cambio.

### Cierre de rama

Aplica cuando:

- la hipotesis principal ya fue probada con una corrida o bloque de corridas suficientes;
- no existe superioridad defendible frente al benchmark o benchmark objetivo;
- la evidencia muestra que la rama no es promocionable bajo su formulacion actual;
- y mantenerla en observacion solo agregaria ambiguedad narrativa.

### Despromocion

Aplica cuando:

- un benchmark vigente pierde integridad,
- pierde reproducibilidad,
- o es superado de forma defendible por un sistema nuevo.

### Sustitucion de benchmark

Aplica solo cuando:

- ya se cumplieron las condiciones de promocion;
- el sistema nuevo supera de forma defendible al benchmark que pretende reemplazar;
- y queda explicitado si sustituye dentro del mismo plano funcional o si resuelve de forma defendible la dualidad vigente.

## Lo que no basta

No basta con:

- ganar por `L_total_Radar` en una lectura unica y simplificada
- mejorar solo `MAE`
- mejorar solo `direction_accuracy`
- ganar un unico horizonte con deterioro serio en los demas
- mostrar una mejora fragil sobre muy pocos casos
- ganar una recombinacion ex post por horizonte sin evidencia prospectiva
- mostrar sensibilidad favorable de thresholds sin una nueva corrida temporal limpia

## Checks minimos obligatorios

Toda decision de promocion o no promocion debe revisar, como minimo:

1. `L_total_Radar`
2. lectura por horizonte con enfasis en `H2` y `H3`
3. estabilidad en `H1` y `H4`
4. `direction_accuracy`
5. `deteccion_caidas`
6. trazabilidad completa
7. ausencia de leakage
8. reproducibilidad
9. comparabilidad contra benchmark vigente
10. costo metodologico agregado frente a la mejora obtenida

## Caso aplicado: E10

Bajo esta politica, `E10` no queda en observacion promocionable.

Queda en `cierre de rama` porque:

- `E10_v1_clean` ya fue corrida real y comparable;
- no supero al selector fijo;
- no supero a `E1_v5_clean`;
- no supero a `E9_v2_clean`;
- y sus accuracies de selector por horizonte fueron bajas.

Por tanto, `E10` se conserva como evidencia historica util, pero no como candidato vigente.

## Caso aplicado: E11

Bajo esta politica, la primera apertura dual de `E11` no queda promocionable.

La familia no queda cerrada como fracaso, pero sus variantes iniciales quedan en `no promocion` porque:

- `E11_v1_clean` preserva exactamente el benchmark numerico `E1_v5_clean`, pero la capa ternaria casi colapsa a `se_mantiene`;
- `E11_v2_clean` preserva exactamente el benchmark numerico y agrega un detector binario de caidas con señal moderada, pero no desplaza a `E9_v2_clean`;
- `E11_v3_clean` agrega complejidad residual dual y no mejora `L_total_Radar` frente a `E1_v5_clean`;
- ninguna variante desplaza de forma defendible la salida dual vigente `E1_v5_clean + E9_v2_clean`.

Por tanto, `E11` se conserva como evidencia dual util y como frontera metodologica futura, pero no como sistema vigente ni como sustitucion de benchmark.

## Caso aplicado: E12

Bajo esta politica, la primera apertura de `E12` no queda promocionable.

La familia deja un `hallazgo parcial sin promocion` porque:

- `E12_v1_clean` y `E12_v2_clean` agregan representacion, pero no mejoran de forma defendible a `E1_v5_clean` ni a `E9_v2_clean`;
- `E12_v3_clean` queda como mejor variante interna al aislar el desacuerdo entre bases;
- aun asi, `E12_v3_clean` sigue por detras de ambos benchmarks vigentes en el mismo subset comun;
- ninguna variante mejora `H1`, que era la hipotesis central de la apertura;
- la complejidad agregada no se justifica con la ganancia obtenida.

Por tanto, `E12` se conserva como evidencia util sobre representacion, pero no como candidata vigente ni como justificacion de expansion inmediata.

## Implicacion metodologica

Mientras `E11` no exista como arquitectura validada, el proyecto no debe actuar como si ya hubiera un sistema final unico que resuelva por si solo la dualidad del Radar.

La promocion futura debe seguir siendo una decision basada en evidencia dual, no en intuicion ni en simplificacion narrativa.
