# ESPECIFICACIÓN 04: CLASIFICACIÓN (LEADERBOARD), XP Y HALL OF FAME

## 1. LÓGICA DE EXPERIENCIA (XP)
- **Ganar Partida de Torneo:** +100 XP por jugador.
- **Campeón de Torneo:** +500 XP extra por jugador.
- **Participación Base:** +25 XP por el simple hecho de competir.
- **Cálculo de Nivel:** `Nivel = Floor(XP / 200) + 1`.

## 2. TABLAS DE CLASIFICACIÓN PÚBLICAS (`/rankings/`)
1. **Leaderboard de Jugadores (MVP):**
   - Muestra avatar, Riot ID / Nickname, Nivel de Perfil, XP total acumulado y torneos ganados.
2. **Leaderboard de Escuadras (Top Clans):**
   - Muestra nombre del clan, victorias consecutivas y Fichas ganadas en la plataforma.
3. **Estilo Visual:** Muestra insignias estilo "Cyber Badge" (Oro, Neón, Cobre) según la posición (Top 1, Top 2, Top 3).