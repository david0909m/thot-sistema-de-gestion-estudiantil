from django.contrib import admin
from .models import Evaluacion, Calificacion, ResumenAcademicoEstudiante


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "materia", "tipo_nota", "fecha", "porcentaje", "nota_maxima", "publicada")
    list_filter = ("materia__clase__periodo", "tipo_nota", "publicada", "es_examen", "es_reparacion")
    search_fields = ("nombre", "materia__nombre", "materia__clase__nombre")


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "materia", "tipo_nota", "resultado", "literal", "es_consolidado", "evaluacion")
    list_filter = ("materia__clase__periodo", "es_consolidado", "tipo_nota")
    search_fields = ("estudiante__codigo_estudiante", "estudiante__primer_nombre", "estudiante__primer_apellido", "materia__nombre")


@admin.register(ResumenAcademicoEstudiante)
class ResumenAcademicoEstudianteAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "periodo", "promedio_general", "materias_reprobadas", "materias_reparadas")
    list_filter = ("periodo",)
    search_fields = ("estudiante__codigo_estudiante", "estudiante__primer_nombre", "estudiante__primer_apellido")
