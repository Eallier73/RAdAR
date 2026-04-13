# data

Estatus: `datos_canonicos`

`data/` contiene únicamente datos canónicos o declarados como tales.

## Subárboles

- `raw/`: adquisición estructurada bruta o semi-bruta
- `text/`: corpus textual canónico por fuente y semana
- `processed/`: datasets listos para modelado y derivados reproducibles
- `reference/`: diccionarios y recursos de referencia
- `external/`: insumos externos versionados

## Regla de frontera

- logs, estado, cache y reportes de ejecución no viven aquí
- si un archivo es efímero o técnico, va a `artifacts/`
- si un archivo es histórico y ya no es canónico, va a `legacy/`

## Naming semanal canónico

La unidad semanal vigente usa el patrón:

`<yyyy-mm-dd>_semana_<tramo_inicio>_<tramo_fin>_<yy>`

Dentro de cada carpeta semanal, los nombres canónicos por fuente son:

- `<semana>_facebook.csv`
- `<semana>_twitter.csv`
- `<semana>_youtube.csv`
- `<semana>_medios.txt`

`<semana>_medios.csv` puede existir como captura estructurada auxiliar cuando el extractor de medios la genera de forma reproducible.
