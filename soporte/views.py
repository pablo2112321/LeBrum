from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from .forms import MensajeTicketForm, TicketForm, TicketStatusForm
from .models import MensajeTicket, TicketSoporte


class TicketListView(LoginRequiredMixin, ListView):
    """Lista los tickets propios o todos para el personal autorizado."""

    model = TicketSoporte
    template_name = 'soporte/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        queryset = TicketSoporte.objects.select_related('usuario', 'partida')
        if not self.request.user.is_staff:
            queryset = queryset.filter(usuario=self.request.user)
        return queryset.order_by('-fecha_creacion')


class TicketCreateView(LoginRequiredMixin, CreateView):
    """Crea un ticket y su primer mensaje en una única operación."""

    model = TicketSoporte
    form_class = TicketForm
    template_name = 'soporte/ticket_form.html'
    success_url = reverse_lazy('soporte:ticket_list')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault('message_form', MensajeTicketForm())
        return context

    @transaction.atomic
    def form_valid(self, form):
        message_form = MensajeTicketForm(self.request.POST)
        if not message_form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, message_form=message_form)
            )
        self.object = form.save(commit=False)
        self.object.usuario = self.request.user
        self.object.save()
        MensajeTicket.objects.create(
            ticket=self.object,
            remitente=self.request.user,
            contenido_mensaje=message_form.cleaned_data['contenido_mensaje'],
            url_adjunto=message_form.cleaned_data.get('url_adjunto'),
        )
        messages.success(self.request, 'Ticket creado. El equipo revisará tu solicitud.')
        return redirect(self.get_success_url())


class TicketDetailView(LoginRequiredMixin, DetailView):
    """Muestra el hilo y habilita respuestas a participantes autorizados."""

    model = TicketSoporte
    template_name = 'soporte/ticket_detail.html'
    context_object_name = 'ticket'

    def get_queryset(self):
        return TicketSoporte.objects.select_related(
            'usuario', 'partida', 'partida__torneo'
        ).prefetch_related('mensajes__remitente')

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        ticket = self.get_object()
        if not (request.user.is_staff or ticket.usuario_id == request.user.id):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['message_form'] = MensajeTicketForm()
        context['status_form'] = TicketStatusForm(instance=self.object)
        return context

    @transaction.atomic
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        if request.user.is_staff and request.POST.get('action') == 'status':
            status_form = TicketStatusForm(request.POST, instance=self.object)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, 'Estado del ticket actualizado.')
            else:
                messages.error(request, 'Selecciona un estado válido.')
            return redirect('soporte:ticket_detail', pk=self.object.pk)
        if self.object.estado in {'Resuelto', 'Cerrado'}:
            messages.error(request, 'Este ticket ya no acepta nuevas respuestas.')
            return redirect('soporte:ticket_detail', pk=self.object.pk)
        message_form = MensajeTicketForm(request.POST)
        if message_form.is_valid():
            reply = message_form.save(commit=False)
            reply.ticket = self.object
            reply.remitente = request.user
            reply.save()
            if self.object.estado == 'Abierto' and request.user.is_staff:
                self.object.estado = 'En Revision'
                self.object.save(update_fields=['estado'])
            messages.success(request, 'Respuesta enviada.')
            return redirect('soporte:ticket_detail', pk=self.object.pk)
        return self.render_to_response(self.get_context_data(message_form=message_form))


ticket_list = TicketListView.as_view()
ticket_create = TicketCreateView.as_view()
ticket_detail = TicketDetailView.as_view()
