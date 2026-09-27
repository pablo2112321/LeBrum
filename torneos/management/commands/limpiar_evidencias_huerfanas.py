from pathlib import Path

from django.core.management.base import BaseCommand

from LeBrum.storage import PrivateMediaStorage
from torneos.models import Partida


class Command(BaseCommand):
    help = 'Elimina archivos de evidencia privada que ya no están referenciados.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra los archivos huérfanos sin eliminarlos.',
        )

    def handle(self, *args, **options):
        storage = PrivateMediaStorage()
        root = Path(storage.location)
        referenced = {
            partida.evidencia_victoria.name.replace('\\', '/')
            for partida in Partida.objects.exclude(evidencia_victoria='')
            if partida.evidencia_victoria
        }
        orphaned = [
            path for path in root.rglob('*')
            if path.is_file()
            and path.relative_to(root).as_posix() not in referenced
        ] if root.exists() else []

        if not options['dry_run']:
            for path in orphaned:
                path.unlink()
        action = 'Encontrados' if options['dry_run'] else 'Eliminados'
        self.stdout.write(self.style.SUCCESS(f'{action} {len(orphaned)} archivos huérfanos.'))
