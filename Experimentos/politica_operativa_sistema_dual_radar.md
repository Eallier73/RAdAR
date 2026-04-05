# Politica Operativa Sistema Dual Radar

Fecha de actualizacion: `2026-04-03`

## Objeto

Esta politica define como debe leerse y usarse el sistema operativo dual vigente del Radar.

## Componentes oficiales

- forecast numerico oficial: `E1_v5_clean`
- alerta oficial de caida: `E9_v2_clean`
- lectura direccional oficial por horizonte:
  - `H1 = E9_v2_clean`
  - `H2 = E1_v5_clean`
  - `H3 = E9_v2_clean`
  - `H4 = E1_v5_clean`

## Reglas de uso

1. La salida numerica principal siempre se toma desde `E1_v5_clean`.
2. La capa de caidas siempre se toma desde `E9_v2_clean`.
3. La lectura direccional se reporta con politica fija `9-1-9-1`.
4. Ninguna salida debe reinterpretarse como mezcla dinamica o seleccion online.
5. Si una capa falta en una fecha/horizonte, la corrida operativa debe reportar cobertura incompleta y no inventar sustituciones.

## Salidas oficiales

### Salida principal

- archivo canonico: `prediccion_numerica_oficial.csv`
- fuente: `E1_v5_clean`
- valor operacional: forecast numerico oficial del Radar

### Salida direccional

- archivo canonico: `lectura_direccional_oficial.csv`
- fuente: politica fija por horizonte `9-1-9-1`
- valor operacional: lectura funcional de direccion por horizonte

### Salida de caidas

- archivo canonico: `alertas_caida_oficiales.csv`
- fuente: `E9_v2_clean`
- valor operacional: alerta oficial de deterioro / caida

### Salida consolidada

- archivo canonico: `salida_dual_operativa_consolidada.csv`
- valor operacional: integra capa numerica, direccional y de caidas sin fingir un modelo unico

## Reglas de no promocion

- ninguna recombinacion ex post promociona nada;
- ninguna mejora parcial en una sola metrica reemplaza a la politica vigente;
- toda sustitucion futura exige comparacion completa contra el sistema dual, no solo contra una capa aislada.

## Politica de reejecucion controlada

- los benchmarks oficiales pueden reejecutarse solo para verificacion controlada de reproducibilidad;
- una reejecucion verificada no reemplaza automaticamente al benchmark congelado;
- si la reejecucion cambia resultados de forma material, debe abrirse incidente metodologico antes de cualquier uso operativo.

## Politica de warnings y bloqueos

Una corrida operativa dual debe bloquearse si ocurre cualquiera de estos casos:

- falta `metadata_run.json`, `parametros_run.json`, `metricas_horizonte.json` o `resumen_modeling_horizontes.json` en un benchmark oficial;
- faltan `predicciones_h1..h4.csv`;
- falta snapshot de scripts del benchmark;
- el registry, el inventario y la tabla maestra no coinciden en benchmark vigente;
- faltan las hojas `tabla_funcional_dual_vigente` o `politica_funcional_dual_vigente`.

Warnings admisibles:

- metadata historica con campos incompletos si el grid y el snapshot preservan trazabilidad suficiente;
- diferencias de cobertura entre `E1` y `E9`, siempre que se reporten explicitamente.
