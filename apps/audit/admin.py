from django.contrib import admin
from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "usuario", "username_log", "accion", "origen", "ip_address", "exito")
    list_filter = ("exito", "origen", "accion", "timestamp")
    search_fields = ("username_log", "usuario__username", "accion", "objeto_tipo", "objeto_id", "descripcion")
    readonly_fields = (
        "timestamp", "usuario", "username_log", "ip_address", "accion",
        "origen", "objeto_tipo", "objeto_id", "descripcion", "detalles", "exito"
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
