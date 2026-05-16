# RAdAR

Repositorio estructurado como base canónica operable del proyecto RAdAR.

Este repositorio ya expone una capa de orquestación operativa controlada en `src/operations/`.
Todavía no debe leerse como un sistema final con scheduling o automatización periódica cerrada.

## Taxonomía oficial de raíz

- `src/`: código activo canónico
- `data/`: datos canónicos
- `artifacts/`: runtime técnico, estado, logs y cache
- `docs/`: gobierno, arquitectura, operación y migración
- `experiments/`: investigación, prompts, auditoría experimental y runs históricos
- `legacy/`: código y datos históricos fuera del flujo canónico

## Estado real del repo

Implementado hoy:

- extracción activa por fuente
- preprocesamiento y normalización de insumos
- capa NLP activa
- núcleo de modelado reutilizable en `src/modeling/`
- orquestación operativa manual y reanudable en `src/operations/`
- tracking y reporting de experimentos
- datos, artifacts y documentación con separación explícita

Reservado para una fase posterior:

- scheduling
- disparo automático periódico
- integración con scheduler externo
- generador final de reporte

## Documentación autoritativa

- [docs/architecture/repository_governance.md](docs/architecture/repository_governance.md)
- [docs/architecture/repository_architecture.md](docs/architecture/repository_architecture.md)
- [docs/architecture/structural_audit.md](docs/architecture/structural_audit.md)
- [docs/migration/repository_restructure_migration.md](docs/migration/repository_restructure_migration.md)

Los documentos en `experiments/` preservan evidencia metodológica e histórica.
La verdad arquitectónica vigente vive en `docs/`.
