from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date
from apps.accounts.models import User
from apps.academic_core.models import PeriodoLectivo
from apps.people.models import Estudiante
from apps.support.models import Incidencia, Mensaje, Adjunto
from apps.support.services import enviar_mensaje_interno


class Fase1CSoporteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_sender = User.objects.create_user(username="remitente1", password="password", is_superuser=True)
        self.user_dest = User.objects.create_user(username="destinatario1", password="password")

        self.periodo = PeriodoLectivo.objects.create(
            nombre="2026", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 11, 30), activo=True
        )
        self.estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-2026-999", primer_nombre="Juan", primer_apellido="López", genero="M"
        )

    def test_enviar_mensaje_interno_con_adjunto(self):
        archivo = SimpleUploadedFile("nota.txt", b"Contenido de prueba", content_type="text/plain")
        mensaje = enviar_mensaje_interno(
            remitente=self.user_sender,
            destinatario=self.user_dest,
            asunto="Aviso importante",
            cuerpo="Contenido del mensaje",
            archivo_adjunto=archivo
        )

        self.assertEqual(mensaje.asunto, "Aviso importante")
        self.assertEqual(Adjunto.objects.count(), 1)
        adjunto = Adjunto.objects.first()
        self.assertEqual(adjunto.nombre_original, "nota.txt")

    def test_incidencias_and_mensajes_views_render(self):
        self.client.force_login(self.user_sender)

        res_inc = self.client.get(reverse("incidencias_list"))
        self.assertEqual(res_inc.status_code, 200)

        res_msg = self.client.get(reverse("mensajes_inbox"))
        self.assertEqual(res_msg.status_code, 200)
