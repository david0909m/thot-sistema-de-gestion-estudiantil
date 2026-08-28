from django.test import TestCase
from apps.accounts.models import User
from apps.people.models import Estudiante
from apps.audit.models import AuditEvent
from apps.audit.services import registrar_evento
from apps.audit.views_history import (
    obtener_historial_entidad,
    consultar_estado_historico_por_fecha,
    restaurar_version_historica
)


class AuditServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="adminuser",
            password="AdminPassword123!"
        )

    def test_registrar_evento_basic(self):
        evento = registrar_evento(
            accion="LOGIN_EXITOSO",
            usuario=self.user,
            ip_address="192.168.1.50",
            origen="WEB",
            descripcion="Inicio de sesión correcto"
        )
        self.assertEqual(AuditEvent.objects.count(), 1)
        self.assertEqual(evento.accion, "LOGIN_EXITOSO")
        self.assertEqual(evento.usuario, self.user)
        self.assertEqual(evento.username_log, "adminuser")
        self.assertTrue(evento.exito)

    def test_registrar_evento_sanitization(self):
        evento = registrar_evento(
            accion="CAMBIO_PASSWORD",
            usuario=self.user,
            detalles={
                "old_password": "MyOldPassword",
                "new_password": "MyNewPassword123",
                "motivo": "Expiración periódica"
            }
        )
        self.assertEqual(evento.detalles["old_password"], "[PROTEGIDO]")
        self.assertEqual(evento.detalles["new_password"], "[PROTEGIDO]")
        self.assertEqual(evento.detalles["motivo"], "Expiración periódica")

    def test_historial_y_restauracion_version(self):
        estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-HIST-01",
            primer_nombre="Mateo",
            primer_apellido="Silva",
            genero="M"
        )
        historial = obtener_historial_entidad(Estudiante, estudiante.id)
        self.assertEqual(historial.count(), 1)

        v1_history_id = historial.first().history_id

        # Modificación de datos
        estudiante.primer_nombre = "Mateo Alejandro"
        estudiante.save()

        historial_actualizado = obtener_historial_entidad(Estudiante, estudiante.id)
        self.assertEqual(historial_actualizado.count(), 2)

        # Restauración a versión 1
        estudiante_restaurado = restaurar_version_historica(
            Estudiante, estudiante.id, v1_history_id, usuario=self.user
        )
        self.assertEqual(estudiante_restaurado.primer_nombre, "Mateo")
        self.assertTrue(
            AuditEvent.objects.filter(accion="RESTAURAR_VERSION_HISTORICA").exists()
        )
