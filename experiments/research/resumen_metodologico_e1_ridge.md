# Resumen Metodologico E1 Ridge

## Estado de la familia

La exploracion principal de la familia Ridge en `E1` se considera cerrada.

## Criterio de cierre

- `E1_v5_clean` queda como mejor Ridge limpio global por `L_total_Radar`.
- `E1_v4_clean` queda como referencia parsimoniosa y mas equilibrada.
- La rama principal de Ridge ya fue explorada suficientemente bajo esta formulacion.

## Lectura principal

- La mejora global de `E1_v5_clean` proviene sobre todo de `H2`.
- No se confirmo la hipotesis de que una memoria mas larga ayude especialmente en `H3/H4`.
- En `H4` la regularizacion quedo pegada al techo del grid (`alpha=10000`), senal de aporte debil o inestable de los lags extra.
- El trade-off observado sugiere que Ridge esta cerca de su limite practico dentro de esta familia lineal regularizada.

## Decision operativa

- No continuar automaticamente con `E1_v6_clean`.
- Mantener Ridge como baseline lineal regularizado principal del proyecto.

## Actualizacion posterior: micro-rama `E1.1 Bayesian`

El `2026-04-02` se ejecuto una verificacion tactica corta y controlada para probar si `BayesianRidge` podia extraer un margen lineal adicional sin reabrir la familia principal.

Run canónico:

- [E1_1_v1_bayesian_base_20260402_063714](/home/emilio/Documentos/RAdAR/experiments/runs/E1_1_v1_bayesian_base_20260402_063714)

Lectura:

- `E1_1_v1_bayesian_base = 0.264946`
- `E1_v5_clean = 0.243442`
- `E1_v4_clean = 0.253277`
- La unica senal parcial aparecio en `H3`.
- No hubo mejora global ni mejor equilibrio operativo frente a las referencias Ridge ya cerradas.

Decision:

- no correr `E1_1_v2_bayesian_control`
- no abrir familia bayesiana nueva
- mantener intacto el cierre principal de `E1`

Documento especifico de la micro-rama:

- [resumen_micro_rama_e1_1_bayesian.md](/home/emilio/Documentos/RAdAR/experiments/research/resumen_micro_rama_e1_1_bayesian.md)

## Continuacion segun plan original

La siguiente familia a explorar, siguiendo el catalogo original del grid, es:

- `E2`: `Huber Regressor`

## Alineacion operativa

- Aunque en la discusion de cierre aparecio la opcion de saltar a una familia no lineal, el orden oficial del plan original del proyecto sigue siendo `E2` antes de `E3` y `E4`.
- Por lo tanto, el cierre de Ridge no habilita un salto automatico a boosting; primero corresponde ejecutar la familia robusta `Huber`.

Despues de `E2`, el orden natural del plan original es:

- `E3`: `Random Forest`
- `E4`: `XGBoost / LightGBM`

## Regla de comparabilidad

La siguiente familia debe conservar:

- horizontes `1,2,3,4`
- validacion externa `walk-forward expanding`
- tuning interno temporal
- funcion de perdida Radar
- trazabilidad completa de predicciones, tuning y artefactos
