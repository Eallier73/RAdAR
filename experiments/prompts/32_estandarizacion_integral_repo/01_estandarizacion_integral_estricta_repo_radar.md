# Estandarización Integral y Estricta del Repositorio RAdAR

**Fecha:** 2026-04-12
**Rama destino:** feature/restructuracion-arquitectonica-repo
**Tipo:** Cierre de reestructura — normalización canónica completa

---

Quiero que hagas una estandarización integral y estricta del repositorio RAdAR sobre la rama feature/restructuracion-arquitectonica-repo.

No quiero una revisión superficial ni cosmética.
Quiero que cierres la reestructura y dejes el repo en estado canónico, consistente y profesional, sin contradicciones normativas ni zonas grises entre código activo, experimentación, artefactos runtime y legado.

## Objetivo central

Convertir la reestructuración actual en una arquitectura final coherente, gobernable y mantenible.

## Criterio rector

Toda pieza del repo debe pertenecer de forma inequívoca a una sola categoría:

- código activo canónico
- dato canónico
- artefacto runtime / estado técnico
- documentación
- experimental
- legado

Si una pieza no cae claramente en una sola categoría, está mal ubicada y debe corregirse.

## Instrucción principal

No te limites a mover carpetas.
Debes normalizar, endurecer y cerrar la arquitectura completa.

## Tareas obligatorias

### 1. Resolver contradicciones documentales

Revisa y corrige cualquier contradicción entre:

- README.md raíz
- docs/architecture/structural_audit.md
- docs/architecture/repository_architecture.md
- docs/migration/repository_restructure_migration.md
- READMEs de subárboles

Debe quedar una sola verdad sobre:

- si los aliases históricos siguen existiendo o ya fueron retirados
- qué rutas son canónicas
- cuáles son transitorias
- qué ya no se permite usar

No se admite documentación ambigua ni doble versión de la verdad arquitectónica.

### 2. Endurecer src/modeling/

Convierte src/modeling/ en una subarquitectura formal y no en un nuevo cajón de sastre.

Debes evaluar y, si corresponde, reorganizar internamente en subcapas claras, por ejemplo:

- core/
- runners/
- classification/
- audit/
- reporting/
- transitional/ o legacy/

Regla:

- capas comunes reutilizables separadas de runners
- runners separados de builders y tablas maestras
- piezas no canónicas fuera de la capa principal

No rompas trazabilidad ni imports sin documentarlo.

### 3. Aplicar convención obligatoria de nombres

Normaliza todo lo activo a esta convención:

- minúsculas
- ASCII
- snake_case
- sin acentos
- sin espacios
- sin faltas históricas
- sin abreviaturas ambiguas

Los nombres históricos solo pueden sobrevivir dentro de legacy/ si hay una razón fuerte.

Si algún archivo activo no cumple la convención, debes renombrarlo y actualizar referencias.

### 4. Endurecer fronteras de capas

Debes revisar que:

- src/ contenga solo código activo
- data/ contenga solo datos canónicos
- artifacts/ contenga solo runtime, estado, logs, cache y salidas técnicas
- experiments/ contenga solo investigación, prompts, auditoría experimental y runs históricos
- docs/ contenga solo documentación estructural, metodológica y operativa
- legacy/ concentre lo preservado pero no canónico

Cualquier excepción debe corregirse.

### 5. Limpiar experiments/

Quiero una separación estricta dentro de experiments/:

- prompts/
- research/
- audit/
- runs/

Además:

- mover backups y snapshots de auditoría a subcarpetas explícitas como audit/backups/
- separar archivos vigentes de históricos
- dejar criterios claros de qué puede vivir en runs/ y qué no
- prohibir que código activo nuevo aparezca en experiments/

### 6. Decidir sobre src/operations/

Si src/operations/ queda como capa canónica, debe contener componentes reales y documentados:

- wrappers operativos
- orquestadores
- runners de operación controlada
- puntos de entrada
- README claro

Si no tiene suficiente sustancia, reubica o redefine la carpeta para que no quede como placeholder ambiguo.

### 7. Crear norma de gobierno del repo

Debes agregar un documento canónico:

`docs/architecture/repository_governance.md`

Ese documento debe definir:

- taxonomía oficial del repo
- criterios de canonicidad
- reglas de naming
- reglas para promover scripts a activos
- reglas para mandar piezas a legacy/
- reglas para artefactos pesados y backups
- reglas para documentación experimental vs. estructural
- política de compatibilidad transitoria
- política de rutas permitidas y prohibidas

### 8. No romper el proyecto silenciosamente

Toda corrección debe dejar:

- trazabilidad de archivos movidos o renombrados
- tabla de migración actualizada
- documentación actualizada
- explicación breve de por qué se hizo cada cambio estructural

## Entregables obligatorios

- lista completa de archivos y carpetas creados, movidos, renombrados o eliminados
- explicación breve y rigurosa de cada cambio
- lista de contradicciones detectadas y cómo se resolvieron
- árbol final resumido del repo
- documento de gobierno arquitectónico
- veredicto final: cerrado y canónico / casi cerrado pero con pendientes / todavía inconsistente

## Restricciones

- No cambies la lógica metodológica del proyecto Radar.
- No mezcles otra vez experimental con canónico.
- No dejes placeholders ambiguos.
- No inventes rutas si ya hay equivalentes válidos.
- No preserves nombres malos solo por costumbre.
- No dejes compatibilidades transitorias sin declararlas explícitamente.

## Criterio de éxito

El trabajo queda bien hecho solo si:

- el repo deja de tener contradicciones estructurales
- cualquier persona puede entender qué vive dónde y por qué
- no queda ninguna carpeta híbrida o ambigua
- naming y jerarquía quedan homogéneos
- la arquitectura final ya puede tratarse como estándar profesional del proyecto
