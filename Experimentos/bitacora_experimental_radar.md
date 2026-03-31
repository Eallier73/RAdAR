# Bitácora Experimental Radar

## Propósito

Esta bitácora resume, en lenguaje operativo, qué se hizo, qué se decidió y en qué rama quedó cada bloque principal del pipeline experimental. No sustituye:

- el grid experimental,
- la tabla maestra,
- ni los artefactos por run.

Su función es servir como capa narrativa corta para ubicarse rápido.

## Estado actual

- Fecha de actualización: `2026-03-30`
- Rama de trabajo actual: `feature/e4-boosting`
- Mejor run global vigente: `E1_v5_clean` con `L_total_Radar=0.243442`
- Mejor no lineal tabular abierta: `E5_v4_clean` con `L_total_Radar=0.247788`
- Plan rector vigente:
  - [plan_de_experimentacion_radar.md](/home/emilio/Documentos/RAdAR/Experimentos/plan_de_experimentacion_radar.md)
- Tabla maestra vigente:
  - [tabla_maestra_experimentos_radar.xlsx](/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar.xlsx)
  - [tabla_maestra_experimentos_radar.csv](/home/emilio/Documentos/RAdAR/Experimentos/tabla_maestra_experimentos_radar.csv)

## Línea de tiempo

### 2026-03-21 | E1 Ridge limpio

- Se reconstruyó `E1_v2_clean` como baseline metodológico oficial sin leakage temporal.
- Se corrió `E1_v3_clean` para probar `target_mode=delta`.
- Se corrió `E1_v4_clean` para probar `feature_mode=corr`.
- Se corrió `E1_v5_clean` para probar memoria larga con `lags=1..6`.

Decisión:

- `E1_v5_clean` quedó como mejor Ridge limpio global con `L_total_Radar=0.243442`.
- `E1_v4_clean` quedó como referencia parsimoniosa con `L_total_Radar=0.253277`.
- `Ridge` quedó cerrada como baseline lineal regularizado principal.

Rama asociada:

- `feature/e1-ridge`

Documentos clave:

- [resumen_metodologico_e1_ridge.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e1_ridge.md)

### 2026-03-23 | E2 Huber limpio

- Se abrió `E2_v1_clean` como baseline robusto.
- Se corrió `E2_v2_clean` como control de convergencia.
- Se corrió `E2_v3_clean` como prueba de memoria corta (`lags=1..4`).

Resultados:

- `E2_v1_clean`: `0.301907`
- `E2_v2_clean`: `0.301920`
- `E2_v3_clean`: `0.286465`

Decisión:

- `E2_v2_clean` descartó convergencia como explicación principal.
- `E2_v3_clean` mejoró internamente a Huber, pero no alcanzó a Ridge.
- `E2` quedó cerrada.

Rama asociada:

- `feature/e2-huber`

Documento clave:

- [resumen_metodologico_e2_huber.md](/home/emilio/Documentos/RAdAR/Experimentos/resumen_metodologico_e2_huber.md)

### 2026-03-23 a 2026-03-25 | E3 árboles tipo bagging

- Se abrió `E3_v1_clean` con `Random Forest` y `feature_mode=corr`.
- Se corrió `E3_v2_clean` con `Random Forest` y `feature_mode=all`.
- Se corrió `E3_v3_clean` con `ExtraTrees`.

Resultados:

- `E3_v1_clean`: `0.280892`
- `E3_v2_clean`: `0.266387`
- `E3_v3_clean`: `0.287289`

Decisión:

- `E3_v2_clean` quedó como mejor run interno de la familia E3.
- `ExtraTrees` no aportó mejora relevante.
- La familia `E3` sí mostró señal no lineal real, pero no desplazó a Ridge.

Rama asociada:

- `feature/e3-random-forest`

Documento asociado:

- [plan_inicial_e3_random_forest.md](/home/emilio/Documentos/RAdAR/Experimentos/plan_inicial_e3_random_forest.md)

### 2026-03-25 | E4 Boosting

- Se abrió `E4_v1_clean` con `xgboost_regressor`, `feature_mode=all`, `target_mode=nivel`.
- Se corrió `E4_v2_clean` cambiando solo `feature_mode=corr`.
- Se corrió `E4_v3_clean` cambiando solo `target_mode=delta`.

Resultados:

- `E4_v1_clean`: `0.283934`
- `E4_v2_clean`: `0.297343`
- `E4_v3_clean`: `0.424774`

Decisión:

- `E4_v2_clean` no mejoró a `E4_v1_clean`.
- `E4_v3_clean` deterioró la familia de forma fuerte.
- `E4` quedó cerrada con evidencia suficiente en su rama base.
- La continuidad metodológica vuelve a `E5`, `E6`, `E7`, `E8` y solo después `E9`.

Rama asociada:

- `feature/e4-boosting`

### 2026-03-25 a 2026-03-30 | Auditoría maestra y preparación para stacking

- Se construyó el script [build_experiments_master_table.py](/home/emilio/Documentos/RAdAR/Scripts/Modeling/build_experiments_master_table.py).
- Se integró la regeneración automática de la auditoría al cierre de runs completos.
- Se amplió la tabla maestra con:
  - `runs_catalogo`
  - `metricas_por_horizonte_long`
  - `stacking_readiness`
  - `cobertura_predicciones`
  - `stacking_base_h1..h4`

Decisión:

- La infraestructura quedó lista para una futura familia de meta-modelado o stacking por horizonte.
- Aún falta estandarizar artefactos explicativos entre familias.

Rama asociada:

- `feature/auditoring-and-stacking`

### 2026-03-30 | E5 CatBoost

- Se ajustó `run_e5_catboost.py` al estándar de familias tabulares.
- Se abrió `E5_v1_clean` con `CatBoostRegressor`, `target_mode=nivel`, `feature_mode=all`, `lags 1..6`.
- Se corrió `E5_v2_clean` para aislar `feature_mode=corr`.
- Se corrió `E5_v3_clean` para bajar `depth`.
- Se abrió una ruta de tuning temporal interno acotado con `E5_v4_clean`.
- Se corrió `E5_v5_clean` como segunda ola focal de tuning.

Resultados:

- `E5_v1_clean`: `0.255259`
- `E5_v2_clean`: `0.261819`
- `E5_v3_clean`: `0.261319`
- `E5_v4_clean`: `0.247788`
- `E5_v5_clean`: `0.264427`

Decisión:

- `E5_v4_clean` queda como campeón interno de la familia.
- `E5_v4_clean` supera a `E1_v4_clean`, `E3_v2_clean` y `E4_v1_clean`.
- `E5_v4_clean` no supera a `E1_v5_clean`.
- `E5_v2_clean`, `E5_v3_clean` y `E5_v5_clean` no mejoraron al campeón.
- La familia `E5` queda abierta pero ya madura, con un ganador interno claro.

Rama asociada:

- `feature/e4-boosting`

### 2026-03-30 | E6 ARIMAX

- Se alineó `run_e6_arimax.py` al estándar del pipeline por familias.
- Se abrió `E6_v1_clean` con `SARIMAX(1,0,1)` y `feature_mode=corr`.
- Se corrió `E6_v2_clean` cambiando solo el universo exógeno a `feature_mode=all`.

Resultados:

- `E6_v1_clean`: `0.370318`
- `E6_v2_clean`: `0.445769`

Decisión provisional:

- `E6_v1_clean` fue una apertura débil, muy por debajo de `E5_v4_clean`, `E1_v4_clean` y `E1_v5_clean`.
- `E6_v2_clean` empeoró todavía más; ampliar exógenas no ayudó.
- La parsimonia exógena sí fue menos mala que `all`, pero la familia no quedó competitiva.
- `ARIMAX` mostró además muchos warnings de convergencia en la estimación por fold externo.
- La familia `E6` queda debilitada y deja de ser línea principal; si reaparece, tendría que ser con una sola hipótesis nueva muy controlada o como insumo de híbridos.

### 2026-03-30 | E7 Prophet con exógenas

- Se alineó `run_e7_prophet.py` al estándar del pipeline por familias.
- Se abrió `E7_v1_clean` como baseline parsimonioso con `feature_mode=corr`.
- Se corrió `E7_v2_clean` cambiando solo el universo exógeno a `feature_mode=all`.
- Se corrió `E7_v3_clean` manteniendo `feature_mode=corr` y subiendo `changepoint_prior_scale` de `0.05` a `0.20`.

Resultados:

- `E7_v1_clean`: `0.325502`
- `E7_v2_clean`: `0.681992`
- `E7_v3_clean`: `0.321328`

Decisión:

- `Prophet` supera con claridad a `E6`, pero no entra al bloque contendiente del proyecto.
- `feature_mode=all` colapsó la familia; la amplitud exógena metió ruido y elevó muchísimo los errores numéricos.
- mayor flexibilidad en changepoints ayudó un poco frente al baseline (`E7_v3_clean > E7_v1_clean`), sobre todo en `H2/H3`, pero no volvió competitiva a la familia frente a `E5_v4_clean`, `E1_v4_clean` o `E3_v2_clean`.
- `E7` queda como familia intermedia: útil como referencia temporal estructurada, no como línea principal.

### 2026-03-30 | Rama planificada de clasificacion C1-C4

- Se dejo documentada una rama paralela de clasificacion del movimiento del Radar.
- Se reorganizo la documentacion en un prompt rector y una carpeta por familia:
  - `09_clasificacion_radar/`
  - `10_clasificacion_random_forest/`
  - `11_clasificacion_xgboost/`
  - `12_clasificacion_catboost/`
  - `13_clasificacion_lightgbm/`
- Se dejaron preparados los runners por familia:
  - `run_c1_random_forest_classifier.py`
  - `run_c2_xgboost_classifier.py`
  - `run_c3_catboost_classifier.py`
  - `run_c4_lightgbm_classifier.py`
- Se guardo un prompt operativo por familia:
  - `C1` RandomForestClassifier
  - `C2` XGBoostClassifier
  - `C3` CatBoostClassifier
  - `C4` LightGBMClassifier
- Se dejo explicitado que cualquier futura implementacion debe registrar todo con `RadarExperimentTracker` igual que en regresion.

Estado:

- documentada y trazable
- scripts preparados
- sin corridas ejecutadas todavia

Documento asociado:

- [plan_inicial_clasificacion_radar_c1_c4.md](/home/emilio/Documentos/RAdAR/Experimentos/plan_inicial_clasificacion_radar_c1_c4.md)

## Lectura consolidada vigente

- Campeón global: `E1_v5_clean`
- Referencia parsimoniosa: `E1_v4_clean`
- Mejor H2 y H4 por `loss_h`: `E2_v3_clean`
- Mejor H3 por `loss_h`: `E1_v2_clean`
- Mejor familia no lineal base de bagging: `E3_v2_clean`
- Mejor familia no lineal tabular abierta: `E5_v4_clean`
- Familias cerradas: `E1`, `E2`, `E4`
- Familias abiertas o vigentes como referencia: `E3`, `E5` y `E7`

## Próximo paso lógico

No hace falta más trabajo sobre `E4` base.

Los siguientes pasos razonables son:

1. decidir si conviene abrir `E8` híbrido residual o si ya vale más preparar la selección formal de candidatos para stacking por horizonte;
2. mantener `E6` y `E7` como referencias temporales estructuradas, no como frente principal salvo nueva hipótesis fuerte;
3. después decidir si conviene seguir con más familias base o pasar a `E9` stacking usando `stacking_base_h1..h4`.
