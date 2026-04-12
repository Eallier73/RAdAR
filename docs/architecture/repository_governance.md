# Repository Governance

Documento autoritativo de gobierno del repositorio RAdAR.
Fecha de vigencia: 2026-04-12 (Fase 3 — estandarizacion integral)

## 1. Taxonomia oficial: las 6 capas

| Capa | Ruta | Contenido canonico | Estado |
| --- | --- | --- | --- |
| **codigo activo** | `src/` | extractores, preprocessors, NLP, modelado, utilitarios compartidos | `canonica_vigente` |
| **datos canonicos** | `data/` | insumos brutos, corpus textual, datasets procesados, referencias, externos | `canonica_vigente` |
| **runtime tecnico** | `artifacts/` | logs, runs, cache, estado de automatizacion | `runtime` |
| **investigacion** | `experiments/` | prompts, bitacoras, auditorias, runs experimentales | `experimental` |
| **documentacion** | `docs/` | arquitectura, migracion, operacion | `documental` |
| **historico** | `legacy/` | codigo y datos fuera del flujo canonico pero preservados | `legacy` |

Cada archivo del repositorio pertenece exactamente a una de estas 6 capas.
No existen capas intermedias, aliases ni rutas transicionales.

## 2. Criterios de canonicidad

Un script o modulo es **codigo activo canonico** si cumple todos los siguientes criterios:

1. Resuelve una responsabilidad real y actual del pipeline.
2. Es reproducible: sus inputs y outputs estan bien definidos.
3. No duplica funcionalidad ya cubierta por otro modulo activo.
4. Su nombre cumple la convencion (ver seccion 3).
5. Vive en `src/` bajo el subarbol correspondiente a su responsabilidad.
6. No depende de rutas absolutas hardcodeadas de entornos personales.

Un dataset es **dato canonico** si:
1. Es insumo del pipeline activo o resultado reproducible de el.
2. No es efimero (no se descarta entre runs).
3. Vive en `data/` bajo el subarbol que corresponde a su tipo.

## 3. Convencion de nombres

### Regla

- **Minusculas**: sin mayusculas en ninguna posicion.
- **ASCII**: sin acentos (a no ser que el contenido del dato lo requiera), sin caracteres especiales.
- **Snake case**: palabras separadas por guion bajo (`_`), no guion medio (`-`) ni espacio.
- **Sin abreviaturas ambiguas**: preferir nombres descriptivos sobre siglas opacas.

### Ejemplos

| Malo | Bueno | Motivo |
| --- | --- | --- |
| `Modelo_Radar_1.py` | `modelo_radar_1.py` | mayusculas prohibidas |
| `aceptación_digital.py` | `aceptacion_digital.py` | acento prohibido |
| `Lageado_Datos_ML.py` | `lageado_datos_ml.py` | mayusculas prohibidas |
| `scripts procesamiento.py` | `scripts_procesamiento.py` | espacio prohibido |
| `procesar-datos.py` | `procesar_datos.py` | guion medio no permitido |
| `tmp_v2_final_BUENO.py` | `procesar_encuestas_v2.py` | nombre descriptivo y sin ruido |

### Alcance

Esta convencion aplica a todo lo que vive en `src/`, `data/`, `artifacts/`, `experiments/` y `docs/`.
En `legacy/` los nombres historicos se conservan como evidencia; no se normalizan.

## 4. Reglas de promocion

Para que un script pase de `experiments/` o `legacy/` a `src/`:

1. **Responsabilidad clara**: debe resolver una tarea concreta del pipeline activo.
2. **Sin duplicar**: confirmar que no existe ya un modulo en `src/` con esa funcion.
3. **Nombre conforme**: renombrar a snake_case ASCII antes de mover.
4. **Imports saneados**: eliminar rutas absolutas personales y referencias a estructuras viejas.
5. **Documentado**: agregar docstring y comentarios suficientes.
6. **Registrado**: crear entrada en `docs/migration/path_migration_table.csv` con `status: moved`.

## 5. Reglas de deprecacion

Para mover una pieza de `src/` o `data/` a `legacy/`:

1. **Confirmar que no es referenciada** por ningun modulo activo (grep en `src/`).
2. **Mover con `git mv`**, no copiar.
3. **Registrar en tabla de migracion**: `docs/migration/path_migration_table.csv` con `status: deprecated`.
4. **Actualizar READMEs** de origen y de `legacy/` si aplica.
5. No se borran archivos historicos con valor documental; se mueven a `legacy/`.

## 6. Politica de artefactos pesados

### Que va en artifacts/

- logs de corridas (`.log`, `.txt` de ejecucion)
- salidas tecnicas temporales (JSONs de metricas, CSVs de predicciones)
- estado de autenticacion (tokens, cursores)
- cache regenerable

### Que no se versiona

Los siguientes tipos de archivos **no deben aparecer en el indice git** (agregar a `.gitignore` si es necesario):

- `__pycache__/` y `.pyc`
- archivos `.env` o de credenciales
- modelos entrenados pesados (`.pkl`, `.joblib`, `.h5` > 50 MB)
- cache de APIs externas

### Que va en experiments/audit/

- grids de experimentos versionados activos (`.xlsx`, `.csv`)
- backups de grid: en `experiments/audit/backups/`
- inventarios de columnas y constructos canonicos
- tablas maestras de resultados

## 7. Politica de documentacion

| Tipo | Ubicacion | Ejemplos |
| --- | --- | --- |
| Documentacion estructural | `docs/architecture/`, `docs/migration/`, `docs/operations/` | arquitectura, governance, tabla de migracion |
| Documentacion experimental | `experiments/research/` | bitacoras, planes, cierres de experimentos |
| Documentacion de modulo | dentro del propio `.py` (docstring) o `README.md` del subarbol | README de `src/modeling/`, docstrings de funciones |

No mezclar: un plan metodologico no va en `docs/`; una decision de arquitectura no va en `experiments/`.

## 8. Politica de compatibilidad

**No se permiten aliases transitorios sin fecha de retiro declarada.**

- Si se crea un alias o wrapper de compatibilidad, debe tener:
  1. Un comentario en el codigo con la fecha de retiro prevista.
  2. Una entrada en `docs/migration/repository_restructure_migration.md` declarando el alias.
- Los aliases de raiz (`Scripts/`, `Experimentos/`, etc.) fueron retirados en Fase 2 y no deben reaparecer.
- Cualquier automatizacion nueva debe apuntar directamente a rutas canonicas.

## 9. Rutas permitidas y prohibidas

### Permitidas

```
src/extraction/runners/
src/preprocessing/
src/nlp/
src/modeling/
src/shared/
data/raw/
data/text/
data/processed/
data/reference/
data/external/
artifacts/runs/
artifacts/logs/
artifacts/cache/
artifacts/state/
experiments/prompts/
experiments/research/
experiments/audit/
experiments/audit/backups/
experiments/runs/
docs/architecture/
docs/migration/
docs/operations/
legacy/code/
legacy/data/
```

### Prohibidas (no deben aparecer como rutas activas)

```
Scripts/
Experimentos/
Datos_RAdAR/
Datos_RadaR_Texto/
Datos_Modelo_ML/
Diccionarios_NLP/
Encuestas/
```

Estas rutas estan extintas desde Fase 2 de la reestructuracion. Su aparicion en imports o paths hardcodeados es un defecto que debe corregirse.

### Zona gris: rutas absolutas personales en codigo

Los extractores y scripts de preprocessing usan rutas absolutas del tipo `/home/emilio/Documentos/Datos_Radar/...` como defaults de CLI.
Esto es aceptable **solo si**:
- La ruta es un argumento CLI con default explicito (no hardcode obligatorio).
- El script puede ejecutarse con ruta diferente via argumento.

Si una ruta personal es obligatoria (sin alternativa), debe corregirse en una siguiente fase.
