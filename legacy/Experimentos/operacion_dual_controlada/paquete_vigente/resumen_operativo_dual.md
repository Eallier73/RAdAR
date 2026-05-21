# Resumen Operativo Dual Radar

- `fase_operativa`: `produccion_controlada_dual`
- `estado_operativo`: `vigente`
- `modelo_unico_final`: `False`
- `output_dir`: `/home/emilio/Documentos/RAdAR/Experimentos/operacion_dual_controlada/paquete_vigente`

## Politica Funcional Congelada

- Salida numerica principal: `E1_v5_clean`
- Deteccion de caidas: `E9_v2_clean`
- Direction H1: `E9_v2_clean`
- Direction H2: `E1_v5_clean`
- Direction H3: `E9_v2_clean`
- Direction H4: `E1_v5_clean`

## Artefactos Canonicos

- `prediccion_numerica_oficial.csv`: `98` fila(s)
- `lectura_direccional_oficial.csv`: `74` fila(s)
- `alertas_caida_oficiales.csv`: `50` fila(s)
- `salida_dual_operativa_consolidada.csv`: `98` fila(s)
- `tabla_funcional_canonica.csv`
- `politica_funcional_dual.csv`
- `manifiesto_operativo_dual.json`

## Reglas de Lectura

- `prediccion_numerica_oficial.csv` es la salida principal del sistema.
- `lectura_direccional_oficial.csv` reporta la politica fija 9-1-9-1 por horizonte.
- `alertas_caida_oficiales.csv` reporta la capa oficial de caidas desde `E9_v2_clean`.
- `salida_dual_operativa_consolidada.csv` integra las tres capas sin fingir un modelo unico.