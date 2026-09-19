from django.db import models, transaction
from django.conf import settings


class Equipo(models.Model):
    MODOS = [
        ('5v5', '5v5'),
        ('2v2', '2v2'),
        ('1v1', '1v1'),
    ]

    capitan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='equipos_capitaneados',
        verbose_name='Capitán'
    )

    torneo = models.ForeignKey(
        'torneos.Torneo',
        on_delete=models.CASCADE,
        related_name='equipos',
        verbose_name='Torneo',
        blank=True,
        null=True,
    )

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre del equipo'
    )

    # Tag oficial de la Crew (ej: [DLB])
    tag = models.CharField(
        max_length=12,
        blank=True,
        default='',
        verbose_name='Tag oficial',
        help_text='Siglas oficiales de la crew (ej: [DLB]).'
    )

    modo = models.CharField(
        max_length=10,
        choices=MODOS,
        default='5v5',
        verbose_name='Modo'
    )

    logo = models.URLField(
        blank=True,
        null=True,
        verbose_name='Logo'
    )

    banner = models.URLField(
        blank=True,
        null=True,
        verbose_name='Banner de la Crew'
    )

    def __str__(self):
        return f"{self.nombre} ({self.torneo.nombre})"

    def save(self, *args, **kwargs):
        es_nuevo = self.pk is None

        if es_nuevo:
            if self.torneo is None:
                raise ValueError('El equipo debe pertenecer a un torneo activo.')
            if self.torneo.estado != self.torneo.ESTADO_ABIERTO:
                raise ValueError('Solo se puede crear un equipo dentro de un torneo abierto para inscripciones.')
            if self.modo != self.torneo.modalidad:
                raise ValueError('La modalidad del equipo debe coincidir con la del torneo.')
            if self.torneo.equipos.count() >= self.torneo.cupo_maximo:
                raise ValueError('El torneo ya alcanzó su cupo máximo de equipos.')

        with transaction.atomic():
            super().save(*args, **kwargs)

            if es_nuevo:
                MiembroEquipo.objects.create(
                    equipo=self,
                    usuario=self.capitan,
                    es_capitan=True
                )

    @property
    def tiene_capitan(self):
        return self.miembros.filter(es_capitan=True).exists() or self.capitan is not None

    @property
    def limite_miembros(self):
        """Capacidad de la escuadra según la modalidad (5v5 -> 5, 2v2 -> 2, 1v1 -> 1)."""
        try:
            return int(str(self.modo).split('v')[0])
        except (ValueError, IndexError):
            return 5

    @property
    def miembros_count(self):
        return self.miembros.count()

    @property
    def roster_lleno(self):
        return self.miembros_count >= self.limite_miembros

    @property
    def torneos_ganados(self):
        """Partidas finalizadas donde esta crew fue declarada ganadora."""
        from torneos.models import Partida
        return Partida.objects.filter(
            ganador=self,
            estado=Partida.ESTADO_FINALIZADO,
        ).count()

    @property
    def partidas_totales(self):
        return self.partidas_como_a.count() + self.partidas_como_b.count()

    @property
    def victorias(self):
        return self.partidas_ganadas.count()

    @property
    def winrate(self):
        """Porcentaje de victorias sobre el total de partidas disputadas."""
        total = self.partidas_totales
        if total == 0:
            return 0
        return round((self.victorias / total) * 100)

    @property
    def puntos_crew(self):
        """Suma de XP DeLaBruma de todos los agentes del roster."""
        return sum((m.usuario.puntos_xp for m in self.miembros.all()), 0)


class MiembroEquipo(models.Model):
    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        related_name='miembros',
        verbose_name='Equipo'
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='equipos_unidos',
        verbose_name='Usuario'
    )

    es_capitan = models.BooleanField(
        default=False,
        verbose_name='Es capitán'
    )

    class Meta:
        unique_together = ('equipo', 'usuario')

    def __str__(self):
        return f"{self.usuario.username} - {self.equipo.nombre}"
