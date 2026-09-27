from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('torneos', '0013_alter_partida_evidencia_victoria_and_more'),
    ]
    operations = [
        migrations.CreateModel(
            name='Noticia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=180)),
                ('slug', models.SlugField(blank=True, max_length=200, unique=True)),
                ('resumen', models.CharField(max_length=280)),
                ('contenido', models.TextField()),
                ('publicada', models.BooleanField(default=True)),
                ('creada_el', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ('-creada_el',)},
        ),
        migrations.CreateModel(
            name='ProductoTienda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.CharField(blank=True, max_length=240)),
                ('categoria', models.CharField(choices=[('titulo', 'Título'), ('fondo', 'Fondo de perfil'), ('estado', 'Estado')], default='titulo', max_length=20)),
                ('precio', models.PositiveIntegerField()),
                ('valor', models.CharField(blank=True, max_length=80)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={'ordering': ('precio', 'nombre')},
        ),
        migrations.CreateModel(
            name='Transmision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=180)),
                ('url', models.URLField()),
                ('plataforma', models.CharField(default='Twitch', max_length=40)),
                ('en_vivo', models.BooleanField(default=False)),
                ('creada_el', models.DateTimeField(auto_now_add=True)),
                ('torneo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transmisiones', to='torneos.torneo')),
            ],
            options={'ordering': ('-en_vivo', '-creada_el')},
        ),
        migrations.CreateModel(
            name='MensajeChat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenido', models.CharField(max_length=300)),
                ('creado_el', models.DateTimeField(auto_now_add=True)),
                ('visible', models.BooleanField(default=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('-creado_el',)},
        ),
        migrations.CreateModel(
            name='CompraTienda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comprada_el', models.DateTimeField(auto_now_add=True)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='principal.productotienda')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='compratienda',
            constraint=models.UniqueConstraint(fields=('usuario', 'producto'), name='compra_usuario_producto_unica'),
        ),
    ]
