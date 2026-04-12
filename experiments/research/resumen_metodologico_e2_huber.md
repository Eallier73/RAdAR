# Cierre Metodologico E2 Huber

Fecha de cierre: 2026-03-23

## Alcance

La familia `E2` se evaluo bajo el mismo esquema limpio temporal ya validado en Ridge:

- dataset maestro identico al usado en `E1`
- horizontes `1, 2, 3 y 4` semanas
- validacion externa `walk-forward expanding`
- tuning interno temporal dentro de cada fold externo
- `feature_mode=corr` calculado solo con `train` del fold correspondiente
- `transform_mode=standard` ajustado dentro del pipeline del estimador
- mismas metricas Radar, mismo tracker y misma integracion al grid

No se detecto evidencia de leakage nueva en `E2_v1_clean`, `E2_v2_clean` ni `E2_v3_clean`.

## Corridas auditadas

- `E2_v1_clean`
  Baseline Huber limpio con `feature_mode=corr`, `lags 1..6` y tuning temporal interno.
- `E2_v2_clean`
  Control de convergencia. Mantiene el setup de `E2_v1_clean` y solo amplifica `max_iter`/`tol`.
- `E2_v3_clean`
  Prueba sin memoria larga. Mantiene Huber limpio y solo reduce `lags` de `1..6` a `1..4`.

## Tabla consolidada

| run_id | family | model | feature_mode | lags | feature_count_prom | mae_promedio | rmse_promedio | direction_accuracy_promedio | deteccion_caidas_promedio | L_total_Radar | lectura |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| E1_v4_clean | E1 | ridge_tscv | corr | 1,2,3,4 | 21.0 | 0.1029 | 0.1329 | 0.7444 | 0.7657 | 0.2533 | referencia parsimoniosa |
| E1_v5_clean | E1 | ridge_tscv | corr | 1,2,3,4,5,6 | 30.0 | 0.1025 | 0.1365 | 0.7438 | 0.7823 | 0.2434 | mejor Ridge global |
| E2_v1_clean | E2 | huber_tscv | corr | 1,2,3,4,5,6 | 30.0 | 0.1467 | 0.1913 | 0.6298 | 0.7268 | 0.3019 | baseline Huber inferior a Ridge |
| E2_v2_clean | E2 | huber_tscv | corr | 1,2,3,4,5,6 | 30.0 | 0.1467 | 0.1912 | 0.6298 | 0.7268 | 0.3019 | control de convergencia sin mejora material |
| E2_v3_clean | E2 | huber_tscv | corr | 1,2,3,4 | 21.0 | 0.1297 | 0.1571 | 0.7076 | 0.7699 | 0.2865 | ganador interno de E2, aun por debajo de Ridge |

## Que probo cada corrida

### E2_v2_clean

`E2_v2_clean` probo si el mal desempeno de `E2_v1_clean` se explicaba principalmente por convergencia incompleta.

Resultado:

- El control de convergencia elimino los `ConvergenceWarning` en `H1`, `H2`, `H3` y `H4`.
- `L_total_Radar` practicamente no cambio: `0.301907 -> 0.301920`.
- `direction_accuracy` y `deteccion_caidas` quedaron iguales en la practica.

Conclusion:

`E2_v2_clean` descarta que la convergencia sea la explicacion principal del mal desempeno de Huber en Radar.

### E2_v3_clean

`E2_v3_clean` probo si Huber funciona mejor sin memoria larga.

Resultado:

- mejora material frente a `E2_v1_clean` en `L_total_Radar`: `0.3019 -> 0.2865`
- mejora clara en `H2`
- mejora fuerte en `H4`
- deterioro operativo importante en `H3`

Conclusion:

La memoria corta ayuda a Huber, pero la mejora es parcial y no lo vuelve competitivo frente a Ridge.

## Lectura por horizonte

- `H2`
  `E2_v3_clean` mejora frente a `E2_v1_clean`, lo que confirma que `lags 1..6` estaban metiendo ruido para Huber.
- `H3`
  `E2_v3_clean` empeora respecto a `E2_v1_clean` y queda claramente por debajo de `E1_v4_clean` y `E1_v5_clean`.
- `H4`
  `E2_v3_clean` mejora mucho frente a `E2_v1_clean`, pero esa ganancia no compensa el deterioro de `H3` ni la brecha global con Ridge.

## Respuestas formales

- ¿Que probo `E2_v2_clean` realmente?
  Que resolver mejor la optimizacion no cambia materialmente el desempeno de Huber.
- ¿Que probo `E2_v3_clean` realmente?
  Que Huber se beneficia de memoria mas corta, pero esa mejora es parcial y no suficiente.
- ¿Huber mejoro por memoria corta o por convergencia?
  Por memoria corta; no por convergencia.
- ¿La mejora fue global o parcial?
  Parcial. Mejora `H2` y `H4`, pero sacrifica `H3`.
- ¿Hubo mejora operativa o solo numerica?
  Hubo mejora operativa parcial frente a `E2_v1_clean`, pero no suficiente para desplazar a Ridge.
- ¿Hay razon real para mantener viva la familia `E2`?
  No.

## Veredicto final formal

- Ganador interno de `E2`: `E2_v3_clean`
- Diagnostico sobre convergencia: `E2_v2_clean` descarta la hipotesis de convergencia como causa principal
- Diagnostico sobre memoria: `E2_v3_clean` muestra que `lags 1..6` perjudicaban a Huber
- Competitividad final: la familia `E2` no alcanza a `E1_v5_clean` ni supera de forma sustantiva a `E1_v4_clean`
- Decisión: `E2` queda cerrada formalmente
- `E2_v4_clean`: cancelada y no ejecutada por decision metodologica explicita, no por olvido

## Siguiente paso

La siguiente familia a abrir es `E3` Random Forest, manteniendo el mismo marco de comparabilidad:

- referencia principal: `E1_v5_clean`
- referencia parsimoniosa: `E1_v4_clean`
- referencia robusta cerrada: `E2_v3_clean`
