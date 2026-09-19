from django.shortcuts import render
from usuarios.models import Usuario, Notificacion
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

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