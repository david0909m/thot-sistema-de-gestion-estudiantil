from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    Docente, Pariente, Estudiante, Responsable, EstudianteClase, Estudio, Experiencia
)


@admin.register(Docente)
class DocenteAdmin(SimpleHistoryAdmin):
    list_display = ("codigo_empleado", "usuario", "especialidad", "telefono")
    search_fields = ("codigo_empleado", "usuario__username", "usuario__first_name", "usuario__last_name", "especialidad")


@admin.register(Pariente)
class ParienteAdmin(SimpleHistoryAdmin):
    list_display = ("get_full_name", "parentesco", "cedula_identidad", "telefono", "email")
    list_filter = ("parentesco",)
    search_fields = ("primer_nombre", "primer_apellido", "cedula_identidad", "telefono", "email")


class ResponsableInline(admin.TabularInline):
    model = Responsable
    extra = 1


@admin.register(Estudiante)
class EstudianteAdmin(SimpleHistoryAdmin):
    list_display = ("codigo_estudiante", "get_full_name", "cedula_identidad", "genero", "activo", "retirado")
    list_filter = ("activo", "retirado", "genero", "estado_civil", "religion")
    search_fields = ("codigo_estudiante", "primer_nombre", "primer_apellido", "cedula_identidad")
    inlines = [ResponsableInline]


@admin.register(Responsable)
class ResponsableAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "pariente", "es_representante_legal", "es_responsable_financiero")
    list_filter = ("es_representante_legal", "es_responsable_financiero", "convive_con_estudiante")
    search_fields = ("estudiante__codigo_estudiante", "pariente__primer_nombre", "pariente__primer_apellido")


@admin.register(EstudianteClase)
class EstudianteClaseAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "clase", "seccion", "periodo", "estado", "fecha_inscripcion")
    list_filter = ("periodo", "estado", "clase__nivel")
    search_fields = ("estudiante__codigo_estudiante", "estudiante__primer_nombre", "estudiante__primer_apellido")


@admin.register(Estudio)
class EstudioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "titulo", "institucion", "fecha_obtencion")
    search_fields = ("usuario__username", "titulo", "institucion")


@admin.register(Experiencia)
class ExperienciaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "cargo", "institucion", "fecha_inicio", "fecha_fin")
    search_fields = ("usuario__username", "cargo", "institucion")
