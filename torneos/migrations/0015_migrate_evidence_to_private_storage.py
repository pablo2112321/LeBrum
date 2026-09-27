from pathlib import Path
import shutil

from django.conf import settings
from django.db import migrations


def move_existing_evidence(apps, schema_editor):
    """Traslada evidencias históricas fuera del directorio público."""
    partida_model = apps.get_model('torneos', 'Partida')
    public_root = Path(settings.MEDIA_ROOT)
    private_root = Path(settings.PRIVATE_MEDIA_ROOT)
    for partida in partida_model.objects.exclude(evidencia_victoria=''):
        name = partida.evidencia_victoria.name
        if not name:
            continue
        source = (public_root / name).resolve()
        destination = (private_root / name).resolve()
        if public_root.resolve() not in source.parents:
            continue
        if private_root.resolve() not in destination.parents:
            continue
        if source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))

    # También retira archivos antiguos sin referencia del árbol público; el
    # comando de limpieza podrá eliminarlos después de inspeccionarlos.
    legacy_root = public_root / 'evidencias_partidas'
    if legacy_root.exists():
        for source in legacy_root.rglob('*'):
            if not source.is_file():
                continue
            relative_name = source.relative_to(public_root)
            destination = private_root / relative_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                shutil.move(str(source), str(destination))


class Migration(migrations.Migration):
    dependencies = [
        ('torneos', '0014_alter_partida_evidencia_victoria'),
    ]

    operations = [
        migrations.RunPython(move_existing_evidence, migrations.RunPython.noop),
    ]
