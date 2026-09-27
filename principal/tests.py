from django.test import TestCase
from django.urls import reverse

from usuarios.models import Usuario
from .models import MensajeChat, Noticia, ProductoTienda


class ModulosPublicosTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(username='runner', password='password123')

    def test_public_module_routes_render(self):
        Noticia.objects.create(titulo='Patch', resumen='Resumen', contenido='Contenido')
        for name in ('noticias', 'transmisiones', 'juegos', 'tienda'):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)

    def test_chat_requires_login_to_write(self):
        response = self.client.post(reverse('chat'), {'contenido': 'hola'})
        self.assertRedirects(response, reverse('login'))
        self.client.force_login(self.usuario)
        response = self.client.post(reverse('chat'), {'contenido': 'hola'})
        self.assertRedirects(response, reverse('chat'))
        self.assertTrue(MensajeChat.objects.filter(usuario=self.usuario).exists())


class TiendaTests(TestCase):
    def test_purchase_requires_balance_and_is_idempotent(self):
        user = Usuario.objects.create_user(username='buyer', password='password123', saldo_fichas=50)
        product = ProductoTienda.objects.create(
            nombre='Operador', categoria='titulo', valor='OPERADOR', precio=40,
        )
        self.client.force_login(user)
        response = self.client.post(reverse('tienda'), {'producto_id': product.pk})
        self.assertRedirects(response, reverse('tienda'))
        user.refresh_from_db()
        self.assertEqual(user.saldo_fichas, 10)
        response = self.client.post(reverse('tienda'), {'producto_id': product.pk})
        self.assertRedirects(response, reverse('tienda'))
        self.assertEqual(user.__class__.objects.get(pk=user.pk).saldo_fichas, 10)
