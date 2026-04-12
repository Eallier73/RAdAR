# Repository Architecture

## Criterio rector

La arquitectura canonica del repo se organiza por responsabilidad y por estado de vida:

- codigo activo
- datos canonicos
- runtime tecnico
- experimentacion
- documentacion
- legacy

## Estructura canonica

```text
RAdAR/
├── src/
│   ├── extraction/
│   │   └── runners/
│   ├── preprocessing/
│   ├── nlp/
│   ├── modeling/
│   ├── operations/
│   └── shared/
├── data/
│   ├── raw/
│   │   └── radar_weekly_flat/
│   ├── text/
│   │   └── radar_weekly_flat/
│   ├── processed/
│   │   └── modeling/
│   ├── reference/
│   │   └── dictionaries_nlp/
│   └── external/
│       └── surveys/
├── artifacts/
│   ├── runs/
│   ├── logs/
│   ├── cache/
│   └── state/
├── experiments/
│   ├── prompts/
│   ├── research/
│   ├── audit/
│   └── runs/
├── docs/
│   ├── architecture/
│   ├── operations/
│   └── migration/
└── legacy/
    ├── code/
    │   └── extraction_variants/
    └── data/
        └── pppp/
```

## Donde va cada cosa nueva

- nuevo codigo activo: `src/`
- nuevo dataset canonico: `data/`
- nuevo log, estado o cache: `artifacts/`
- nueva bitacora, plan o auditoria metodologica: `experiments/`
- nueva documentacion de arquitectura u operacion: `docs/`
- codigo o dato jubilado pero valioso: `legacy/`

## Rutas historicas retiradas

- `Scripts/`
- `Datos_RAdAR/`
- `Datos_RadaR_Texto/`
- `Experimentos/`
- `Datos_Modelo_ML/`
- `Diccionarios_NLP/`
- `Encuestas/`

Esas rutas ya no son canonicas ni siguen vivas en el arbol actual.

La migracion controlada ya retiro esas capas puente. Cualquier automatizacion nueva debe apuntar directamente a `src/`, `data/`, `artifacts/`, `experiments/`, `docs/` o `legacy/`.

## Convencion de nombres

- carpetas nuevas en minusculas, `snake_case` y ASCII
- nombres historicos de archivos se conservan cuando cambiarlo arriesga compatibilidad
- la normalizacion fuerte se aplica en la arquitectura, no por renombre masivo caprichoso de cada script legado

## Politica de crecimiento

1. No agregar scripts nuevos en la raiz.
2. No mezclar runtime con `data/`.
3. No mezclar operacion vigente con `experiments/`.
4. No rescatar carpetas deprecated como base estructural.
5. Toda nueva ruta estructural debe poder clasificarse como una de estas: `canonica_vigente`, `operativa_vigente`, `experimental`, `runtime`, `legacy`, `documental`.
