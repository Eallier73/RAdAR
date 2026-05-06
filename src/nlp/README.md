# nlp

Estatus: `codigo_activo_canonico`

`src/nlp/` es la capa activa y script-oriented para la parte NLP del proyecto.
Hoy todavia conviven aqui piezas canonicas, de soporte e historicas pendientes de separacion fisica completa.
El estatus operativo exacto de cada script debe leerse contra `src/nlp/README_pipeline_nlp_modelado.md`.

## Contenido relevante hoy

- construcción de sentimiento semanal
- unión de encuestas y sentimiento
- refresco de `ml_ready` desde PMI normalizado
- generación de lags para datasets de modelado
- reconstrucción del dataset final para modelado
- clasificacion tematica PMI+Confianza y normalizacion de resultados
- scripts historicos y de soporte que todavia no se han reubicado a un subarbol `legacy/`

## Limpieza aplicada

- prototipos de forecasting y demos fueron movidos a `legacy/`
- los nombres activos quedaron en ASCII y minúsculas
- `experiment_logger.py` quedó como wrapper explícito hacia la implementación canónica de `src/modeling/tracking/`

## Regla

La meta sigue siendo que `src/nlp/` contenga solo piezas vigentes.
Mientras esa separacion no termine, cualquier decision operativa debe tomarse con el mapa de estatus documentado en `src/nlp/README_pipeline_nlp_modelado.md`.

## Documentacion operativa

- ruta NLP -> modelado auditada: `src/nlp/README_pipeline_nlp_modelado.md`
- bitacora de esta intervencion: `src/nlp/CHANGELOG_NLP_MODELADO.md`
