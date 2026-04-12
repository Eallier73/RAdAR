# Preparacion de tabla E9 stacking controlado

## Objetivo

Preparar la tabla maestra del proyecto Radar para la familia `E9` como stacking clasico controlado por horizonte, sin entrenar todavia el meta-modelo y sin romper la arquitectura vigente por familias.

## Alcance

Esta etapa SI debe:

- preservar la tabla maestra original como universo maestro;
- construir una copia curada y versionada para `E9`;
- distinguir entre universo maestro, candidatos elegibles y base operativa final;
- documentar constructos, reglas de inclusion y reglas de exclusion;
- dejar bases pequenas por horizonte listas para alimentar un `run_e9_stacking.py` posterior;
- mantener compatibilidad con `experiment_logger.py`, `pipeline_common.py`, `evaluation.py` y el tracker vigente.

Esta etapa NO debe:

- entrenar el stacking final;
- mezclar predicciones in-sample con OOF;
- meter todos los runs solo porque existen;
- fabricar un ensemble ex post con ganadores por horizonte sin reglas;
- mezclar corridas canonicas con intentos fallidos o trazabilidad dudosa.

## Reglas metodologicas

- usar solo predicciones OOF comparables por horizonte;
- exigir trazabilidad suficiente para todo run considerado;
- excluir variantes dominadas, colapsadas o redundantes sin diversidad real;
- mantener una base pequena por horizonte:
  - ideal `3 a 5` candidatos;
  - maximo razonable `6`;
- documentar explicitamente:
  - por que entra cada candidato;
  - por que sale cada candidato;
  - que constructo representa dentro de `E9`.

## Hojas requeridas

La salida curada debe dejar, como minimo:

- `E9_curacion_resumen`
- `E9_diccionario_constructos`
- `E9_metricas_candidatos`
- `E9_diagnostico_h1`
- `E9_diagnostico_h2`
- `E9_diagnostico_h3`
- `E9_diagnostico_h4`
- `E9_base_h1`
- `E9_base_h2`
- `E9_base_h3`
- `E9_base_h4`
- `E9_bases_resumen`

## Constructos obligatorios

- `campeon global de familia`
- `referencia parsimoniosa`
- `especialista de horizonte`
- `candidato reserva`
- `run dominado`
- `run no preferible para ensemble principal`

## Criterio final esperado

La tabla curada debe dejar preparado el terreno para `E9`, pero sin mezclarlo todavia con una familia posterior tipo meta-selector contextual.

Si hay duda entre meter mas columnas o dejar una base mas limpia, debe preferirse la base mas limpia siempre que no sacrifique diversidad util.
