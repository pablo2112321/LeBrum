from typing import Any

from .models import Partida, Torneo
from equipos.models import Equipo


def admin_overview(request: Any) -> dict[str, Any]:
    """Expone métricas competitivas para el dashboard administrativo."""
    if not request.path.startswith('/ojo-de-halcon/'):
        return {}

    return {
        'admin_torneos_activos': Torneo.objects.filter(
            estado=Torneo.ESTADO_EN_CURSO,
        ).count(),
        'admin_partidas_pendientes': Partida.objects.filter(
            estado=Partida.ESTADO_PENDIENTE,
        ).count(),
        'admin_equipos_totales': Equipo.objects.count(),
        'admin_torneos_en_curso': Torneo.objects.filter(
            estado=Torneo.ESTADO_EN_CURSO,
        ).prefetch_related('partidas'),
    }
