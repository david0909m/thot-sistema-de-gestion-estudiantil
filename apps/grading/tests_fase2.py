from django.test import TestCase
from decimal import Decimal
from datetime import date
from django.core.exceptions import ValidationError
from apps.academic_core.models import PeriodoLectivo, Nivel, Asignatura, Clase, Seccion, Materia, TipoNota
from apps.people.models import Estudiante, EstudianteClase
from apps.grading.models import Evaluacion, Calificacion, ResumenAcademicoEstudiante
from apps.grading.services import (
    crear_evaluacion_con_calificaciones,
    consolidar_calificaciones_materia,
    reabrir_consolidado_materia,
    calcular_promedio_estudiante,
    convertir_nota_a_literal
)


class Fase2CalificacionesTests(TestCase):
    def setUp(self):
        self.periodo = PeriodoLectivo.objects.create(
            nombre="2026", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 11, 30), activo=True
        )
        self.tipo_bloque = TipoNota.objects.create(nombre="Bloque I", periodo=self.periodo, es_consolidado=True, orden=1)
        self.tipo_parcial = TipoNota.objects.create(nombre="Parcial 1", periodo=self.periodo, padre=self.tipo_bloque, orden=2)

        self.nivel = Nivel.objects.create(nombre="Secundaria")
        self.clase = Clase.objects.create(periodo=self.periodo, nivel=self.nivel, nombre="7mo Grado")
        self.seccion = Seccion.objects.create(clase=self.clase, codigo="SEC-7A", nombre="Sección A")
        self.asignatura = Asignatura.objects.create(nombre="Matemáticas", codigo="MAT101")
        self.materia = Materia.objects.create(
            nombre="Matemáticas I", asignatura=self.asignatura, clase=self.clase, seccion=self.seccion
        )

        self.estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-2026-777", primer_nombre="Ana", primer_apellido="Martínez", genero="F"
        )
        self.matricula = EstudianteClase.objects.create(
            estudiante=self.estudiante, periodo=self.periodo, clase=self.clase, seccion=self.seccion
        )

    def test_evaluacion_percentage_cap_validation(self):
        crear_evaluacion_con_calificaciones(
            materia=self.materia,
            tipo_nota=self.tipo_parcial,
            nombre="Tarea 1",
            fecha=date(2026, 3, 1),
            porcentaje=Decimal("60.00")
        )

        with self.assertRaises(ValidationError):
            crear_evaluacion_con_calificaciones(
                materia=self.materia,
                tipo_nota=self.tipo_parcial,
                nombre="Tarea 2",
                fecha=date(2026, 3, 5),
                porcentaje=Decimal("50.00")  # 60 + 50 = 110 > 100
            )

    def test_literal_scale_conversion(self):
        self.assertEqual(convertir_nota_a_literal(Decimal("95.50")), "A")
        self.assertEqual(convertir_nota_a_literal(Decimal("82.00")), "B")
        self.assertEqual(convertir_nota_a_literal(Decimal("75.00")), "C")
        self.assertEqual(convertir_nota_a_literal(Decimal("65.00")), "D")
        self.assertEqual(convertir_nota_a_literal(Decimal("45.00")), "F")

    def test_recursive_decimal_consolidation_and_reopen(self):
        eval1 = crear_evaluacion_con_calificaciones(
            materia=self.materia,
            tipo_nota=self.tipo_parcial,
            nombre="Examen 1",
            fecha=date(2026, 3, 10),
            porcentaje=Decimal("100.00")
        )

        calif = Calificacion.objects.get(evaluacion=eval1, estudiante=self.estudiante)
        calif.resultado = Decimal("88.50")
        calif.save()

        # Consolidar
        consolidados = consolidar_calificaciones_materia(self.materia, self.tipo_parcial)
        self.assertEqual(len(consolidados), 1)
        self.assertEqual(consolidados[0].resultado, Decimal("88.50"))

        # Reabrir
        reabiertos = reabrir_consolidado_materia(self.materia, self.tipo_parcial)
        self.assertEqual(reabiertos, 1)

    def test_student_general_average_calculation(self):
        Calificacion.objects.create(
            materia=self.materia,
            tipo_nota=self.tipo_bloque,
            estudiante=self.estudiante,
            resultado=Decimal("85.00"),
            es_consolidado=True
        )

        resumen = calcular_promedio_estudiante(self.estudiante, self.periodo)
        self.assertIsNotNone(resumen)
        self.assertEqual(resumen.promedio_general, Decimal("85.00"))
        self.assertEqual(resumen.materias_reprobadas, 0)
