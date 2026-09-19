# ESPECIFICACIÓN 02: MOTOR DE TORNEOS Y GESTIÓN DE ESCUADRAS (16 PLAZAS)

## 1. REGLAS DE NEGOCIO Y CICLO DE VIDA DEL TORNEO
1. **Creación de Torneo:** Únicamente creada por el Admin desde el panel "Ojo de Halcón".
   - Un torneo define: Nombre, Videojuego (LoL, Valorant, etc.), Cupo Máximo (`max_equipos`, por defecto 16), Fecha/Hora programada de inicio, Pozo de Premios en Fichas.
2. **Inscripción de Equipos:**
   - Los usuarios solo pueden registrar equipos cuando el torneo está en estado `"ABIERTO"`.
   - El creador del equipo ingresa el nombre de la escuadra y se asigna automáticamente como `capitan`.
3. **Regla Automatizada de las 16 Plazas:**
   - **Milisegundo Exacto 16/16:** Cuando se confirma el registro del equipo número 16, el sistema automáticamente:
     a) Cambia el estado del torneo a `"LLENO"`.
     b) Bloquea nuevas inscripciones.
     c) Activa un temporizador regresivo de **40 minutos** para la generación de brackets e inicio de partidas.
4. **Caso Límite por Tiempo:** Si llega la fecha/hora programada y no se completan los 16 cupos, el Admin puede iniciar el torneo manualmente con los equipos inscritos.

## 2. MODELOS DE DATOS (`torneos/models.py`)
- `Torneo`:
  - `nombre`: CharField
  - `juego`: CharField
  - `estado`: CharField (Choices: 'ABIERTO', 'LLENO', 'EN_CURSO', 'FINALIZADO')
  - `max_equipos`: IntegerField (Default: 16)
  - `fecha_inicio`: DateTimeField
  - `inicio_temporizador`: DateTimeField (null=True, blank=True)
- `Equipo`:
  - `nombre`: CharField
  - `torneo`: ForeignKey(Torneo, related_name='equipos')
  - `capitan`: ForeignKey(User, related_name='equipos_liderados')
  - `fecha_registro`: DateTimeField(auto_now_add=True)