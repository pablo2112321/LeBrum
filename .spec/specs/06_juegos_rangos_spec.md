# ESPECIFICACIÓN 06 (REVISADA): INTEGRACIÓN DE RIOT API Y STEAM OPENID

## 1. SEGURIDAD DE CREDENCIALES
- Todas las API Keys (Riot y Steam) deben almacenarse en variables de entorno (.env).
- Prohibido dejar claves en duro en `settings.py` o en archivos de vistas.

## 2. INTEGRACIÓN RIOT GAMES
- Endpoint: `https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}`
- Parámetro Header: `X-Riot-Token: ENV('RIOT_API_KEY')`
- Acción: Almacena `riot_id` y valida existencia en tiempo real.

## 3. INTEGRACIÓN STEAM (OPENID)
- Flujo de Autenticación: Steam OpenID / Social Auth.
- Endpoint de Datos: `https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/`
- Parámetros: `key=ENV('STEAM_API_KEY')` & `steamids={SteamID64}`
- Datos Extraídos: `personaname`, `avatarfull`, `vac_banned`.