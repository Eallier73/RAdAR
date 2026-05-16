# Prompt para el agente - Estructuracion operable de la etapa NLP del proyecto RAdAR

## Rol

Actua como arquitecto tecnico del proyecto RAdAR en fase de endurecimiento operativo.

Tu tarea es dejar **operable, clara, trazable y profesional** la **etapa de NLP previa al modelado**, con una estructura explicita, reproducible y alineada con el estado actual del repo.

## Objetivo principal

Organizar la etapa de NLP para que quede definida como un pipeline formal que arranca en los corpus semanales preprocesados y termina en el dataset maestro final de modelado usado por la capa `Scripts/Modeling`.

No quiero una reorganizacion cosmetica.
Quiero una organizacion operativa real:

* documentacion clara,
* rutas resueltas contra el arbol actual,
* scripts identificados como canonicos,
* orden correcto de ejecucion,
* entradas y salidas explicitas,
* distincion entre scripts activos, scripts historicos y scripts fuera de ruta.

## Advertencia critica que debes respetar

Las rutas que aparecen en esta especificacion funcional **no estan actualizadas** y **no debes asumirlas literalmente**.

Tu obligacion es:

1. inspeccionar la estructura real del repo en la rama sobre la que estas trabajando,
2. localizar los scripts y artefactos equivalentes reales,
3. corregir las rutas en la documentacion final,
4. no inventar ubicaciones nuevas si ya existe una convencion valida en el repo.

Dicho de otro modo:

* la logica funcional que te doy **si es la referencia**,
* pero las rutas textuales pegadas aqui **pueden ser historicas**,
* asi que debes mapear esa logica a la estructura real del proyecto.

## Alcance exacto de la etapa NLP

La etapa debe quedar definida asi, de principio a fin:

### 1. Entrada de la etapa

Entrada formal:

* corpus semanales ya preprocesados en texto plano,
* un `.txt` por semana y por fuente,
* provenientes de la etapa previa de extraccion + limpieza.

Dependencia previa:

* la etapa anterior ya dejo operables extraccion y limpieza,
* esta etapa NLP comienza despues de `run_stage2_text_preprocessing.py` o su equivalente real en el repo.

Tu trabajo aqui es documentar con precision:

* cual es la carpeta real de entrada,
* como esta organizada por fuente,
* cual es la convencion de nombres por semana,
* que precondiciones minimas debe cumplir el corpus para pasar a NLP.

---

### 2. Sentimiento semanal

Script canonico esperado:

* `aceptacion_digital_redes_ponderacion_medios.py`
  o el equivalente real si en el repo el nombre exacto cambio.

Entradas logicas:

* corpus de Facebook
* corpus de Twitter
* corpus de YouTube
* corpus de Medios

Salidas esperadas:

* archivo semanal consolidado de sentimiento, equivalente funcional a:
  `aceptacion_digital_redes_medios_sentimiento_semanal.xlsx`

Variables esperadas generadas por esta etapa:

* `sentimiento_facebook`
* `sentimiento_twitter`
* `sentimiento_youtube`
* `sentimiento_redes_ponderado`
* `sentimiento_medios`
* `promedio_redes_medios`

Debes verificar:

* si estas columnas siguen existiendo exactamente con esos nombres o con variantes,
* donde se guardan realmente,
* si el script sigue siendo el canonico o si fue reemplazado por otro.

---

### 3. Diccionario tematico

Script historico que lo genero:

* `diccionario_temas_pmi_confianza.py`

Pero esta etapa, en operacion normal, **no debe regenerar el diccionario**.

Regla operativa:

* se usan diccionarios congelados ya construidos,
* especificamente los equivalentes funcionales de:

  * `diccionario_pmi_confianza_v5.xlsx`
  * `diccionario_pmi_confianza_v10.xlsx`

Debes dejar explicito:

* donde estan realmente esos diccionarios,
* si esos dos archivos siguen siendo los vigentes,
* si hay version canonica mas reciente,
* como debe consumirlos la clasificacion tematica.

Debes marcar `diccionario_temas_pmi_confianza.py` como:

* script historico de generacion,
* no parte del rerun normal del pipeline.

---

### 4. Clasificacion semanal de temas

Script canonico esperado:

* `clasificacion_temas_pmi_confianza.py`

Entradas logicas:

* corpus `.txt`
* diccionarios congelados `v5` y `v10`

Regla metodologica que debes preservar y documentar:

* scoring basado en `Delta_PMI * hits * Confianza`
* exclusion de Facebook en esta etapa

Salidas esperadas:

* resultados por corpus
* consolidado tematico semanal

Debes verificar y dejar claro:

* si Facebook efectivamente queda excluido por diseno en la implementacion actual,
* como se representa esa exclusion en codigo,
* que archivos intermedios genera,
* cual es la salida consolidada real.

---

### 5. Normalizacion de temas

Script canonico esperado:

* `resultados_clasificacion_temas_pmi_confianza_normalizado.py`

Entrada logica:

* consolidado tematico semanal no normalizado

Salida logica:

* consolidado PMI normalizado

Debes documentar:

* archivo de entrada real,
* archivo de salida real,
* reglas de normalizacion que aplica,
* si la normalizacion es por corpus, por semana o por consolidado total.

---

### 6. Fusion inicial hacia ML

Script canonico esperado:

* `unir_ml_ready_con_sentimiento.py`

Salida esperada:

* archivo equivalente funcional a `datos_ML_0.xlsx`

Debes documentar:

* que insumos une exactamente,
* que columnas incorpora,
* que material legacy aun arrastra,
* que partes siguen existiendo por compatibilidad historica.

Es importante que dejes explicito si aqui todavia sobrevive material viejo de encuestas o columnas heredadas.

---

### 7. Construccion del dataset final

Script canonico esperado:

* `reconstruir_dataset_aceptacion_digital.py`

Este script debe quedar documentado como el responsable de la reconstruccion final de dataset para modelado.

Debe cubrir y dejar explicitas estas transformaciones logicas:

1. `datos_ML_0.xlsx -> datos_ML_3.xlsx`

   * poda manual 1

2. `datos_ML_3.xlsx -> datos_ML_4.xlsx`

   * creacion de lags
   * reutilizacion de la logica historica de lageado

3. `datos_ML_4.xlsx -> datos_ML_5.xlsx`

   * poda manual 2

4. `datos_ML_5.xlsx -> datos_ML_master.xlsx`

   * rama legacy

5. construccion de la rama de modelado:

   * `datos_ML_master_1.xlsx`
   * `datos_ML_master_2.xlsx`
   * `datos_ML_master_3.xlsx`
   * `datos_ML_master_4.xlsx`
   * `datos_ML_master_indice_aceptacion_digital.xlsx`

6. cambio de target:

   * `y_t = sentimiento_redes_ponderado`
   * `target_1w..4w = sentimiento_redes_ponderado` desplazado temporalmente

Debes verificar en el repo real:

* si todos esos pasos siguen existiendo como archivos fisicos intermedios,
* si algunos se volvieron opcionales,
* si el script produce todos esos outputs o solo una parte,
* si hay helpers equivalentes o scripts legacy absorbidos en esta reconstruccion.

---

### 8. Dataset maestro final de modelado

Archivo final esperado:

* `datos_ML_master_indice_aceptacion_digital.xlsx`

Este punto debe quedar amarrado explicitamente con la capa de modelado actual.

Debes verificar y documentar que:

* este es el dataset maestro efectivamente usado por `Scripts/Modeling`,
* esta alineado con `config.py`,
* esta alineado con `data_master.py`,
* sus columnas target y features son compatibles con el pipeline experimental actual.

Si detectas divergencias entre la etapa NLP y la etapa de modelado, debes reportarlas explicitamente.

## Pipeline resumido que debes dejar documentado

La documentacion final debe dejar esta logica, pero corregida contra rutas reales:

* corpus `.txt` semanales
  -> sentimiento semanal
  -> archivo semanal de sentimiento

* corpus `.txt` + diccionarios PMI congelados
  -> clasificacion tematica
  -> consolidado tematico
  -> normalizacion tematica

* sentimiento + PMI normalizado
  -> union inicial ML
  -> `datos_ML_0.xlsx`

* `datos_ML_0.xlsx`
  -> reconstruccion de dataset
  -> `datos_ML_master_indice_aceptacion_digital.xlsx`

## Scripts que deben quedar identificados como parte de la ruta canonica

Debes localizar y documentar como ruta activa del pipeline NLP, o sus equivalentes reales:

* `aceptacion_digital_redes_ponderacion_medios.py`
* `clasificacion_temas_pmi_confianza.py`
* `resultados_clasificacion_temas_pmi_confianza_normalizado.py`
* `unir_ml_ready_con_sentimiento.py`
* `reconstruir_dataset_aceptacion_digital.py`

## Scripts que deben quedar identificados como historicos o de soporte, pero no parte del rerun normal

* `diccionario_temas_pmi_confianza.py`

## Scripts que deben quedar identificados como fuera de la ruta usada

Debes confirmar si siguen fuera de ruta los equivalentes de:

* `diccionario_temas_pmi.py`
* `diccionario_temas_wpmi.py`
* `clasificacion_temas.py`

No lo asumas sin verificar: revisalo contra el repo actual y deja la clasificacion correcta.

## Entregables obligatorios

Quiero que entregues exactamente esto:

### 1. Diagnostico de estructura actual

Un diagnostico serio del estado actual de la etapa NLP:

* que ya existe,
* que esta disperso,
* que esta mal nombrado,
* que esta bien encaminado,
* que sigue siendo historico pero util,
* que esta fuera de ruta.

### 2. README nuevo

Debes crear un documento llamado exactamente:

`README_pipeline_nlp_modelado.md`

Este README debe quedar dentro del lugar correcto del repo segun la convencion actual.
No lo pongas donde se te ocurra: ubicalo donde haga sentido estructuralmente para la etapa NLP/modelado.

El README debe incluir:

* objetivo de la etapa,
* entradas,
* salidas,
* orden de ejecucion,
* scripts canonicos,
* scripts historicos,
* scripts fuera de ruta,
* artefactos generados,
* dependencia con la etapa previa,
* dependencia con el modelado,
* advertencias metodologicas,
* observaciones sobre rutas resueltas.

### 3. Mapa de rutas reales

Una lista clara de:

* scripts encontrados,
* ruta real dentro del repo,
* funcion de cada uno,
* estatus:

  * canonico
  * historico
  * soporte
  * fuera de ruta
  * pendiente de aclaracion

### 4. Estandarizacion minima de nombres y ubicacion

Si detectas desorden serio, puedes proponer o ejecutar una reorganizacion minima, pero con estas reglas:

* no rompas imports ni llamadas existentes,
* no cambies nombres historicos sin justificacion fuerte,
* no muevas archivos si no es realmente necesario,
* si mueves algo, actualiza referencias,
* prioriza documentacion y wrappers antes que reubicaciones destructivas.

### 5. Punto de entrada operativo de la etapa

Debes dejar claro:

* como se corre la etapa completa,
* si debe correrse script por script,
* si conviene crear un runner/orquestador especifico de NLP,
* o si por ahora debe quedar documentada como secuencia manual controlada.

No inventes un orquestador si todavia no hace falta, pero si deja claro cual seria el punto de entrada operativo recomendado.

### 6. Validacion final

Debes cerrar con una verificacion explicita de:

* que la etapa NLP termina realmente en el dataset usado por modelado,
* que no hay una ruptura entre `reconstruir_dataset_aceptacion_digital.py` y `Scripts/Modeling`,
* que la documentacion quedo alineada con el estado real del repo.

## Restricciones duras

* No inventes rutas.
* No inventes scripts.
* No asumas que los nombres historicos siguen vigentes.
* No rehagas la metodologia.
* No cambies la logica analitica de sentimiento, PMI, normalizacion o reconstruccion salvo que detectes una ruptura tecnica real.
* No mezcles esta tarea con experimentacion de modelado.
* No toques la parte de `Scripts/Modeling` mas alla de verificar compatibilidad con el dataset final.
* No borres archivos historicos.
* Si algo no esta claro, clasificalo como "pendiente de aclaracion", no lo maquilles.

## Criterio de exito

La tarea estara bien hecha si al final queda:

1. una ruta NLP explicita y profesional,
2. un README claro y util,
3. los scripts canonicos correctamente identificados,
4. las rutas reales corregidas,
5. el dataset final NLP conectado sin ambiguedad con el modelado,
6. la etapa lista para futura automatizacion sin perder trazabilidad.

## Forma de trabajo obligatoria

Hazlo por etapas, no todo de golpe:

### Etapa A

Auditar estructura real del repo y localizar scripts/artefactos.

### Etapa B

Clasificar cada script:

* canonico
* historico
* fuera de ruta
* soporte

### Etapa C

Redactar y guardar `README_pipeline_nlp_modelado.md`.

### Etapa D

Verificar compatibilidad con `Scripts/Modeling`.

### Etapa E

Entregar resumen final con:

* archivos creados o modificados,
* decisiones tomadas,
* pendientes detectados,
* riesgos o ambiguedades.

## Formato final de entrega del agente

Quiero que el agente entregue al final:

1. Archivos creados o modificados
2. README generado
3. Mapa de scripts con estatus
4. Ruta operativa final de la etapa NLP
5. Validacion de compatibilidad con modelado
6. Riesgos, huecos o decisiones pendientes

Se estricto, no complaciente.
No maquilles huecos.
No asumas.
Mapea la logica funcional a la estructura real del repo y deja la etapa NLP lista para operar con estandar profesional.

## Registro obligatorio de cambios

Ademas de la reorganizacion y documentacion, debes llevar **registro explicito de todos los cambios realizados** durante esta tarea.

No quiero cambios silenciosos.

Debes crear y/o actualizar un artefacto de trazabilidad de cambios donde quede asentado, como minimo:

* fecha y momento del cambio
* archivo modificado o creado
* tipo de cambio:

  * creacion
  * modificacion
  * reubicacion
  * renombrado
  * ajuste documental
  * correccion de ruta
  * aclaracion metodologica
* descripcion breve pero precisa de que se cambio
* motivo del cambio
* impacto esperado
* si el cambio afecta o no compatibilidad hacia atras
* si requiere accion adicional posterior

## Artefacto esperado para este registro

Debes generar un archivo de control, con nombre claro y consistente, por ejemplo:

* `CHANGELOG_NLP_MODELADO.md`
  o
* `bitacora_cambios_nlp_modelado.md`

Ubicalo en el lugar correcto del repo segun la estructura actual.
No lo pongas al azar.

## Regla de trazabilidad

Cada vez que modifiques, crees, muevas, renombres o reclasifiques algo relevante, debes registrarlo.

Esto incluye:

* creacion del `README_pipeline_nlp_modelado.md`
* cambios de rutas documentadas
* reclasificacion de scripts como canonicos, historicos o fuera de ruta
* ajustes a nombres de archivos
* wrappers o helpers nuevos si hicieran falta
* cualquier correccion necesaria para alinear NLP con modelado

## Si haces cambios en archivos existentes

Debes dejar claro:

* que habia antes
* que quedo ahora
* por que se cambio
* si el cambio fue estructural, documental u operativo

## Si decides no cambiar algo

Tambien debes registrarlo cuando sea importante, indicando:

* que detectaste
* por que decidiste no tocarlo
* que riesgo o deuda tecnica queda abierta

## Entregable adicional obligatorio

Agrega al final de la entrega una seccion llamada:

### Registro de cambios ejecutados

Y ahi resume:

1. archivo de bitacora generado
2. lista de cambios principales
3. cambios con impacto operativo
4. cambios solo documentales
5. pendientes no resueltos

## Restriccion

No des por cerrada la tarea si:

* hiciste cambios y no quedaron registrados,
* reclasificaste scripts sin dejar constancia,
* corregiste rutas sin documentarlo,
* o modificaste la estructura sin bitacora.

## Criterio de exito adicional

La etapa no solo debe quedar ordenada:
tambien debe quedar **auditada**.

Cualquier persona que revise el repo despues debe poder entender:

* que cambio,
* por que cambio,
* que se toco,
* que no se toco,
* y que queda pendiente.

## Complemento posterior del usuario

`/home/emilio/Documentos/RAdAR/Scripts/NLP_Data_Procesing/reconstruir_dataset_aceptacion_digital.py`

Este es la direccion indicada por el usuario para copiar el archivo faltante.
