# src

Estatus: `canonica_vigente`

Proposito:

- concentrar todo el codigo fuente activo del repositorio
- separar el codigo por responsabilidad real
- evitar que nuevos scripts se acumulen en raices ambiguas

Lo que si vive aqui:

- `extraction/`: extractores activos y runners de adquisicion
- `preprocessing/`: organizacion, limpieza y transformacion previa al modelado
- `nlp/`: construccion de variables textuales, diccionarios y clasificacion tematica
- `modeling/`: pipeline experimental/modelado reusable del Radar
- `shared/`: utilitarios comunes y logging runtime reutilizable

Lo que no debe vivir aqui:

- datasets
- outputs generados
- logs
- cache
- auditorias experimentales en Excel o CSV
- legacy historico

Relacion con otras carpetas:

- lee insumos canonicos desde `data/`
- escribe runtime en `artifacts/`
- consume y documenta experimentacion en `experiments/`
- referencia arquitectura y migracion en `docs/`

Regla de gobierno:

- nuevo codigo activo entra en `src/`
- nuevos wrappers de compatibilidad no deben convertirse en canonicos
- las rutas historicas tipo `Scripts/` ya fueron retiradas del arbol canonico
