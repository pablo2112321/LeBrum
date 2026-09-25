# ESPECIFICACIÓN 00: SISTEMA VISUAL Y TEMA UI/UX (CYBERPUNK GRAFFITI)

## 1. DECLARACIÓN DE IDENTIDAD Y LEYES VISUALES
- **Temática Oficial:** CYBERPUNK GRAFFITI AVANZADO (eSports Underground).
- **PROHIBICIÓN STRICTA:** Prohibido en su totalidad el uso de elementos galácticos, estrellas, nebulosas, polvo cósmico o imágenes de fondo espacial.
- **Atmósfera:** Urbano, industrial, agresivo, tecnológico y competitivo.

## 2. PALETA DE COLORES (SISTEMA HEX/RGB)
- **Fondo Base (Background):** `#0a0a0f` (Concreto / Asfalto Oscuro).
- **Contenedores y Tarjetas:** `#12131a` con bordes de contraste y textura.
- **Acentos Neón Principales:**
  - Amarillo Cyber: `#ffe600` (Botones de acción primaria, alertas de tiempo).
  - Magenta Abrasivo: `#ff0055` (Estados de peligro, torneos en curso, disputas).
  - Cian Eléctrico: `#00f0ff` (Enlaces, badges informativos, contadores).
- **Texto:**
  - Principal: `#ffffff` (Blanco Puro).
  - Secundario / Muted: `#a0a5b5` (Gris Metálico).

## 3. ESTILOS Y COMPONENTES CSS MANDATORIOS
- **Bordes biselados (Cyber-Cut):** Usar `clip-path` angular en lugar de `border-radius` tradicional:
  `clip-path: polygon(0 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%);`
- **Textura de Fondo:** Líneas de escaneo sutiles (scanlines) o rejillas industriales.
- **Efecto Glitch:** Aplicar animación de distorsión ligera en texto al pasar el cursor (`:hover`).
- **Resplandores:** Sombras proyectadas abrasivas (`box-shadow: 0 0 15px rgba(255, 230, 0, 0.4)`).
- **Tipografía:** Títulos en mayúsculas en negrita, estética stencil/graffiti.

## 4. ARCHIVOS CSS AFECTADOS
- `static/css/global_cyberpunk.css` (Variables globales, resets y clases reutilizables).
- `static/css/paginas/*.css` (Estilos específicos por módulo).