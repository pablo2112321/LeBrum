from django.shortcuts import render
from usuarios.models import Usuario, Notificacion
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from torneos.models import Torneo


class LobbyView(TemplateView):
    """Muestra el lobby competitivo con los torneos disponibles."""

    template_name = 'principal/lobby.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['torneos'] = Torneo.objects.filter(
            estado__in=(Torneo.ESTADO_ABIERTO, Torneo.ESTADO_EN_CURSO),
        ).select_related('juego').order_by('-creado_el')
        contexto['top_jugadores'] = Usuario.objects.order_by('-puntos_globales')[:3]
        contexto['notificaciones'] = []
        contexto['notificaciones_no_leidas_count'] = 0

        if self.request.user.is_authenticated:
            contexto['notificaciones'] = Notificacion.objects.filter(
                usuario=self.request.user,
            ).order_by('-creada_el')[:10]
            contexto['notificaciones_no_leidas_count'] = Notificacion.objects.filter(
                usuario=self.request.user,
                leida=False,
            ).count()
            contexto.update({
                'rango_jugador': self.request.user.rango,
                'rango_nivel_jugador': self.request.user.rango_nivel,
                'xp_jugador': self.request.user.puntos_xp,
                'progreso_rango': self.request.user.progreso_rango,
                'rango_siguiente': self.request.user.rango_siguiente,
                'trofeos_ganados': self.request.user.trofeos_ganados,
                'titulo_equipado': self.request.user.titulo_equipado,
                'estado_equipado': self.request.user.estado_equipado,
                'estado_conexion_css': self.request.user.estado_conexion.lower().replace(' ', '_'),
                'estado_conexion_display': self.request.user.get_estado_conexion_display(),
            })
        return contexto

def lobby_principal(request):
    # 1. Buscamos a los 3 mejores jugadores ordenados por puntos (asumiendo que usas 'puntos_globales')
    top_jugadores = Usuario.objects.order_by('-puntos_globales')[:3]
    
    # 2. Inicializamos las variables de notificaciones
    notificaciones = []
    notificaciones_no_leidas_count = 0
    
    # Si el usuario está autenticado, buscamos sus notificaciones reales
    if request.user.is_authenticated:
        notificaciones = Notificacion.objects.filter(usuario=request.user).order_by('-creada_el')[:10]
        notificaciones_no_leidas_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()

    # 3. Empaquetamos todo
    contexto = {
        'top_jugadores': top_jugadores,
        'notificaciones': notificaciones,
        'notificaciones_no_leidas_count': notificaciones_no_leidas_count,
    }

    # Datos del jugador logueado (rango DeLaBruma + vitrina de trofeos)
    if request.user.is_authenticated:
        contexto['rango_jugador'] = request.user.rango
        contexto['rango_nivel_jugador'] = request.user.rango_nivel
        contexto['xp_jugador'] = request.user.puntos_xp
        contexto['progreso_rango'] = request.user.progreso_rango
        contexto['rango_siguiente'] = request.user.rango_siguiente
        contexto['trofeos_ganados'] = request.user.trofeos_ganados
        # Equipables del Loadout (Hero Banner dinámico)
        contexto['titulo_equipado'] = request.user.titulo_equipado
        contexto['estado_equipado'] = request.user.estado_equipado
        contexto['estado_conexion_css'] = request.user.estado_conexion.lower().replace(' ', '_')
        contexto['estado_conexion_display'] = request.user.get_estado_conexion_display()

    return render(request, 'principal/lobby.html', contexto)

def en_construccion(request):
    return render(request, 'principal/en_construccion.html')

@login_required
def marcar_notificaciones_leidas(request):
    if request.method == 'POST':
        Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# ==========================================
# NUEVA VISTA: RANKING OFICIAL
# ==========================================
def vista_ranking(request):
    # Obtenemos todos los usuarios, los ordenamos de mayor a menor según sus puntos.
    # NOTA: Cambia 'puntos_globales' si en tu base de datos la columna se llama diferente (ej: 'puntos' o 'victorias').
    usuarios_top = Usuario.objects.order_by('-puntos_globales')[:50] # Traemos hasta los 50 mejores
    
    # Pasamos los usuarios al HTML usando la variable "ranking" (que es la que usa tu HTML)
    return render(request, 'principal/ranking.html', {'ranking': usuarios_top})