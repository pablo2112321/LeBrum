from typing import Any

from .models import Notificacion


def notificaciones_usuario(request: Any) -> dict[str, Any]:
    """Expone el centro de notificaciones en todas las plantillas."""
    if not request.user.is_authenticated:
        return {
            'notificaciones': [],
            'notificaciones_no_leidas': [],
            'notificaciones_no_leidas_count': 0,
        }

    notificaciones = list(
        Notificacion.objects.filter(usuario=request.user)
        .order_by('-creada_el')[:10]
    )
    no_leidas = [notificacion for notificacion in notificaciones if notificacion.leida is False]
    return {
        'notificaciones': notificaciones,
        'notificaciones_no_leidas': no_leidas,
        'notificaciones_no_leidas_count': Notificacion.objects.filter(
            usuario=request.user,
            leida=False,
        ).count(),
    }
