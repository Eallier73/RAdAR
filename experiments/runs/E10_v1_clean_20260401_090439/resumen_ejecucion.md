# Resumen ejecucion E10_v1_clean

- run_id: `E10_v1_clean`
- tabla_e10: `/home/emilio/Documentos/RAdAR/experiments/audit/tabla_e10_meta_selector_base.csv`
- inventario_columnas: `/home/emilio/Documentos/RAdAR/experiments/audit/inventario_columnas_e10.csv`
- target_selector: `mejor_modelo_loss_radar_local`
- target_vs_operativo_same_share: `1.0`
- initial_train_size: `12`
- meta_model: `logistic_regression`
- selector_c: `0.1`
- class_weight: `balanced`
- use_only_complete_rows: `False`
- L_total_Radar_E10: `0.271220`

## Horizontes

### H1

- rows_total_horizonte: `28`
- rows_eval: `16`
- clases_train_iniciales: `{'E2_v3_clean': 4, 'E5_v4_clean': 3, 'E7_v3_clean': 3, 'E3_v2_clean': 1, 'E1_v5_clean': 1}`
- accuracy_selector: `0.187500`
- balanced_accuracy_selector: `0.15833333333333333`
- loss_h_E10: `0.099370`
- benchmark_fijo_loss_h: `0.085779`

### H2

- rows_total_horizonte: `27`
- rows_eval: `15`
- clases_train_iniciales: `{'E2_v3_clean': 5, 'E7_v3_clean': 3, 'E1_v5_clean': 3, 'E5_v4_clean': 1}`
- accuracy_selector: `0.200000`
- balanced_accuracy_selector: `0.16666666666666666`
- loss_h_E10: `0.074758`
- benchmark_fijo_loss_h: `0.080326`

### H3

- rows_total_horizonte: `26`
- rows_eval: `14`
- clases_train_iniciales: `{'E1_v5_clean': 4, 'E2_v3_clean': 3, 'E7_v3_clean': 3, 'E5_v4_clean': 2}`
- accuracy_selector: `0.142857`
- balanced_accuracy_selector: `0.1`
- loss_h_E10: `0.058884`
- benchmark_fijo_loss_h: `0.059051`

### H4

- rows_total_horizonte: `25`
- rows_eval: `13`
- clases_train_iniciales: `{'E2_v3_clean': 5, 'E5_v4_clean': 4, 'E1_v5_clean': 2, 'E7_v3_clean': 1}`
- accuracy_selector: `0.307692`
- balanced_accuracy_selector: `0.3055555555555555`
- loss_h_E10: `0.038207`
- benchmark_fijo_loss_h: `0.040072`

## Lectura corta

- E10 se evalua como selector duro retrospectivo, pero el criterio principal sigue siendo el sistema final Radar.
- El benchmark fijo se construye dentro de train con perdida local historica media y nunca usa el bloque de test para definirse.
- Las columnas prohibidas, diagnosticas y targets retrospectivos no entran al entrenamiento del selector.

## Benchmarks globales sobre el mismo subset de evaluacion

- selector_fijo: `0.265229`
- E1_v5_clean: `0.21786553684588505`
- E9_v2_clean: `0.22750962017362367`
