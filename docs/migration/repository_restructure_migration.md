# Repository Restructure Migration

## Que cambio

1. El codigo activo se concentro en `src/`.
2. Los datos canonicos se concentraron en `data/`.
3. El runtime tecnico se separo en `artifacts/`.
4. La evidencia metodologica y experimental se separo en `experiments/`.
5. La documentacion de arquitectura y migracion se centralizo en `docs/`.
6. Lo historico util se encapsulo en `legacy/`.

## Por que cambio

- para eliminar la dependencia de conocimiento tacito
- para volver evidente que parte del repo es vigente y que parte es historica
- para evitar que codigo, datos, runtime y documentacion sigan mezclados
- para dejar una base sostenible para automatizacion futura

## Que queda canonico

- `src/`
- `data/`
- `artifacts/`
- `experiments/`
- `docs/`
- `legacy/`

## Que queda deprecated y retirado

- `Scripts/`
- `Datos_RAdAR/`
- `Datos_RadaR_Texto/`
- `Experimentos/`
- `Datos_Modelo_ML/`
- `Diccionarios_NLP/`
- `Encuestas/`

Estas rutas ya no existen como aliases versionados. Se retiran para forzar el uso de la arquitectura canonica.

## Fases de migracion

1. Fase 1:
   se movio el contenido a rutas canonicas y se dejaron aliases transicionales.
2. Fase 2:
   se canonizaron las referencias activas y se retiraron los aliases de raiz.

## Wrappers que permanecen

- wrappers internos estrictamente necesarios dentro de `src/`, como `src/nlp/experiment_logger.py`
- no quedan aliases de raiz como parte del arbol versionado

## Limites del cambio

- no se rediseño la metodologia del pipeline
- no se eliminaron archivos historicos utiles
- no se forzo un renombre masivo de todos los archivos legacy
- se mantuvo el raw semanal plano porque ese era el flujo real vigente y migrarlo funcionalmente era otro proyecto

## Pendientes abiertos

1. Evaluar renombre de algunos scripts historicos con caracteres no ASCII si deja de haber dependencias externas.
2. Definir una politica explicita de que artefactos deben versionarse y cuales no.
3. Revisar si ciertos snapshots experimentales deben conservar rutas historicas como evidencia o actualizarse de forma sistematica.

## Tabla completa de migracion

La tabla exhaustiva `old_path -> new_path` vive en:

- [path_migration_table.csv](path_migration_table.csv)
