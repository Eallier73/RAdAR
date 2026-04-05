# Cierre Formal de E10 como Rama No Promocionable

Fecha de actualizacion: `2026-04-02`

## Proposito

Este documento fija el cierre formal de `E10` como rama probada, evaluada y no promovida bajo su formulacion actual.

No borra la familia.
No oculta la corrida.
No reescribe el resultado.

La conserva como evidencia metodologica util, pero cierra su via de promocion inmediata.

## Corrida canonica evaluada

- run: [E10_v1_clean_20260401_090439](/home/emilio/Documentos/RAdAR/Experimentos/runs/E10_v1_clean_20260401_090439)
- runner: [run_e10_meta_selector.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e10_meta_selector.py)
- logica: selector duro retrospectivo por horizonte con `LogisticRegression` regularizado, tabla E10 auditada, validacion `walk-forward expanding` y reconstruccion numerica final desde el modelo base seleccionado

## Evidencia comparativa relevante

Sobre el mismo subset de evaluacion del sistema:

- `E10_v1_clean`: `0.271220`
- `selector_fijo`: `0.265229`
- `E1_v5_clean`: `0.217866`
- `E9_v2_clean`: `0.227510`

Lectura:

- `E10_v1_clean` quedo por encima del selector fijo del mismo subset
- `E10_v1_clean` quedo por encima de `E1_v5_clean`
- `E10_v1_clean` quedo por encima de `E9_v2_clean`

Como `L_total_Radar` es una perdida, eso implica peor desempeno global.

## Accuracy del selector por horizonte

- `H1`: `0.187500`
- `H2`: `0.200000`
- `H3`: `0.142857`
- `H4`: `0.307692`

Balanced accuracy:

- `H1`: `0.158333`
- `H2`: `0.166667`
- `H3`: `0.100000`
- `H4`: `0.305556`

Estas accuracies son bajas y consistentes con una senal de seleccion insuficiente para promocion seria.

## Veredicto

La hipotesis principal de `E10` no quedo confirmada en esta formulacion.

Conclusiones obligatorias:

- `E10_v1_clean` fue una corrida real y metodologicamente limpia
- `E10_v1_clean` no supero al selector fijo
- `E10_v1_clean` no supero a `E1_v5_clean`
- `E10_v1_clean` no supero a `E9_v2_clean`
- la mejora contextual esperada no aparecio de forma defendible
- no procede promocion

## Estado canonico desde ahora

`E10` queda clasificada como:

- arquitectura probada
- selector duro retrospectivo ya evaluado
- hipotesis no confirmada
- rama cerrada para promocion bajo su formulacion actual
- referencia metodologica util para la frontera futura, no benchmark vigente

## Regla de no reapertura por inercia

`E10` no debe reabrirse por:

- retuning menor
- ajuste cosmetico de hiperparametros
- cambio pequeno de columnas
- insistencia narrativa

Solo podria reconsiderarse si existiera una reformulacion realmente distinta y defendible del problema contextual, con nuevo diseno y nueva hipotesis previa.
