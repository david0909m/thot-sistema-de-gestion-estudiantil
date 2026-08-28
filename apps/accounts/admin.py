from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from simple_history.admin import SimpleHistoryAdmin
from .models import User, Perfil, Permiso, Autorizacion, AsignacionUsuario


@admin.register(User)
class UserAdmin(BaseUserAdmin, SimpleHistoryAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Información Adicional THOT", {
            "fields": (
                "segundo_nombre", "segundo_apellido", "cedula_identidad",
                "requiere_cambio_password", "habilitado", "ultimo_acceso_ip",
                "fecha_vencimiento_password"
            )
        }),
    )
    list_display = (
        "username", "email", "first_name", "last_name", "cedula_identidad",
        "habilitado", "requiere_cambio_password", "is_staff"
    )
    list_filter = ("habilitado", "requiere_cambio_password", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "first_name", "last_name", "email", "cedula_identidad")


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "activo")
    search_fields = ("nombre", "codigo")
    list_filter = ("activo",)


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "modulo")
    search_fields = ("codigo", "nombre", "modulo")
    list_filter = ("modulo",)


@admin.register(Autorizacion)
class AutorizacionAdmin(admin.ModelAdmin):
    list_display = ("perfil", "permiso")
    list_filter = ("perfil", "permiso__modulo")
    search_fields = ("perfil__nombre", "permiso__codigo", "permiso__nombre")


@admin.register(AsignacionUsuario)
class AsignacionUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "perfil", "content_type", "object_id", "activo", "fecha_inicio", "fecha_fin")
    list_filter = ("perfil", "activo", "content_type")
    search_fields = ("usuario__username", "usuario__first_name", "usuario__last_name", "perfil__nombre")
