from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.people.models import Docente, Pariente, Estudiante, EstudianteClase, Responsable
from apps.academic_core.models import PeriodoLectivo, Nivel, Clase, Seccion, Asignatura, Materia

User = get_user_model()


class PeopleSectionAUITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="admin_test",
            email="admin@test.com",
            password="adminpassword123"
        )
        self.client.force_login(self.user)

        self.periodo = PeriodoLectivo.objects.create(
            nombre="2026",
            fecha_inicio=date(2026, 1, 15),
            fecha_fin=date(2026, 11, 30),
            activo=True
        )
        self.nivel = Nivel.objects.create(nombre="Secundaria")
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

        self.estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-2026-001",
            primer_nombre="Carlos",
            primer_apellido="Pérez",
            genero="M",
            activo=True
        )

        self.docente_user = User.objects.create_user(
            username="prof_roberto",
            first_name="Roberto",
            last_name="Gómez",
            email="roberto@test.com",
            password="Password123!"
        )
        self.docente = Docente.objects.create(
            usuario=self.docente_user,
            codigo_empleado="DOC-001",
            especialidad="Ciencias"
        )

        self.pariente = Pariente.objects.create(
            primer_nombre="María",
            primer_apellido="Pérez",
            parentesco="MADRE",
            telefono="555-1234"
        )

    def test_docentes_views_render_200(self):
        response_list = self.client.get(reverse("docentes_list"))
        self.assertEqual(response_list.status_code, 200)
        self.assertContains(response_list, "Planta Docente")

        response_detail = self.client.get(reverse("docente_detail", args=[self.docente.id]))
        self.assertEqual(response_detail.status_code, 200)
        self.assertContains(response_detail, "Roberto Gómez")

        response_create = self.client.get(reverse("docente_create"))
        self.assertEqual(response_create.status_code, 200)

        response_edit = self.client.get(reverse("docente_edit", args=[self.docente.id]))
        self.assertEqual(response_edit.status_code, 200)

    def test_parientes_views_render_200(self):
        response_list = self.client.get(reverse("parientes_list"))
        self.assertEqual(response_list.status_code, 200)
        self.assertContains(response_list, "Directorio de Familiares")

        response_create = self.client.get(reverse("pariente_create"))
        self.assertEqual(response_create.status_code, 200)

        response_edit = self.client.get(reverse("pariente_edit", args=[self.pariente.id]))
        self.assertEqual(response_edit.status_code, 200)

    def test_estudiantes_extended_views_render_200(self):
        response_create = self.client.get(reverse("estudiante_create"))
        self.assertEqual(response_create.status_code, 200)

        response_edit = self.client.get(reverse("estudiante_edit", args=[self.estudiante.id]))
        self.assertEqual(response_edit.status_code, 200)

        response_matricular = self.client.get(reverse("matricular_estudiante", args=[self.estudiante.id]))
        self.assertEqual(response_matricular.status_code, 200)

        response_asignar = self.client.get(reverse("asignar_responsable", args=[self.estudiante.id]))
        self.assertEqual(response_asignar.status_code, 200)

    def test_post_crear_estudiante(self):
        data = {
            "codigo_estudiante": "EST-NEW-999",
            "primer_nombre": "Lucía",
            "primer_apellido": "García",
            "genero": "F",
            "activo": True
        }
        response = self.client.post(reverse("estudiante_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Estudiante.objects.filter(codigo_estudiante="EST-NEW-999").exists())

    def test_post_matricular_estudiante(self):
        data = {
            "estudiante_id": self.estudiante.id,
            "periodo": self.periodo.id,
            "clase": self.clase.id,
            "seccion": self.seccion.id,
            "estado": "INSCRITO"
        }
        response = self.client.post(reverse("matricular_estudiante", args=[self.estudiante.id]), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            EstudianteClase.objects.filter(estudiante=self.estudiante, seccion=self.seccion).exists()
        )
