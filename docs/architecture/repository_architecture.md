# Repository Architecture

Arquitectura vigente del repositorio RAdAR entendida como base canónica operable con orquestación controlada.

## 1. Estructura de raíz

```text
RAdAR/
├── src/
│   ├── extraction/
│   ├── preprocessing/
│   ├── nlp/
│   ├── modeling/
│   ├── shared/
│   └── operations/
├── data/
├── artifacts/
├── docs/
├── experiments/
└── legacy/
```

## 2. Arquitectura actual vigente

| Capa | Estado | Notas |
| --- | --- | --- |
| extracción | implementada | runners por fuente; Facebook deja artefactos intermedios en `artifacts/` |
| preprocessing | implementada | expone CLIs activas y un wrapper parcial de stage; no es una capa final de operación |
| NLP | implementada | sentimiento, diccionarios, clasificación y ensamblado de variables |
| modeling | implementada | núcleo reusable con `core/`, `runners/`, `reporting/`, `tracking/` |
| shared | implementada | utilitarios transversales mínimos |
| operations | implementada | orquestador operativo manual, trazable, reanudable y con estado persistente |
| docs/data/artifacts/experiments/legacy | implementados | capas ya separadas y gobernadas |

## 3. Arquitectura posterior o no cerrada

| Capa | Estado | Notas |
| --- | --- | --- |
| scheduling | no implementado | la CLI operativa todavía se dispara manualmente |
| automatización periódica | no implementada | cron/systemd/Airflow/GitHub Actions quedan fuera de esta capa |
| reporte final | no implementado | `report` deja un stub controlado con insumos publicados |

## 4. `src/modeling/` como núcleo técnico

`src/modeling/` es hoy la capa más madura del repo.
Su estructura física vigente es:

```text
src/modeling/
├── core/
├── runners/
├── reporting/
└── tracking/
```

Esto separa:

- lógica reusable
- entrypoints por familia
- construcción de tablas y reportes
- tracking experimental

## 5. `src/operations/`

La carpeta ya implementa la capa operativa controlada del repo.
Su función es coordinar el pipeline canónico mediante etapas explícitas, persistir estado por corrida y dejar artefactos auditables en `artifacts/operations/`.
