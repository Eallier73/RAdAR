# RAdAR

Repositorio estructurado como base canónica pre-automatización del proyecto RAdAR.

Este repositorio no debe leerse como un sistema final con orquestación end-to-end ya cerrada.
Sí debe leerse como una arquitectura fuente profesional sobre la cual todavía se puede construir la automatización integral sin volver a mezclar código, datos, runtime, documentación, experimentación y legado.

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
- tracking y reporting de experimentos
- datos, artifacts y documentación con separación explícita

Reservado para una fase posterior:

- automatización integral
- orquestación end-to-end
- scheduling
- integración operativa completa
- wrappers operativos finales

`src/operations/` existe como namespace reservado para esa fase posterior.
No representa una capa operativa final ya implementada.

## Documentación autoritativa

- [docs/architecture/repository_governance.md](docs/architecture/repository_governance.md)
- [docs/architecture/repository_architecture.md](docs/architecture/repository_architecture.md)
- [docs/architecture/structural_audit.md](docs/architecture/structural_audit.md)
- [docs/migration/repository_restructure_migration.md](docs/migration/repository_restructure_migration.md)

Los documentos en `experiments/` preservan evidencia metodológica e histórica.
La verdad arquitectónica vigente vive en `docs/`.
