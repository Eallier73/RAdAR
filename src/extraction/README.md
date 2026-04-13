# extraction

Estatus: `codigo_activo_canonico`

`src/extraction/` contiene runners de adquisición por fuente.
Es una capa activa, pero todavía fuente-específica y previa a la automatización integral.

## Estado real

- `twitter_extractor_tampico.py`, `youtube_extractor_tampico.py` y `medios_extractor.py` pueden emitir archivos semanales canónicos en `data/raw/radar_weekly_flat/`
- `facebook_extractor_apify_tampico.py` produce artefactos intermedios de adquisición en `artifacts/runs/extraction/facebook/`
- la promoción de esos artefactos intermedios a dato canónico de Facebook ocurre en `src/preprocessing/`

## Reglas

- tokens, sesiones y cursores viven en `artifacts/state/`
- caches técnicos viven en `artifacts/cache/`
- la capa no debe presentarse como orquestación integral ni scheduling
- cada runner debe decir con claridad si escribe dato canónico o artefacto intermedio
