from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, ListView
from torneos.models import RecompensaPartida
from django.db.models import Q
from .forms import EditarPerfilForm, LoadoutForm, RegistroUsuarioForm
from .models import CuentaJuego, Usuario
from torneos.models import Torneo
import requests  # Para hacer peticiones a la API oficial


# ==========================================
# VALIDACIÓN EN TIEMPO REAL (JSON / AJAX)
# ==========================================
@require_GET
def verificar_usuario(request):
    valor = request.GET.get('valor', '').strip()
    en_uso = bool(valor) and Usuario.objects.filter(username__iexact=valor).exists()
    return JsonResponse({
        'campo': 'username',
        'valor': valor,
        'disponible': not en_uso,
    })


@require_GET
def verificar_tag(request):
    valor = request.GET.get('valor', '').strip()
    en_uso = bool(valor) and Usuario.objects.filter(tag_jugador__iexact=valor).exists()
    return JsonResponse({
        'campo': 'tag_jugador',
        'valor': valor,
        'disponible': not en_uso,
    })


# Función de seguridad: Simulador / PING Real a la API de Riot Games
def verificar_id_juego(plataforma, id_externo):
    if plataforma == 'Riot Games':
        if '#' not in id_externo:
            return False
        try:
            nombre, tag = id_externo.split('#')
        except ValueError:
            return False

        try:
            url_api = f"https://api.henrikdev.xyz/valorant/v1/account/{nombre}/{tag}"
            respuesta = requests.get(url_api, timeout=5)
            return respuesta.status_code == 200
        except requests.exceptions.RequestException:
            return False

    elif plataforma == 'Steam':
        if len(id_externo) != 17 or not id_externo.isdigit():
            return False
        return True

    return False


def registro_view(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)

        if form.is_valid():
            check_riot = request.POST.get('check_riot')
            id_riot = request.POST.get('id_riot')

            check_steam = request.POST.get('check_steam')
            id_steam = request.POST.get('id_steam')

            if check_riot == 'on' and id_riot:
                if not verificar_id_juego('Riot Games', id_riot):
                    messages.error(
                        request,
                        f"El Riot ID '{id_riot}' no existe o es inválido en los servidores oficiales."
                    )
                    return render(request, 'usuarios/registro.html', {'form': form})

            if check_steam == 'on' and id_steam:
                if not verificar_id_juego('Steam', id_steam):
                    messages.error(
                        request,
                        f"El Steam ID '{id_steam}' es inválido. Debe tener 17 dígitos."
                    )
                    return render(request, 'usuarios/registro.html', {'form': form})

            nuevo_usuario = form.save(commit=False)
            nuevo_usuario.rol_plataforma = 'Jugador'
            nuevo_usuario.save()

            if check_riot == 'on' and id_riot:
                nuevo_usuario.riot_id = id_riot
                nuevo_usuario.save(update_fields=['riot_id'])
                CuentaJuego.objects.create(
                    usuario=nuevo_usuario,
                    plataforma='Riot Games',
                    id_externo=id_riot
                )

            if check_steam == 'on' and id_steam:
                nuevo_usuario.steam_id = id_steam
                nuevo_usuario.save(update_fields=['steam_id'])
                CuentaJuego.objects.create(
                    usuario=nuevo_usuario,
                    plataforma='Steam',
                    id_externo=id_steam
                )

            login(request, nuevo_usuario)
            messages.success(request, f"¡Bienvenido a LeBrum, {nuevo_usuario.username}! Tu cuenta fue creada.")
            return redirect('redireccionar_segun_rol')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'usuarios/registro.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('redireccionar_segun_rol')

    if request.method == 'POST':
        datos = request.POST.copy()
        username_or_email = datos.get('username', '').strip()

        if '@' in username_or_email:
            usuario_email = Usuario.objects.filter(email__iexact=username_or_email).first()
            if usuario_email:
                datos['username'] = usuario_email.username

        form = AuthenticationForm(request, data=datos)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, f"Bienvenido de nuevo, {request.user.username}.")
            return redirect('redireccionar_segun_rol')
    else:
        form = AuthenticationForm()

    return render(request, 'usuarios/login.html', {'form': form})


@login_required
def redireccionar_segun_rol(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin:index')
    return redirect('perfil_detalle', nametag=request.user.username)


@staff_member_required(login_url='login')
def ojo_de_halcon(request):
    contexto = {
        'total_jugadores': Usuario.objects.count(),
        'torneos': Torneo.objects.select_related('juego').order_by('-creado_el'),
    }
    return render(request, 'usuarios/ojo_de_halcon.html', contexto)


def logout_usuario(request):
    logout(request)
    return redirect('login')


@login_required
def perfil_redirect(request):
    """/perfil/ -> perfil público del usuario logueado."""
    return redirect('perfil_detalle', nametag=request.user.username)


class PerfilDetalleView(DetailView):
    """Vista pública de la tarjeta competitiva de un jugador."""

    model = Usuario
    template_name = 'usuarios/perfil_jugador.html'
    context_object_name = 'jugador'
    slug_url_kwarg = 'nametag'
    slug_field = 'username'

    def get_queryset(self):
        return Usuario.objects.prefetch_related('equipos_unidos__equipo')

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        jugador = self.object
        total_partidas = jugador.victorias + jugador.derrotas
        contexto['winrate'] = (
            round(jugador.victorias * 100 / total_partidas)
            if total_partidas else 0
        )
        contexto['equipos_jugador'] = [
            miembro.equipo
            for miembro in jugador.equipos_unidos.select_related('equipo')
        ]
        contexto['historial_partidas'] = (
            RecompensaPartida.objects.filter(usuario=jugador)
            .select_related('partida__torneo__juego')
            .order_by('-creada_el')[:10]
        )
        contexto['es_propietario'] = (
            self.request.user.is_authenticated
            and self.request.user.id == jugador.id
        )
        return contexto


class RankingView(ListView):
    """Muestra los cincuenta jugadores con mayor experiencia competitiva."""

    model = Usuario
    template_name = 'usuarios/ranking.html'
    context_object_name = 'jugadores'

    def get_queryset(self):
        return Usuario.objects.order_by('-puntos_xp', '-victorias', 'username')[:50]


@login_required
def editar_perfil(request):
    """Actualiza la identidad visual y competitiva del jugador autenticado."""
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil_detalle', nametag=request.user.username)
    else:
        form = EditarPerfilForm(instance=request.user)
    return render(request, 'usuarios/editar_perfil.html', {'form': form})


def _fondo_css_slug(slug):
    """Valor CSS de background-image según el slug del fondo."""
    fondos = {
        'carbono': "repeating-linear-gradient(135deg, rgba(255,255,255,0.03) 0 2px, transparent 2px 8px), linear-gradient(160deg, #0a0a0f, #12131a)",
        'asfalto': "repeating-linear-gradient(0deg, rgba(0,240,255,0.04) 0 1px, transparent 1px 5px), #0a0a0f",
        'rejilla-industrial': "linear-gradient(rgba(0,240,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(0,240,255,0.06) 1px, transparent 1px), #0a0a0f",
        'scanlines': "repeating-linear-gradient(0deg, rgba(255,230,0,0.04) 0 1px, transparent 1px 4px), #0a0a0f",
    }
    return fondos.get(slug, fondos['carbono'])


def _fondo_css(usuario):
    """Resuelve el valor CSS del background según el fondo equipado."""
    return _fondo_css_slug(usuario.fondo_perfil)


def buscar_jugador(request):
    """Busca un jugador por Username o NameTag y navega a su perfil público."""
    q = request.GET.get('q', '').strip()
    if q:
        usuario = Usuario.objects.filter(
            Q(username__iexact=q) | Q(tag_jugador__iexact=q)
        ).first()
        if usuario:
            return redirect('perfil_detalle', nametag=usuario.username)
        messages.error(request, f"No se encontró a '{q}' en la arena de LeBrum.")
    else:
        messages.error(request, "Escribe un Username o NameTag para buscar.")
    return redirect(request.META.get('HTTP_REFERER') or 'lobby')


def perfil_usuario(request, nametag):
    """Landing Page pública del agente. Si es_dueno=True permite editar,
    guardar el inventario y cambiar el fondo del perfil."""
    usuario_perfil = get_object_or_404(
        Usuario,
        Q(username__iexact=nametag) | Q(tag_jugador__iexact=nametag)
    )
    es_dueno = request.user.is_authenticated and request.user == usuario_perfil

    if request.method == 'POST':
        # Solo el dueño puede modificar su loadout
        if not es_dueno:
            return redirect('perfil_detalle', nametag=usuario_perfil.username)
        form = LoadoutForm(request.POST, instance=usuario_perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Loadout actualizado. ¡Equipamiento y fondo listos!")
            return redirect('perfil_detalle', nametag=usuario_perfil.username)
    else:
        form = LoadoutForm(instance=usuario_perfil) if es_dueno else None

    contexto = {
        'usuario_perfil': usuario_perfil,
        'es_dueno': es_dueno,
        'form': form,
        'titulos_disponibles': [t[1] for t in Usuario.TITULOS_DISPONIBLES],
        'estados_disponibles': [e[1] for e in Usuario.ESTADOS_DISPONIBLES],
        'estados_conexion': [(c[0], c[0].lower().replace(' ', '_')) for c in Usuario.ESTADOS_CONEXION],
        'fondos_disponibles': [(f[0], f[1], _fondo_css_simple(f[0]), _fondo_css_slug(f[0])) for f in Usuario.FONDOS_DISPONIBLES],
        'tiene_id_competitivo': usuario_perfil.tiene_id_competitivo,
        'estado_conexion_css': usuario_perfil.estado_conexion.lower().replace(' ', '_'),
        'estado_conexion_display': usuario_perfil.get_estado_conexion_display(),
        'fondo_css': _fondo_css(usuario_perfil),
        'fondo_activo': usuario_perfil.fondo_perfil,
    }

    return render(request, 'usuarios/perfil.html', contexto)


def _fondo_css_simple(slug):
    """Miniatura CSS para las tarjetas de selección del fondo."""
    fondos = {
        'carbono': "repeating-linear-gradient(135deg, rgba(255,255,255,0.03) 0 2px, transparent 2px 8px), #0a0a0f",
        'asfalto': "repeating-linear-gradient(0deg, rgba(0,240,255,0.04) 0 1px, transparent 1px 5px), #0a0a0f",
        'rejilla-industrial': "linear-gradient(rgba(0,240,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(0,240,255,0.06) 1px, transparent 1px), #0a0a0f",
        'scanlines': "repeating-linear-gradient(0deg, rgba(255,230,0,0.04) 0 1px, transparent 1px 4px), #0a0a0f",
    }
    return fondos.get(slug, fondos['carbono'])


@login_required
def panel_control(request):
    if not request.user.is_superuser and getattr(request.user, 'rol_plataforma', None) != 'Dueño':
        messages.error(request, "Acceso denegado. Esta zona es exclusiva para la administración principal.")
        return redirect('lobby')

    return render(request, 'usuarios/panel_control.html')