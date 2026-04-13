# preprocessing

Estatus: `codigo_activo_canonico`

`src/preprocessing/` contiene CLIs activas para normalizar el raw semanal, completar faltantes desde fuentes mensuales y promover salidas hacia `data/text/`.

## Estado real

- sí existe automatización parcial del stage mediante `ejecutar_preprocesamiento_base.py`
- no existe automatización integral del repo ni wrapper operativo final
- los scripts siguen siendo de propósito específico; el wrapper solo coordina la secuencia base de preprocessing

## Entry point canónico

```bash
python -m src.preprocessing pipeline-base --help
```

El wrapper expone automatización parcial de esta capa y no debe confundirse con una orquestación end-to-end del repositorio.

## Inventario activo

| Script | Rol | Estado |
| --- | --- | --- |
| `ejecutar_preprocesamiento_base.py` | wrapper del stage | canónico |
| `prefijar_carpetas_semanales.py` | agrega prefijo ISO a carpetas semanales heredadas | activo transicional |
| `normalizar_semanas_canonicas.py` | normaliza nombres, crea semanas faltantes y reporta faltantes | canónico |
| `distribuir_facebook_semanal.py` | asigna archivos Facebook ya cortados por rango semanal | activo transicional |
| `distribuir_medios_semanales.py` | asigna TXT o CSV externos de medios a semanas | activo transicional |
| `completar_facebook_semanal_desde_mensual.py` | genera faltantes semanales de Facebook desde mensual | canónico |
| `completar_twitter_semanal_desde_mensual.py` | genera faltantes semanales de Twitter/X desde mensual | canónico |
| `completar_youtube_semanal_desde_mensual.py` | genera faltantes semanales de YouTube desde mensual | canónico |
| `promover_raw_a_texto.py` | promueve `data/raw/` semanal hacia `data/text/` | canónico |

## Secuencia base recomendada

1. `normalizar-semanas`
2. `distribuir-facebook` o `completar-facebook`, según el tipo de fuente disponible
3. `distribuir-medios`
4. `completar-twitter`
5. `completar-youtube`
6. `promover-texto`

## Responsabilidades vigentes

- completar semanas faltantes desde fuentes mensuales
- mover ingresos externos a la semana correspondiente
- normalizar naming de carpetas y archivos semanales
- promover `data/raw/` hacia `data/text/`

## Reglas de frontera

- los datos canónicos resultantes viven en `data/raw/` o `data/text/`
- todos los logs técnicos de preprocessing viven en `artifacts/logs/preprocessing/`
- no debe escribirse runtime dentro de `data/`
- esta capa puede contener helpers de ingreso manual, pero deben declarar su propósito y no fingir automatización cerrada
- los nombres activos de scripts deben expresar acción y fuente; no se conservan nombres vagos como `acomodar`, `cleanup` o `rellenar`
