from typing import Any

from django import forms
from django.utils import timezone

from torneos.models import Partida

from .models import MensajeTicket, TicketSoporte


class TicketForm(forms.ModelForm):
    """Formulario para registrar una solicitud de soporte."""

    class Meta:
        model = TicketSoporte
        fields = ('categoria', 'partida')
        widgets = {
            'categoria': forms.Select(attrs={'class': 'cyber-input'}),
            'partida': forms.Select(attrs={'class': 'cyber-input'}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields['partida'].queryset = Partida.objects.select_related(
            'torneo', 'equipo_local', 'equipo_visitante'
        ).order_by('-id')
        self.fields['partida'].required = False
        self.fields['partida'].label = 'Partida relacionada (opcional)'

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if cleaned_data.get('categoria') == 'Disputa' and not cleaned_data.get('partida'):
            self.add_error(
                'partida',
                'Las disputas deben enlazarse a una partida.',
            )
        return cleaned_data


class MensajeTicketForm(forms.ModelForm):
    """Formulario de conversación dentro de un ticket."""

    class Meta:
        model = MensajeTicket
        fields = ('contenido_mensaje', 'url_adjunto')
        widgets = {
            'contenido_mensaje': forms.Textarea(attrs={
                'class': 'cyber-input',
                'rows': 5,
                'placeholder': 'Describe la situación con claridad...',
            }),
            'url_adjunto': forms.URLInput(attrs={
                'class': 'cyber-input',
                'placeholder': 'https://...',
            }),
        }


class TicketStatusForm(forms.ModelForm):
    """Formulario reservado para moderadores del equipo de soporte."""

    class Meta:
        model = TicketSoporte
        fields = ('estado',)
        widgets = {'estado': forms.Select(attrs={'class': 'cyber-input'})}

    def save(self, commit: bool = True) -> TicketSoporte:
        ticket = super().save(commit=False)
        ticket.fecha_termino = (
            timezone.now() if ticket.estado in {'Resuelto', 'Cerrado'} else None
        )
        if commit:
            ticket.save(update_fields=['estado', 'fecha_termino'])
        return ticket
