# Recomendacion de thresholds para E11 o futura clasificacion

- Threshold descartable: `+-0.5`.
- Thresholds plausibles para pruebas futuras: `+-0.10`, `+-0.15`, `+-0.20`.
- Threshold preferente: `+-0.15`.

Justificacion:

- `+-0.15` reduce fuertemente el colapso a `se_mantiene` sin volver la tarea una simple traduccion del ruido semanal.
- `+-0.10` deja una distribucion mas balanceada, pero es mas agresivo y arriesga meter demasiado movimiento pequeno en las clases extremas.
- `+-0.20` ya empieza a comprimir demasiado la masa central en algunos horizontes.
- El fracaso de `E11_v1_clean` fue consistente con un problema de threshold mal calibrado, no con una invalidez estructural total de la formulacion ternaria.