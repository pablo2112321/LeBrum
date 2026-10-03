import secrets

from django.db import transaction
from django.utils import timezone

from .models import SolicitudPrivacidad, Usuario


@transaction.atomic
def anonimizar_cuenta(usuario: Usuario) -> None:
    """Anonimiza los datos personales y desactiva la cuenta del titular."""
    suffix = secrets.token_hex(8)
    usuario.username = f'anonymized_{usuario.pk}_{suffix}'
    usuario.email = ''
    usuario.first_name = ''
    usuario.last_name = ''
    usuario.tag_jugador = ''
    usuario.riot_id = None
    usuario.steam_id = None
    usuario.discord_id = None
    usuario.avatar.delete(save=False)
    usuario.avatar = None
    usuario.set_unusable_password()
    usuario.is_active = False
    usuario.save(update_fields=[
        'username', 'email', 'first_name', 'last_name', 'tag_jugador',
        'riot_id', 'steam_id', 'discord_id', 'avatar', 'password', 'is_active',
    ])


@transaction.atomic
def procesar_solicitud_privacidad(
    solicitud: SolicitudPrivacidad,
    procesada_por: Usuario,
) -> SolicitudPrivacidad:
    """Procesa una solicitud aprobada y registra quién la gestionó."""
    solicitud.estado = 'processing'
    solicitud.procesada_por = procesada_por
    solicitud.save(update_fields=['estado', 'procesada_por'])

    if solicitud.tipo == 'erasure':
        anonimizar_cuenta(solicitud.usuario)

    solicitud.estado = 'completed'
    solicitud.procesada_el = timezone.now()
    solicitud.save(update_fields=['estado', 'procesada_el'])
    return solicitud
