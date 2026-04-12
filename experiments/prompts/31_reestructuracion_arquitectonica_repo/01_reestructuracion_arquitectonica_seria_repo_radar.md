Quiero que hagas una reestructuración arquitectónica seria, conservadora y profesional del repositorio RAdAR, trabajando sobre una rama nueva en un worktree separado, nunca sobre main ni sobre el árbol vivo principal.

Tu objetivo no es “ordenar carpetas para que se vean bonitas”. Tu objetivo es dejar una arquitectura clara, sostenible, trazable y profesional, donde quede inequívocamente separado qué es código fuente, qué son datos canónicos, qué son artefactos runtime, qué es experimentación, qué es operación vigente, qué es documentación y qué es legacy.

Debes partir de este diagnóstico base:

la raíz del repo mezcla demasiadas cosas al mismo nivel: código, datos, diccionarios, encuestas, experimentos y outputs;
Scripts/ mezcla varias lógicas a la vez: extracción, procesamiento, modelado, preprocesamiento, operación controlada y estado/runtime;
Scripts/Extracting_Procesing contiene arrastre histórico y scripts numerados específicos por fuente o caso, útiles pero no canónicos;
Scripts/Modeling ya refleja una arquitectura más madura y reusable, y debe tomarse como referencia de estándar;
Experimentos/ mezcla prompts, runs, auditorías, análisis metodológicos, cierres y hasta piezas operativas;
hay duplicidad conceptual entre la capa operativa vigente y la capa experimental/documental;
los datos por fuente conviven con material agregado, histórico, cache y trazabilidad técnica;
el naming del repo es inconsistente y revela deriva histórica: Extracting_Procesing, NLP_Data_Procesing, Prepocessing, Operational_Controlada, Datos_RadaR_Texto, etc.;
la estructura actual todavía depende demasiado del conocimiento tácito del proyecto.

Quiero que resuelvas eso con criterio profesional y sin hacer una demolición innecesaria.

Reglas críticas:

No trabajar sobre main.
No trabajar sobre el árbol principal vivo.
Trabajar en una rama nueva tipo feature/<tema>, idealmente desde dev, dentro de un worktree separado.
No romper compatibilidad operativa de golpe.
No borrar material legacy útil.
Sí mover, reclasificar, renombrar y encapsular con criterio.
Sí dejar wrappers, README de transición o capas puente cuando haga falta.
No mezclar datos canónicos con cache, runs o artefactos temporales.
No mezclar operación vigente con experimentación histórica.
Toda convención de nombres debe ser única, explícita, consistente y aplicada de extremo a extremo.

Tu tarea debe hacerse en dos capas:

Primero, auditoría estructural rigurosa.
Después, reestructuración e implementación de una nueva arquitectura.

Quiero que hagas lo siguiente, en este orden:

Auditar el árbol actual completo.
Clasificar cada carpeta principal y subárbol relevante como una de estas categorías:
canonica_vigente
operativa_vigente
experimental
runtime
legacy
documental
Detectar ambigüedades estructurales, duplicidades de función, naming inconsistente y carpetas híbridas.
Diseñar una estructura objetivo más profesional y migrable.
Validar compatibilidad mínima con el estado actual del proyecto.
Ejecutar la reorganización en el worktree.
Crear documentación de transición y arquitectura.
Dejar una tabla completa de migración old_path -> new_path.
Reportar riesgos abiertos y pendientes.

No quiero una reestructuración arbitraria. Debe estar guiada por separación real de responsabilidades.

La estructura objetivo debe seguir esta lógica, aunque puedes ajustar nombres si encuentras una solución mejor y más compatible:

una zona clara para código fuente activo;
una zona clara para datos;
una zona clara para artefactos generados, runtime, logs, cache y estado;
una zona clara para experimentación y análisis;
una zona clara para documentación;
una zona clara para legacy.

La lógica esperada es aproximadamente esta:

src/ o equivalente para código activo
extraction/
preprocessing/
nlp/
modeling/
operations/
shared/
data/ o equivalente para datos
raw/
processed/
text/
external/
archive/
artifacts/ o equivalente para runtime y outputs técnicos
runs/
logs/
cache/
state/
experiments/ o equivalente para investigación y trazabilidad experimental
prompts/
research/
audit/
reports/
docs/
architecture/
methodology/
operations/
migration/
legacy/

No te amarres ciegamente a esos nombres si detectas una opción más compatible con el repo actual, pero sí debes respetar la separación conceptual.

Criterios específicos de decisión:

Para código:

todo el código activo debe quedar agrupado por responsabilidad;
debes separar claramente extractores, procesamiento/limpieza, NLP, modelado, operación controlada y utilitarios compartidos;
si una carpeta actual mezcla vigente y legacy, debes separarla;
si hay scripts históricos útiles, deben ir a legacy/ o a un subárbol equivalente claramente marcado;
Scripts/Modeling debe preservarse como referencia de arquitectura reusable;
evita seguir acumulando scripts sueltos en raíces ambiguas.

Para datos:

debes separar datos canónicos de cache, runs, trazas técnicas, consolidaciones históricas y materiales agregados;
debe quedar claro qué es input operativo, output procesado, output textual, insumo externo y archivo histórico;
si existen carpetas como Juntos o equivalentes agregados, clasifícalas explícitamente como archive o legacy_data según corresponda;
no permitas que runtime técnico compita visualmente con dato canónico.

Para experimentos:

Experimentos/ no puede seguir significando todo a la vez;
debes separar prompts, corridas/runs, auditorías, análisis metodológicos, cierres y documentación experimental;
si dentro de experimentación hay piezas que ya son operación vigente, debes reubicarlas o dejar explícita su transición;
no perder trazabilidad de runs ya existentes.

Para operación vigente:

la capa operativa controlada debe quedar separada de la experimental;
no debe redefinir metodología;
debe apuntar a scripts o benchmarks ya congelados;
si hoy hay duplicidad entre Scripts/Operational_Controlada y material operativo dentro de Experimentos, debes resolverla;
debe quedar una sola ruta canónica para la operación vigente.

Para legacy:

legacy no se borra;
legacy se encapsula;
todo lo histórico que ya no sea arquitectura destino debe quedar fuera del flujo canónico, pero fácil de consultar;
debes crear README por carpeta legacy explicando qué es, por qué existe y por qué ya no debe usarse como base estructural.

Para naming:

define y aplica una convención única;
preferencia: minúsculas, snake_case, ASCII y nombres semánticos;
corrige nombres inconsistentes o mal escritos cuando eso mejore semántica y mantenibilidad;
documenta siempre equivalencias old_path -> new_path;
no hagas renombres caprichosos.

Entregables obligatorios:

Inventario inicial del árbol actual.
Clasificación estructural de cada carpeta principal y subárbol relevante.
Diagnóstico resumido de problemas arquitectónicos detectados.
Propuesta de nueva estructura objetivo.
Implementación de esa nueva estructura en el worktree.
Lista exacta de carpetas y archivos movidos.
Tabla completa old_path -> new_path.
Lista de wrappers, alias o capas puente creadas para compatibilidad.
READMEs nuevos o actualizados en carpetas clave.
Documento de arquitectura canónica del repo.
Documento de migración con:
qué cambió
por qué cambió
qué queda deprecated
qué queda canónico
qué queda legacy
qué queda pendiente

Documentación mínima obligatoria:

Debes crear o actualizar README en:

raíz del repo
la carpeta canónica de código fuente
la carpeta de datos
la carpeta de artifacts/runtime
la carpeta de experiments
la carpeta de docs
la carpeta de legacy

Cada README debe explicar:

propósito;
qué sí vive ahí;
qué no debe vivir ahí;
relación con otras carpetas;
estatus de esa carpeta: canónica, runtime, experimental, operativa, legacy, etc.

Restricciones técnicas:

no inventes lógica metodológica nueva;
no alteres el pipeline de modelado vigente salvo por movimiento, encapsulamiento o mejora estructural mínima necesaria;
no rompas trazabilidad de experiment_logger ni de runs ya existentes;
no cambies scripts de modelado solo por estética si ya funcionan bien;
no destruyas rutas importantes sin dejar transición documentada cuando sea relevante;
no mezcles archivos generados con código fuente;
no dejes carpetas tipo misc, otros, varios, tmp_final, nuevo_nuevo o equivalentes vagos.

Estándar de calidad esperado:

La nueva estructura debe cumplir estas propiedades:

Un tercero debe poder entender el repo sin conocer toda su historia.
Debe ser evidente qué parte del repo es arquitectura vigente.
Debe ser evidente qué parte es legacy.
Debe ser evidente qué parte es operación y qué parte es investigación.
Debe ser evidente dónde van nuevos scripts y dónde no.
Debe reducir la probabilidad de seguir acumulando desorden histórico.
Debe dejar una base profesional para la automatización futura del sistema.

Formato de salida que quiero:

Diagnóstico resumido del árbol encontrado.
Clasificación estructural por carpetas.
Propuesta de nueva estructura.
Lista exacta de movimientos realizados.
Tabla old_path -> new_path.
READMEs creados o actualizados.
Notas de compatibilidad o transición.
Riesgos abiertos o pendientes.
Veredicto final:
si la nueva estructura ya quedó en estándar alto y profesional,
o qué faltaría para cerrar completamente esa etapa.

Criterio de éxito:

El trabajo estará bien hecho si al final:

el repo deja de depender de conocimiento histórico implícito;
la capa canónica vigente queda inequívoca;
legacy queda encapsulado;
experimentación deja de ser un cajón de sastre;
operación vigente queda separada;
la estructura resultante se ve profesional, gobernable y lista para crecer sin volver a desordenarse.

Además, quiero una postura analítica clara al final, no tibia:
dime si la nueva estructura quedó realmente profesional o si solo quedó “menos desordenada”.
