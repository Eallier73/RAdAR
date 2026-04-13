# Structural Audit

Auditoría estructural estricta del repositorio RAdAR en clave pre-automatización.

## 1. Dictamen de raíz

| Ruta | Categoría | Estado final | Dictamen |
| --- | --- | --- | --- |
| `src/` | código activo canónico | limpia y gobernada | `aprueba` |
| `data/` | datos canónicos | separada de runtime | `aprueba` |
| `artifacts/` | runtime técnico | endurecida con reglas de versionado | `aprueba` |
| `docs/` | documentación estructural y operativa | gobierna y ya no solo describe | `aprueba` |
| `experiments/` | experimentación e investigación | separada de código y runtime | `aprueba` |
| `legacy/` | histórico | concentra material retirado | `aprueba` |

## 2. Dictamen de `src/`

| Ruta | Dictamen | Estado final |
| --- | --- | --- |
| `src/extraction/` | `aprueba` | rutas saneadas; Facebook declarado como extracción intermedia y no como dato canónico final |
| `src/preprocessing/` | `aprueba` | logs reubicados a `artifacts/`; salidas canónicas alineadas con `data/raw` |
| `src/nlp/` | `aprueba` | prototipos y demos movidos a `legacy/`; naming activo saneado |
| `src/modeling/` | `aprueba` | separación física entre `core/`, `runners/`, `reporting/` y `tracking/` |
| `src/shared/` | `aprueba` | utilitarios mínimos y acotados |
| `src/operations/` | `aprueba` | capa reservada explícitamente; no se presenta como implementada |

## 3. Contradicciones resueltas

| Contradicción detectada | Resolución aplicada |
| --- | --- |
| la documentación describía `src/modeling/` como capa plana | se reestructuró físicamente y se reescribió la documentación |
| la documentación decía que la normalización activa ya estaba cerrada | se completó el saneamiento activo y se retiró el sobreclaim |
| existía runtime versionado en `src/` y `data/` | `__pycache__` salió de `src/`; logs y estado quedaron bajo `artifacts/` |
| `src/operations/` existía sin decir la verdad sobre su madurez | quedó declarado como capa reservada, opción A |
| `src/nlp/` mezclaba piezas activas con prototipos | los prototipos se movieron a `legacy/` y se documentó el wrapper de compatibilidad restante |
| los extractores y preprocessors usaban rutas personales hardcodeadas | se migraron a rutas relativas al repo |
| `experiments/` podía volver a leerse como cajón de sastre | se endurecieron reglas de frontera y retención |

## 4. Veredicto final

Marco correcto:

- no es sistema final automatizado
- sí es base canónica pre-automatización

Clasificación final del repo:

- **A. Base canónica pre-automatización ya cerrada**

La arquitectura ya quedó lo suficientemente limpia, coherente y gobernable para construir encima la automatización futura sin reabrir la mezcla estructural anterior.
