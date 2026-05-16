# shared

Estatus: `codigo_activo_canonico`

`src/shared/` existe para utilitarios transversales mínimos y estables.

Reglas:

- no debe absorber lógica de negocio por comodidad
- no debe convertirse en un cajón de sastre
- solo deben vivir aquí helpers realmente reutilizados por más de una capa activa
