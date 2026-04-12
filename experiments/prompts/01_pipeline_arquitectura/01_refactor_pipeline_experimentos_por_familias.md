Quiero que reestructures el pipeline experimental del proyecto Radar para que quede organizado por familias de modelos, no por corrida individual.

OBJETIVO GENERAL
Crear una arquitectura limpia, escalable y trazable donde haya un script por familia de modelo, y cada script acepte parámetros para correr distintas variantes experimentales sin duplicar código innecesariamente.

REGLA PRINCIPAL
NO quiero un script distinto para cada mini experimento.
SÍ quiero un script distinto por familia de modelo.

FAMILIAS A IMPLEMENTAR
1. lineal regularizado
2. robusto
3. arboles / boosting
4. series de tiempo con exógenas
5. híbridos / ensembles

ESTRUCTURA ESPERADA DE SCRIPTS
Debes crear o dejar listos scripts con esta lógica:

- run_e1_ridge.py
- run_e2_huber.py
- run_e3_random_forest.py
- run_e4_xgboost.py
- run_e5_catboost.py
- run_e6_arimax.py
- run_e7_prophet.py
- run_e8_hibrido_residuales.py
- run_e9_stacking.py

Si alguno no puede quedar totalmente funcional todavía, al menos déjalo como plantilla consistente y documentada, pero E1 y E2 deben quedar operables.

REQUISITOS DE DISEÑO
Todos los scripts deben seguir una estructura homogénea:

1. parse_args()
2. build_estimator() o equivalente
3. carga del dataset maestro
4. construcción del model frame
5. validación temporal walk-forward o equivalente correcto para la familia
6. cálculo de métricas Radar
7. guardado de predicciones por horizonte
8. guardado de métricas por horizonte
9. registro completo en el experiment tracker
10. finalize del run con trazabilidad suficiente

PARAMETROS QUE DEBEN ACEPTAR LOS SCRIPTS TABULARES
Como mínimo, los scripts tabulares deben aceptar por CLI:

- --run-id
- --target-mode   (choices: nivel, delta)
- --lags          (ejemplo: 1,2,3,4)
- --feature-mode  (choices: all, corr, lasso)
- --initial-train-size
- --horizons      (default: 1,2,3,4)

Para modelos que necesiten parámetros extra, agrégalos de forma coherente.

ESTANDAR DE TRAZABILIDAD
Cada corrida debe guardar:

- metadata_run.json
- parametros_run.json
- metricas_horizonte.json
- resumen_modeling_horizontes.json
- predicciones_h1.csv
- predicciones_h2.csv
- predicciones_h3.csv
- predicciones_h4.csv

Y debe registrar correctamente esos artefactos en el grid / tracker.

ESTANDAR DE RESULTADOS
Cada horizonte debe producir, como mínimo:

- horizonte_sem
- mae
- rmse
- direccion_accuracy
- deteccion_caidas
- l_num
- l_trend
- l_risk
- l_tol
- loss_h

Y el run completo debe calcular también:

- L_total_Radar
- si es posible, L_coh
- estado
- comentarios
- notas_config

IMPORTANTE
No quiero que cambies la lógica metodológica central del proyecto Radar.
Debes respetar:

- validación temporal
- horizonte 1,2,3,4 semanas
- trazabilidad completa
- evaluación multicomponente Radar
- uso del dataset maestro ya existente

REFACTOR ESPERADO
Debes identificar y extraer la lógica reusable a funciones comunes cuando convenga, por ejemplo:

- parse_lags
- resolve_feature_mode
- compute_total_radar_loss
- run_tabular_experiment
- save_run_outputs

Pero sin romper el funcionamiento actual de E1_v2.

ENTREGABLES
Quiero que me entregues:

1. lista de archivos creados o modificados
2. breve explicación de la función de cada archivo
3. scripts completos
4. cualquier helper nuevo necesario
5. explicación de cómo correr cada script desde terminal
6. nota explícita sobre qué quedó totalmente funcional y qué quedó como plantilla

RESTRICCIONES
- No inventes rutas si ya existen módulos equivalentes en el proyecto.
- Reutiliza config.py, data_master.py, evaluation.py, experiment_logger.py y feature_engineering.py si ya resuelven parte del problema.
- No rompas compatibilidad con el tracker actual.
- No metas validación aleatoria simple.
- No dupliques código si puede resolverse con una función compartida.

CRITERIO DE EXITO
La arquitectura final debe permitir que una corrida como esta sea posible con un solo script de familia:

python run_e1_ridge.py --run-id E1_v3 --target-mode delta --feature-mode all --lags 1,2,3,4

y también:

python run_e1_ridge.py --run-id E1_v4 --target-mode nivel --feature-mode corr --lags 1,2,3,4

Empieza por revisar el código actual, detectar qué partes del script E1_v2 ya son reutilizables, y construir la arquitectura sin perder trazabilidad.