from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest

from .models import AuditEvent


def record_audit_event(
    action: str,
    *,
    request: HttpRequest | None = None,
    actor: Any = None,
    target: Any = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    """Registra una acción sensible sin interrumpir la operación principal."""
    if actor is None and request is not None and request.user.is_authenticated:
        actor = request.user
    target_type = ''
    target_id = ''
    if target is not None:
        target_type = f'{target._meta.app_label}.{target._meta.model_name}'
        target_id = str(target.pk)
    ip_address = None
    path = ''
    if request is not None:
        trusted_proxy_count = int(getattr(settings, 'TRUSTED_PROXY_COUNT', 0))
        if trusted_proxy_count:
            forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
            addresses = [address.strip() for address in forwarded.split(',') if address.strip()]
            if len(addresses) > trusted_proxy_count:
                ip_address = addresses[-trusted_proxy_count - 1]
        ip_address = ip_address or request.META.get('REMOTE_ADDR')
        path = request.path
    return AuditEvent.objects.create(
        action=action,
        actor=actor if getattr(actor, 'is_authenticated', True) else None,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata or {},
        ip_address=ip_address,
        path=path,
    )
