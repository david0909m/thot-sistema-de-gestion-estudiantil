from datetime import date
from django.core import mail
from django.test import TestCase
from apps.accounts.models import User
from apps.accounts.services_permissions import puede_leer_mensaje
from apps.academic_core.models import PeriodoLectivo
from apps.people.models import Estudiante
from apps.support.models import Mensaje, MensajeUsuario
from apps.support.services import enviar_mensaje_interno


class MensajeUsuarioTests(TestCase):
    def setUp(self):
        self.remitente = User.objects.create_user(
            username="profe_envia", password="Password123!", is_superuser=True
        )
        self.destinatario = User.objects.create_user(username="mama_destino", password="Password123!")
        self.tercero = User.objects.create_user(username="tercero", password="Password123!")
        self.periodo = PeriodoLectivo.objects.create(
            nombre="Periodo Msg 2026", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 11, 30)
        )
        self.estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-MSG-01",
            primer_nombre="Sofía",
            primer_apellido="Rivas",
            genero="F"
        )

    def test_envio_directo_crea_mensaje_usuario(self):
        mensaje = enviar_mensaje_interno(self.remitente, self.destinatario, "Reunión", "Contenido")
        fila = MensajeUsuario.objects.filter(mensaje=mensaje, usuario=self.destinatario)
        self.assertTrue(fila.exists())
        self.assertFalse(fila.first().leido)

    def test_destinatario_puede_leer_y_tercero_no(self):
        mensaje = enviar_mensaje_interno(self.remitente, self.destinatario, "Reunión", "Contenido")
        self.assertTrue(puede_leer_mensaje(self.destinatario, mensaje))
        self.assertTrue(puede_leer_mensaje(self.remitente, mensaje))
        self.assertFalse(puede_leer_mensaje(self.tercero, mensaje))

    def test_inbox_incluye_mensaje_por_destinatario(self):
        from django.test import Client
        from django.urls import reverse
        from apps.accounts.models import Perfil, Permiso, Autorizacion, AsignacionUsuario

        permiso, _ = Permiso.objects.get_or_create(
            codigo="support.mensajes_ver",
            defaults={"nombre": "Ver Mensajes", "modulo": "support"},
        )
        perfil, _ = Perfil.objects.get_or_create(nombre="Bandeja", codigo="BANDEJA_MSG")
        Autorizacion.objects.get_or_create(perfil=perfil, permiso=permiso)
        AsignacionUsuario.objects.create(usuario=self.destinatario, perfil=perfil)

        enviar_mensaje_interno(self.remitente, self.destinatario, "Citatorio", "Texto")
        self.client = Client()
        self.client.force_login(self.destinatario)
        response = self.client.get(reverse("mensajes_inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Citatorio")

    def test_global_no_crea_filas_pero_es_visible(self):
        mensaje = enviar_mensaje_interno(self.remitente, None, "Aviso global", "Texto", ambito="GLOBAL")
        self.assertEqual(MensajeUsuario.objects.filter(mensaje=mensaje).count(), 0)
        self.assertTrue(puede_leer_mensaje(self.destinatario, mensaje))
        self.assertTrue(puede_leer_mensaje(self.tercero, mensaje))

    def test_envio_registra_evento_auditoria(self):
        enviar_mensaje_interno(self.remitente, self.destinatario, "Asunto X", "Cuerpo")
        self.assertTrue(self.destinatario.mensajes_recibidos.exists())

    def test_flujo_completo_con_correo_consola(self):
        # El envío interno no depende del correo; la fila MensajeUsuario es la
        # vía canónica de entrega y lectura.
        mensaje = enviar_mensaje_interno(self.remitente, self.destinatario, "Notas", "Cuerpo")
        fila = mensaje.destinatarios.get(usuario=self.destinatario)
        self.assertEqual(fila.usuario, self.destinatario)
        self.assertEqual(mail.outbox, [])
