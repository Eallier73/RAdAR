# Fase de Produccion Controlada Radar

Fecha de actualizacion: `2026-04-03`

## Proposito

Este documento fija la entrada del proyecto Radar a una fase de produccion controlada.

Nota de alcance posterior:

- Este documento sigue siendo canonico para explicar por que el proyecto entro a produccion controlada.
- Su formulacion original precede a la primera apertura dual real de `E11`.
- Tambien precede al cierre temporal de expansion experimental y a la apertura formal de la fase operativa dual vigente.
- El estado canonico posterior de `E11` debe leerse hoy junto con:
  - [resumen_metodologico_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e11_dual.md)
  - [plan_de_experimentacion_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/plan_de_experimentacion_radar.md)
  - [bitacora_experimental_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/bitacora_experimental_radar.md)
- La etapa vigente de sistema operativo compuesto debe leerse hoy junto con:
  - [fase_produccion_controlada_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/fase_produccion_controlada_dual_radar.md)
  - [politica_operativa_sistema_dual_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/politica_operativa_sistema_dual_radar.md)
  - [preparacion_automatizacion_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/preparacion_automatizacion_radar.md)

No declara un cierre del proyecto ni un modelo final unico. Su funcion es:

- congelar la infraestructura madura del pipeline,
- separar con claridad la capa experimental de la capa operativa,
- formalizar los benchmarks vigentes,
- y preparar el puente hacia una arquitectura dual que en ese momento todavia no habia sido ejecutada y que luego tuvo una primera apertura controlada.

## Por que si entra a produccion controlada

La evidencia acumulada ya es suficiente para operar con referentes vigentes estables y trazables:

- `E1_v5_clean` como benchmark numerico puro principal
- `E9_v2_clean` como benchmark operativo de riesgo-direccion-caidas

Ademas, la infraestructura comun del proyecto ya esta suficientemente madura:

- dataset maestro estable
- construccion homogenea del model frame
- validacion temporal correcta
- metricas Radar por horizonte
- tracker y artefactos por run
- auditoria maestra e inventario retrospectivo

## Por que todavia no entra a produccion final unificada

La evidencia vigente no sostiene una arquitectura ganadora unica.

Hechos relevantes:

- `E1_v5_clean` sigue siendo el mejor referente numerico puro
- `E9_v2_clean` sigue siendo el mejor referente operativo de riesgo, direccion y caidas
- `E10_v1_clean` ya fue corrido y no desplazo a los benchmarks centrales; su formulacion actual queda cerrada para promocion
- `E11` ya fue abierta con tres variantes duales controladas, pero sigue sin constituir una solucion validada ni promocionable
- la clasificacion existe como rama real, pero no esta consolidada
- la explicabilidad transversal sigue siendo parcial intra-familia

## Dualidad funcional vigente

El Radar debe leerse, de forma explicita, en dos planos funcionales:

### 1. Plano numerico

Pronostico del porcentaje o nivel esperado del Radar.

Benchmark vigente:

- `E1_v5_clean`

### 2. Plano operativo

Lectura del movimiento del Radar, con prioridad especial en direccion y deteccion de caidas.

Benchmark vigente:

- `E9_v2_clean`

Conclusión canónica:

`E1_v5_clean` no reemplaza a `E9_v2_clean`, y `E9_v2_clean` no reemplaza a `E1_v5_clean`.
Ambos cumplen funciones distintas y complementarias dentro del Radar.

## Separacion de capas

### Capa experimental

Alcance:

- seguir corriendo familias nuevas o hipotesis nuevas bajo el estandar metodologico completo del proyecto

Reglas:

- validacion temporal correcta
- comparabilidad fuerte
- artefactos completos por run
- prohibicion estricta de leakage

Estado:

- activa

### Capa operativa controlada

Alcance:

- ejecutar de manera estable y trazable los benchmarks vigentes sin cambiar su logica experimental canonica

Benchmarks congelados:

- numerico puro: `E1_v5_clean`
- operativo riesgo-direccion-caidas: `E9_v2_clean`

Estado:

- activa

Implementacion visible:

- registro canónico: [registro_operacion_controlada_radar.json](/home/emilio/Documentos/RAdAR/Experimentos/registro_operacion_controlada_radar.json)
- dispatcher operativo: [run_benchmarks_operativos_vigentes.py](/home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/run_benchmarks_operativos_vigentes.py)
- capa operativa: [README.md](/home/emilio/Documentos/RAdAR/Scripts/Operational_Controlada/README.md)

### Capa futura dual

Alcance:

- arquitectura `E11` para resolver en una sola arquitectura la dualidad numerica + categorica/operativa

Estado:

- evaluada sin promocion

## Que se congela

Se congela como infraestructura madura, salvo correcciones criticas controladas:

- carga del dataset maestro
- construccion del model frame
- helpers comunes de features y preprocessing
- evaluacion Radar
- tracker
- builders de auditoria maestra e inventario
- arquitectura por familias y estandar de artefactos

Regla:

todo cambio futuro sobre esta infraestructura comun debe quedar versionado y documentado como cambio controlado, no como ajuste informal de experimento.

## Que sigue experimental

- `E10`: corrido y cerrado para promocion bajo su formulacion actual
- `E11`: familia dual ya ejecutada, todavia no promocionable
- `C1-C4`: rama existente pero no consolidada
- cualquier nueva hipotesis que busque desplazar a `E1_v5_clean` o `E9_v2_clean`

## Politica de benchmarks vigentes

Se reconocen formalmente como benchmarks operativos vigentes:

- benchmark numerico puro: `E1_v5_clean`
- benchmark operativo de riesgo-direccion-caidas: `E9_v2_clean`

Ambos deben seguir registrandose y auditandose bajo el mismo tracker y el mismo estandar de artefactos.

## Politica de promocion futura

Un sistema futuro solo podra considerarse promovible si mejora de forma defendible la funcion dual del Radar.

Esto exige leer dos planos:

- componente numerico:
  - `MAE`
  - `RMSE`
  - `loss_h`
  - `L_total_Radar`
- componente operativo:
  - `direction_accuracy`
  - `deteccion_caidas`
  - lectura de cambios
  - robustez en la anticipacion de bajas

No se podra declarar superioridad futura solo por bajar error numerico marginal si eso deteriora la funcion operativa del sistema.

Documentos de continuacion operativa:

- [consolidacion_operativa_post_produccion_controlada.md](/home/emilio/Documentos/RAdAR/Experimentos/consolidacion_operativa_post_produccion_controlada.md)
- [cierre_formal_e10_no_promocionable.md](/home/emilio/Documentos/RAdAR/Experimentos/cierre_formal_e10_no_promocionable.md)
- [especificacion_futura_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/especificacion_futura_e11_dual.md)
- [resumen_metodologico_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e11_dual.md)

## Estado de familias bajo esta fase

- `E1`: cerrada como familia principal; benchmark numerico vigente
- `E9`: util y pausada metodologicamente; benchmark operativo vigente
- `E10`: corrida real ya evaluada y cerrada para promocion
- `E11`: evaluada sin promocion; primera apertura dual ya ejecutada
- `C1`: corrida real y pausa temprana
- `C2-C4`: infraestructura preparada sin corrida

## Cierre

El proyecto Radar si puede entrar a una fase de produccion controlada de infraestructura y operacion comparativa, pero todavia no a una fase de produccion predictiva final unificada, porque la evidencia vigente sostiene una dualidad funcional no resuelta todavia en una sola arquitectura ganadora.
