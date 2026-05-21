Instrucción para el agente: reconstruir E1_v2 sin fuga temporal

Quiero que reconstruyas la corrida E1_v2 manteniendo su definición original, pero corrigiendo cualquier posible fuga temporal en el ajuste de hiperparámetros.

Objetivo

Rehacer E1_v2 como una versión metodológicamente limpia para series de tiempo.

Definición que se debe conservar

La nueva corrida debe seguir siendo:

familia: E1
versión: E1_v2_clean
modelo base: Ridge
target_mode: level
feature_mode: all
lags: 1..4
validación externa: walk-forward expanding
transformación: igual que en E1_v2 original, salvo que detectes una razón técnica muy fuerte para cambiarla
mismas columnas base, mismos horizontes y misma lógica general del pipeline

No quiero que cambies la filosofía del experimento. Solo quiero eliminar el posible leakage temporal.

Problema detectado que debes corregir

En la E1_v2 original se usó RidgeCV sin un esquema temporal explícito de validación interna. Eso puede introducir una fuga temporal dentro del bloque de entrenamiento al seleccionar alpha.

La reconstrucción debe eliminar ese problema.

Cambio principal que debes implementar
No uses RidgeCV con CV por defecto

En lugar de eso, implementa una de estas dos rutas, priorizando la primera:

Ruta preferida

Usa:

Ridge(alpha=...)
búsqueda manual de alpha
validación interna con TimeSeriesSplit

La selección de alpha debe hacerse solo dentro del bloque de entrenamiento de cada fold externo.

Es decir:

En cada paso del walk-forward externo:
toma train_data = data.iloc[:test_idx]
toma test_data = data.iloc[[test_idx]]
Dentro de ese train_data:
ejecuta una búsqueda de alpha con TimeSeriesSplit
evalúa cada alpha únicamente con splits temporales
elige el mejor alpha con base en una métrica explícita
Con ese alpha óptimo:
ajusta el pipeline final en todo el train_data
predice test_data
Ruta aceptable si simplifica mucho el código

Usa GridSearchCV o RandomizedSearchCV, pero solamente si el CV interno es TimeSeriesSplit y si todo ocurre dentro del train_data de cada fold externo.

No quiero ningún esquema de CV aleatorio o estándar de scikit-learn que mezcle tiempos.

Restricciones metodológicas

Debes respetar estas reglas:

1. Nada de mirar el futuro

En ningún punto del pipeline se puede usar información posterior al punto de prueba.

2. Transformadores ajustados solo en train

Cualquier scaler, winsorizer, selector o transformador debe hacer fit solo con el bloque de entrenamiento del fold correspondiente.

3. Nada de selección global previa

No hagas selección de variables, correlaciones, tuning ni normalización usando toda la muestra antes del walk-forward.

4. Lags iguales a la versión original

Conserva la misma construcción de lags 1..4 sobre:

target actual
features base definidas para E1
5. Target igual a la versión original

Debe seguir siendo:

target_mode = level
Métrica para elegir alpha

Quiero que el agente use una métrica sencilla y consistente para el tuning interno.

Regla

Elegir alpha minimizando:

preferentemente MAE promedio
si no es viable por la arquitectura actual, usar RMSE promedio

Pero debe quedar explícito cuál se usó.

Mi preferencia es:

MAE, porque es más robusto y más coherente con nuestra lógica de evaluación
Espacio de búsqueda de alpha

Quiero que explores un grid razonable de alpha en escala logarítmica.

Por ejemplo:

alphas = np.logspace(-4, 4, 40)

o algo equivalente.

No uses un grid demasiado pequeño.

Qué debe producir el agente
1. Nuevo script

Debe crear una nueva versión del script, por ejemplo:

run_e1_ridge_clean.py
o
run_e1_v2_clean.py
2. Nueva corrida

Debe registrar la corrida como algo claramente distinguible de la original, por ejemplo:

experiment_id = E1_v2_clean
model_name = ridge_tscv
3. Salidas equivalentes a las de E1_v2 original

Quiero los mismos tipos de output si es posible:

métricas por horizonte
resumen global
predicciones por horizonte
parámetros de corrida
metadata del run
4. Registro adicional

Además, quiero que guarde:

best_alpha elegido en cada fold externo
promedio, mediana, mínimo y máximo de best_alpha por horizonte

Eso es importante para entender la estabilidad del tuning.

Validaciones que debe correr el agente

El agente debe verificar y reportar explícitamente:

A. Que no haya leakage temporal

Debe confirmar por escrito que:

el tuning de alpha ocurre solo dentro del train de cada fold externo
el test externo nunca participa en el ajuste ni en la selección de hiperparámetros
B. Que la corrida sea comparable con E1_v2 original

Debe mantener:

mismos horizontes
misma lógica de features
mismo target
misma estructura de evaluación externa
C. Comparación final

Al terminar, debe comparar E1_v2 original vs E1_v2_clean y reportar:

cambio en loss_h
cambio en MAE
cambio en RMSE
cambio en direction_accuracy
cambio en risk_detection

Y debe interpretar si la versión original estaba inflada o si el efecto del leakage era marginal.

Preguntas que el agente debe responder al final

Quiero que el agente cierre con respuestas breves a estas preguntas:

¿La reconstrucción eliminó la fuga temporal detectada?
¿Cuánto cambió el rendimiento respecto a E1_v2 original?
¿La mejora o caída fue pequeña, moderada o grande?
¿E1_v2 original era confiable como benchmark o estaba metodológicamente comprometida?
¿La versión clean debe sustituir oficialmente a la E1_v2 original en la bitácora?
Criterio de decisión

Usa este criterio interpretativo:

Si E1_v2_clean rinde muy parecido a E1_v2, entonces concluimos que la fuga temporal era menor y que la versión original era razonablemente confiable.
Si E1_v2_clean cae de forma clara y consistente, entonces concluimos que la versión original estaba parcialmente inflada por tuning no temporal.
Si E1_v2_clean mejora, entonces probablemente el tuning temporal ordenado estabilizó mejor el modelo.
Instrucción final para el agente

No rehagas toda la arquitectura desde cero. Haz el cambio mínimo necesario para preservar comparabilidad con E1_v2, pero dejando el tuning de Ridge completamente alineado con series de tiempo.