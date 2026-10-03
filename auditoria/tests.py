import logging
from datetime import timedelta

from django.core import management
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

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

    def test_retention_command_deletes_only_expired_events(self):
        expired = AuditEvent.objects.create(
            actor=self.user,
            action='admin_access',
        )
        expired.created_at = timezone.now() - timedelta(days=366)
        expired.save(update_fields=['created_at'])
        recent = AuditEvent.objects.create(
            actor=self.user,
            action='admin_access',
        )
        recent.created_at = timezone.now() - timedelta(days=364)
        recent.save(update_fields=['created_at'])

        management.call_command('limpiar_auditoria', days=365, verbosity=0)

        self.assertFalse(AuditEvent.objects.filter(pk=expired.pk).exists())
        self.assertTrue(AuditEvent.objects.filter(pk=recent.pk).exists())

    def test_retention_command_rejects_less_than_thirty_days(self):
        with self.assertRaises(ValueError):
            management.call_command('limpiar_auditoria', days=29, verbosity=0)

    def test_middleware_logs_forbidden_responses(self):
        request = RequestFactory().get('/usuarios/privacidad/solicitudes/1/procesar/')
        request.user = self.user
        middleware = SensitiveAccessAuditMiddleware(lambda request: None)
        with self.assertLogs('lebrum.security', level=logging.WARNING) as logs:
            middleware.process_response(
                request,
                type('Response', (), {'status_code': 403})(),
            )
        self.assertIn('Acceso rechazado', logs.output[0])
