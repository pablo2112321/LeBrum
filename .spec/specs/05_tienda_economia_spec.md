# ESPECIFICACIÓN 05: ECONOMÍA DE FICHAS Y TIENDA DE RECOMPENSAS

## 1. SISTEMA MONETARIO INTERNO (FICHAS LEBRUM)
- La moneda virtual de la plataforma se denomina **Fichas LeBrum**.
- Las Fichas se obtienen como premios en torneos o acreditación manual del Admin.

## 2. FLUJO DE LA TIENDA DE CANJE (`/tienda/`)
1. Vista pública en cuadrícula Cyberpunk con artículos canjeables:
   - Tarjetas de regalo (Riot Points, VP Valorant, Saldo Steam).
   - Skins o pases de batalla.
   - Marcos/Badges de Perfil personalizados para LeBrum.
2. **Proceso de Compra:**
   - El Jugador selecciona el producto y presiona "Canjear".
   - La vista valida que `perfil.fichas >= producto.precio_fichas`.
   - Se descuentan las fichas en la BD inmediatamente.
   - Se genera un registro `OrdenCanje` en estado `"PENDIENTE_ENTREGA"`.
3. **Entrega de Código:** El Admin ve la orden en el panel Ojo de Halcón, ingresa el código digital de la tarjeta y marca la orden como `"ENTREGADA"`. El usuario ve su código en su historial de compras.