from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
import re

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo Electrónico")

    tag_jugador = forms.CharField(
        required=True,
        label="Tag de Jugador",
        widget=forms.TextInput(attrs={'placeholder': 'Tu tag competitivo (ej: Legión#777)'})
    )

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'tag_jugador', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limpiamos los textos de ayuda y aplicamos clases a todos los campos
        for field_name, field in self.fields.items():
            field.help_text = ''
            if 'password' in field_name:
                max_len = 50
            elif field_name == 'username':
                max_len = 16
            elif field_name == 'tag_jugador':
                max_len = 20
            else:
                max_len = 150
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({
                    'class': 'neo-input',
                    'placeholder': f'Ingresa tu {field.label or field_name}',
                    'maxlength': max_len
                })

        # Placeholder especial para el tag de jugador
        self.fields['tag_jugador'].widget.attrs['placeholder'] = 'Tu tag competitivo (ej: Legión#777)'

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise forms.ValidationError("El nombre de usuario debe tener al menos 3 caracteres.")
        if len(username) > 16:
            raise forms.ValidationError("El nombre de usuario no puede exceder los 16 caracteres.")
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise forms.ValidationError("Solo se permiten letras, números, guiones (-) y guiones bajos (_).")
        if Usuario.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado.")
        return username

    def clean_tag_jugador(self):
        tag = self.cleaned_data.get('tag_jugador', '').strip()
        if len(tag) < 3:
            raise forms.ValidationError("El tag debe tener al menos 3 caracteres.")
        if len(tag) > 20:
            raise forms.ValidationError("El tag no puede exceder los 20 caracteres.")
        if not re.match(r'^[a-zA-Z0-9_#-]+$', tag):
            raise forms.ValidationError("Solo se permiten letras, números, #, guiones (-) y guiones bajos (_).")
        if Usuario.objects.filter(tag_jugador__iexact=tag).exists():
            raise forms.ValidationError("Este tag ya está en uso por otro jugador.")
        return tag

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        dominios_permitidos = ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com', 'live.com']
        if email:
            dominio = email.split('@')[1] if '@' in email else ''
            if dominio not in dominios_permitidos:
                raise forms.ValidationError("Solo aceptamos correos de: Gmail, Outlook, Hotmail o Yahoo.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if len(password) > 50:
            raise forms.ValidationError("Máximo 50 caracteres permitidos.")
        if not re.match(r'^[a-zA-Z0-9]+$', password):
            raise forms.ValidationError("No se permiten signos (+, -, @, etc.). Solo letras y números.")
        numeros = sum(c.isdigit() for c in password)
        if numeros < 3:
            raise forms.ValidationError("Debe incluir al menos 3 números.")
        return password


class LoadoutForm(forms.ModelForm):
    titulo_equipado = forms.ChoiceField(
        choices=Usuario.TITULOS_DISPONIBLES,
        label="Título Equipado"
    )

    estado_equipado = forms.ChoiceField(
        choices=Usuario.ESTADOS_DISPONIBLES,
        label="Estado Equipado"
    )

    estado_conexion = forms.ChoiceField(
        choices=Usuario.ESTADOS_CONEXION,
        label="Estado de Conexión"
    )

    fondo_perfil = forms.ChoiceField(
        choices=Usuario.FONDOS_DISPONIBLES,
        label="Fondo de Perfil"
    )

    class Meta:
        model = Usuario
        fields = ('riot_id', 'steam_id',
                  'titulo_equipado', 'estado_equipado', 'estado_conexion',
                  'fondo_perfil')
        widgets = {
            'riot_id': forms.TextInput(attrs={
                'placeholder': 'Nombre#Etiqueta (ej: Legión#777)',
                'data-validate': 'riot',
            }),
            'steam_id': forms.TextInput(attrs={
                'placeholder': 'ID64 de 17 dígitos',
                'data-validate': 'steam',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.help_text = ''
            max_len = 50
            if field_name == 'estado_equipado':
                max_len = 60
            elif field_name == 'titulo_equipado':
                max_len = 40
            widget = field.widget
            widget.attrs.setdefault('class', 'neo-input')
            widget.attrs.update({
                'maxlength': max_len,
                'autocomplete': 'off',
            })

        # El estado de conexión es parte del HUD del agente
        self.fields['estado_conexion'].widget.attrs.update({'class': 'neo-input'})

    def clean_riot_id(self):
        riot = (self.cleaned_data.get('riot_id') or '').strip()
        if riot:
            if '#' not in riot:
                raise forms.ValidationError("El Riot ID debe incluir el separador '#' (ej: Nombre#TAG).")
            if len(riot) > 50:
                raise forms.ValidationError("El Riot ID no puede exceder los 50 caracteres.")
            if not re.match(r'^[A-Za-z0-9À-ÿ_.\- ]+#[A-Za-z0-9_\-]{2,}$', riot):
                raise forms.ValidationError("Formato inválido. Usa Nombre#TAG sin espacios en el TAG.")
        return riot or None

    def clean_steam_id(self):
        steam = (self.cleaned_data.get('steam_id') or '').strip()
        if steam:
            if not re.match(r'^\d{17}$', steam):
                raise forms.ValidationError("El Steam ID debe tener exactamente 17 dígitos.")
        return steam or None