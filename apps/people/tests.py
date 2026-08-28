from datetime import date
from django.test import TestCase
from apps.academic_core.models import PeriodoLectivo, Nivel, Clase, Seccion
from apps.people.models import Estudiante, Pariente, Responsable, EstudianteClase
from apps.people.services import trasladar_estudiante


class PeopleModelAndServiceTests(TestCase):
    def setUp(self):
        self.periodo = PeriodoLectivo.objects.create(
            nombre="Año Escolar 2026",
            fecha_inicio=date(2026, 1, 15),
            fecha_fin=date(2026, 11, 30),
            activo=True
        )
        self.nivel = Nivel.objects.create(nombre="Primaria", codigo="PRIM")
        self.clase = Clase.objects.create(nombre="5to Grado", periodo=self.periodo, nivel=self.nivel)
        self.seccion_a = Seccion.objects.create(nombre="Sección A", codigo="5A", clase=self.clase)
        self.seccion_b = Seccion.objects.create(nombre="Sección B", codigo="5B", clase=self.clase)

        self.estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-2026-001",
            primer_nombre="Carlos",
            primer_apellido="Mendoza",
            genero="M"
        )

        self.pariente = Pariente.objects.create(
            primer_nombre="Roberto",
            primer_apellido="Mendoza",
            parentesco="PADRE",
            telefono="8888-9999"
        )

        self.responsable = Responsable.objects.create(
            estudiante=self.estudiante,
            pariente=self.pariente,
            es_representante_legal=True,
            es_responsable_financiero=True
        )

        self.matricula = EstudianteClase.objects.create(
            estudiante=self.estudiante,
            clase=self.clase,
            seccion=self.seccion_a,
            periodo=self.periodo,
            estado="INSCRITO"
        )

    def test_estudiante_and_responsable_creation(self):
        self.assertEqual(self.estudiante.codigo_estudiante, "EST-2026-001")
        self.assertEqual(self.estudiante.responsables.count(), 1)
        self.assertEqual(self.estudiante.responsables.first().pariente, self.pariente)

    def test_estudiante_history(self):
        self.assertEqual(self.estudiante.history.count(), 1)
        self.estudiante.segundo_nombre = "Alberto"
        self.estudiante.save()
        self.assertEqual(self.estudiante.history.count(), 2)

    def test_trasladar_estudiante_service(self):
        matricula_actualizada = trasladar_estudiante(self.matricula, self.seccion_b)
        
        self.assertEqual(matricula_actualizada.seccion, self.seccion_b)
        self.assertEqual(matricula_actualizada.estado, "TRASLADADO")
