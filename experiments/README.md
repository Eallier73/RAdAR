# experiments

Estatus: `experimental`

Proposito:

- concentrar investigacion, prompts, auditorias experimentales y runs historicos de modelado
- dejar atras el antiguo cajon de sastre `Experimentos/`

Subarboles:

- `prompts/`: prompts de agente y material de direccion experimental
- `research/`: planes, bitacoras, cierres y notas metodologicas
- `audit/`: grid experimental, tablas maestras, inventarios y auditorias vigentes
  - `audit/backups/`: backups historicos de grid (archivos `.backup_*.xlsx`)
- `runs/`: corridas experimentales ya ejecutadas

Lo que si vive aqui:

- evidencia metodologica y trazabilidad experimental
- insumos documentales para decisiones de modelado
- runs historicos de experimentacion

Lo que no debe vivir aqui:

- codigo fuente activo
- datasets canonicos operativos
- cache o estado tecnico transversal

Relacion con otras carpetas:

- `src/modeling` consume y actualiza varios artefactos de `experiments/audit` y `experiments/runs`
- `docs/` fija la arquitectura canonica; `experiments/` documenta exploracion y validacion

Estado:

- el alias historico `Experimentos/` ya fue retirado
- toda referencia vigente debe usar `experiments/`
