from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from datetime import date, time
from apps.accounts.models import User
from apps.academic_core.models import PeriodoLectivo, Nivel, Asignatura, Clase, Seccion, Materia, Horario


class Fase1AStructureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="admin_fase1a", password="password", is_superuser=True
        )
        self.periodo = PeriodoLectivo.objects.create(
            nombre="2026", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 11, 30), activo=True
        )
        self.nivel = Nivel.objects.create(nombre="Secundaria")
        self.clase = Clase.objects.create(periodo=self.periodo, nivel=self.nivel, nombre="8vo Grado")
        self.seccion = Seccion.objects.create(clase=self.clase, codigo="SEC-8A", nombre="Sección A")
        self.asignatura = Asignatura.objects.create(nombre="Física", codigo="FIS101")
        self.materia = Materia.objects.create(
            nombre="Física I", asignatura=self.asignatura, clase=self.clase, seccion=self.seccion, lock_version=0
        )

    def test_materia_optimistic_locking_prevents_stale_update(self):
        materia_instance_1 = Materia.objects.get(pk=self.materia.pk)
        materia_instance_2 = Materia.objects.get(pk=self.materia.pk)

        materia_instance_1.nombre = "Física Elemental"
        materia_instance_1.save()  # Increases lock_version to 1

        materia_instance_2.nombre = "Física II"
        with self.assertRaises(ValidationError):
            materia_instance_2.save()  # Fails because lock_version is 0

    def test_horario_overlap_validation(self):
        Horario.objects.create(
            materia=self.materia,
            dia_semana=1,
            hora_inicio=time(8, 0),
            hora_fin=time(9, 30),
            aula="101"
        )

        overlapping_horario = Horario(
            materia=self.materia,
            dia_semana=1,
            hora_inicio=time(9, 0),
            hora_fin=time(10, 30),
            aula="102"
        )
        with self.assertRaises(ValidationError):
            overlapping_horario.full_clean()

    def test_clases_and_horarios_views_render(self):
        self.client.force_login(self.user)

        res_clases = self.client.get(reverse("clases_list"))
        self.assertEqual(res_clases.status_code, 200)
        self.assertContains(res_clases, "8vo Grado")

        res_horarios = self.client.get(reverse("horarios_list"))
        self.assertEqual(res_horarios.status_code, 200)
