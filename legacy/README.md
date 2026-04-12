# legacy

Estatus: `legacy`

Proposito:

- encapsular codigo y datos historicos que siguen teniendo valor de consulta
- sacarlos del flujo canonico sin borrarlos

Lo que si vive aqui:

- variantes historicas de extractores
- datos archivados o proyectos paralelos ya fuera de la arquitectura destino

Lo que no debe vivir aqui:

- nuevas implementaciones
- codigo activo canonico
- datos operativos vigentes

Relacion con otras carpetas:

- `src/` contiene el flujo activo
- `legacy/` conserva referencias historicas y compatibilidad documental

Regla de gobierno:

- si algo nuevo nace hoy, no entra a `legacy/`
- si algo se mueve aqui, debe quedar claro por que ya no es canonico
