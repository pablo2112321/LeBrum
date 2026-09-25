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
            self.fields['equipo'].queryset = Equipo.objects.filter(
                capitan=self.user,
                modo=self.torneo.modalidad,
            ).exclude(inscripciones__torneo=self.torneo)

    def clean_equipo(self):
        equipo = self.cleaned_data.get('equipo')
        if equipo and self.torneo and equipo.modo != self.torneo.modalidad:
            raise forms.ValidationError('La modalidad del equipo debe coincidir con la del torneo.')
        return equipo


class ResultadoPartidaForm(forms.Form):
    """Valida el ganador declarado y la evidencia obligatoria de la partida."""

    ganador = forms.ChoiceField(
        choices=(),
        widget=forms.RadioSelect,
        label='Equipo ganador',
    )
    captura_evidencia = forms.ImageField(
        label='Captura de evidencia',
        required=True,
    )

    def __init__(self, *args, partida=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.partida = partida
        if partida is not None:
            self.fields['ganador'].choices = (
                (str(partida.equipo_local_id), partida.equipo_local.nombre),
                (str(partida.equipo_visitante_id), partida.equipo_visitante.nombre),
            )
