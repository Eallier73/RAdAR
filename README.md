# RAdAR

Reestructuracion arquitectonica conservadora del repositorio para separar de forma explicita:

- `src/`: codigo fuente activo
- `data/`: datos canonicos
- `artifacts/`: runtime, estado, logs y cache
- `experiments/`: investigacion, prompts, auditoria experimental y runs historicos
- `docs/`: arquitectura, metodologia, operacion y migracion
- `legacy/`: codigo y datos historicos fuera del flujo canonico

Lo que si vive aqui:

- pipeline activo de extraccion, preprocesamiento, NLP y modelado
- datos canonicos del Radar
- artefactos tecnicos necesarios para correr y auditar el sistema
- documentacion de arquitectura y migracion

Lo que no debe vivir mezclado en la raiz:

- scripts nuevos sueltos
- reportes runtime dentro de `src/`
- cache o estado mezclado con datos canonicos
- piezas operativas nuevas dentro de `experiments/`

Estructura canonica:

- [src/README.md](src/README.md)
- [data/README.md](data/README.md)
- [artifacts/README.md](artifacts/README.md)
- [experiments/README.md](experiments/README.md)
- [docs/README.md](docs/README.md)
- [legacy/README.md](legacy/README.md)

Estado de migracion:

- los aliases historicos de raiz ya fueron retirados
- las rutas viejas ya no forman parte del arbol versionado
- cualquier referencia nueva debe usar solo rutas canonicas

Documentacion clave:

- [docs/architecture/structural_audit.md](docs/architecture/structural_audit.md)
- [docs/architecture/repository_architecture.md](docs/architecture/repository_architecture.md)
- [docs/migration/repository_restructure_migration.md](docs/migration/repository_restructure_migration.md)
- [docs/migration/path_migration_table.csv](docs/migration/path_migration_table.csv)
