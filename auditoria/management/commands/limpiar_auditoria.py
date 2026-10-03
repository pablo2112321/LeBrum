from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from auditoria.models import AuditEvent


class Command(BaseCommand):
    help = 'Elimina eventos de auditoría que superaron el plazo configurado.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=365)

    def handle(self, *args, **options):
        days = options['days']
        if days < 30:
            raise ValueError('El plazo mínimo de auditoría es de 30 días.')
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = AuditEvent.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(
            self.style.SUCCESS(f'Se eliminaron {deleted} registros de auditoría.')
        )
