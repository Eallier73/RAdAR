# Analisis recombinacion ex post por horizontes E1 vs E9

## Regla metodologica

- Este analisis es ex post.
- No entrena ningun modelo nuevo.
- No es promocionable.
- Solo mide si la separacion por horizonte merece una pregunta experimental futura.

## Hallazgos

- Mejor combinacion global: `9111` con `L_total_Radar=0.207397`.
- Esa combinacion usa `H1=e9`, `H2=e1`, `H3=e1`, `H4=e1`.
- Delta contra `E1_v5_clean` en subset comun: `-0.018161`.
- Delta contra `E9_v2_clean` en subset comun: `-0.020113`.
- Mejor combinacion por deteccion de caidas: `9111` con `deteccion_caidas_promedio=0.916667`.
- Mejor combinacion por trade-off global: `9111`.

## Interpretacion

- La mejor combinacion ex post usa `E9` solo en `H1` y `E1` en `H2-H4`.
- La ganancia potencial no esta repartida de forma uniforme; se concentra en el primer horizonte.
- Esto no prueba capacidad prospectiva, pero si sugiere que un selector por horizonte podria ser una pregunta metodologicamente legitima.
- ¿Alguna combinacion supera a ambos benchmarks en `L_total_Radar` sobre el subset comun? Si.