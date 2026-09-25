from typing import Any

from .models import Equipo


def jugador_equipo(request) -> dict[str, Any]:
    """Expone el primer equipo del jugador para la navegación global."""
    if not request.user.is_authenticated:
        return {'mi_equipo': None}

    equipo = (
        Equipo.objects.filter(miembros__usuario=request.user)
        .select_related('capitan')
        .first()
    )
    return {'mi_equipo': equipo}
