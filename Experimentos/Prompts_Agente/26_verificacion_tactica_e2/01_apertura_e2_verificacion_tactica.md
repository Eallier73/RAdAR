Nombre: Verificacion tactica corta de E2 / Huber posterior a E11

Objetivo:

- resolver si `E2` merece expansion posterior o solo cierre rapido como verificacion tactica;
- hacerlo sin abrir una rama larga ni duplicar corridas ya suficientes.

Decision metodologica de partida:

- si la evidencia tactica de `E2_v1_clean`, `E2_v2_clean` y `E2_v3_clean` ya responde la pregunta, no se re-corre por inercia;
- solo se corre una nueva variante si existe un hueco real de comparabilidad o trazabilidad.

Hipotesis minima:

- `Huber` podria cambiar algo relevante frente a outliers;
- si no cambia el balance global frente a `E1`, la familia queda cerrada.

Reglas:

- mantener comparabilidad con `E1`;
- no hacer grid grande;
- no hacer tuning expansivo;
- no promocionar mejoras parciales ambiguas;
- no reabrir `E2` como familia viva si la evidencia ya la cerro.

Salida esperada:

- `resumen_resultados_e2_verificacion_tactica.md`
- cierre explicito de si `E2` merece expansion o no
