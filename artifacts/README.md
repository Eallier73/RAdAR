# artifacts

Estatus: `runtime`

`artifacts/` absorbe todo lo efímero o técnico que no debe contaminar `src/` ni `data/`.

## Subárboles

- `logs/`: logs, reportes técnicos y trazabilidad operativa
- `cache/`: cache regenerable
- `runs/`: workdirs y salidas técnicas auxiliares
- `state/`: sesiones, cursores y snapshots operativos

## Política de versionado

- sí se versionan `README.md`, `.gitkeep` y archivos `*.example.*`
- no se versionan sesiones reales, logs generados, caches vivos ni workdirs de extracción

Ejemplos:

- `artifacts/state/x_state.json`: no versionado
- `artifacts/state/x_state.example.json`: sí versionado
- `artifacts/logs/preprocessing/*.csv`: no versionado
- `artifacts/runs/extraction/facebook/*`: no versionado
