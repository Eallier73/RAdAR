# Operacional Controlada

Este directorio separa la capa operativa controlada de la capa experimental del Radar.

Principio:

- la logica metodologica canonica sigue viviendo en `Scripts/Modeling/`
- la capa operativa controlada no redefine modelos ni evaluacion
- solo congela que referentes vigentes pueden ejecutarse de manera estable y trazable

Benchmarks operativos vigentes:

- numerico puro: `E1_v5_clean`
- riesgo-direccion-caidas: `E9_v2_clean`
- sistema dual / funcional vigente:
  - salida numerica principal: `E1_v5_clean`
  - deteccion de caidas: `E9_v2_clean`
  - direction por horizonte: `9-1-9-1`

Fuente canonica de referencia:

- `/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_dual_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/registro_operacion_controlada_radar.json`

Script utilitario:

- `run_benchmarks_operativos_vigentes.py`
- `run_sistema_dual_operativo_radar.py`

Paquete operativo dual canonico:

- `/home/emilio/Documentos/RAdAR/Experimentos/operacion_dual_controlada/paquete_vigente/prediccion_numerica_oficial.csv`
- `/home/emilio/Documentos/RAdAR/Experimentos/operacion_dual_controlada/paquete_vigente/lectura_direccional_oficial.csv`
- `/home/emilio/Documentos/RAdAR/Experimentos/operacion_dual_controlada/paquete_vigente/alertas_caida_oficiales.csv`
- `/home/emilio/Documentos/RAdAR/Experimentos/operacion_dual_controlada/paquete_vigente/salida_dual_operativa_consolidada.csv`
- `/home/emilio/Documentos/RAdAR/Experimentos/operacion_dual_controlada/paquete_vigente/manifiesto_operativo_dual.json`

Validacion y auditoria operativa:

- `run_benchmarks_operativos_vigentes.py --validate --strict`
- `run_sistema_dual_operativo_radar.py --strict`
- reporte JSON: `/home/emilio/Documentos/RAdAR/Experimentos/auditoria_benchmarks_operativos_controlados.json`
- reporte Markdown: `/home/emilio/Documentos/RAdAR/Experimentos/auditoria_benchmarks_operativos_controlados.md`

Gobernanza asociada:

- `/home/emilio/Documentos/RAdAR/Experimentos/consolidacion_operativa_post_produccion_controlada.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/politica_operativa_sistema_dual_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/preparacion_automatizacion_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/verificacion_reproducibilidad_dual_controlada.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/politica_promocion_sistemas_radar.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/cierre_formal_e10_no_promocionable.md`
- `/home/emilio/Documentos/RAdAR/Experimentos/especificacion_futura_e11_dual.md`

Reglas:

- no reemplazar los runners canonicos de `Scripts/Modeling/`
- no simplificar validacion temporal
- no introducir atajos metodologicos por “operacion”
- no reinterpretar la politica fija `9-1-9-1` como mezcla dinamica
- cualquier cambio en esta capa debe tratarse como cambio controlado y documentado
