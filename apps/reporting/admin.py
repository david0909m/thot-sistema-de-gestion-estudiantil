from django.contrib import admin
from .models import ConfiguracionInstitucion


@admin.register(ConfiguracionInstitucion)
class ConfiguracionInstitucionAdmin(admin.ModelAdmin):
    list_display = ("nombre_institucion", "telefono", "correo")

    def has_add_permission(self, request):
        # Impedir múltiples configuraciones institucionales
        if ConfiguracionInstitucion.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False
