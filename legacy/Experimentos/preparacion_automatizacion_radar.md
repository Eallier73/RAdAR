# Preparacion Automatizacion Radar

Fecha de actualizacion: `2026-04-03`

## Alcance

Este documento no implementa la automatizacion.
Define la arquitectura minima que la siguiente etapa debe automatizar sin reinterpretar el sistema vigente.

## Script maestro futuro

Script rector propuesto:

- [run_sistema_dual_operativo_radar.py](/home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_sistema_dual_operativo_radar.py)

Script auxiliar obligatorio:

- [run_benchmarks_operativos_vigentes.py](/home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_benchmarks_operativos_vigentes.py)

## Pipeline futuro propuesto

1. validar integridad operativa:
   - `run_benchmarks_operativos_vigentes.py --validate --strict`
2. reejecutar benchmarks oficiales solo cuando la politica de mantenimiento lo requiera
3. empaquetar salidas:
   - `run_sistema_dual_operativo_radar.py --strict`
4. publicar o consumir los artefactos generados
5. registrar logs, warnings y estados finales

## Entradas

- `registro_operacion_controlada_radar.json`
- `inventario_experimentos_radar.json`
- `tabla_maestra_experimentos_radar.xlsx`
- `grid_experimentos_radar.xlsx`
- runs congelados de `E1_v5_clean` y `E9_v2_clean`

## Salidas obligatorias

- `prediccion_numerica_oficial.csv`
- `lectura_direccional_oficial.csv`
- `alertas_caida_oficiales.csv`
- `salida_dual_operativa_consolidada.csv`
- `tabla_funcional_canonica.csv`
- `politica_funcional_dual.csv`
- `manifiesto_operativo_dual.json`
- `resumen_operativo_dual.md`

## Validaciones minimas de una corrida automatizada

Bloqueantes:

- auditoria operativa con `gaps_total > 0`
- ausencia de artefactos base de benchmarks
- ausencia de snapshots
- mismatch entre registry, inventario y workbook maestro
- imposibilidad de generar el paquete dual completo

Warnings permitidos:

- diferencias de cobertura entre las capas oficiales
- metadata historica parcial si el tracker y el snapshot preservan trazabilidad suficiente

## Logging y control de errores

La automatizacion debe:

- registrar inicio, fin y duracion de cada bloque;
- distinguir errores bloqueantes de warnings;
- guardar logs con timestamp;
- persistir el estado final de la corrida automatizada.

## Reporteo futuro

Sin implementarlo todavia, la siguiente etapa debe contemplar:

- reporte resumido de corrida valida
- reporte de cobertura por horizonte
- reporte de gaps
- reporte de diferencias frente a benchmarks congelados cuando exista reejecucion controlada

## Regla de gobierno

La automatizacion futura no puede redefinir:

- la politica dual congelada;
- los benchmarks vigentes;
- la evaluacion temporal;
- ni la lectura funcional del sistema.

Su tarea sera ejecutar y verificar, no reinterpretar.
