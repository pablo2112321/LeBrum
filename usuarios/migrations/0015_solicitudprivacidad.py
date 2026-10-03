from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0014_alter_usuario_avatar'),
    ]

    operations = [
        migrations.CreateModel(
            name='SolicitudPrivacidad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('access', 'Acceso'), ('rectification', 'Rectificación'), ('erasure', 'Eliminación'), ('opposition', 'Oposición')], max_length=20)),
                ('detalle', models.TextField(blank=True, default='')),
                ('estado', models.CharField(choices=[('pending', 'Pendiente'), ('processing', 'En proceso'), ('completed', 'Completada'), ('rejected', 'Rechazada')], default='pending', max_length=20)),
                ('creada_el', models.DateTimeField(auto_now_add=True)),
                ('procesada_el', models.DateTimeField(blank=True, null=True)),
                ('procesada_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solicitudes_privacidad_procesadas', to=settings.AUTH_USER_MODEL)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitudes_privacidad', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('-creada_el',)},
        ),
    ]
