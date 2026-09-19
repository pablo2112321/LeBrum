# ESPECIFICACIÓN 01: AUTENTICACIÓN, PERFILES Y ROLES DE USUARIO

## 1. ROLES DEL SISTEMA
1. **Administrador supremo ("Ojo de Halcón"):**
   - Atributos: `is_staff = True` o `is_superuser = True`.
   - Permisos: Control total del panel Django, creación de torneos, resolución de disputas y acreditación de fichas.
2. **Jugador Común:**
   - Usuario registrado nativo de Django. Posee balance de "Fichas LeBrum", Puntos XP y cuentas de juego vinculadas.
3. **Capitán de Escuadra:**
   - Rol dinámico que adquiere un Jugador Común en el momento exacto en que crea/registra una escuadra para un torneo activo.

## 2. FLUJO DE AUTENTICACIÓN Y REDIRECCIÓN INTELIGENTE
- **Registro (`/registro/`):** Formulario nativo Django. Al registrarse, se crea automáticamente un perfil `PerfilUsuario` asociado mediante `OneToOneField`.
- **Login (`/login/`):**
  - Si el usuario que inicia sesión es Administrador (`is_staff` / `is_superuser`), la vista lo redirige automáticamente a `/admin/` (Panel Ojo de Halcón).
  - Si el usuario es un Jugador Común, lo redirige a la "Arena de Torneos" (`/torneos/`).
- **Logout (`/logout/`):** Cierra sesión de forma segura y redirige al inicio.

## 3. MODELO DE DATOS (`usuarios/models.py`)
- `PerfilUsuario`:
  - `user`: OneToOneField(User)
  - `fichas`: IntegerField (Default: 0)
  - `xp`: IntegerField (Default: 0)
  - `riot_id`: CharField (opcional, ej. "Player#LAN")
  - `steam_id`: CharField (opcional)
  - `discord_tag`: CharField (opcional)
  - `avatar`: ImageField (opcional)