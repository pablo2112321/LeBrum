from django.test import TestCase
from django.urls import reverse

from usuarios.models import Usuario

from .models import MensajeTicket, TicketSoporte


class SupportFlowTests(TestCase):
    """Verifica creación, visibilidad y respuestas del canal de soporte."""

    def setUp(self) -> None:
        self.owner = Usuario.objects.create_user(username='owner', password='pass12345')
        self.other = Usuario.objects.create_user(username='other', password='pass12345')
        self.staff = Usuario.objects.create_user(
            username='moderator',
            password='pass12345',
            is_staff=True,
        )

    def test_anonymous_users_are_redirected(self) -> None:
        response = self.client.get(reverse('soporte:ticket_list'))
        self.assertEqual(response.status_code, 302)

    def test_user_creates_ticket_with_first_message(self) -> None:
        self.client.login(username='owner', password='pass12345')
        response = self.client.post(reverse('soporte:ticket_create'), {
            'categoria': 'Otro',
            'partida': '',
            'contenido_mensaje': 'No puedo acceder a la sala.',
            'url_adjunto': '',
        })
        self.assertRedirects(response, reverse('soporte:ticket_list'))
        ticket = TicketSoporte.objects.get()
        self.assertEqual(ticket.usuario, self.owner)
        self.assertEqual(ticket.mensajes.count(), 1)

    def test_owner_can_reply_but_other_user_cannot_view(self) -> None:
        ticket = TicketSoporte.objects.create(usuario=self.owner, categoria='Otro')
        self.client.login(username='other', password='pass12345')
        response = self.client.get(reverse('soporte:ticket_detail', args=[ticket.pk]))
        self.assertEqual(response.status_code, 403)
        self.client.login(username='owner', password='pass12345')
        response = self.client.post(reverse('soporte:ticket_detail', args=[ticket.pk]), {
            'contenido_mensaje': 'Adjunto más información.',
            'url_adjunto': '',
        })
        self.assertRedirects(response, reverse('soporte:ticket_detail', args=[ticket.pk]))
        self.assertEqual(ticket.mensajes.count(), 1)

    def test_staff_can_reply_and_change_status(self) -> None:
        ticket = TicketSoporte.objects.create(usuario=self.owner, categoria='Otro')
        self.client.login(username='moderator', password='pass12345')
        detail_url = reverse('soporte:ticket_detail', args=[ticket.pk])
        self.client.post(detail_url, {'contenido_mensaje': 'Estamos revisando.', 'url_adjunto': ''})
        self.client.post(detail_url, {'action': 'status', 'estado': 'Resuelto'})
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado, 'Resuelto')
        self.assertIsNotNone(ticket.fecha_termino)
        self.assertEqual(MensajeTicket.objects.filter(ticket=ticket).count(), 1)
