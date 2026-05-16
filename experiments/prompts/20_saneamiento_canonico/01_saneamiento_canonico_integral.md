# Saneamiento canonico integral del estado experimental Radar

## Objetivo

Ejecutar un saneamiento documental y metodologico integral del proyecto Radar para que plan, bitacora, inventario, tabla maestra y README(s) canónicos describan exactamente el mismo estado real de la experimentacion.

## Mandato

- No abrir nuevas familias.
- No correr nueva experimentacion salvo regeneracion minima de auditoria y metadatos.
- No borrar historia.
- No maquillar inconsistencias.
- No reescribir el pasado para que parezca mas ordenado de lo que fue.

## Problemas a resolver

1. Desalineacion documental sobre `E10`.
2. Desalineacion documental sobre la rama de clasificacion, especialmente `C1`.
3. Riesgo de divergencia entre plan, bitacora, inventario, tabla maestra y README(s).
4. Ausencia de una lectura canonica y prudente sobre la capa explicativa transversal.

## Criterios de correccion

- Primacia del estado real: toda narrativa debe obedecer a inventario, tabla maestra y artefactos reales.
- Trazabilidad total: toda afirmacion importante debe poder rastrearse a run, auditoria o documento canonico.
- Conservacion de historia: las entradas historicas se preservan; si quedan superadas, se anotan notas de actualizacion.
- Precision terminologica: distinguir entre infraestructura preparada, corrida real, familia evaluada, familia pausada, referencia historica y linea futura.
- Prudencia metodologica: no inflar `E10`, no negar `C1`, no presentar la interpretabilidad heterogenea como si ya fuera transversal canonica.

## Puntos obligatorios a fijar

### E10

- Si fue abierto formalmente.
- Si ya tiene corrida canonica real.
- Cual es su estado exacto.
- Como debe leerse frente a `E1_v5_clean` y `E9_v2_clean`.

### Clasificacion

- Que ramas `C1-C4` existen realmente.
- Cuales tienen infraestructura.
- Cuales tienen corridas reales.
- Estado exacto de `C1`.
- Estado exacto de `C2`, `C3` y `C4`.

### Capa explicativa transversal

- Que artefactos explicativos existen realmente.
- Si son comparables entre familias o no.
- Clasificacion unica del estado de esa capa.
- Que faltaria para considerarla transversal canonica.

## Entregables

- `plan_de_experimentacion_radar.md` actualizado
- `bitacora_experimental_radar.md` actualizada
- README(s) canónicos corregidos si aplica
- `inventario_experimentos_radar.json` corregido o regenerado si aplica
- `tabla_maestra_experimentos_radar.csv/xlsx` corregida o regenerada si aplica
- `resumen_saneamiento_documental_radar.md`

## Resultado exigido

Un lector tecnico independiente debe poder revisar los documentos principales y concluir, sin contradicciones:

- que se ha corrido realmente;
- que sigue vigente;
- que esta pausado;
- que papel tienen `E1_v5_clean`, `E9_v2_clean` y `E10`;
- que tan avanzada esta clasificacion;
- y que la capa explicativa transversal todavia no esta plenamente resuelta.
