from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
import re


# Fondos de perfil seleccionables desde la Tienda (Slot "Fondo de Perfil")
FONDOS_DISPONIBLES = [
    ('carbono', 'Carbono Neón'),
    ('asfalto', 'Asfalto Industrial'),
    ('rejilla-industrial', 'Rejilla Industrial'),
    ('scanlines', 'Scanlines'),
]


def validar_riot_id(valor):
    """Prepara el campo riot_id para la futura API de Riot Games
    (Match-v5): el valor debe respetar el formato Nombre#Etiqueta."""
    if valor and valor.strip():
        if not re.match(r'^[A-Za-z0-9À-ÿ_.\- ]+#[A-Za-z0-9_\-]{2,}$', valor.strip()):
            raise ValidationError(
                'El Riot ID debe usar el formato "Nombre#Etiqueta" (ej: Legión#777).'
            )


class Usuario(AbstractUser):
    ROLES = [
        ('Dueño', 'Dueño de la Plataforma'),
        ('Admin', 'Administrador'),
        ('Jugador', 'Jugador'),
    ]

    rol_plataforma = models.CharField(
        max_length=20,
        choices=ROLES,
        default='Jugador'
    )

    # Tag de jugador para la escena competitiva (ej: "Legión#777")
    tag_jugador = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='Tag de Jugador'
    )

    # IDs de juegos para inscripciones en torneos.
    # NOTA FUTURA: serán obligatorios para unirse a torneos competitivos.
    riot_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        validators=[validar_riot_id],
        verbose_name='Riot ID',
        help_text='Tu Riot ID en formato Nombre#Etiqueta (ej: Legión#777).'
    )

    steam_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Steam ID',
        help_text='Tu Steam ID64 (17 dígitos).'
    )

    # Identificador opcional para el Bot Árbitro / Discord
    discord_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True
    )

    # Sistema de Ranking Mundial
    puntos_globales = models.IntegerField(default=0)

    # Billetera virtual de fichas LeBrum
    # Se inicializa en 0 al crear el usuario
    saldo_fichas = models.IntegerField(
        default=0,
        verbose_name='Saldo de Fichas LeBrum'
    )

    # ============================================================
    # SISTEMA DE RANGO "DELABRUMA" (Crew de Graffiti)
    # ============================================================
    # Puntos de experiencia que determinan el rango del jugador.
    puntos_xp = models.IntegerField(
        default=0,
        verbose_name='Puntos XP (Rango DeLaBruma)'
    )

    # ============================================================
    # PERSONALIZACIÓN DE PERFIL (preparación para la Tienda)
    # ============================================================
    # URL del avatar del jugador. Si está vacío se usa la imagen
    # gamer genérica por defecto (img/Usuario.jpg).
    avatar = models.ImageField(
        upload_to='avatares/',
        blank=True,
        null=True,
        verbose_name='Avatar',
        help_text='Imagen de perfil del jugador.'
    )

    # Título equipado por el jugador (Loadout DeLaBruma)
    titulo_equipado = models.CharField(
        max_length=40,
        blank=True,
        default='NOVATO DE LA BRUMA',
        verbose_name='Título Equipado'
    )

    victorias = models.PositiveIntegerField(
        default=0,
        verbose_name='Victorias'
    )

    derrotas = models.PositiveIntegerField(
        default=0,
        verbose_name='Derrotas'
    )

    # Estado equipado (frase visible bajo el nombre en el perfil)
    estado_equipado = models.CharField(
        max_length=60,
        blank=True,
        default='Listo para la batalla',
        verbose_name='Estado Equipado'
    )

    # Estado de conexión actual del agente (HUD en tiempo real)
    estado_conexion = models.CharField(
        max_length=20,
        choices=[
            ('ONLINE', 'ONLINE'),
            ('EN BUSQUEDA', 'EN BUSQUEDA'),
            ('EN BATALLA', 'EN BATALLA'),
            ('OFFLINE', 'OFFLINE'),
        ],
        default='ONLINE',
        verbose_name='Estado de Conexión'
    )

    # Fondo del perfil (Slot de la Tienda). Decide el backdrop de la
    # Landing Page pública del agente.
    fondo_perfil = models.CharField(
        max_length=30,
        choices=FONDOS_DISPONIBLES,
        default='carbono',
        verbose_name='Fondo de Perfil'
    )

    # Catálogos de equipables disponibles (para la tarjeta de selección)
    FONDOS_DISPONIBLES = FONDOS_DISPONIBLES
    TITULOS_DISPONIBLES = [
        ('NOVATO DE LA BRUMA', 'NOVATO DE LA BRUMA'),
        ('OPERADOR', 'OPERADOR'),
        ('CAZATROFEOS', 'CAZATROFEOS'),
        ('FANTASMA', 'FANTASMA'),
        ('GRAFFITI MASTER', 'GRAFFITI MASTER'),
        ('LEYENDA URBANA', 'LEYENDA URBANA'),
        ('IMBATIBLE', 'IMBATIBLE'),
        ('CREW ELITE', 'CREW ELITE'),
    ]

    ESTADOS_DISPONIBLES = [
        ('Listo para la batalla', 'Listo para la batalla'),
        ('Cazando trofeos', 'Cazando trofeos'),
        ('Entrenando en la arena', 'Entrenando en la arena'),
        ('Busco crew', 'Busco crew'),
        ('Modo silencio', 'Modo silencio'),
        ('Fuera de combate', 'Fuera de combate'),
    ]

    ESTADOS_CONEXION = [
        ('ONLINE', 'ONLINE'),
        ('EN BUSQUEDA', 'EN BUSQUEDA'),
        ('EN BATALLA', 'EN BATALLA'),
        ('OFFLINE', 'OFFLINE'),
    ]

    # Escala de rangos oficial de DeLaBruma: (pts mínimos, nombre)
    RANGOS_DELABRUMA = [
        (0,   'Recluta'),
        (100, 'Veterano'),
        (300, 'Avanzado'),
        (500, 'Elite'),
        (800, 'CREW'),
    ]

    @property
    def rango(self):
        """Devuelve el rango actual del jugador según sus puntos XP."""
        for puntos_min, nombre in reversed(self.RANGOS_DELABRUMA):
            if self.puntos_xp >= puntos_min:
                return nombre
        return 'Recluta'

    @property
    def rango_nivel(self):
        """Nivel 0..4 del rango (0 = Recluta, 4 = CREW). Útil para CSS."""
        for indice, (puntos_min, _nombre) in enumerate(self.RANGOS_DELABRUMA):
            if self.puntos_xp < puntos_min:
                return max(0, indice - 1)
        return len(self.RANGOS_DELABRUMA) - 1

    @property
    def rango_siguiente(self):
        """Nombre del rango superior, o None si ya es CREW."""
        for indice, (puntos_min, nombre) in enumerate(self.RANGOS_DELABRUMA):
            if self.puntos_xp < puntos_min:
                return nombre
        return None

    @property
    def progreso_rango(self):
        """Porcentaje de avance hacia el siguiente rango (0-100)."""
        indice_actual = self.rango_nivel
        base = self.RANGOS_DELABRUMA[indice_actual][0]
        if indice_actual >= len(self.RANGOS_DELABRUMA) - 1:
            return 100
        tope = self.RANGOS_DELABRUMA[indice_actual + 1][0]
        avance = self.puntos_xp - base
        total = tope - base
        return max(0, min(100, round((avance / total) * 100))) if total > 0 else 0

    @property
    def trofeos_ganados(self):
        """Cantidad de torneos finalizados donde su equipo (o el capitaneado)
        fue declarado ganador. Devuelve 0 si aún no hay datos."""
        try:
            from torneos.models import Torneo
            from equipos.models import Equipo

            torneos_ganados = Torneo.objects.filter(
                ganador__isnull=False,
                estado=Torneo.ESTADO_FINALIZADO,
            ).values_list('ganador_id', flat=True)

            equipos_ganadores_ids = list(torneos_ganados)
            if not equipos_ganadores_ids:
                return 0

            # Equipos donde el jugador participó (como miembro o capitán)
            equipos_del_jugador = self.equipos_unidos.filter(
                equipo_id__in=equipos_ganadores_ids
            ).values_list('equipo_id', flat=True)

            return len(set(equipos_del_jugador))
        except Exception:
            return 0

    @property
    def tiene_id_competitivo(self):
        """True si el agente registró al menos un ID competitivo
        (Riot ID o Steam ID). Sin él, el perfil se marca 'Pendiente'."""
        return bool((self.riot_id and self.riot_id.strip()) or
                    (self.steam_id and self.steam_id.strip()))

    def __str__(self):
        return self.username


class CuentaJuego(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='cuentas_juego'
    )
    plataforma = models.CharField(max_length=50)
    id_externo = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.usuario.username} - {self.plataforma} ({self.id_externo})"


class Notificacion(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    mensaje = models.CharField(max_length=255)
    url_destino = models.CharField(max_length=255, blank=True, default='')
    icono = models.CharField(max_length=50, default='fas fa-bell')
    tipo = models.CharField(max_length=50, default='general')
    leida = models.BooleanField(default=False)
    creada_el = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificación para {self.usuario.username}: {self.mensaje[:30]}"

    @property
    def texto(self):
        """Mantiene compatibilidad con las plantillas heredadas."""
        return self.mensaje
