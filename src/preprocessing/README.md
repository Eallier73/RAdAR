# preprocessing

Estatus: `codigo_activo_canonico`

`src/preprocessing/` contiene scripts activos para promover, normalizar y consolidar insumos antes del NLP y del modelado.

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
