from django.test import TestCase
from django.urls import reverse
from django.contrib import admin

from .models import Equipo, MiembroEquipo
from usuarios.models import Usuario


class EquipoFlowTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='constructor',
            password='password-segura',
            riot_id='Constructor#001',
        )

    def test_capitan_puede_crear_equipo_desde_frontend(self):
        self.client.force_login(self.usuario)

        response = self.client.post(
            reverse('crear_equipo'),
            {'nombre': 'Crew Test', 'tag': '[TST]', 'modo': '1v1'},
        )

        self.assertRedirects(
            response,
            reverse('detalle_equipo', kwargs={'equipo_id': 1}),
        )
        equipo = Equipo.objects.get(nombre='Crew Test')
        self.assertEqual(equipo.capitan, self.usuario)
        self.assertTrue(
            MiembroEquipo.objects.filter(
                equipo=equipo,
                usuario=self.usuario,
                es_capitan=True,
            ).exists()
        )

    def test_unirse_requiere_post(self):
        equipo = Equipo.objects.create(nombre='Crew Join', capitan=self.usuario)
        self.client.force_login(self.usuario)
        response = self.client.get(
            reverse('unirse_equipo', kwargs={'equipo_id': equipo.pk}),
        )
        self.assertEqual(response.status_code, 405)

    def test_equipo_y_miembro_estan_disponibles_en_admin(self):
        self.assertIn(Equipo, admin.site._registry)
        self.assertIn(MiembroEquipo, admin.site._registry)
