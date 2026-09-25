from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from usuarios.models import Notificacion


class Command(BaseCommand):
    help = 'Elimina notificaciones leídas con más de siete días de antigüedad.'

    def handle(self, *args, **options):
        fecha_limite = timezone.now() - timedelta(days=7)
        notificaciones = Notificacion.objects.filter(
            leida=True,
            creada_el__lt=fecha_limite,
        )
        eliminadas, _ = notificaciones.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f'Se eliminaron {eliminadas} notificaciones leídas.'
            )
        )
