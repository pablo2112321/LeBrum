from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'actor', 'target_type', 'target_id', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('target_type', 'target_id', 'actor__username', 'path')
    readonly_fields = (
        'created_at', 'actor', 'action', 'target_type', 'target_id',
        'metadata', 'ip_address', 'path',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
