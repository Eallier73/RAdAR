# data

Estatus: `canonica_vigente`

Proposito:

- separar claramente el dato canonico del runtime tecnico
- distinguir insumo bruto, texto canonico, datasets procesados, referencias y externos

Subarboles canonicos:

- `raw/`: extraccion estructurada bruta o semi-bruta del Radar
- `text/`: corpus textual canonico por fuente y semana
- `processed/`: datasets listos para modelado y derivados estructurados
- `reference/`: diccionarios y recursos de referencia
- `external/`: insumos externos como encuestas

Lo que si vive aqui:

- insumos y salidas de datos reproducibles
- datasets canonicos que alimentan pipelines
- referencias y diccionarios versionables

Lo que no debe vivir aqui:

- logs
- cache
- estado de autenticacion
- reportes de corrida
- experimentos metodologicos

Relacion con otras carpetas:

- `src/` consume y produce datos canonicos aqui
- `artifacts/` guarda lo efimero que no debe contaminar `data/`
- `legacy/data/` encapsula materiales historicos fuera del flujo canonico
