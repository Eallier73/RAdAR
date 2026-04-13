# src

Estatus: `codigo_activo_canonico`

`src/` contiene únicamente código fuente activo del proyecto.
No debe contener datasets, logs, cache, estado técnico, auditorías en Excel/CSV ni arrastre histórico.

## Subárboles vigentes

- `extraction/`: adquisición activa por fuente
- `preprocessing/`: promoción, normalización y saneamiento de insumos
- `nlp/`: construcción de variables textuales, diccionarios y clasificación temática
- `modeling/`: núcleo técnico vigente de modelado, tracking y reporting experimental
- `shared/`: utilitarios transversales mínimos
- `operations/`: capa reservada para automatización futura; hoy no implementada

## Reglas

- `src/` lee datos canónicos desde `data/`
- `src/` escribe runtime en `artifacts/`
- `src/` nunca escribe estado o logs dentro de sí mismo
- las rutas históricas tipo `Scripts/` no son canónicas
- cualquier wrapper transitorio debe declararse explícitamente

La decisión arquitectónica vigente sobre `src/operations/` es la opción A:
capa reservada para futura automatización integral, todavía no implementada.
