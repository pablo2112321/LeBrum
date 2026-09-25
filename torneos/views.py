from collections import OrderedDict
from typing import Any

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.views.generic import DetailView, ListView, View
from .models import Torneo, Inscripcion, Partida
from .forms import InscripcionForm, ResultadoPartidaForm
from .services import procesar_inscripcion, procesar_resultado


class TorneoDetailView(DetailView):
    """Presenta la ficha pública de un torneo y sus participantes."""

    model = Torneo
    template_name = 'torneos/detalle_torneo.html'
    context_object_name = 'torneo'
    pk_url_kwarg = 'torneo_id'

    def get_queryset(self):
        return Torneo.objects.select_related('juego').prefetch_related(
            'inscripciones__equipo',
            'partidas__equipo_local',
            'partidas__equipo_visitante',
            'partidas__ganador',
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['inscripciones'] = self.object.inscripciones_completadas.select_related(
            'equipo',
            'pagador',
        )
        contexto['partidas'] = self.object.partidas.select_related(
            'equipo_local',
            'equipo_visitante',
            'ganador',
        ).order_by('ronda', 'numero_partida')
        contexto['bracket_rondas'] = self._obtener_bracket()
        contexto['form_inscripcion'] = InscripcionForm(
            user=self.request.user if self.request.user.is_authenticated else None,
            torneo=self.object,
        )
        contexto['equipos_disponibles'] = (
            contexto['form_inscripcion'].fields['equipo'].queryset.exists()
        )
        return contexto

    def _obtener_bracket(self) -> list[dict[str, Any]]:
        """Agrupa las partidas del torneo en columnas ordenadas del bracket."""
        if self.object.estado not in (
            Torneo.ESTADO_EN_CURSO,
            Torneo.ESTADO_FINALIZADO,
        ):
            return []

        partidas = list(
            self.object.partidas.select_related(
                'equipo_local',
                'equipo_visitante',
                'ganador',
            ).order_by('numero_partida')
        )
        if not partidas:
            return []

        rondas = OrderedDict()
        partidas_ordenadas = sorted(
            partidas,
            key=lambda partida: (
                int(partida.ronda) if (partida.ronda or '').isdigit() else 0,
                partida.numero_partida,
            ),
        )
        for partida in partidas_ordenadas:
            clave_ronda = partida.ronda or '1'
            rondas.setdefault(clave_ronda, []).append(partida)

        total_rondas = len(rondas)
        nombres_ronda = {
            total_rondas: 'FINAL',
            total_rondas - 1: 'SEMIFINALES',
            total_rondas - 2: 'CUARTOS DE FINAL',
        }

        bracket = []
        for posicion, (clave_ronda, partidas_ronda) in enumerate(rondas.items(), start=1):
            bracket.append({
                'clave': clave_ronda,
                'nombre': nombres_ronda.get(posicion, f'RONDA {clave_ronda}'),
                'partidas': partidas_ronda,
            })
        return bracket


class MisTorneosView(ListView):
    """Muestra las inscripciones y la próxima partida del jugador."""

    template_name = 'torneos/mis_torneos.html'
    context_object_name = 'inscripciones'

    def get_queryset(self) -> Any:
        partidas = Partida.objects.filter(
            estado__in=(
                Partida.ESTADO_PENDIENTE,
                Partida.ESTADO_JUGANDO,
                Partida.ESTADO_EN_REVISION,
            ),
        ).select_related(
            'torneo',
            'equipo_local',
            'equipo_visitante',
        ).order_by('fecha_hora_programada', 'id')
        return Inscripcion.objects.filter(
            equipo__capitan=self.request.user,
        ).select_related(
            'torneo',
            'equipo',
        ).prefetch_related(
            Prefetch('equipo__partidas_como_local', queryset=partidas, to_attr='partidas_pendientes'),
            Prefetch('equipo__partidas_como_visitante', queryset=partidas, to_attr='partidas_pendientes_visitante'),
        ).order_by('-creado_el')

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class SalaPartidaView(View):
    """Expone la sala únicamente a los capitanes de los equipos enfrentados."""

    template_name = 'torneos/sala_partida.html'

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect('login')

        self.partida = get_object_or_404(
            Partida.objects.select_related(
                'torneo',
                'equipo_local__capitan',
                'equipo_visitante__capitan',
                'ganador',
            ).filter(
                equipo_local__isnull=False,
                equipo_visitante__isnull=False,
            ),
            pk=kwargs['partida_id'],
        )
        if not self._es_capitan(request):
            raise PermissionDenied('Solo los capitanes de esta partida pueden acceder a la sala.')
        return super().dispatch(request, *args, **kwargs)

    def _es_capitan(self, request: HttpRequest) -> bool:
        return request.user.id in {
            self.partida.equipo_local.capitan_id,
            self.partida.equipo_visitante.capitan_id,
        }

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return self._render(request)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.POST.get('action') == 'disputar':
            detalle = request.POST.get('detalle_disputa', '').strip()
            if not detalle:
                messages.error(request, 'Debes explicar brevemente el motivo de la disputa.')
                return redirect('detalle_partida', partida_id=self.partida.pk)
            if self.partida.estado == Partida.ESTADO_FINALIZADO:
                messages.error(request, 'Una partida finalizada no puede abrir una disputa.')
                return redirect('detalle_partida', partida_id=self.partida.pk)
            self.partida.en_disputa = True
            self.partida.detalle_disputa = detalle
            self.partida.estado = Partida.ESTADO_EN_REVISION
            self.partida.save(update_fields=['en_disputa', 'detalle_disputa', 'estado'])
            messages.warning(request, 'Disputa abierta. El Ojo de Halcón revisará la evidencia.')
            return redirect('detalle_partida', partida_id=self.partida.pk)

        if self.partida.en_disputa:
            messages.error(request, 'La partida está bloqueada mientras se revisa la disputa.')
            return redirect('detalle_partida', partida_id=self.partida.pk)
        if self.partida.estado not in (
            Partida.ESTADO_PENDIENTE,
            Partida.ESTADO_JUGANDO,
        ):
            messages.error(request, 'Esta partida no admite nuevos reportes.')
            return redirect('detalle_partida', partida_id=self.partida.pk)

        form = ResultadoPartidaForm(
            request.POST,
            request.FILES,
            partida=self.partida,
        )
        if not form.is_valid():
            return self._render(request, form)

        equipo_ganador = (
            self.partida.equipo_local
            if int(form.cleaned_data['ganador']) == self.partida.equipo_local_id
            else self.partida.equipo_visitante
        )
        self.partida.evidencia_victoria = form.cleaned_data['captura_evidencia']
        self.partida.save(update_fields=['evidencia_victoria'])
        try:
            siguiente = procesar_resultado(self.partida, equipo_ganador)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('detalle_partida', partida_id=self.partida.pk)

        if siguiente is None:
            messages.success(request, f'Victoria registrada. {equipo_ganador.nombre} ganó el torneo.')
        else:
            messages.success(request, f'Victoria registrada. {equipo_ganador.nombre} avanza a la siguiente ronda.')
        return redirect('detalle_partida', partida_id=self.partida.pk)

    def _render(
        self,
        request: HttpRequest,
        form: ResultadoPartidaForm | None = None,
    ) -> HttpResponse:
        self.partida.refresh_from_db()
        contexto = {
            'partida': self.partida,
            'form_resultado': form or ResultadoPartidaForm(partida=self.partida),
            'es_capitan_a': request.user.id == self.partida.equipo_local.capitan_id,
            'es_capitan_b': request.user.id == self.partida.equipo_visitante.capitan_id,
        }
        return render(request, self.template_name, contexto)


@login_required
def inscribir_equipo(request: HttpRequest, torneo_id: int) -> HttpResponse:
    """Procesa la inscripción de un equipo mediante el servicio de dominio."""
    if request.method != 'POST':
        return redirect('detalle_torneo', torneo_id=torneo_id)

    torneo = get_object_or_404(Torneo, pk=torneo_id)
    form = InscripcionForm(request.POST, user=request.user, torneo=torneo)
    if not form.is_valid():
        for error in form.non_field_errors():
            messages.error(request, error)
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
        return redirect('detalle_torneo', torneo_id=torneo.pk)

    try:
        inscripcion = procesar_inscripcion(torneo, form.cleaned_data['equipo'])
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        if inscripcion.estado_pago == Inscripcion.ESTADO_PAGADO:
            messages.success(request, 'Equipo inscrito correctamente. El pago fue confirmado.')
        else:
            messages.warning(
                request,
                'Inscripción creada. Queda pendiente de aprobación manual del pago.',
            )
    return redirect('detalle_torneo', torneo_id=torneo.pk)


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
    partidas = torneo.partidas.select_related('equipo_local', 'equipo_visitante', 'ganador').order_by('id')
    return render(request, 'torneos/detalle_torneo.html', {
        'torneo': torneo,
        'form': form,
        'mensaje': mensaje,
        'inscripciones': inscripciones,
        'partidas': partidas,
    })


def detalle_partida(request, partida_id):
    """Compatibilidad con el nombre histórico de la ruta de la sala."""
    return SalaPartidaView.as_view()(request, partida_id=partida_id)


@login_required
def reportar_resultado(request, partida_id):
    """Redirige el endpoint histórico al flujo seguro de la sala."""
    return SalaPartidaView.as_view()(request, partida_id=partida_id)
