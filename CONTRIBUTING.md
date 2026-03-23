# Convencion de Ramas

Este repositorio usa una convencion simple para separar lo estable de lo experimental.

## Ramas

- `main`
  Estado estable del proyecto. Aqui solo entran cambios ya validados.
- `dev`
  Rama de integracion para trabajo en curso antes de pasar a `main`.
- `feature/<tema>`
  Rama corta para una tarea concreta, por ejemplo:
  - `feature/e2-huber`
  - `feature/e3-random-forest`
  - `feature/grid-tracker`
  - `feature/docs-prompts`

## Flujo recomendado

1. Partir desde `dev` para trabajo nuevo.
2. Crear una rama `feature/<tema>`.
3. Hacer commits pequenos y descriptivos.
4. Integrar la rama a `dev` cuando el cambio este consistente.
5. Pasar de `dev` a `main` solo cuando el cambio ya sea estable.

## Criterio practico para Radar

- Cambios metodologicos o de pipeline: `feature/<tema>`
- Corridas experimentales: registrar artefactos fuera de Git y subir solo codigo, prompts y configuracion
- `main` no debe usarse para trabajo improvisado
