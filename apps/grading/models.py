from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.academic_core.models import PeriodoLectivo, TipoNota, Materia
from apps.people.models import Estudiante


class Evaluacion(models.Model):
    """
    Evaluación específica o prueba parcial dentro de una materia y tipo de nota.
    """
    materia = models.ForeignKey(
        Materia, on_delete=models.CASCADE, related_name="evaluaciones", verbose_name="Materia"
    )
    tipo_nota = models.ForeignKey(
        TipoNota, on_delete=models.CASCADE, related_name="evaluaciones", verbose_name="Tipo de Nota"
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre de la evaluación")
    descripcion = models.TextField(blank=True, verbose_name="Descripción de la tarea o examen")
    fecha = models.DateField(verbose_name="Fecha de aplicación")
    porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name="Porcentaje dentro del TipoNota"
    )
    nota_maxima = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("100.00"), verbose_name="Nota Máxima"
    )
    es_examen = models.BooleanField(default=False, verbose_name="¿Es Examen?")
    es_reparacion = models.BooleanField(default=False, verbose_name="¿Es Reparación / Convocatoria Extraordinaria?")
    publicada = models.BooleanField(default=True, verbose_name="Publicada")

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        ordering = ["materia", "tipo_nota", "fecha"]

    def __str__(self):
        return f"[{self.materia.nombre}] {self.nombre} ({self.porcentaje}%)"


class Calificacion(models.Model):
    """
    Nota obtenida por un estudiante en una evaluación individual o resultado consolidado.
    Soporta jerarquía mediante `calificacion_padre` para vincular notas parciales con su consolidado.
    """
    evaluacion = models.ForeignKey(
        Evaluacion, on_delete=models.CASCADE, null=True, blank=True,
        related_name="calificaciones", verbose_name="Evaluación de origen"
    )
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name="calificaciones", verbose_name="Estudiante"
    )
    materia = models.ForeignKey(
        Materia, on_delete=models.CASCADE, related_name="calificaciones", verbose_name="Materia"
    )
    tipo_nota = models.ForeignKey(
        TipoNota, on_delete=models.CASCADE, related_name="calificaciones", verbose_name="Tipo de Nota"
    )

    resultado = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Resultado / Nota (Decimal 5,2)"
    )
    literal = models.CharField(max_length=10, blank=True, verbose_name="Literal (Escala Cualitativa)")
    es_consolidado = models.BooleanField(
        default=False, verbose_name="¿Es una nota consolidada?",
        help_text="Indica si esta nota es el cálculo agregado de evaluaciones/consolidados inferiores."
    )
    calificacion_padre = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True,
        related_name="desglosadas", verbose_name="Nota Consolidada Padre"
    )
    observacion = models.CharField(max_length=255, blank=True, verbose_name="Observación / Comentario")
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Última modificación por"
    )

    class Meta:
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        ordering = ["materia", "estudiante", "tipo_nota"]

    def __str__(self):
        val_str = str(self.resultado) if self.resultado is not None else "Sin Calificar"
        tipo_str = "Consolidado" if self.es_consolidado else "Parcial"
        return f"{self.estudiante.codigo_estudiante} - {self.materia.nombre} ({self.tipo_nota.nombre}): {val_str} [{tipo_str}]"


class ResumenAcademicoEstudiante(models.Model):
    """
    Promedio acumulado y resumen de rendimiento académico de un estudiante por período lectivo.
    """
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name="resumenes_academicos", verbose_name="Estudiante"
    )
    periodo = models.ForeignKey(
        PeriodoLectivo, on_delete=models.CASCADE, related_name="resumenes_academicos", verbose_name="Período Lectivo"
    )
    promedio_general = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Promedio General Acumulado"
    )
    materias_reprobadas = models.PositiveIntegerField(default=0, verbose_name="Número de materias reprobadas")
    materias_reparadas = models.PositiveIntegerField(default=0, verbose_name="Número de materias en reparación")

    class Meta:
        verbose_name = "Resumen Académico de Estudiante"
        verbose_name_plural = "Resúmenes Académicos de Estudiantes"
        unique_together = ("estudiante", "periodo")

    def __str__(self):
        prom_str = str(self.promedio_general) if self.promedio_general is not None else "N/A"
        return f"{self.estudiante.codigo_estudiante} ({self.periodo.nombre}): Promedio {prom_str}"
