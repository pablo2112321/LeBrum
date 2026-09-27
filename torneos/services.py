"""Servicios de dominio para la generación y resolución de brackets."""

import math
import random
from typing import Final

from django.db import transaction
from django.db.models import F

from equipos.models import Equipo
from usuarios.models import Notificacion, Usuario
from auditoria.services import record_audit_event

from .models import (
    EventoRating,
    Inscripcion,
    Partida,
    RecompensaPartida,
    Torneo,
)
from .realtime import publish_match_event


_ESTADOS_CIERRE: Final[set[str]] = {
    Torneo.ESTADO_CERRADO,
    Torneo.ESTADO_LLENO,
}


@transaction.atomic
def procesar_inscripcion(torneo: Torneo, equipo: Equipo) -> Inscripcion:
    """Crea una inscripción reservando una plaza de forma atómica."""
    with transaction.atomic():
        torneo = Torneo.objects.select_for_update().get(pk=torneo.pk)
        if Inscripcion.objects.filter(torneo=torneo, equipo=equipo).exists():
            raise ValueError('El equipo ya está inscrito en este torneo.')
        if torneo.estado != Torneo.ESTADO_ABIERTO:
            raise ValueError('El torneo no admite nuevas inscripciones.')
        if equipo.modo != torneo.modalidad:
            raise ValueError('La modalidad del equipo debe coincidir con la del torneo.')
        if torneo.plazas_ocupadas >= torneo.cupo_maximo:
            raise ValueError('El torneo no tiene plazas disponibles.')

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


@transaction.atomic
def pagar_inscripcion(inscripcion: Inscripcion, usuario: Usuario) -> Inscripcion:
    """Debita fichas y confirma un pago sin permitir dobles cargos."""
    locked = Inscripcion.objects.select_for_update().select_related(
        'torneo',
    ).get(pk=inscripcion.pk)
    if locked.estado_pago == Inscripcion.ESTADO_PAGADO:
        if locked.pagador_id not in (None, usuario.pk):
            raise ValueError('La inscripción ya fue pagada por otro usuario.')
        return locked
    if locked.estado_pago not in (
        Inscripcion.ESTADO_PENDIENTE,
        Inscripcion.ESTADO_RECHAZADO,
    ):
        raise ValueError('La inscripción no admite transiciones de pago.')

    torneo = Torneo.objects.select_for_update().get(pk=locked.torneo_id)
    usuario = Usuario.objects.select_for_update().get(pk=usuario.pk)
    cuota = torneo.cuota
    if cuota < 0 or cuota != cuota.to_integral_value():
        raise ValueError('La cuota del torneo debe ser una cantidad entera no negativa.')
    fichas = int(cuota)
    if torneo.inscripciones.exclude(
        estado_pago=Inscripcion.ESTADO_RECHAZADO,
    ).count() > torneo.cupo_maximo:
        raise ValueError('El torneo ha superado su capacidad; el pago fue cancelado.')
    if usuario.saldo_fichas < fichas:
        raise ValueError('Saldo insuficiente en fichas LeBrum para completar la inscripción.')

    usuario.saldo_fichas -= fichas
    locked.fichas_usadas = fichas
    locked.pagador = usuario
    locked.estado_pago = Inscripcion.ESTADO_PAGADO
    usuario.save(update_fields=['saldo_fichas'])
    locked.save(update_fields=['fichas_usadas', 'pagador', 'estado_pago'])
    record_audit_event(
        'balance_change',
        actor=usuario,
        target=usuario,
        metadata={'before': usuario.saldo_fichas + fichas, 'after': usuario.saldo_fichas,
                  'source': 'payment'},
    )
    record_audit_event(
        'payment_state_change',
        actor=usuario,
        target=locked,
        metadata={'before': Inscripcion.ESTADO_PENDIENTE, 'after': locked.estado_pago,
                  'fichas': fichas, 'source': 'payment'},
    )
    return locked


@transaction.atomic
def confirmar_pago_manual(inscripcion: Inscripcion) -> Inscripcion:
    """Confirma un pago externo sin volver a cobrar fichas al usuario."""
    locked = Inscripcion.objects.select_for_update().get(pk=inscripcion.pk)
    if locked.estado_pago == Inscripcion.ESTADO_PAGADO:
        return locked
    if locked.estado_pago not in (
        Inscripcion.ESTADO_PENDIENTE,
        Inscripcion.ESTADO_RECHAZADO,
    ):
        raise ValueError('La inscripción no admite confirmación manual.')
    locked.estado_pago = Inscripcion.ESTADO_PAGADO
    locked.save(update_fields=['estado_pago'])
    return locked


def _es_potencia_de_dos(valor: int) -> bool:
    return valor > 1 and valor & (valor - 1) == 0


def _siguiente_potencia_de_dos(valor: int) -> int:
    """Devuelve el tamaño de bracket mínimo para un número de equipos."""
    resultado = 2
    while resultado < valor:
        resultado *= 2
    return resultado


@transaction.atomic
def generar_bracket(torneo: Torneo) -> list[Partida]:
    """Genera la primera ronda, incluyendo avances automáticos cuando procede."""
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
    if len(equipos) < 2:
        raise ValueError(
            'El bracket requiere al menos dos inscripciones pagadas.'
        )

    random.SystemRandom().shuffle(equipos)
    tamano_bracket = _siguiente_potencia_de_dos(len(equipos))
    byes = tamano_bracket - len(equipos)
    pairs: list[tuple[int | None, int | None]] = [
        (equipo_id, None) for equipo_id in equipos[:byes]
    ]
    remaining = equipos[byes:]
    pairs.extend(
        (remaining[indice], remaining[indice + 1])
        for indice in range(0, len(remaining), 2)
    )
    partidas = [
        Partida(
            torneo=torneo,
            equipo_local_id=local_id,
            equipo_visitante_id=visitante_id,
            ronda='1',
            numero_partida=numero,
            estado=(
                Partida.ESTADO_FINALIZADO
                if local_id is not None and visitante_id is None
                else Partida.ESTADO_PENDIENTE
            ),
            ganador_id=(
                local_id
                if local_id is not None and visitante_id is None
                else None
            ),
            es_bye=local_id is not None and visitante_id is None,
        )
        for numero, (local_id, visitante_id) in enumerate(pairs, start=1)
    ]
    Partida.objects.bulk_create(partidas)
    for partida in partidas:
        if partida.es_bye and partida.equipo_local_id:
            equipo = Equipo.objects.get(pk=partida.equipo_local_id)
            _asignar_ganador_siguiente(partida, equipo)
    rondas = int(math.log2(tamano_bracket))
    for ronda in range(2, rondas + 1):
        partidos_en_ronda = tamano_bracket // (2 ** ronda)
        for numero in range(1, partidos_en_ronda + 1):
            Partida.objects.get_or_create(
                torneo=torneo,
                ronda=str(ronda),
                numero_partida=numero,
                defaults={'estado': Partida.ESTADO_PENDIENTE},
            )
    torneo.estado = Torneo.ESTADO_EN_CURSO
    torneo.save(update_fields=['estado'])
    return list(
        torneo.partidas.filter(ronda='1').order_by('numero_partida')
    )


def _otorgar_recompensas_partida(
    partida: Partida,
    equipo: Equipo,
    *,
    victorias: int = 0,
    derrotas: int = 0,
    xp: int = 0,
) -> None:
    """Registra y aplica la recompensa de cada jugador una sola vez."""
    usuarios_ids = equipo.miembros.values_list('usuario_id', flat=True)
    for usuario_id in usuarios_ids:
        recompensa, creada = RecompensaPartida.objects.get_or_create(
            partida=partida,
            usuario_id=usuario_id,
            defaults={'xp_otorgada': xp},
        )
        if not creada:
            continue
        Usuario.objects.filter(pk=usuario_id).update(
            victorias=F('victorias') + victorias,
            derrotas=F('derrotas') + derrotas,
            puntos_xp=F('puntos_xp') + xp,
        )
        if victorias:
            Notificacion.objects.create(
                usuario_id=usuario_id,
                mensaje=(
                    '¡Victoria confirmada! Has avanzado a la siguiente ronda.'
                ),
                url_destino=f'/torneos/partida/{partida.pk}/',
                tipo='resultado',
            )


def _asignar_ganador_siguiente(partida: Partida, equipo_ganador: Equipo) -> Partida:
            """Coloca un ganador en su posición de la siguiente ronda."""
            siguiente_numero = (partida.numero_partida + 1) // 2
            es_local = partida.numero_partida % 2 == 1
            campo_equipo = 'equipo_local' if es_local else 'equipo_visitante'
            siguiente, creado = Partida.objects.get_or_create(
                torneo=partida.torneo,
                ronda=str(int(partida.ronda or '1') + 1),
                numero_partida=siguiente_numero,
                defaults={
                    'estado': Partida.ESTADO_PENDIENTE,
                    campo_equipo: equipo_ganador,
                },
            )
            if not creado and getattr(siguiente, f'{campo_equipo}_id') is None:
                setattr(siguiente, campo_equipo, equipo_ganador)
                siguiente.save(update_fields=[campo_equipo])
            return siguiente


def _actualizar_rating(
            partida: Partida,
            equipo_ganador: Equipo,
            equipo_perdedor: Equipo,
) -> None:
            """Actualiza el rating ELO individual usando el promedio de cada equipo."""
            ganadores = list(
                Usuario.objects.select_for_update().filter(
                    equipos_unidos__equipo=equipo_ganador,
                ).distinct()
            )
            perdedores = list(
                Usuario.objects.select_for_update().filter(
                    equipos_unidos__equipo=equipo_perdedor,
                ).distinct()
            )
            if not ganadores or not perdedores:
                return

            promedio_ganador = sum(usuario.rating_competitivo for usuario in ganadores) / len(ganadores)
            promedio_perdedor = sum(usuario.rating_competitivo for usuario in perdedores) / len(perdedores)
            esperado = 1 / (1 + 10 ** ((promedio_perdedor - promedio_ganador) / 400))
            delta = max(1, round(32 * (1 - esperado)))

            for usuario in ganadores:
                anterior = usuario.rating_competitivo
                nuevo = anterior + delta
                Usuario.objects.filter(pk=usuario.pk).update(rating_competitivo=nuevo)
                EventoRating.objects.create(
                    usuario=usuario,
                    partida=partida,
                    torneo=partida.torneo,
                    rating_anterior=anterior,
                    rating_nuevo=nuevo,
                    delta=delta,
                    resultado=EventoRating.RESULTADO_VICTORIA,
                )
            for usuario in perdedores:
                anterior = usuario.rating_competitivo
                nuevo = max(100, anterior - delta)
                Usuario.objects.filter(pk=usuario.pk).update(rating_competitivo=nuevo)
                EventoRating.objects.create(
                    usuario=usuario,
                    partida=partida,
                    torneo=partida.torneo,
                    rating_anterior=anterior,
                    rating_nuevo=nuevo,
                    delta=nuevo - anterior,
                    resultado=EventoRating.RESULTADO_DERROTA,
                )


@transaction.atomic
def procesar_resultado(
    partida: Partida,
    equipo_ganador: Equipo,
    *,
    force: bool = False,
) -> Partida | None:
    """Finaliza una partida y coloca al ganador en la siguiente ronda."""
    partida = Partida.objects.select_for_update().select_related('torneo').get(pk=partida.pk)
    if partida.estado == Partida.ESTADO_FINALIZADO:
        raise ValueError('La partida ya fue finalizada.')
    if partida.en_disputa and not force:
        raise ValueError('La partida está en disputa y requiere intervención administrativa.')
    if equipo_ganador not in (partida.equipo_local, partida.equipo_visitante):
        raise ValueError('El equipo ganador debe participar en la partida.')
    if partida.equipo_local is None or partida.equipo_visitante is None:
        raise ValueError('No se puede finalizar una partida con equipos sin asignar.')

    equipo_perdedor = (
        partida.equipo_visitante
        if equipo_ganador.pk == partida.equipo_local_id
        else partida.equipo_local
    )
    partida.estado = Partida.ESTADO_FINALIZADO
    partida.ganador = equipo_ganador
    partida.en_disputa = False
    partida.detalle_disputa = ''
    partida.save(update_fields=['estado', 'ganador', 'en_disputa', 'detalle_disputa'])

    _otorgar_recompensas_partida(
        partida,
        equipo_ganador,
        victorias=1,
        xp=100,
    )
    _otorgar_recompensas_partida(
        partida,
        equipo_perdedor,
        derrotas=1,
        xp=10,
    )
    _actualizar_rating(partida, equipo_ganador, equipo_perdedor)

    ronda_actual = int(partida.ronda or '1')
    partidas_primera_ronda = partida.torneo.partidas.filter(ronda='1').count()
    total_rondas = int(math.log2(partidas_primera_ronda)) + 1
    if ronda_actual >= total_rondas:
        partida.torneo.estado = Torneo.ESTADO_FINALIZADO
        partida.torneo.save(update_fields=['estado'])
        transaction.on_commit(lambda: publish_match_event(partida))
        return None

    siguiente_ronda = str(ronda_actual + 1)
    siguiente = _asignar_ganador_siguiente(partida, equipo_ganador)
    campo_equipo = (
        'equipo_local'
        if partida.numero_partida % 2 == 1
        else 'equipo_visitante'
    )
    if getattr(siguiente, f'{campo_equipo}_id') != equipo_ganador.pk:
        raise ValueError('La siguiente partida ya tiene ese puesto asignado.')
    transaction.on_commit(lambda: publish_match_event(partida))
    transaction.on_commit(lambda: publish_match_event(siguiente))
    return siguiente
