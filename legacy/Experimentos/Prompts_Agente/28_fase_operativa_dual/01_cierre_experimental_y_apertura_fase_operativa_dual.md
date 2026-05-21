# Cierre Experimental y Apertura de Fase Operativa Dual

Fecha de archivo: `2026-04-03`

## Instruccion rectora

Se cierra temporalmente la expansion experimental del proyecto Radar y se abre una fase operativa / produccion controlada dual.

Base canonica:

- `E1_v5_clean` como salida numerica principal
- `E9_v2_clean` como capa oficial de deteccion de caidas
- politica direccional fija `9-1-9-1`
  - `H1 = E9_v2_clean`
  - `H2 = E1_v5_clean`
  - `H3 = E9_v2_clean`
  - `H4 = E1_v5_clean`

## Alcance exigido

- congelar formalmente el sistema dual vigente;
- dejar evidencia de reproducibilidad fuerte o reejecucion controlada;
- crear documentacion canonica operativa;
- definir empaquetado estable de salidas;
- dejar lista la transicion a automatizacion sin implementarla todavia.

## Restricciones

- no abrir nuevas familias experimentales;
- no reabrir `E12`;
- no promocionar combinaciones ex post por horizonte;
- no introducir una mezcla dinamica online;
- no perder trazabilidad ni comparabilidad historica.

## Entregables pedidos

- `fase_produccion_controlada_dual_radar.md`
- `politica_operativa_sistema_dual_radar.md`
- `preparacion_automatizacion_radar.md`
- actualizaciones en plan, bitacora y README(s)
- empaquetado operativo canónico
- evidencia de reejecucion controlada de benchmarks congelados
