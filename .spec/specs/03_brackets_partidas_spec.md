# ESPECIFICACIÓN 03: BRACKETS (LLAVES), PARTIDAS Y REPORTE DE RESULTADOS

## 1. ESTRUCTURA DEL BRACKET
- **Formato:** Eliminación Directa de 16 Equipos.
- **Rondas:** - Octavos de Final (16 equipos -> 8 partidas)
  - Cuartos de Final (8 equipos -> 4 partidas)
  - Semifinales (4 equipos -> 2 partidas)
  - Gran Final (2 equipos -> 1 campeón)

## 2. REPORTE Y VALIDACIÓN DE RESULTADOS
1. Cada partida asigna un enfrentamiento entre `Equipo_A` y `Equipo_B`.
2. Al finalizar la partida, los **Capitanes** deben subir una captura de pantalla del resultado del juego y declarar la victoria.
3. **Casos de Confirmación:**
   - **Coincidencia:** Si ambos capitanes reportan el mismo ganador, la vista actualiza la partida a `"FINALIZADA"` y avanza automáticamente al ganador a la siguiente ronda del bracket.
   - **Conflicto / Disputa:** Si los reportes difieren o un capitán reclama trampa, la partida pasa inmediatamente a estado `"DISPUTA"`.

## 3. MODELO DE DATOS (`torneos/models.py`)
- `Partida`:
  - `torneo`: ForeignKey(Torneo)
  - `ronda`: IntegerField (1=Octavos, 2=Cuartos, 3=Semi, 4=Final)
  - `equipo_a`: ForeignKey(Equipo, related_name='partidas_a')
  - `equipo_b`: ForeignKey(Equipo, related_name='partidas_b')
  - `ganador`: ForeignKey(Equipo, null=True, blank=True)
  - `estado`: CharField (Choices: 'PENDIENTE', 'EN_CURSO', 'DISPUTA', 'FINALIZADA')
  - `captura_equipo_a`: ImageField(null=True, blank=True)
  - `captura_equipo_b`: ImageField(null=True, blank=True)