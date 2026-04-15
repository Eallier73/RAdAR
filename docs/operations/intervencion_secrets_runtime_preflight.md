# Intervención: Capa mínima de runtime seguro + preflight + orquestador canónico

**Fecha:** 2026-04-14
**Tipo:** Intervención quirúrgica controlada
**Estado:** Implementado

---

## Objetivo general

Cerrar dos huecos operativos reales sin tocar la metodología central ni reescribir el sistema:

1. Gestión canónica de secretos, credenciales y state persistente para extractores.
2. Orquestador canónico mínimo que coordine el pipeline y ejecute chequeos previos serios antes de correr.

---

## Regla máxima de esta intervención

No modificar nada fuera del alcance mínimo necesario.

- No rehacer extractores completos.
- No rehacer modelado.
- No cambiar criterios metodológicos.
- No mover directorios por gusto.
- No renombrar módulos si no es indispensable.
- No introducir refactorización arquitectónica más grande que la pedida.
- No tocar outputs históricos si no es obligatorio.
- No aprovechar esta tarea para "limpiar" otras cosas del repo.

---

## Qué debe quedar resuelto

### A. Secrets y state ya no deben pedirse una y otra vez

- Las API keys y tokens deben configurarse una sola vez.
- Los extractores deben leerlos automáticamente.
- El state de Twitter/X debe persistirse y reutilizarse.
- No debe pedirse login o regeneración de state en cada corrida.
- Si falta algo, el error debe ser claro.

### B. El orquestador debe saber validar eso antes de correr

- Antes de ejecutar extracción, debe hacer un preflight check.
- Debe verificar secrets requeridos.
- Debe verificar state persistente requerido.
- Debe verificar rutas runtime.
- Si falta algo, debe cortar con error claro o marcar partial si así se configuró.
- Debe registrar ese resultado en estado y artefactos.

---

## Alcance exacto de la implementación

### Bloque 1: Capa compartida de secrets y runtime

- `src/shared/secrets.py`: loader de `.env`, validador de secretos, sin exponer valores.
- `src/shared/runtime_paths.py`: rutas canónicas (TWITTER_STATE_PATH, DOT_ENV_PATH, etc.).
- `src/shared/check_config.py`: checker standalone de configuración.
- `src/shared/__init__.py`: re-exporta utilidades nuevas.

### Bloque 2: Corrección mínima de extractores

- `src/extraction/runners/youtube_extractor_tampico.py`: elimina API key hardcodeada, usa `YOUTUBE_API_KEY` de env.
- `src/extraction/runners/facebook_extractor_apify_tampico.py`: elimina Serper API key hardcodeada, usa `SERPER_API_KEY` de env.
- `src/extraction/runners/twitter_extractor_tampico.py`: usa `TWITTER_STATE_PATH` de `src.shared.runtime_paths`.

### Bloque 3: Preflight en orquestador

- `src/operations/stages/preflight_stage.py`: etapa nueva de preflight.
- `src/operations/config.py`: agrega "preflight" como primera etapa en STAGE_NAMES.
- `src/operations/contracts.py`: agrega contrato de preflight.
- `src/operations/pipeline_orchestrator.py`: registra preflight en STAGE_RUNNERS.
- `src/operations/stages/__init__.py`: exporta `run_preflight_stage`.

### Bloque 4: Configuración y documentación

- `.env.example`: placeholders reales de todas las variables usadas.
- `.gitignore`: agrega `.env` y `.env.local`.
- `docs/operations/secrets_and_runtime.md`: documentación de operación.

---

## Lo que NO se tocó

- Lógica de scraping de ningún extractor.
- Contratos metodológicos de modelado.
- Criterios de evaluación Radar.
- Estructura de datos canónicos (raw, text, processed).
- NLP, modelado, export, report stages.
- Nombres históricos de archivos o directorios.
- Outputs existentes.

---

## Criterio de éxito

- Credenciales configuradas una sola vez en `.env`.
- Extractores ya no piden keys repetidamente.
- Twitter/X reutiliza state persistente.
- Solo se regenera state si se fuerza o si expiró/corrompió.
- No quedan secretos hardcodeados.
- El orquestador valida todo eso antes de correr.
- Si falta algo, falla con mensaje claro.
- No se modificó más de lo necesario.
- La metodología del proyecto quedó intacta.
