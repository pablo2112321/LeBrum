from django import forms
from .models import Equipo


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ['nombre', 'tag', 'modo', 'logo', 'banner']
        labels = {
            'nombre': 'Nombre de la Crew',
            'tag': 'Tag oficial',
            'modo': 'Modalidad',
            'logo': 'Escudo del equipo',
            'banner': 'URL del banner',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'neo-input', 'placeholder': 'Nombre de la escuadra'}),
            'tag': forms.TextInput(attrs={'class': 'neo-input', 'placeholder': '[DLB]'}),
            'modo': forms.Select(attrs={'class': 'neo-input'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'neo-input', 'accept': 'image/*'}),
            'banner': forms.URLInput(attrs={'class': 'neo-input', 'placeholder': 'https://.../banner.png'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
