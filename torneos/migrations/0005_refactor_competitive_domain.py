import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipos', '0007_remove_equipo_torneo'),
        ('torneos', '0004_partida_sistema_reportes'),
    ]

    operations = [
        migrations.RenameField(
            model_name='partida',
            old_name='equipo_a',
            new_name='equipo_local',
        ),
        migrations.RenameField(
            model_name='partida',
            old_name='equipo_b',
            new_name='equipo_visitante',
        ),
        migrations.RenameField(
            model_name='partida',
            old_name='reporte_equipo_a',
            new_name='reporte_equipo_local',
        ),
        migrations.RenameField(
            model_name='partida',
            old_name='reporte_equipo_b',
            new_name='reporte_equipo_visitante',
        ),
        migrations.AlterField(
            model_name='partida',
            name='equipo_local',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name='partidas_como_local',
                to='equipos.equipo',
                verbose_name='Equipo local',
            ),
        ),
        migrations.AlterField(
            model_name='partida',
            name='equipo_visitante',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name='partidas_como_visitante',
                to='equipos.equipo',
                verbose_name='Equipo visitante',
            ),
        ),
        migrations.AlterField(
            model_name='partida',
            name='reporte_equipo_local',
            field=models.CharField(
                blank=True,
                choices=[('GANADOR', 'Ganador'), ('PERDEDOR', 'Perdedor')],
                max_length=10,
                null=True,
                verbose_name='Reporte del equipo local',
            ),
        ),
        migrations.AlterField(
            model_name='partida',
            name='reporte_equipo_visitante',
            field=models.CharField(
                blank=True,
                choices=[('GANADOR', 'Ganador'), ('PERDEDOR', 'Perdedor')],
                max_length=10,
                null=True,
                verbose_name='Reporte del equipo visitante',
            ),
        ),
        migrations.AlterField(
            model_name='torneo',
            name='estado',
            field=models.CharField(
                choices=[
                    ('Abierto', 'Abierto para inscripciones'),
                    ('Lleno', 'Lleno / En espera'),
                    ('En Curso', 'En curso'),
                    ('Finalizado', 'Finalizado'),
                    ('Cancelado', 'Cancelado'),
                ],
                default='Abierto',
                max_length=20,
                verbose_name='Estado del torneo',
            ),
        ),
        migrations.AlterField(
            model_name='partida',
            name='estado',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente'),
                    ('JUGANDO', 'En Curso'),
                    ('EN REVISION', 'Disputa'),
                    ('FINALIZADO', 'Finalizada'),
                ],
                default='PENDIENTE',
                max_length=20,
                verbose_name='Estado',
            ),
        ),
        migrations.AlterModelOptions(
            name='videojuego',
            options={
                'verbose_name': 'videojuego',
                'verbose_name_plural': 'videojuegos',
            },
        ),
        migrations.AlterModelOptions(
            name='torneo',
            options={
                'verbose_name': 'torneo',
                'verbose_name_plural': 'torneos',
            },
        ),
        migrations.AlterModelOptions(
            name='inscripcion',
            options={
                'unique_together': {('torneo', 'equipo')},
                'verbose_name': 'inscripción',
                'verbose_name_plural': 'inscripciones',
            },
        ),
        migrations.AlterModelOptions(
            name='partida',
            options={
                'verbose_name': 'partida',
                'verbose_name_plural': 'partidas',
            },
        ),
    ]
