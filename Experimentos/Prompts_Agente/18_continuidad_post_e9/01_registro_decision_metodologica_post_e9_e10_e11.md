# Registro de decision metodologica posterior a E9 y apertura controlada de E10 / preapertura de E11

Quiero que actualices formalmente la documentacion, el criterio metodologico y el estado del plan de experimentacion del proyecto Radar con base en la lectura ya consolidada de `E9_v2_clean` frente a `E1_v5_clean`.

## Objetivo general

Registrar de forma explicita una decision metodologica importante del proyecto:

1. `E1_v5_clean` queda reconocido como el mejor modelo numerico puro observado hasta ahora.
2. `E9_v2_clean` queda reconocido como el mejor modelo orientado a riesgo, direccion y deteccion de caidas dentro de la rama `E9`.
3. Esa diferencia no debe interpretarse como contradiccion sino como complementariedad funcional entre dos tareas predictivas distintas del Radar.
4. La familia `E9` no se cierra todavia como descartada, pero queda en pausa metodologica.
5. La continuacion inmediata del proyecto debe seguir con la familia `E10`.
6. Debe abrirse formalmente en el plan una nueva familia conceptual `E11`, definida como arquitectura dual:
   - un modelo para prediccion numerica del porcentaje
   - otro modelo para prediccion categorica de sube / baja / se mantiene
7. `E11` debe quedar abierta solo como linea de investigacion planificada y documentada, no como rama a ejecutar todavia.

## Regla de redaccion

La documentacion final debe dejar claro que el proyecto Radar ya no debe leerse como si tuviera una sola tarea predictiva.

Debe distinguir, como minimo:

- tarea numerica
- tarea categórica / operativa

y debe dejar explicitamente asentado que detectar caidas tiene prioridad operativa superior.

## Entregables minimos

1. Documento metodologico de actualizacion posterior a `E9`.
2. Actualizacion del plan de experimentacion con el nuevo estado de `E9`, `E10` y `E11`.
3. Actualizacion de la bitacora y de cualquier capa narrativa equivalente.
4. Si existe tabla maestra o resumen maestro de familias, anadir una capa que refleje esta lectura metodologica sin destruir la trazabilidad automatica por run.
