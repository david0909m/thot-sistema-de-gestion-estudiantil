from django.contrib import admin
from .models import (
    EstadoCivil, Religion, Escolaridad, Recorrido,
    Nivel, Asignatura, Escala, PeriodoLectivo, TipoNota,
    Clase, Seccion, Materia, Horario, DocenteMateria
)


@admin.register(EstadoCivil)
class EstadoCivilAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "orden")
    search_fields = ("nombre", "codigo")


@admin.register(Religion)
class ReligionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "orden")
    search_fields = ("nombre", "codigo")


@admin.register(Escolaridad)
class EscolaridadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "orden")
    search_fields = ("nombre", "codigo")


@admin.register(Recorrido)
class RecorridoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo")
    search_fields = ("nombre", "codigo")


@admin.register(Nivel)
class NivelAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "orden", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "codigo")


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "codigo")


@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "nota_minima_aprobatoria", "nota_maxima")
    search_fields = ("nombre", "codigo")


class TipoNotaInline(admin.TabularInline):
    model = TipoNota
    extra = 1
    fk_name = "periodo"


@admin.register(PeriodoLectivo)
class PeriodoLectivoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "fecha_inicio", "fecha_fin", "activo", "abierto", "visible")
    list_filter = ("activo", "abierto", "visible")
    search_fields = ("nombre",)
    inlines = [TipoNotaInline]


@admin.register(TipoNota)
class TipoNotaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "periodo", "padre", "es_consolidado", "orden", "peso", "porcentaje")
    list_filter = ("periodo", "es_consolidado")
    search_fields = ("nombre", "periodo__nombre")


@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ("nombre", "periodo", "nivel")
    list_filter = ("periodo", "nivel")
    search_fields = ("nombre",)


@admin.register(Seccion)
class SeccionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "clase", "capacidad_maxima")
    list_filter = ("clase__periodo", "clase__nivel")
    search_fields = ("nombre", "codigo", "clase__nombre")


class HorarioInline(admin.TabularInline):
    model = Horario
    extra = 1


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "asignatura", "clase", "seccion", "docente", "lock_version")
    list_filter = ("clase__periodo", "clase__nivel", "asignatura")
    search_fields = ("nombre", "clase__nombre", "docente__username")
    inlines = [HorarioInline]


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ("materia", "dia_semana", "hora_inicio", "hora_fin", "aula")
    list_filter = ("dia_semana",)
    search_fields = ("materia__nombre", "aula")


@admin.register(DocenteMateria)
class DocenteMateriaAdmin(admin.ModelAdmin):
    list_display = ("materia", "docente", "es_titular")
    list_filter = ("es_titular",)
    search_fields = ("materia__nombre", "docente__username")
