from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.people.models import Estudiante
from apps.academic_core.models import PeriodoLectivo
from apps.support.models import Incidencia, Mensaje

User = get_user_model()


class SupportDetailUITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="admin_soporte",
            email="admin_soporte@test.com",
            password="adminpassword123"
        )
        self.client.force_login(self.user)

        self.periodo = PeriodoLectivo.objects.create(
            nombre="2026",
            fecha_inicio="2026-01-01",
            fecha_fin="2026-12-31",
            activo=True
        )

        self.estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-SOP-01",
            primer_nombre="Mateo",
            primer_apellido="García",
            genero="M",
            activo=True
        )

        self.incidencia = Incidencia.objects.create(
            estudiante=self.estudiante,
            periodo=self.periodo,
            tipo_incidencia="GRAVE",
            descripcion="Uso indebido de celular en clase.",
            sancion="Llamado de atención.",
            reportado_por=self.user
        )

        self.mensaje = Mensaje.objects.create(
            remitente=self.user,
            asunto="Reunión General Docente",
            cuerpo="Se convoca a reunión este viernes a las 3:00 PM."
        )

    def test_incidencia_detail_view_render_200(self):
        url = reverse("incidencia_detail", args=[self.incidencia.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Uso indebido de celular en clase.")
        self.assertContains(res, "Mateo García")

    def test_actualizar_sancion_post(self):
        url = reverse("incidencia_detail", args=[self.incidencia.id])
        res = self.client.post(url, {
            "actualizar_sancion": "1",
            "sancion": "Suspención de 1 día y citación a tutor."
        })
        self.assertEqual(res.status_code, 302)
        self.incidencia.refresh_from_db()
        self.assertEqual(self.incidencia.sancion, "Suspención de 1 día y citación a tutor.")

    def test_mensaje_detail_view_render_200(self):
        url = reverse("mensaje_detail", args=[self.mensaje.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Reunión General Docente")
        self.assertContains(res, "Se convoca a reunión este viernes")

    def test_admin_base_renders_thot_branding(self):
        res = self.client.get(reverse("admin:index"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "THOT")
