"""Servicios de dominio para la generación y resolución de brackets."""

import math
import random
from typing import Final

from django.db import transaction

from equipos.models import Equipo

from .models import Inscripcion, Partida, Torneo


_ESTADOS_CIERRE: Final[set[str]] = {
    Torneo.ESTADO_CERRADO,
    Torneo.ESTADO_LLENO,
}


@transaction.atomic
def procesar_inscripcion(torneo: Torneo, equipo: Equipo) -> Inscripcion:
    """Crea una inscripción y simula la aprobación del pago gratuito."""
    if Inscripcion.objects.filter(torneo=torneo, equipo=equipo).exists():
        raise ValueError('El equipo ya está inscrito en este torneo.')
    if not torneo.puede_inscribir_equipo(equipo):
        raise ValueError('El equipo no puede inscribirse en este torneo.')

    estado = (
        Inscripcion.ESTADO_PAGADO
        if torneo.cuota == 0
        else Inscripcion.ESTADO_PENDIENTE
    )
    return Inscripcion.objects.create(
        torneo=torneo,
        equipo=equipo,
        estado_pago=estado,
    )


def _es_potencia_de_dos(valor: int) -> bool:
    return valor > 1 and valor & (valor - 1) == 0


@transaction.atomic
def generar_bracket(torneo: Torneo) -> list[Partida]:
    """Genera la primera ronda de un torneo con inscripciones confirmadas."""
    if torneo.estado not in _ESTADOS_CIERRE:
        raise ValueError('El torneo debe estar cerrado o lleno para generar el bracket.')
    if torneo.partidas.exists():
        raise ValueError('El torneo ya tiene partidas generadas.')

    equipos = list(
        Inscripcion.objects.filter(
            torneo=torneo,
            estado_pago=Inscripcion.ESTADO_PAGADO,
        ).select_related('equipo').values_list('equipo_id', flat=True)
    )
    if len(equipos) < 2 or not _es_potencia_de_dos(len(equipos)):
        raise ValueError(
            'El bracket requiere al menos dos inscripciones pagadas y una cantidad '
            'completa en potencia de dos.'
        )

    random.SystemRandom().shuffle(equipos)
    partidas = [
        Partida(
            torneo=torneo,
            equipo_local_id=equipos[indice],
            equipo_visitante_id=equipos[indice + 1],
            ronda='1',
            numero_partida=(indice // 2) + 1,
            estado=Partida.ESTADO_PENDIENTE,
        )
        for indice in range(0, len(equipos), 2)
    ]
    Partida.objects.bulk_create(partidas)
    torneo.estado = Torneo.ESTADO_EN_CURSO
    torneo.save(update_fields=['estado'])
    return list(
        torneo.partidas.filter(ronda='1').order_by('numero_partida')
    )


@transaction.atomic
def procesar_resultado(partida: Partida, equipo_ganador: Equipo) -> Partida | None:
    """Finaliza una partida y coloca al ganador en la siguiente ronda."""
    partida = Partida.objects.select_for_update().select_related('torneo').get(pk=partida.pk)
    if partida.estado == Partida.ESTADO_FINALIZADO:
        raise ValueError('La partida ya fue finalizada.')
    if equipo_ganador not in (partida.equipo_local, partida.equipo_visitante):
        raise ValueError('El equipo ganador debe participar en la partida.')
    if partida.equipo_local is None or partida.equipo_visitante is None:
        raise ValueError('No se puede finalizar una partida con equipos sin asignar.')

    partida.estado = Partida.ESTADO_FINALIZADO
    partida.ganador = equipo_ganador
    partida.save(update_fields=['estado', 'ganador'])

    ronda_actual = int(partida.ronda or '1')
    partidas_primera_ronda = partida.torneo.partidas.filter(ronda='1').count()
    total_rondas = int(math.log2(partidas_primera_ronda)) + 1
    if ronda_actual >= total_rondas:
        partida.torneo.estado = Torneo.ESTADO_FINALIZADO
        partida.torneo.save(update_fields=['estado'])
        return None

    siguiente_ronda = str(ronda_actual + 1)
    siguiente_numero = (partida.numero_partida + 1) // 2
    es_local = partida.numero_partida % 2 == 1
    defaults = {
        'estado': Partida.ESTADO_PENDIENTE,
        'equipo_local' if es_local else 'equipo_visitante': equipo_ganador,
    }
    siguiente, _ = Partida.objects.get_or_create(
        torneo=partida.torneo,
        ronda=siguiente_ronda,
        numero_partida=siguiente_numero,
        defaults=defaults,
    )
    campo_equipo = 'equipo_local' if es_local else 'equipo_visitante'
    if getattr(siguiente, f'{campo_equipo}_id') is None:
        setattr(siguiente, campo_equipo, equipo_ganador)
        siguiente.save(update_fields=[campo_equipo])
    elif getattr(siguiente, f'{campo_equipo}_id') != equipo_ganador.pk:
        raise ValueError('La siguiente partida ya tiene ese puesto asignado.')
    return siguiente
