# Cierre Ridge y Transicion a Familia No Lineal

## Instruccion
Cierra la exploracion principal de Ridge en `E1` con este criterio de decision:

1. Registrar oficialmente:
- `E1_v5_clean` como mejor Ridge limpio global por `L_total_Radar`
- `E1_v4_clean` como referencia parsimoniosa y mas equilibrada

2. No continuar automaticamente con `E1_v6_clean`.
Razon:
- `E1_v5_clean` mejora el global, pero no confirma la hipotesis sustantiva de que mas memoria ayude especialmente en `H3/H4`.
- La mejora viene sobre todo por `H2`.
- En `H4` la regularizacion pega en el techo del grid (`alpha=10000` en todos los folds externos), senal de que los lags extra no estan aportando senal robusta.

3. Actualizar el grid de experimentos y el resumen metodologico de `E1` con esta lectura:
- Ridge ya fue explorado suficientemente en su rama principal.
- El trade-off observado sugiere rendimiento cercano al limite de esta familia bajo esta formulacion.

4. Siguiente paso:
Disenar y correr la siguiente familia de modelos para `E1`, priorizando una familia no lineal.
Orden sugerido:
- Familia 2: `ElasticNet` con el mismo esquema limpio temporal
o, si ya estaba definido en el plan original,
- Familia 2: `XGBoost / arboles boosting` con validacion walk-forward y tuning temporal interno

5. Mantener exactamente el mismo marco de evaluacion para comparabilidad:
- mismos horizontes: `1,2,3,4`
- misma validacion externa `walk-forward expanding`
- mismo tuning interno temporal
- misma funcion de perdida Radar
- mismos artefactos obligatorios por horizonte
- mismo dataset base

6. Antes de correr la nueva familia:
- reutilizar la estructura de scripts de `E1_v5_clean`
- preservar trazabilidad completa de features, predicciones y tuning
- documentar explicitamente que Ridge queda cerrado como baseline lineal regularizado principal

## Nota Operativa
Guardar y ordenar este prompt.
No ejecutar por el momento.
