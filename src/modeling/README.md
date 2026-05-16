# modeling

Estatus: `codigo_activo_canonico`

`src/modeling/` es el núcleo técnico vigente del repo.
Ya no se documenta como una capa plana: la separación `core/`, `runners/`, `reporting/` y `tracking/` existe físicamente en disco y define la estructura canónica de modelado.

## Subcapas

- `core/`: configuración, carga del dataset maestro, feature engineering, evaluación y utilitarios reutilizables
- `runners/`: entrypoints por familia de modelos y pipelines comunes
- `reporting/`: builders de tablas maestras y backfills metodológicos
- `tracking/`: logger y control de trazabilidad experimental

## Criterio de organización

- las familias viven por responsabilidad técnica, no por corrida individual ad hoc
- los runners delegan la lógica reusable a `core/`
- `reporting/` y `tracking/` no se mezclan con entrenamiento
- los artefactos de corrida viven en `experiments/` y `artifacts/`, no aquí

## Ejecución

La forma canónica de ejecutar runners es como módulos de paquete, por ejemplo:

```bash
python -m src.modeling.runners.run_e5_catboost
python -m src.modeling.runners.run_c1_random_forest_classifier
```

## Compatibilidad

- `src/nlp/experiment_logger.py` es un wrapper explícito hacia `src/modeling/tracking/experiment_logger.py`
- no deben reaparecer rutas históricas como `Scripts/Modeling/*`
