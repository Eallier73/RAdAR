# Apertura formal de E11 como arquitectura dual controlada

Fecha de archivo: `2026-04-03`

## Intencion del prompt

Abrir formalmente la familia `E11` como una arquitectura dual controlada, metodologicamente rigurosa, completamente trazable y estrictamente comparable contra los benchmarks vigentes del Radar.

## Estado oficial asumido por el prompt

- `E10_v1_clean` ya fue ejecutado y `E10` quedo formalmente cerrado como rama no promocionable.
- `E1_v5_clean` es el benchmark numerico puro vigente.
- `E9_v2_clean` es el benchmark operativo vigente.
- `E11` existe solo como arquitectura futura especificada, todavia no ejecutada, al momento de emitir este prompt.

## Hipotesis central

Una arquitectura dual puede capturar mejor la tension real del problema Radar que un modelo unico, porque el sistema necesita simultaneamente:

- buen desempeño numerico
- buena lectura de direccion
- buena deteccion de caidas

## Variantes pedidas

1. `E11_v1_clean`
   - `dual_mode = parallel`
   - regresion numerica + clasificacion ternaria `baja / se_mantiene / sube`

2. `E11_v2_clean`
   - `dual_mode = fall_detector`
   - regresion numerica + detector binario `cae / no_cae`

3. `E11_v3_clean`
   - `dual_mode = residual_dual`
   - pronostico numerico base + capa residual + capa categorica de contexto

## Reglas metodologicas no negociables

- horizontes `1,2,3,4`
- validacion externa `walk-forward expanding`
- tuning interno temporal cuando aplique
- mismo dataset base
- misma evaluacion Radar
- comparacion explicita contra `E1_v5_clean` y `E9_v2_clean`
- prohibicion estricta de leakage temporal
- prohibicion de validacion aleatoria
- comparacion ex ante, no ex post

## Artefactos exigidos

Minimo por run:

- `metadata_run.json`
- `parametros_run.json`
- `metricas_horizonte.json`
- `resumen_modeling_horizontes.json`
- `predicciones_h1.csv` a `predicciones_h4.csv`

Y por tratarse de arquitectura dual:

- `predicciones_clasificacion_h1.csv` a `predicciones_clasificacion_h4.csv`
- `probabilidades_clasificacion_h1.csv` a `probabilidades_clasificacion_h4.csv`
- `resumen_dual_horizontes.json`
- `thresholds_clases.json`
- `features_seleccionadas_h1.csv` a `features_seleccionadas_h4.csv` si aplica
- `residuales_h1.csv` a `residuales_h4.csv` si aplica la variante residual

## Criterio de cierre solicitado

Determinar si `E11`:

- agrega valor real o no;
- cual variante dual fue la mejor;
- si alguna conserva mejor el componente numerico;
- si alguna mejora el componente operativo;
- si alguna es promocionable;
- y si la familia debe expandirse, congelarse o cerrarse.
