# Repository Architecture

Arquitectura vigente del repositorio RAdAR entendida como base canónica pre-automatización.

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
| preprocessing | implementada | completa semanas, mueve insumos y normaliza outputs |
| NLP | implementada | sentimiento, diccionarios, clasificación y ensamblado de variables |
| modeling | implementada | núcleo reusable con `core/`, `runners/`, `reporting/`, `tracking/` |
| shared | implementada | utilitarios transversales mínimos |
| docs/data/artifacts/experiments/legacy | implementados | capas ya separadas y gobernadas |

## 3. Arquitectura futura o reservada

| Capa | Estado | Notas |
| --- | --- | --- |
| `src/operations/` | reservada | namespace para futura automatización integral |
| orquestación end-to-end | no implementada | no existe capa final de scheduling o pipeline completo |
| wrappers operativos finales | no implementados | el repo aún no expone una fachada única de operación |

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

La carpeta existe, pero no debe interpretarse como capa operativa implementada.
Su función actual es reservar el namespace y evitar que la futura automatización vuelva a nacer desordenada en la raíz o dentro de `experiments/`.
