# Especificacion E11 Dual: documento base y lectura posterior

Fecha de actualizacion: `2026-04-03`

## Estado vigente

Este documento conserva la especificacion base con la que se abrio `E11`.

Actualizacion posterior:

- `E11` ya fue ejecutada en una primera apertura dual controlada:
  - [E11_v1_clean_20260403_051406](/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v1_clean_20260403_051406)
  - [E11_v2_clean_20260403_051823](/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v2_clean_20260403_051823)
  - [E11_v3_clean_20260403_051823](/home/emilio/Documentos/RAdAR/Experimentos/runs/E11_v3_clean_20260403_051823)
- La familia queda `evaluada sin promocion` en su primera apertura dual.
- `E11_v2_clean` fue la mejor apertura interna.
- El estado canonico posterior debe leerse junto con [resumen_metodologico_e11_dual.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e11_dual.md).

Lectura vigente:

- `E11` ya no es solo arquitectura futura abstracta.
- No debe confundirse con una extension natural de `E10`.
- No debe presentarse como solucion vigente del Radar.

## Problema que intentaria resolver

La evidencia vigente sostiene una dualidad funcional real:

- `E1_v5_clean` resuelve mejor el plano numerico puro;
- `E9_v2_clean` resuelve mejor el plano operativo de direccion y deteccion de caidas.

`E11` solo tendria sentido si logra resolver de forma defendible esa dualidad en una arquitectura compuesta y evaluable.

## Entradas esperadas

La arquitectura `E11` deberia consumir, como minimo:

- dataset maestro del Radar bajo el mismo estandar temporal canonico;
- señales numericas comparables con las usadas en regresion;
- señales categóricas o direccionales observables en tiempo `t`;
- artefactos compatibles con el mismo tracker y la misma auditoria maestra.

## Salidas esperadas

`E11` deberia producir dos salidas coordinadas:

1. una salida numerica:
   - porcentaje, nivel o cambio esperado del Radar;
2. una salida categórica/operativa:
   - direccion,
   - baja,
   - mantenimiento,
   - o una taxonomia futura equivalente bien justificada.

## Evaluacion minima exigida

`E11` no deberia evaluarse solo por una metrica unica.

Debe competir al menos contra:

- `E1_v5_clean` en el plano numerico;
- `E9_v2_clean` en el plano operativo;
- y cualquier arquitectura compuesta intermedia solo si es temporalmente comparable.

Variables minimas:

- `MAE`
- `RMSE`
- `loss_h`
- `L_total_Radar`
- `direction_accuracy`
- `deteccion_caidas`
- estabilidad por horizonte
- lectura clara del costo metodologico agregado

## Criterio para reemplazar la salida dual vigente

`E11` solo podria reemplazar la salida dual actual si:

- mejora de forma defendible el benchmark numerico o al menos no lo degrada severamente;
- mejora de forma defendible el benchmark operativo o al menos no lo degrada severamente;
- demuestra comparabilidad fuerte, reproducibilidad y trazabilidad total;
- y su complejidad adicional se justifica con evidencia real, no con narrativa de elegancia arquitectonica.

## Riesgos metodologicos principales

- leakage entre salidas numericas y categóricas;
- pseudo-validacion por mezclar objetivos dentro del mismo periodo de forma indebida;
- sobreajuste por tratar de resolver demasiado con muestra aun limitada;
- promocion prematura por intuicion narrativa;
- confusion entre coexistencia funcional y superioridad unificada real.

## Regla de disciplina

`E11` debe permanecer como arquitectura futura hasta que exista:

- una especificacion operacional cerrada;
- una tabla o pipeline de datos sin leakage para ambas salidas;
- y una corrida propia evaluada bajo el mismo estandar temporal del proyecto.
