# nlp

Estatus: `codigo_activo_canonico`

`src/nlp/` es una capa activa y script-oriented.
No es un sandbox legado reubicado: aquí deben vivir únicamente piezas NLP vigentes del proyecto.

## Contenido vigente

- construcción de sentimiento semanal
- unión de encuestas y sentimiento
- generación de lags para datasets de modelado
- construcción de diccionarios PMI y WPMI
- clasificación temática y normalización de sus resultados

## Limpieza aplicada

- prototipos de forecasting y demos fueron movidos a `legacy/`
- los nombres activos quedaron en ASCII y minúsculas
- `experiment_logger.py` quedó como wrapper explícito hacia la implementación canónica de `src/modeling/tracking/`

## Regla

Si un script NLP deja de ser parte del flujo vigente o existe solo como referencia, debe salir de `src/nlp/` y moverse a `legacy/`.
