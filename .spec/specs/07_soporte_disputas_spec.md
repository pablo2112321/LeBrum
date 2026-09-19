# ESPECIFICACIÓN 07: SISTEMA DE DISPUTAS Y ARBITRAJE ADMIN

## 1. FLUJO DE DISPUTA DE ENFRENTAMIENTOS
1. Cuando una partida entra en estado `"DISPUTA"`, las inscripciones del torneo correspondiente a esa llave quedan congeladas.
2. Se genera una alerta en tiempo real en el Panel Administrador ("Ojo de Halcón").

## 2. MÓDULO DE ARBITRAJE ADMIN (`/admin/disputas/`)
1. El Administrador accede a la pantalla de arbitraje de la partida afectada.
2. La pantalla muestra en paralelo:
   - La captura de pantalla subida por el Capitán A.
   - La captura de pantalla subida por el Capitán B.
   - Los nicks y Discord de ambos capitanes.
3. **Dictamen Final:** El Admin presiona "Declarar Ganador a Equipo A" o "Declarar Ganador a Equipo B".
4. El sistema asigna la victoria, reactiva el bracket y avanza de ronda automáticamente.