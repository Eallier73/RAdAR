# artifacts/state

Estatus: `runtime`

Este directorio guarda estado operativo persistente pero no canónico, por ejemplo:

- sesiones autenticadas para extractores
- cursores o checkpoints de reanudación
- snapshots técnicos necesarios para continuar una adquisición manual

Reglas:

- el archivo real `x_state.json` no se versiona
- el único JSON permitido en git es `x_state.example.json`
- ningún script de `src/` debe escribir aquí código, datos canónicos ni reportes
