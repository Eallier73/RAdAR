# Analisis distribucion delta IAD

## Hallazgo principal

- El threshold `+-0.5` usado en `E11_v1_clean` es excesivo para la escala empirica observada del delta.
- En todos los horizontes, `+-0.5` colapsa casi toda la masa a `se_mantiene`.
- La magnitud tipica del movimiento semanal absoluto queda mas cerca del rango `0.10-0.20` que del rango `0.50`.

## Lectura por horizonte

```text
 horizonte_sem  rows_total  media_delta  mediana_delta  std_delta  p05_delta  p10_delta  p25_delta  p50_delta  p75_delta  p90_delta  p95_delta  mediana_abs_delta  p90_abs_delta  share_abs_delta_le_0_05  share_abs_delta_le_0_10
             1          72    -0.000991      -0.013939   0.188121  -0.309566  -0.197445  -0.114861  -0.013939   0.113504   0.198381   0.286260           0.114288       0.307911                 0.194444                 0.388889
             2          71    -0.000749       0.006162   0.189651  -0.357702  -0.283822  -0.074001   0.006162   0.120311   0.251114   0.288448           0.087713       0.333874                 0.281690                 0.521127
             3          70    -0.001806      -0.005974   0.191944  -0.290400  -0.224575  -0.122514  -0.005974   0.105738   0.213990   0.319745           0.116337       0.313030                 0.200000                 0.442857
             4          69    -0.010713      -0.004838   0.174477  -0.309937  -0.262728  -0.096327  -0.004838   0.097794   0.188162   0.275757           0.097740       0.305685                 0.231884                 0.521739
```