from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Notificacion, SolicitudPrivacidad, Usuario


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

    def test_exportacion_requiere_autenticacion(self):
        response = self.client.get(reverse('exportar_datos'))
        self.assertEqual(response.status_code, 302)

    def test_usuario_puede_crear_solicitud_de_eliminacion(self):
        usuario = Usuario.objects.create_user(
            username='titular',
            email='titular@example.com',
            password='password-segura',
        )
        self.client.force_login(usuario)

        response = self.client.post(
            reverse('solicitar_privacidad'),
            {'tipo': 'erasure', 'detalle': 'Eliminar mi cuenta'},
        )

        self.assertEqual(response.status_code, 201)
        solicitud = SolicitudPrivacidad.objects.get(usuario=usuario)
        self.assertEqual(solicitud.tipo, 'erasure')

    def test_solicitud_privacidad_rechaza_tipo_invalido(self):
        usuario = Usuario.objects.create_user(
            username='tipo-invalido',
            password='password-segura',
        )
        self.client.force_login(usuario)

        response = self.client.post(
            reverse('solicitar_privacidad'),
            {'tipo': 'delete-everything'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(SolicitudPrivacidad.objects.filter(usuario=usuario).exists())

    def test_exportacion_devuelve_solo_los_datos_del_usuario_autenticado(self):
        usuario = Usuario.objects.create_user(
            username='titular-exportacion',
            email='titular@example.com',
            password='password-segura',
            tag_jugador='Titular#001',
        )
        Usuario.objects.create_user(
            username='otro-usuario',
            email='otro@example.com',
            password='password-segura',
            tag_jugador='Otro#002',
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse('exportar_datos'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['usuario']['username'], 'titular-exportacion')
        self.assertNotContains(response, 'otro@example.com')
        self.assertNotContains(response, 'Otro#002')

    def test_procesamiento_de_eliminacion_anonimiza_cuenta(self):
        usuario = Usuario.objects.create_user(
            username='para-anonimizar',
            email='personal@example.com',
            password='password-segura',
            riot_id='Player#123',
        )
        solicitud = SolicitudPrivacidad.objects.create(
            usuario=usuario,
            tipo='erasure',
        )
        admin = Usuario.objects.create_user(
            username='staff',
            password='password-segura',
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('procesar_privacidad', args=[solicitud.pk]),
        )

        self.assertEqual(response.status_code, 200)
        usuario.refresh_from_db()
        solicitud.refresh_from_db()
        self.assertFalse(usuario.is_active)
        self.assertEqual(usuario.email, '')
        self.assertIsNone(usuario.riot_id)
        self.assertEqual(solicitud.estado, 'completed')

    def test_procesamiento_de_privacidad_requiere_personal_autorizado(self):
        usuario = Usuario.objects.create_user(
            username='solicitante',
            password='password-segura',
        )
        solicitud = SolicitudPrivacidad.objects.create(
            usuario=usuario,
            tipo='access',
        )
        self.client.force_login(usuario)

        response = self.client.post(
            reverse('procesar_privacidad', args=[solicitud.pk]),
        )

        self.assertEqual(response.status_code, 302)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'pending')

    def test_usuario_no_puede_procesar_solicitud_de_otro_usuario(self):
        propietario = Usuario.objects.create_user(
            username='propietario',
            password='password-segura',
        )
        solicitud = SolicitudPrivacidad.objects.create(
            usuario=propietario,
            tipo='erasure',
        )
        staff = Usuario.objects.create_user(
            username='staff-no-superuser',
            password='password-segura',
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.post(
            reverse('procesar_privacidad', args=[solicitud.pk]),
        )

        self.assertEqual(response.status_code, 200)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'completed')
