import django.db.models.deletion
from django.db import migrations, models


def convertir_estados(apps, schema_editor):
    Partida = apps.get_model('torneos', 'Partida')
    mapa = {
        'Pendiente': 'PENDIENTE',
        'En Curso': 'JUGANDO',
        'Finalizada': 'FINALIZADO',
        'En Disputa': 'EN REVISION',
    }
    for viejo, nuevo in mapa.items():
        Partida.objects.filter(estado=viejo).update(estado=nuevo)


class Migration(migrations.Migration):

    dependencies = [
        ('torneos', '0003_remove_torneo_premios_torneo_cupo_maximo_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='partida',
            old_name='equipo_local',
            new_name='equipo_a',
        ),
        migrations.RenameField(
            model_name='partida',
            old_name='equipo_visitante',
            new_name='equipo_b',
        ),
        migrations.AlterField(
            model_name='partida',
            name='equipo_a',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name='partidas_como_a',
                to='equipos.equipo',
                verbose_name='Equipo A',
            ),
        ),
        migrations.AlterField(
            model_name='partida',
            name='equipo_b',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name='partidas_como_b',
                to='equipos.equipo',
                verbose_name='Equipo B',
            ),
        ),
        migrations.AlterField(
            model_name='partida',
            name='estado',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente'),
                    ('JUGANDO', 'Jugando'),
                    ('EN REVISION', 'En Revisión'),
                    ('FINALIZADO', 'Finalizada'),
                ],
                default='PENDIENTE',
                max_length=20,
                verbose_name='Estado',
            ),
        ),
        migrations.AddField(
            model_name='partida',
            name='evidencia_victoria',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='evidencias_partidas/',
                verbose_name='Evidencia de victoria',
            ),
        ),
        migrations.AddField(
            model_name='partida',
            name='ganador',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='partidas_ganadas',
                to='equipos.equipo',
                verbose_name='Equipo ganador',
            ),
        ),
        migrations.AddField(
            model_name='partida',
            name='reporte_creado_el',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Fecha del primer reporte',
            ),
        ),
        migrations.AddField(
            model_name='partida',
            name='reporte_equipo_a',
            field=models.CharField(
                blank=True,
                choices=[('GANADOR', 'Ganador'), ('PERDEDOR', 'Perdedor')],
                max_length=10,
                null=True,
                verbose_name='Reporte del equipo A',
            ),
        ),
        migrations.AddField(
            model_name='partida',
            name='reporte_equipo_b',
            field=models.CharField(
                blank=True,
                choices=[('GANADOR', 'Ganador'), ('PERDEDOR', 'Perdedor')],
                max_length=10,
                null=True,
                verbose_name='Reporte del equipo B',
            ),
        ),
        migrations.RunPython(convertir_estados, migrations.RunPython.noop),
    ]
