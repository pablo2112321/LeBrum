from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Notificacion, Usuario


class UsuarioFlowTests(TestCase):
    def test_usuario_puede_marcar_y_limpiar_notificaciones_antiguas(self):
        usuario = Usuario.objects.create_user(
            username='notificado',
            password='password-segura',
        )
        antigua = Notificacion.objects.create(
            usuario=usuario,
            mensaje='Antigua',
            leida=True,
        )
        antigua.creada_el = timezone.now() - timedelta(days=8)
        antigua.save(update_fields=['creada_el'])
        reciente = Notificacion.objects.create(
            usuario=usuario,
            mensaje='Reciente',
            leida=False,
        )
        self.client.force_login(usuario)

        response = self.client.post(reverse('marcar_notificaciones_leidas'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Notificacion.objects.filter(pk=antigua.pk).exists())
        reciente.refresh_from_db()
        self.assertTrue(reciente.leida)
