# artifacts

Estatus: `runtime`

Proposito:

- centralizar artefactos tecnicos generados por ejecucion
- separar runtime del codigo y del dato canonico

Subarboles:

- `runs/`: salidas tecnicas de corridas operativas o auxiliares
- `logs/`: logs, reportes y trazabilidad generada
- `cache/`: cache descartable o regenerable
- `state/`: estado operativo persistente como tokens, snapshots o cursores

Lo que si vive aqui:

- archivos generados en runtime
- reportes temporales o tecnicos
- estado requerido para reanudar automatizaciones

Lo que no debe vivir aqui:

- codigo fuente
- datasets canonicos
- documentacion metodologica

Relacion con otras carpetas:

- `src/` escribe aqui todo lo efimero
- `data/` permanece limpio de runtime
- `experiments/` conserva evidencia metodologica, no estado tecnico operativo
