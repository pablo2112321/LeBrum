from django import forms

from .models import MensajeChat


class MensajeChatForm(forms.ModelForm):
    """Valida mensajes cortos del canal global."""

    class Meta:
        model = MensajeChat
        fields = ('contenido',)
        widgets = {'contenido': forms.TextInput(attrs={'maxlength': 300, 'placeholder': 'Escribe al canal...'})}
