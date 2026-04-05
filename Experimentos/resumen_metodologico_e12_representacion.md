# Resumen Metodologico E12 Representacion

Fecha de actualizacion: `2026-04-03`

## Proposito

`E12` abre una familia de representacion controlada para probar una hipotesis muy precisa:

- si parte de la ventaja operativa observada en `E9_v2_clean`, especialmente en `H1`, puede absorberse dentro de un modelo simple y trazable;
- usando enriquecimiento de representacion y no mayor complejidad arquitectonica.

La familia no nace para probar otro algoritmo. Nace para probar si una capa de representacion enriquecida permite capturar mejor senales de corto plazo sin destruir la robustez de `E1_v5_clean` en `H2-H4`.

## Marco experimental

- runner canonico: [run_e12_representacion.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/run_e12_representacion.py)
- familia base: `Ridge`
- target: `nivel`
- feature_mode base: `corr`
- lags: `1,2,3,4,5,6`
- transformacion: `standard`
- validacion externa: `walk-forward expanding`
- tuning interno: seleccion temporal de `alpha`
- horizontes: `1,2,3,4`
- comparadores obligatorios:
  - `E1_v5_clean`
  - `E9_v2_clean`
  - `E1_v4_clean`

## Variantes abiertas

### `E12_v1_clean`

- rol: baseline de representacion minima enriquecida
- corrida canonica: [E12_v1_clean_20260403_075150](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v1_clean_20260403_075150)
- bloques usados:
  - predicciones archivadas de `E1_v5_clean` y `E5_v4_clean`
  - spreads y consensos minimos entre ambas
  - bloque de regimen observable en `t`

### `E12_v2_clean`

- rol: representacion ampliada de diversidad
- corrida canonica: [E12_v2_clean_20260403_075843](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v2_clean_20260403_075843)
- bloques usados:
  - predicciones archivadas de `E1_v5_clean`, `E5_v4_clean`, `E3_v2_clean`, `E7_v3_clean`
  - spreads y consensos ampliados entre familias
  - bloque de regimen observable en `t`

### `E12_v3_clean`

- rol: stress test metodologico de desacuerdo puro
- corrida canonica: [E12_v3_clean_20260403_080040](/home/emilio/Documentos/RAdAR/Experimentos/runs/E12_v3_clean_20260403_080040)
- bloques usados:
  - predicciones archivadas de `E1_v5_clean`, `E5_v4_clean`, `E3_v2_clean`, `E7_v3_clean`
  - solo senales de consenso y desacuerdo entre bases
  - sin bloque de regimen observable

## Validez temporal

`E12` usa dos fuentes de informacion enriquecida:

1. predicciones archivadas por fecha/horizonte de runs canonicos previos;
2. constructos de regimen construidos unicamente con `y_t` y sus lags observables.

La validez temporal se sostiene asi:

- no se usa ninguna etiqueta del tipo “modelo ganador por fila”;
- no se usa la tabla `E10` ni ninguna curacion ex post por desempeno;
- no se usa la recombinacion `9111` como sistema entrenable;
- no se usan metricas futuras como features;
- las predicciones archivadas se consumen solo como senales historicas alineadas por fecha/horizonte ya existentes;
- el bloque de regimen se calcula con datos observables en `t`, nunca con `y` futuro.

Costo metodologico reconocido:

- para poder consumir esas predicciones archivadas se restringe el sample a filas donde las bases historicas existen para ese horizonte;
- por eso `E12` opera sobre `26/25/24/23` filas de modelado por horizonte y `14/13/12/11` filas evaluables con `initial_train_size=12`.

## Resultado sintetico

Ninguna variante mejora de forma defendible a `E1_v5_clean` ni a `E9_v2_clean`.

Lectura interna de la familia:

- `E12_v1_clean` empeora claramente.
- `E12_v2_clean` tambien empeora y no justifica la ampliacion del bloque enriquecido.
- `E12_v3_clean` queda como mejor variante interna; eso sugiere que el desacuerdo entre bases aporta mas que el bloque de regimen usado en esta primera apertura.

Pero la hipotesis central no queda confirmada:

- la mejora esperada en `H1` no aparece;
- `H2-H4` no compensan suficientemente;
- la familia no captura de forma util la ventaja operativa de `E9`.

## Decision metodologica vigente

`E12` queda como `familia evaluada sin promocion`.

Lectura correcta:

- no es un fracaso opaco;
- no es una familia promotable;
- deja un hallazgo parcial util:
  - el bloque de desacuerdo parece mas prometedor que el bloque de regimen usado aqui;
  - pero la evidencia actual no justifica expansion inmediata.

Decision:

- no promover;
- no expandir por inercia;
- reabrir solo si aparece una hipotesis de `H1` mas precisa y metodologicamente defendible.
