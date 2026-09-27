from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='AuditEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[
                    ('admin_access', 'Acceso administrativo'),
                    ('dispute_resolution', 'Resolución de disputa'),
                    ('evidence_download', 'Descarga de evidencia'),
                    ('balance_change', 'Cambio de saldo'),
                    ('payment_state_change', 'Cambio de estado de pago'),
                ], max_length=40)),
                ('target_type', models.CharField(blank=True, max_length=100)),
                ('target_id', models.CharField(blank=True, max_length=100)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('path', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'evento de auditoría',
                'verbose_name_plural': 'eventos de auditoría',
                'ordering': ('-created_at',),
            },
        ),
        migrations.AddIndex(
            model_name='auditevent',
            index=models.Index(fields=['action', '-created_at'], name='auditoria_a_action_c78e0e_idx'),
        ),
        migrations.AddIndex(
            model_name='auditevent',
            index=models.Index(fields=['target_type', 'target_id'], name='auditoria_a_target__108ba6_idx'),
        ),
    ]
