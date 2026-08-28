from django.contrib import admin
from .models import Incidencia, Mensaje, Adjunto


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "tipo_incidencia", "fecha", "periodo", "reportado_por")
    list_filter = ("tipo_incidencia", "periodo", "fecha")
    search_fields = ("estudiante__codigo_estudiante", "estudiante__primer_nombre", "estudiante__primer_apellido", "descripcion")


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ("asunto", "remitente", "ambito_destinatario", "fecha_envio")
    list_filter = ("ambito_destinatario", "fecha_envio")
    search_fields = ("asunto", "remitente__username", "cuerpo")


@admin.register(Adjunto)
class AdjuntoAdmin(admin.ModelAdmin):
    list_display = ("nombre_original", "content_type", "object_id")
    search_fields = ("nombre_original",)
