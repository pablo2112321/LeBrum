from django import forms
from .models import Inscripcion
from equipos.models import Equipo


class InscripcionForm(forms.ModelForm):
    class Meta:
        model = Inscripcion
        fields = ['equipo']
        labels = {
            'equipo': 'Equipo a inscribir',
        }
        widgets = {
            'equipo': forms.Select(attrs={'class': 'neo-input'}),
        }

    def __init__(self, *args, user=None, torneo=None, **kwargs):
        self.user = user
        self.torneo = torneo
        super().__init__(*args, **kwargs)
        self.fields['equipo'].queryset = Equipo.objects.none()
        self.fields['equipo'].empty_label = 'Selecciona un equipo'

        if self.user and self.torneo:
            self.fields['equipo'].queryset = Equipo.objects.filter(capitan=self.user, torneo=self.torneo)

    def clean_equipo(self):
        equipo = self.cleaned_data.get('equipo')
        if equipo and self.torneo and equipo.torneo != self.torneo:
            raise forms.ValidationError('El equipo debe pertenecer al torneo seleccionado.')
        return equipo
