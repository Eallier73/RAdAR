# Repository Restructure Migration

Resumen de migración hacia la estructura canónica actual.

## 1. Resultado

La migración consolidó el repositorio en seis capas explícitas:

- `src/`
- `data/`
- `artifacts/`
- `docs/`
- `experiments/`
- `legacy/`

## 2. Qué quedó retirado como raíz activa

- `Scripts/`
- `Datos_RAdAR/`
- `Datos_RadaR_Texto/`
- `Experimentos/`
- `Datos_Modelo_ML/`
- `Diccionarios_NLP/`
- `Encuestas/`

Esas rutas sobreviven solo como referencia histórica en la documentación de migración o en `legacy/`.

## 3. Qué se reforzó en esta fase

- separación física real de `src/modeling/`
- limpieza de naming activo en NLP y datos de referencia
- retiro de prototipos activos hacia `legacy/`
- declaración explícita de `src/operations/` como capa reservada
- salida de logs y estado técnico hacia `artifacts/`

## 4. Cómo leer `path_migration_table.csv`

[path_migration_table.csv](path_migration_table.csv) es un ledger histórico de la migración desde la estructura previa.
Puede contener destinos intermedios de fases anteriores.
La especificación vigente del árbol y de la canonicidad vive en:

- [../architecture/repository_governance.md](../architecture/repository_governance.md)
- [../architecture/repository_architecture.md](../architecture/repository_architecture.md)
- [../architecture/structural_audit.md](../architecture/structural_audit.md)
