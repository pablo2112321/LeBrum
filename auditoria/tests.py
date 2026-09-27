from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings

from .middleware import SensitiveAccessAuditMiddleware
from .models import AuditEvent
from .services import record_audit_event


class AuditEventTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='auditor-test',
            password='test-password',
        )

    def test_records_actor_target_and_request_context(self):
        request = RequestFactory().get(
            '/ojo-de-halcon/torneos/partida/1/change/',
            REMOTE_ADDR='192.0.2.10',
        )
        request.user = self.user
        event = record_audit_event(
            'dispute_resolution',
            request=request,
            target=self.user,
            metadata={'winner_team_id': 7},
        )
        self.assertEqual(event.actor, self.user)
        self.assertEqual(event.target_type, 'usuarios.usuario')
        self.assertEqual(event.target_id, str(self.user.pk))
        self.assertEqual(event.ip_address, '192.0.2.10')

    @override_settings(MEDIA_URL='/media/')
    def test_middleware_records_evidence_access(self):
        request = RequestFactory().get('/media/evidencias_partidas/proof.png')
        request.user = self.user
        middleware = SensitiveAccessAuditMiddleware(lambda request: None)
        middleware.process_response(request, type('Response', (), {'status_code': 200})())
        event = AuditEvent.objects.get(action='evidence_download')
        self.assertEqual(event.actor, self.user)
        self.assertEqual(event.path, request.path)
