import logging

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from .services import record_audit_event

security_logger = logging.getLogger('lebrum.security')


class SensitiveAccessAuditMiddleware(MiddlewareMixin):
    """Audita accesos administrativos y lecturas de evidencias de partidas."""

    def process_response(self, request, response):
        if request.user.is_authenticated:
            if request.path.startswith('/ojo-de-halcon/'):
                record_audit_event('admin_access', request=request, metadata={
                    'method': request.method,
                    'status_code': response.status_code,
                })
            evidence_prefix = f'{settings.MEDIA_URL}evidencias_partidas/'
            protected_evidence = (
                request.path.startswith('/torneos/partida/')
                and request.path.endswith('/evidencia/')
            )
            if request.path.startswith(evidence_prefix) or protected_evidence:
                record_audit_event('evidence_download', request=request, metadata={
                    'method': request.method,
                    'status_code': response.status_code,
                })
        if response.status_code >= 500:
            security_logger.error(
                'Error interno en %s %s con estado %s',
                request.method,
                request.path,
                response.status_code,
            )
        elif response.status_code in {401, 403}:
            security_logger.warning(
                'Acceso rechazado en %s %s con estado %s',
                request.method,
                request.path,
                response.status_code,
            )
        return response
