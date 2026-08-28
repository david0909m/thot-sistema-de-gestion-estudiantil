from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.academic_core.models import (
    PeriodoLectivo, TipoNota, Nivel, Asignatura, Clase, Seccion, Materia
)
from apps.people.models import Estudiante, EstudianteClase
from apps.grading.models import Evaluacion, Calificacion, ResumenAcademicoEstudiante
from apps.grading.services import (
    crear_evaluacion_con_calificaciones,
    consolidar_calificaciones_materia,
    reabrir_consolidado_materia,
    calcular_promedio_estudiante
)


class GradingServiceTests(TestCase):
    def setUp(self):
        self.periodo = PeriodoLectivo.objects.create(
            nombre="Año Lectivo 2026",
            fecha_inicio=date(2026, 1, 15),
            fecha_fin=date(2026, 11, 30),
            activo=True
        )
        self.nivel = Nivel.objects.create(nombre="Secundaria", codigo="SEC")
        self.clase = Clase.objects.create(nombre="8vo Grado", periodo=self.periodo, nivel=self.nivel)
        self.seccion = Seccion.objects.create(nombre="Sección A", codigo="8A", clase=self.clase)

        self.asignatura = Asignatura.objects.create(nombre="Matemáticas", codigo="MAT-8")
        self.materia = Materia.objects.create(
            nombre="Matemáticas 8vo A",
            asignatura=self.asignatura,
            clase=self.clase,
            seccion=self.seccion
        )

        # Jerarquía de Notas: Bloque I (Consolidado) -> Parcial 1
        self.tipo_bloque = TipoNota.objects.create(
            nombre="Bloque I",
            periodo=self.periodo,
            es_consolidado=True,
            orden=1
        )
        self.tipo_parcial = TipoNota.objects.create(
            nombre="Parcial 1",
            periodo=self.periodo,
            padre=self.tipo_bloque,
            es_consolidado=False,
            orden=1,
            porcentaje=Decimal("100.00")
        )

        # Alumnos matriculados
        self.estudiante_1 = Estudiante.objects.create(
            codigo_estudiante="EST-GRD-01",
            primer_nombre="Mario",
            primer_apellido="Bros",
            genero="M"
        )
        self.estudiante_2 = Estudiante.objects.create(
            codigo_estudiante="EST-GRD-02",
            primer_nombre="Luigi",
            primer_apellido="Bros",
            genero="M"
        )

        EstudianteClase.objects.create(
            estudiante=self.estudiante_1, clase=self.clase, seccion=self.seccion, periodo=self.periodo
        )
        EstudianteClase.objects.create(
            estudiante=self.estudiante_2, clase=self.clase, seccion=self.seccion, periodo=self.periodo
        )

    def test_crear_evaluacion_autogenera_calificaciones(self):
        evaluacion = crear_evaluacion_con_calificaciones(
            materia=self.materia,
            tipo_nota=self.tipo_parcial,
            nombre="Examen Corto 1",
            fecha=date(2026, 3, 1),
            porcentaje=Decimal("40.00")
        )

        self.assertEqual(evaluacion.calificaciones.count(), 2)
        calif_mario = Calificacion.objects.get(evaluacion=evaluacion, estudiante=self.estudiante_1)
        self.assertIsNone(calif_mario.resultado)
        self.assertFalse(calif_mario.es_consolidado)

    def test_consolidacion_ponderada_decimal_exacta(self):
        # 1. Crear 2 evaluaciones con porcentajes 40% y 60%
        eval_1 = crear_evaluacion_con_calificaciones(
            materia=self.materia, tipo_nota=self.tipo_parcial,
            nombre="Trabajos Prácticos", fecha=date(2026, 3, 10), porcentaje=Decimal("40.00")
        )
        eval_2 = crear_evaluacion_con_calificaciones(
            materia=self.materia, tipo_nota=self.tipo_parcial,
            nombre="Examen Parcial", fecha=date(2026, 3, 25), porcentaje=Decimal("60.00")
        )

        # 2. Asignar notas: Mario -> (85.50 @ 40%) + (92.00 @ 60%) = 34.20 + 55.20 = 89.40
        c1 = Calificacion.objects.get(evaluacion=eval_1, estudiante=self.estudiante_1)
        c1.resultado = Decimal("85.50")
        c1.save()

        c2 = Calificacion.objects.get(evaluacion=eval_2, estudiante=self.estudiante_1)
        c2.resultado = Decimal("92.00")
        c2.save()

        # 3. Consolidar calificaciones para Parcial 1
        consolidados = consolidar_calificaciones_materia(self.materia, self.tipo_parcial, redondear=False)

        c_parcial = Calificacion.objects.get(
            materia=self.materia, tipo_nota=self.tipo_parcial, estudiante=self.estudiante_1, es_consolidado=True
        )
        self.assertEqual(c_parcial.resultado, Decimal("89.40"))

    def test_consolidacion_recursiva_padre_hijo(self):
        # 1. Generar consolidado Parcial 1
        eval_1 = crear_evaluacion_con_calificaciones(
            materia=self.materia, tipo_nota=self.tipo_parcial,
            nombre="Prueba Parcial", fecha=date(2026, 3, 25), porcentaje=Decimal("100.00")
        )
        c1 = Calificacion.objects.get(evaluacion=eval_1, estudiante=self.estudiante_1)
        c1.resultado = Decimal("95.00")
        c1.save()

        consolidar_calificaciones_materia(self.materia, self.tipo_parcial, redondear=False)

        # 2. Consolidar Bloque I (que agrupa Parcial 1)
        consolidar_calificaciones_materia(self.materia, self.tipo_bloque, redondear=False)

        c_bloque = Calificacion.objects.get(
            materia=self.materia, tipo_nota=self.tipo_bloque, estudiante=self.estudiante_1, es_consolidado=True
        )
        self.assertEqual(c_bloque.resultado, Decimal("95.00"))

    def test_reabrir_consolidado_materia(self):
        eval_1 = crear_evaluacion_con_calificaciones(
            materia=self.materia, tipo_nota=self.tipo_parcial,
            nombre="Prueba", fecha=date(2026, 3, 25), porcentaje=Decimal("100.00")
        )
        c1 = Calificacion.objects.get(evaluacion=eval_1, estudiante=self.estudiante_1)
        c1.resultado = Decimal("70.00")
        c1.save()

        consolidar_calificaciones_materia(self.materia, self.tipo_parcial)

        # Reabrir
        reabrir_consolidado_materia(self.materia, self.tipo_parcial)
        c_consolidado = Calificacion.objects.get(
            materia=self.materia, tipo_nota=self.tipo_parcial, estudiante=self.estudiante_1, es_consolidado=True
        )
        self.assertIsNone(c_consolidado.resultado)

    def test_calcular_promedio_estudiante(self):
        # Crear segunda materia para promediar
        asig_his = Asignatura.objects.create(nombre="Historia", codigo="HIS-8")
        materia_his = Materia.objects.create(nombre="Historia 8vo A", asignatura=asig_his, clase=self.clase, seccion=self.seccion)

        # Nota 1: Matemáticas -> 90.00
        Calificacion.objects.create(
            materia=self.materia, tipo_nota=self.tipo_bloque, estudiante=self.estudiante_1,
            resultado=Decimal("90.00"), es_consolidado=True
        )
        # Nota 2: Historia -> 80.00
        Calificacion.objects.create(
            materia=materia_his, tipo_nota=self.tipo_bloque, estudiante=self.estudiante_1,
            resultado=Decimal("80.00"), es_consolidado=True
        )

        resumen = calcular_promedio_estudiante(self.estudiante_1, self.periodo)
        self.assertEqual(resumen.promedio_general, Decimal("85.00"))
        self.assertEqual(resumen.materias_reprobadas, 0)
