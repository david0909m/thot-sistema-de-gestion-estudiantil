from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.academic_core.models import (
    PeriodoLectivo, Nivel, Clase, Seccion, Asignatura, Escala, TipoNota,
    EstadoCivil, Religion, Escolaridad, Recorrido
)
from apps.reporting.models import ConfiguracionInstitucion

User = get_user_model()


class AcademicSectionBUITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="admin_test_b",
            email="admin_b@test.com",
            password="adminpassword123"
        )
        self.client.force_login(self.user)

        self.institucion = ConfiguracionInstitucion.get_solo()
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
        self.escala = Escala.objects.create(nombre="Escala 0-100", codigo="ESC-100")
        self.tipo_nota = TipoNota.objects.create(
            nombre="Bloque 1", periodo=self.periodo, es_consolidado=True, porcentaje=50, orden=1
        )

        EstadoCivil.objects.create(nombre="Soltero", codigo="SOL")
        Religion.objects.create(nombre="Católica", codigo="CAT")
        Escolaridad.objects.create(nombre="Primaria Completa", codigo="PRI")
        Recorrido.objects.create(nombre="Ruta Norte", codigo="R-01")

    def test_configuracion_institucion_view_render_200(self):
        res = self.client.get(reverse("configuracion_institucion"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Identidad Institucional")

    def test_periodo_create_and_edit_render_200(self):
        res_create = self.client.get(reverse("periodo_create"))
        self.assertEqual(res_create.status_code, 200)

        res_edit = self.client.get(reverse("periodo_edit", args=[self.periodo.id]))
        self.assertEqual(res_edit.status_code, 200)

    def test_clase_and_seccion_create_and_edit_render_200(self):
        res_clase_create = self.client.get(reverse("clase_create"))
        self.assertEqual(res_clase_create.status_code, 200)

        res_clase_edit = self.client.get(reverse("clase_edit", args=[self.clase.id]))
        self.assertEqual(res_clase_edit.status_code, 200)

        res_sec_create = self.client.get(reverse("seccion_create"))
        self.assertEqual(res_sec_create.status_code, 200)

        res_sec_edit = self.client.get(reverse("seccion_edit", args=[self.seccion.id]))
        self.assertEqual(res_sec_edit.status_code, 200)

    def test_asignaturas_and_niveles_views_render_200(self):
        res_asig_list = self.client.get(reverse("asignaturas_list"))
        self.assertEqual(res_asig_list.status_code, 200)
        self.assertContains(res_asig_list, "Matemáticas")

        res_asig_create = self.client.get(reverse("asignatura_create"))
        self.assertEqual(res_asig_create.status_code, 200)

        res_asig_edit = self.client.get(reverse("asignatura_edit", args=[self.asignatura.id]))
        self.assertEqual(res_asig_edit.status_code, 200)

        res_niv_list = self.client.get(reverse("niveles_list"))
        self.assertEqual(res_niv_list.status_code, 200)

        res_niv_create = self.client.get(reverse("nivel_create"))
        self.assertEqual(res_niv_create.status_code, 200)

        res_niv_edit = self.client.get(reverse("nivel_edit", args=[self.nivel.id]))
        self.assertEqual(res_niv_edit.status_code, 200)

    def test_tipos_nota_and_escalas_views_render_200(self):
        res_tn_list = self.client.get(reverse("tipos_nota_list"))
        self.assertEqual(res_tn_list.status_code, 200)
        self.assertContains(res_tn_list, "Bloque 1")

        res_tn_create = self.client.get(reverse("tipo_nota_create"))
        self.assertEqual(res_tn_create.status_code, 200)

        res_tn_edit = self.client.get(reverse("tipo_nota_edit", args=[self.tipo_nota.id]))
        self.assertEqual(res_tn_edit.status_code, 200)

        res_esc_list = self.client.get(reverse("escalas_list"))
        self.assertEqual(res_esc_list.status_code, 200)

        res_esc_create = self.client.get(reverse("escala_create"))
        self.assertEqual(res_esc_create.status_code, 200)

        res_esc_edit = self.client.get(reverse("escala_edit", args=[self.escala.id]))
        self.assertEqual(res_esc_edit.status_code, 200)

    def test_catalogos_panel_render_200(self):
        res_cat = self.client.get(reverse("catalogos_panel"))
        self.assertEqual(res_cat.status_code, 200)
        self.assertContains(res_cat, "Estados Civiles")
        self.assertContains(res_cat, "Catálogo de Religiones")
