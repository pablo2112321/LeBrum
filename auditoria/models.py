from typing import Any

from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    ACTIONS = (
        ('admin_access', 'Acceso administrativo'),
        ('dispute_resolution', 'Resolución de disputa'),
        ('evidence_download', 'Descarga de evidencia'),
        ('balance_change', 'Cambio de saldo'),
        ('payment_state_change', 'Cambio de estado de pago'),
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_events',
    )
    action = models.CharField(max_length=40, choices=ACTIONS)
    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = (
            models.Index(fields=('action', '-created_at')),
            models.Index(fields=('target_type', 'target_id')),
        )
        verbose_name = 'evento de auditoría'
        verbose_name_plural = 'eventos de auditoría'

    def __str__(self) -> str:
        return f'{self.get_action_display()} #{self.pk}'
