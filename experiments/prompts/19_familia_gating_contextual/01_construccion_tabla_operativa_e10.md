## Nombre

Construccion de tabla operativa E10 para meta-seleccion / gating contextual

## Objetivo

Construir una tabla derivada, trazable y metodologicamente limpia para la familia `E10`, distinta de la tabla usada por `E9`, orientada a investigar mas adelante:

- meta-selector duro
- gating blando
- selector por objetivo operativo

Sin correr todavia el modelo final de `E10`.

## Principios obligatorios

- La tabla maestra oficial del proyecto sigue siendo la fuente canonica.
- `E10` trabaja sobre una tabla derivada especifica.
- La unidad de analisis canonica es `fila-horizonte`.
- Toda construccion debe evitar leakage temporal, snooping y reconstrucciones dudosas.
- Debe separarse con claridad:
  - columnas usables como `feature_candidate`
  - columnas diagnosticas retrospectivas
  - columnas objetivo del selector
  - columnas prohibidas para entrenamiento

## Modelos base minimos

Incluir, cuando exista cobertura alineable y trazable:

- `E1_v5_clean`
- `E5_v4_clean`
- `E9_v2_clean`

Y evaluar inclusion adicional solo si aporta diversidad real y trazabilidad suficiente.

## Estructura minima

La tabla E10 debe contener:

1. Identidad y trazabilidad
- `row_id`
- `fecha`
- `horizonte`
- `y_real`
- indicadores de integridad y cobertura

2. Predicciones base por modelo
- `pred_modelo_X`
- direccion y senal de caida derivadas cuando aplique

3. Error ex post por modelo
- `abs_error_modelo_X`
- `sq_error_modelo_X`
- `acierto_direccion_modelo_X`
- `acierto_caida_modelo_X`
- `loss_local_modelo_X`

4. Variables de desacuerdo
- rango, dispersion, consenso de direccion, numero de modelos que anticipan caida, etc.

5. Contexto observable en `t`
- nivel reciente
- cambios recientes
- volatilidad reciente
- tendencia reciente
- variables temporales basicas defendibles

6. Etiquetas objetivo del selector
- `mejor_modelo_error_abs`
- `mejor_modelo_direccion`
- `mejor_modelo_caida`
- `mejor_modelo_loss_radar_local`
- `mejor_modelo_operativo`

## Entregables esperados

- `tabla_e10_meta_selector_base.csv`
- `tabla_e10_meta_selector_base.xlsx`
- `diccionario_tabla_e10.md`
- `inventario_columnas_e10.csv`
- `resumen_construccion_tabla_e10.md`

## Cierre metodologico esperado

La tabla debe permitir afirmar que ya existe una base estructurada, trazable y metodologicamente limpia para investigar `E10` como familia de meta-seleccion o gating, distinguiendo de forma explicita entre:

- predicciones base
- contexto observable
- desacuerdo entre modelos
- diagnostico retrospectivo
- targets del selector

Sin confundirlos ni mezclar informacion ex post dentro de las features futuras.
