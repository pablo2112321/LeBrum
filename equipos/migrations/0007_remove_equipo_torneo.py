from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('equipos', '0006_equipo_banner_equipo_tag'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='equipo',
            name='torneo',
        ),
        migrations.AlterModelOptions(
            name='equipo',
            options={
                'verbose_name': 'equipo',
                'verbose_name_plural': 'equipos',
            },
        ),
        migrations.AlterModelOptions(
            name='miembroequipo',
            options={
                'unique_together': {('equipo', 'usuario')},
                'verbose_name': 'miembro de equipo',
                'verbose_name_plural': 'miembros de equipo',
            },
        ),
    ]
