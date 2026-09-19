from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .forms import EquipoForm
from .models import Equipo, MiembroEquipo

MSG_PERFIL_INCOMPLETO = 'Debes registrar tu Riot ID o Steam ID en tu Perfil antes de unirte a una Crew'


def listar_equipos(request):
    equipos = (
        Equipo.objects
        .select_related('torneo', 'capitan')
        .annotate(num_miembros=Count('miembros'))
        .all()
    )
    return render(request, 'equipos/listar_equipos.html', {'equipos': equipos})


@login_required
def crear_equipo(request):
    if not request.user.tiene_id_competitivo:
        messages.error(request, MSG_PERFIL_INCOMPLETO)
        return render(request, 'equipos/crear_equipo.html', {
            'form': None,
            'perfil_incompleto': True,
        })

    if request.method == 'POST':
        form = EquipoForm(request.POST)
        if form.is_valid():
            equipo = form.save(commit=False)
            equipo.capitan = request.user
            equipo.save()
            messages.success(request, f'¡Crew {equipo.nombre} forjada! El capitán eres tú, agente.')
            return redirect('detalle_equipo', equipo_id=equipo.id)
    else:
        form = EquipoForm()

    return render(request, 'equipos/crear_equipo.html', {'form': form})


def detalle_equipo(request, equipo_id):
    equipo = get_object_or_404(
        Equipo.objects.select_related('torneo', 'capitan').prefetch_related('miembros__usuario'),
        pk=equipo_id,
    )
    miembros = equipo.miembros.select_related('usuario').order_by('-es_capitan', 'usuario__username')

    return render(request, 'equipos/detalle_equipo.html', {
        'equipo': equipo,
        'miembros': miembros,
        'es_capitan': equipo.capitan_id == request.user.id,
        'ya_es_miembro': (
            request.user.is_authenticated
            and equipo.miembros.filter(usuario_id=request.user.id).exists()
        ),
    })


@login_required
def unirse_equipo(request, equipo_id):
    equipo = get_object_or_404(Equipo, pk=equipo_id)

    if not request.user.tiene_id_competitivo:
        messages.error(request, MSG_PERFIL_INCOMPLETO)
        return redirect('detalle_equipo', equipo_id=equipo.pk)

    if equipo.miembros.filter(usuario_id=request.user.id).exists():
        messages.error(request, 'Ya formas parte de esta crew, agente.')
        return redirect('detalle_equipo', equipo_id=equipo.pk)

    if equipo.roster_lleno:
        messages.error(request, 'El roster de esta crew está completo.')
        return redirect('detalle_equipo', equipo_id=equipo.pk)

    MiembroEquipo.objects.create(equipo=equipo, usuario=request.user, es_capitan=False)
    messages.success(request, f'¡Bienvenido a {equipo.nombre}! Tu solicitud de ingreso fue aceptada.')
    return redirect('detalle_equipo', equipo_id=equipo.pk)


@login_required
def expulsar_miembro(request, equipo_id, usuario_id):
    equipo = get_object_or_404(Equipo, pk=equipo_id)

    if equipo.capitan_id != request.user.id:
        messages.error(request, 'Solo el capitán puede gestionar el roster de la crew.')
        return redirect('detalle_equipo', equipo_id=equipo.pk)

    miembro = get_object_or_404(MiembroEquipo, equipo=equipo, usuario_id=usuario_id)
    if miembro.es_capitan:
        messages.error(request, 'No puedes expulsar al capitán de la crew.')
        return redirect('detalle_equipo', equipo_id=equipo.pk)

    nombre = miembro.usuario.username
    miembro.delete()
    messages.success(request, f'{nombre} fue removido del roster.')
    return redirect('detalle_equipo', equipo_id=equipo.pk)
