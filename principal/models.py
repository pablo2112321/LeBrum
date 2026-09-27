from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Noticia(models.Model):
    """Publicación editorial visible en el canal de noticias."""

    titulo = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    resumen = models.CharField(max_length=280)
    contenido = models.TextField()
    publicada = models.BooleanField(default=True)
    creada_el = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ('-creada_el',)


class Transmision(models.Model):
    """Enlace a una retransmisión oficial o comunitaria."""

    titulo = models.CharField(max_length=180)
    url = models.URLField()
    plataforma = models.CharField(max_length=40, default='Twitch')
    torneo = models.ForeignKey(
        'torneos.Torneo', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transmisiones',
    )
    en_vivo = models.BooleanField(default=False)
    creada_el = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-en_vivo', '-creada_el')


class MensajeChat(models.Model):
    """Mensaje persistido del chat global, moderable desde administración."""

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenido = models.CharField(max_length=300)
    creado_el = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ('-creado_el',)


class ProductoTienda(models.Model):
    """Artículo cosmético que se compra con fichas LeBrum."""

    CATEGORIAS = (('titulo', 'Título'), ('fondo', 'Fondo de perfil'), ('estado', 'Estado'))
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=240, blank=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='titulo')
    precio = models.PositiveIntegerField()
    valor = models.CharField(max_length=80, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ('precio', 'nombre')


class CompraTienda(models.Model):
    """Inventario adquirido por un jugador; evita compras duplicadas."""

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    producto = models.ForeignKey(ProductoTienda, on_delete=models.CASCADE)
    comprada_el = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('usuario', 'producto'), name='compra_usuario_producto_unica',
            ),
        ]
