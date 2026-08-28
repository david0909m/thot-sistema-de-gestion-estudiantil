from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User
from apps.academic_core.models import PeriodoLectivo
from apps.people.models import Estudiante, FichaMedica
from apps.support.models import Incidencia, Mensaje


class SupportModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="profesor1", password="Password123!")
        self.periodo = PeriodoLectivo.objects.create(
            nombre="Periodo Support Test",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 11, 30)
        )
        self.estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-SUP-01",
            primer_nombre="Lucía",
            primer_apellido="Torres",
            genero="F"
        )

    def test_incidencia_creation(self):
        incidencia = Incidencia.objects.create(
            estudiante=self.estudiante,
            periodo=self.periodo,
            tipo_incidencia="MERITO",
            descripcion="Participación destacada en la feria científica.",
            reportado_por=self.user
        )
        self.assertEqual(incidencia.tipo_incidencia, "MERITO")
        self.assertEqual(self.estudiante.incidencias.count(), 1)

    def test_ficha_medica_unicay_visible_en_detalle(self):
        """
        El expediente médico vive únicamente en people.FichaMedica y se muestra
        en el detalle 360° del estudiante.
        """
        ficha = FichaMedica.objects.create(
            estudiante=self.estudiante,
            tipo_sangre="O+",
            alergias="Penicilina",
            contacto_emergencia_nombre="María Torres",
            contacto_emergencia_telefono="8877-6655"
        )
        self.assertEqual(self.estudiante.ficha_medica.tipo_sangre, "O+")
        self.assertEqual(ficha.alergias, "Penicilina")

        admin = User.objects.create_user(username="adminsup", password="Password123!", is_superuser=True)
        client = Client()
        client.force_login(admin)
        response = client.get(reverse("estudiante_detail", kwargs={"estudiante_id": self.estudiante.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "O+")
        self.assertContains(response, "Penicilina")

    def test_mensaje_creation(self):
        mensaje = Mensaje.objects.create(
            remitente=self.user,
            asunto="Aviso importante de reunión",
            cuerpo="Estimados padres, se les convoca a la reunión general.",
            ambito_destinatario="GLOBAL"
        )
        self.assertEqual(mensaje.asunto, "Aviso importante de reunión")
        self.assertEqual(mensaje.ambito_destinatario, "GLOBAL")
