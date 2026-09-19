from django import forms
from .models import Equipo
from torneos.models import Torneo


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ['nombre', 'tag', 'torneo', 'modo', 'logo', 'banner']
        labels = {
            'nombre': 'Nombre de la Crew',
            'tag': 'Tag oficial',
            'torneo': 'Torneo',
            'modo': 'Modalidad',
            'logo': 'URL del logo',
            'banner': 'URL del banner',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'neo-input', 'placeholder': 'Nombre de la escuadra'}),
            'tag': forms.TextInput(attrs={'class': 'neo-input', 'placeholder': '[DLB]'}),
            'torneo': forms.Select(attrs={'class': 'neo-input'}),
            'modo': forms.Select(attrs={'class': 'neo-input'}),
            'logo': forms.URLInput(attrs={'class': 'neo-input', 'placeholder': 'https://.../logo.png'}),
            'banner': forms.URLInput(attrs={'class': 'neo-input', 'placeholder': 'https://.../banner.png'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['torneo'].queryset = Torneo.objects.filter(estado=Torneo.ESTADO_ABIERTO)
        self.fields['torneo'].empty_label = 'Selecciona un torneo abierto'

    def clean(self):
        cleaned_data = super().clean()
        torneo = cleaned_data.get('torneo')
        modo = cleaned_data.get('modo')

        if torneo and modo and torneo.modalidad != modo:
            self.add_error('modo', 'La modalidad del equipo debe coincidir con la modalidad del torneo.')

        return cleaned_data
