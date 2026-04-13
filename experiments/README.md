# experiments

Estatus: `experimental`

`experiments/` conserva evidencia metodológica, prompts, auditoría experimental y runs históricos.
No es una segunda capa de código fuente.

## Subárboles

- `prompts/`: instrucciones y dirección experimental
- `research/`: bitácoras, planes y cierres metodológicos
- `audit/`: tablas maestras, inventarios y auditoría experimental vigente
- `audit/backups/`: backups físicos de workbooks y tablas
- `runs/`: evidencia histórica de corridas ejecutadas

## Reglas duras

- no entra código activo nuevo
- no entran datos canónicos operativos
- no entran cache, tokens ni estado técnico transversal
- `runs/` es inmutable como evidencia: los IDs históricos pueden conservar mayúsculas y convenciones previas
- documentos históricos dentro de `research/` y `prompts/` pueden citar rutas antiguas o scripts viejos como evidencia; eso no gobierna la arquitectura vigente

La arquitectura vigente se gobierna desde `docs/`, no desde `experiments/`.
