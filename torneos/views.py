from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Torneo, Inscripcion, Partida
from .forms import InscripcionForm


def listar_torneos(request):
    torneos = Torneo.objects.select_related('juego').all()
    return render(request, 'torneos/listar_torneos.html', {'torneos': torneos})


def detalle_torneo(request, torneo_id):
    torneo = get_object_or_404(Torneo, pk=torneo_id)
    mensaje = None

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')

        form = InscripcionForm(request.POST, user=request.user, torneo=torneo)
        if form.is_valid():
            inscripcion = form.save(commit=False)
            inscripcion.torneo = torneo
            try:
                inscripcion.pagar_inscripcion(request.user)
                mensaje = 'Inscripción realizada y pago completado.'
            except ValueError as exc:
                mensaje = str(exc)
        else:
            mensaje = 'Por favor corrige los errores del formulario.'
    else:
        form = InscripcionForm(user=request.user if request.user.is_authenticated else None, torneo=torneo)

    inscripciones = torneo.inscripciones_completadas.select_related('equipo', 'pagador')
    partidas = torneo.partidas.select_related('equipo_a', 'equipo_b', 'ganador').order_by('id')
    return render(request, 'torneos/detalle_torneo.html', {
        'torneo': torneo,
        'form': form,
        'mensaje': mensaje,
        'inscripciones': inscripciones,
        'partidas': partidas,
    })


def detalle_partida(request, partida_id):
    partida = get_object_or_404(
        Partida.objects.select_related('torneo', 'equipo_a', 'equipo_b', 'ganador'),
        pk=partida_id,
    )
    partida.revisar_vencimientos()
    partida.refresh_from_db()

    return render(request, 'torneos/sala_partida.html', {
        'partida': partida,
        'es_capitan_a': partida.equipo_a.capitan_id == request.user.id,
        'es_capitan_b': partida.equipo_b.capitan_id == request.user.id,
    })


@login_required
def reportar_resultado(request, partida_id):
    partida = get_object_or_404(Partida, pk=partida_id)

    if request.method != 'POST':
        return redirect('detalle_partida', partida_id=partida.pk)

    resultado = request.POST.get('resultado', '')
    if resultado not in dict(partida.REPORTES):
        messages.error(request, 'Resultado de reporte inválido.')
        return redirect('detalle_partida', partida_id=partida.pk)

    if partida.estado == partida.ESTADO_FINALIZADO:
        messages.error(request, 'Esta partida ya fue finalizada.')
        return redirect('detalle_partida', partida_id=partida.pk)

    if partida.equipo_a.capitan_id == request.user.id:
        equipo = partida.equipo_a
    elif partida.equipo_b.capitan_id == request.user.id:
        equipo = partida.equipo_b
    else:
        messages.error(request, 'Solo el capitán de un equipo participante puede reportar el resultado.')
        return redirect('detalle_partida', partida_id=partida.pk)

    evidencia = request.FILES.get('evidencia_victoria')
    if resultado == partida.REPORTE_GANADOR and evidencia is None:
        messages.error(
            request,
            'Para reclamar la victoria es obligatorio adjuntar una captura como evidencia.'
        )
        return redirect('detalle_partida', partida_id=partida.pk)

    try:
        partida.aplicar_reporte(equipo, resultado, evidencia=evidencia)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('detalle_partida', partida_id=partida.pk)

    partida.refresh_from_db()
    if partida.estado == partida.ESTADO_FINALIZADO:
        messages.success(request, f'Reporte registrado. ¡{partida.ganador.nombre} gana la partida!')
    elif partida.estado == partida.ESTADO_EN_REVISION:
        messages.warning(
            request,
            'Reporte registrado. Disputa activa: los jueces de la crew revisarán la evidencia.'
        )
    else:
        messages.success(request, 'Reporte registrado. Esperando la confirmación del equipo rival...')

    return redirect('detalle_partida', partida_id=partida.pk)
