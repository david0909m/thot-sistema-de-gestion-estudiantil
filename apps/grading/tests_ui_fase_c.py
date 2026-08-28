from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.academic_core.models import PeriodoLectivo, Nivel, Clase, Seccion, Asignatura, Materia, TipoNota
from apps.people.models import Estudiante, EstudianteClase
from apps.grading.models import Evaluacion, Calificacion

User = get_user_model()


class GradingSectionCUITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="admin_test_c",
            email="admin_c@test.com",
            password="adminpassword123"
        )
        self.client.force_login(self.user)

        self.periodo = PeriodoLectivo.objects.create(
            nombre="2026",
            fecha_inicio=date(2026, 1, 15),
            fecha_fin=date(2026, 11, 30),
            activo=True
        )
        self.nivel = Nivel.objects.create(nombre="Secundaria", codigo="SEC", orden=1)
        self.clase = Clase.objects.create(periodo=self.periodo, nivel=self.nivel, nombre="Séptimo Grado")
        self.seccion = Seccion.objects.create(clase=self.clase, nombre="A", codigo="SEC-7A")
        self.asignatura = Asignatura.objects.create(nombre="Matemáticas", codigo="MAT-01")
        self.materia = Materia.objects.create(
            nombre="Matemáticas 7A",
            asignatura=self.asignatura,
            clase=self.clase,
            seccion=self.seccion,
            docente=self.user
        )
        self.tipo_nota = TipoNota.objects.create(
            nombre="Bloque 1", periodo=self.periodo, es_consolidado=True, porcentaje=50, orden=1
        )
        self.estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-2026-001",
            primer_nombre="Carlos",
            primer_apellido="Pérez",
            genero="M",
            activo=True
        )
        self.matricula = EstudianteClase.objects.create(
            estudiante=self.estudiante,
            periodo=self.periodo,
            clase=self.clase,
            seccion=self.seccion,
            estado="INSCRITO"
        )

        self.evaluacion = Evaluacion.objects.create(
            materia=self.materia,
            tipo_nota=self.tipo_nota,
            nombre="Examen Parcial 1",
            fecha=date(2026, 3, 15),
            porcentaje=Decimal("30.00")
        )

    def test_evaluacion_views_render_200(self):
        res_list = self.client.get(reverse("evaluaciones_list"))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, "Gestor de Evaluaciones")

        res_create = self.client.get(reverse("evaluacion_create"))
        self.assertEqual(res_create.status_code, 200)

        res_edit = self.client.get(reverse("evaluacion_edit", args=[self.evaluacion.id]))
        self.assertEqual(res_edit.status_code, 200)

        res_notas = self.client.get(reverse("evaluacion_ingreso_notas", args=[self.evaluacion.id]))
        self.assertEqual(res_notas.status_code, 200)
        self.assertContains(res_notas, "Examen Parcial 1")

    def test_sabana_and_boletin_render_200(self):
        res_sabana = self.client.get(reverse("sabana_notas"))
        self.assertEqual(res_sabana.status_code, 200)
        self.assertContains(res_sabana, "Sábana General de Calificaciones")

        res_boletin = self.client.get(reverse("boletin_web", args=[self.estudiante.id]))
        self.assertEqual(res_boletin.status_code, 200)
        self.assertContains(res_boletin, "Boletín Oficial de Calificaciones")
        self.assertContains(res_boletin, "Carlos")

    def test_post_ingreso_notas(self):
        calif = Calificacion.objects.filter(evaluacion=self.evaluacion, estudiante=self.estudiante).first()
        if not calif:
            calif = Calificacion.objects.create(
                materia=self.materia,
                tipo_nota=self.tipo_nota,
                evaluacion=self.evaluacion,
                estudiante=self.estudiante,
                resultado=Decimal("0.00")
            )
        
        post_data = {
            f"nota_{calif.id}": "88.50"
        }
        res = self.client.post(reverse("evaluacion_ingreso_notas", args=[self.evaluacion.id]), post_data)
        self.assertEqual(res.status_code, 302)
        calif.refresh_from_db()
        self.assertEqual(calif.resultado, Decimal("88.50"))
