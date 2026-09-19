from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q
from .forms import LoadoutForm, RegistroUsuarioForm
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
        return redirect('ojo_de_halcon')
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


def _fondo_css_slug(slug):
    """Valor CSS de background-image según el slug del fondo."""
    from django.templatetags.static import static
    galaxia = static('img/galaxia.jpg')
    fondos = {
        'galaxia': f"url('{galaxia}')",
        'carbono': "radial-gradient(circle at 12% 8%, rgba(236,0,140,0.28), transparent 42%), radial-gradient(circle at 88% 92%, rgba(0,229,255,0.22), transparent 48%), linear-gradient(160deg, #0a0a0e, #05050a)",
        'neon-cyan': "radial-gradient(circle at 80% 8%, rgba(0,229,255,0.38), transparent 46%), radial-gradient(circle at 15% 95%, rgba(0,229,255,0.12), transparent 40%), linear-gradient(160deg, #02090f, #04141c)",
        'magenta': "radial-gradient(circle at 18% 90%, rgba(236,0,140,0.42), transparent 52%), radial-gradient(circle at 85% 15%, rgba(236,0,140,0.16), transparent 40%), linear-gradient(160deg, #0f020a, #1a0412)",
        'zona-roja': "radial-gradient(circle at 72% 18%, rgba(239,68,68,0.36), transparent 46%), radial-gradient(circle at 20% 90%, rgba(239,68,68,0.14), transparent 42%), linear-gradient(160deg, #0c0202, #1a0606)",
    }
    return fondos.get(slug, fondos['galaxia'])


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
    from django.templatetags.static import static
    galaxia = static('img/galaxia.jpg')
    fondos = {
        'galaxia': f"url('{galaxia}') center/cover",
        'carbono': "linear-gradient(160deg, #14141c, #05050a)",
        'neon-cyan': "linear-gradient(160deg, #02202e, #04141c)",
        'magenta': "linear-gradient(160deg, #2a0520, #1a0412)",
        'zona-roja': "linear-gradient(160deg, #2a0707, #1a0606)",
    }
    return fondos.get(slug, fondos['galaxia'])


@login_required
def panel_control(request):
    if not request.user.is_superuser and getattr(request.user, 'rol_plataforma', None) != 'Dueño':
        messages.error(request, "Acceso denegado. Esta zona es exclusiva para la administración principal.")
        return redirect('lobby')

    return render(request, 'usuarios/panel_control.html')