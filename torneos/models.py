from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Videojuego(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre del videojuego'
    )

    genero = models.CharField(
        max_length=50,
        verbose_name='Género'
    )

    imagen_portada = models.ImageField(
        upload_to='videojuegos/',
        blank=True,
        null=True,
        verbose_name='Imagen de portada'
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'videojuego'
        verbose_name_plural = 'videojuegos'


class Torneo(models.Model):
    ESTADO_ABIERTO = 'Abierto'
    ESTADO_LLENO = 'Lleno'
    ESTADO_CERRADO = 'Cerrado'
    ESTADO_EN_CURSO = 'En Curso'
    ESTADO_FINALIZADO = 'Finalizado'
    ESTADO_CANCELADO = 'Cancelado'

    ESTADOS = [
        (ESTADO_ABIERTO, 'Abierto para inscripciones'),
        (ESTADO_LLENO, 'Lleno / En espera'),
        (ESTADO_CERRADO, 'Cerrado'),
        (ESTADO_EN_CURSO, 'En curso'),
        (ESTADO_FINALIZADO, 'Finalizado'),
        (ESTADO_CANCELADO, 'Cancelado'),
    ]

    MODOS = [
        ('5v5', '5v5'),
        ('2v2', '2v2'),
        ('1v1', '1v1'),
    ]

    juego = models.ForeignKey(
        Videojuego,
        on_delete=models.RESTRICT,
        related_name='torneos',
        verbose_name='Videojuego'
    )

    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre del torneo'
    )

    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descripción del torneo'
    )

    cuota = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name='Cuota del torneo'
    )

    modalidad = models.CharField(
        max_length=10,
        choices=MODOS,
        default='5v5',
        verbose_name='Modalidad del torneo'
    )

    cupo_maximo = models.PositiveIntegerField(
        default=16,
        verbose_name='Cupo máximo de equipos'
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_ABIERTO,
        verbose_name='Estado del torneo'
    )

    fecha_inicio_primera_ronda = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Inicio de la primera ronda'
    )

    creado_el = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    def __str__(self):
        return self.nombre

    @property
    def inscripciones_completadas(self):
        return self.inscripciones.filter(estado_pago=Inscripcion.ESTADO_PAGADO)

    @property
    def plazas_ocupadas(self):
        return self.inscripciones_completadas.count()

    @property
    def plazas_disponibles(self):
        return max(0, self.cupo_maximo - self.plazas_ocupadas)

    def actualizar_estado_capacidad(self, save_changes=True):
        estado_anterior = self.estado

        if self.plazas_ocupadas >= self.cupo_maximo:
            self.estado = self.ESTADO_LLENO
            if self.fecha_inicio_primera_ronda is None:
                self.fecha_inicio_primera_ronda = timezone.now() + timedelta(minutes=40)
        elif self.estado == self.ESTADO_LLENO:
            self.estado = self.ESTADO_ABIERTO
            self.fecha_inicio_primera_ronda = None

        if save_changes and self.estado != estado_anterior:
            self.save(update_fields=['estado', 'fecha_inicio_primera_ronda'])

    def puede_inscribir_equipo(self, equipo):
        if self.estado != self.ESTADO_ABIERTO:
            return False
        if self.plazas_ocupadas >= self.cupo_maximo:
            return False
        if equipo.modo != self.modalidad:
            return False
        if self.inscripciones.filter(equipo=equipo).exists():
            return False
        return True

    class Meta:
        verbose_name = 'torneo'
        verbose_name_plural = 'torneos'


class Inscripcion(models.Model):
    ESTADO_PENDIENTE = 'Pendiente'
    ESTADO_PAGADO = 'Pagado'
    ESTADO_RECHAZADO = 'Rechazado'

    ESTADOS_PAGO = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_PAGADO, 'Pagado'),
        (ESTADO_RECHAZADO, 'Rechazado'),
    ]

    torneo = models.ForeignKey(
        Torneo,
        on_delete=models.CASCADE,
        related_name='inscripciones',
        verbose_name='Torneo'
    )

    equipo = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.CASCADE,
        related_name='inscripciones',
        verbose_name='Equipo inscrito'
    )

    estado_pago = models.CharField(
        max_length=20,
        choices=ESTADOS_PAGO,
        default='Pendiente',
        verbose_name='Estado del pago'
    )

    fichas_usadas = models.IntegerField(
        default=0,
        verbose_name='Fichas LeBrum usadas'
    )

    pagador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inscripciones_realizadas',
        verbose_name='Usuario que pagó'
    )

    creado_el = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de inscripción'
    )

    def pagar_inscripcion(self, usuario):
        if self.estado_pago == self.ESTADO_PAGADO:
            return

        if usuario.saldo_fichas < self.torneo.cuota:
            raise ValueError('Saldo insuficiente en fichas LeBrum para completar la inscripción.')

        if not self.torneo.puede_inscribir_equipo(self.equipo):
            raise ValueError('El equipo no puede inscribirse en este torneo.')

        self.fichas_usadas = int(self.torneo.cuota)
        self.pagador = usuario
        self.estado_pago = self.ESTADO_PAGADO

        usuario.saldo_fichas -= self.fichas_usadas
        if usuario.saldo_fichas < 0:
            raise ValueError('El pago dejó saldo negativo, operación cancelada.')

        with transaction.atomic():
            usuario.save(update_fields=['saldo_fichas'])
            self.save()

    class Meta:
        unique_together = ('torneo', 'equipo')
        verbose_name = 'inscripción'
        verbose_name_plural = 'inscripciones'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.torneo.actualizar_estado_capacidad()

    def delete(self, *args, **kwargs):
        torneo = self.torneo
        super().delete(*args, **kwargs)
        torneo.actualizar_estado_capacidad()

    def __str__(self):
        return f"{self.equipo.nombre} - {self.torneo.nombre} ({self.estado_pago})"


class Partida(models.Model):
    ESTADO_PENDIENTE = 'PENDIENTE'
    ESTADO_JUGANDO = 'JUGANDO'
    ESTADO_EN_REVISION = 'EN REVISION'
    ESTADO_FINALIZADO = 'FINALIZADO'
    ESTADO_DISPUTA = ESTADO_EN_REVISION

    ESTADOS_PARTIDA = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_JUGANDO, 'En Curso'),
        (ESTADO_EN_REVISION, 'Disputa'),
        (ESTADO_FINALIZADO, 'Finalizada'),
    ]

    REPORTE_GANADOR = 'GANADOR'
    REPORTE_PERDEDOR = 'PERDEDOR'

    REPORTES = [
        (REPORTE_GANADOR, 'Ganador'),
        (REPORTE_PERDEDOR, 'Perdedor'),
    ]

    HORAS_ESPERA_REVISION = 2

    torneo = models.ForeignKey(
        Torneo,
        on_delete=models.CASCADE,
        related_name='partidas',
        verbose_name='Torneo'
    )

    equipo_local = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.RESTRICT,
        related_name='partidas_como_local',
        blank=True,
        null=True,
        verbose_name='Equipo local'
    )

    equipo_visitante = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.RESTRICT,
        related_name='partidas_como_visitante',
        blank=True,
        null=True,
        verbose_name='Equipo visitante'
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_PARTIDA,
        default=ESTADO_PENDIENTE,
        verbose_name='Estado'
    )

    ganador = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='partidas_ganadas',
        verbose_name='Equipo ganador'
    )

    reporte_equipo_local = models.CharField(
        max_length=10,
        choices=REPORTES,
        null=True,
        blank=True,
        verbose_name='Reporte del equipo local'
    )

    reporte_equipo_visitante = models.CharField(
        max_length=10,
        choices=REPORTES,
        null=True,
        blank=True,
        verbose_name='Reporte del equipo visitante'
    )

    evidencia_victoria = models.ImageField(
        upload_to='evidencias_partidas/',
        null=True,
        blank=True,
        verbose_name='Evidencia de victoria'
    )

    reporte_creado_el = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha del primer reporte'
    )

    ronda = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Ronda'
    )

    numero_partida = models.PositiveIntegerField(
        default=1,
        verbose_name='Número de partida',
        help_text='Posición de la partida dentro de su ronda.',
    )

    fecha_hora_programada = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha y hora programada'
    )

    estadisticas_detalladas = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Estadísticas detalladas'
    )

    @property
    def enfrentamiento(self):
        local = self.equipo_local.nombre if self.equipo_local else 'Por definir'
        visitante = self.equipo_visitante.nombre if self.equipo_visitante else 'Por definir'
        return f"{local} vs {visitante}"

    def aplicar_reporte(self, equipo, resultado, evidencia=None):
        if self.estado == self.ESTADO_FINALIZADO:
            raise ValueError('La partida ya está finalizada.')

        if resultado not in dict(self.REPORTES):
            raise ValueError('Resultado de reporte inválido.')

        if equipo == self.equipo_local:
            self.reporte_equipo_local = resultado
        elif equipo == self.equipo_visitante:
            self.reporte_equipo_visitante = resultado
        else:
            raise ValueError('El equipo no participa en esta partida.')

        if evidencia is not None:
            self.evidencia_victoria = evidencia

        if self.reporte_creado_el is None:
            self.reporte_creado_el = timezone.now()

        self.save()
        self._resolver_automaticamente()

    def _resolver_automaticamente(self):
        reporte_a = self.reporte_equipo_local
        reporte_b = self.reporte_equipo_visitante

        if reporte_a == self.REPORTE_GANADOR and reporte_b == self.REPORTE_PERDEDOR:
            self.ganador = self.equipo_local
            self.estado = self.ESTADO_FINALIZADO
        elif reporte_a == self.REPORTE_PERDEDOR and reporte_b == self.REPORTE_GANADOR:
            self.ganador = self.equipo_visitante
            self.estado = self.ESTADO_FINALIZADO
        elif reporte_a == self.REPORTE_GANADOR and reporte_b == self.REPORTE_GANADOR:
            self.ganador = None
            self.estado = self.ESTADO_EN_REVISION
        elif reporte_a == self.REPORTE_PERDEDOR and reporte_b == self.REPORTE_PERDEDOR:
            self.ganador = None
            self.estado = self.ESTADO_EN_REVISION
        else:
            self.estado = self.ESTADO_JUGANDO

        self.save(update_fields=['ganador', 'estado'])

    def revisar_vencimientos(self):
        """Si un equipo reclamó victoria y el rival no confirmó derrota en
        HORAS_ESPERA_REVISION, la partida escala a EN REVISION."""
        if self.reporte_creado_el is None:
            return False
        if self.estado in (self.ESTADO_FINALIZADO, self.ESTADO_EN_REVISION):
            return False

        reporte_a = self.reporte_equipo_local
        reporte_b = self.reporte_equipo_visitante
        reclamo_sin_confirmar = (
            (reporte_a == self.REPORTE_GANADOR and reporte_b is None) or
            (reporte_b == self.REPORTE_GANADOR and reporte_a is None)
        )
        if not reclamo_sin_confirmar:
            return False

        vencido = timezone.now() >= self.reporte_creado_el + timedelta(hours=self.HORAS_ESPERA_REVISION)
        if vencido:
            self.estado = self.ESTADO_EN_REVISION
            self.save(update_fields=['estado'])
            return True
        return False

    def __str__(self):
        return f"{self.enfrentamiento} - {self.ronda or 'Sin ronda definida'}"

    class Meta:
        verbose_name = 'partida'
        verbose_name_plural = 'partidas'
        constraints = [
            models.UniqueConstraint(
                fields=['torneo', 'ronda', 'numero_partida'],
                name='torneo_ronda_numero_partida_unico',
            ),
        ]