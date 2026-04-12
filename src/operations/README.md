# operations

Estatus: `operativa_vigente`

Este subarbol queda reservado para wrappers y orquestadores de operacion controlada que deban coordinar piezas ya canonicas de `src/`.

No debe redefinir metodologia ni duplicar pipelines.

Uso esperado:

- runners de operacion controlada
- puentes CLI estables
- coordinacion de etapas ya definidas en `src/extraction/`, `src/preprocessing/`, `src/nlp/` y `src/modeling/`
