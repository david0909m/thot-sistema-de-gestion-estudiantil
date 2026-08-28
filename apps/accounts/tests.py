from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from apps.accounts.models import User, Perfil, Permiso, Autorizacion, AsignacionUsuario
from apps.academic_core.models import Nivel


class AccountsModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="jdoe",
            email="jdoe@colegio.edu",
            password="SecurePassword123!",
            first_name="John",
            last_name="Doe",
            segundo_nombre="Alexander",
            segundo_apellido="Smith",
            cedula_identidad="001-010190-0001A",
            requiere_cambio_password=True,
            habilitado=True
        )

        self.perfil_docente = Perfil.objects.create(
            nombre="Docente",
            codigo="DOCENTE",
            descripcion="Perfil para profesores"
        )

        self.permiso_ver_notas = Permiso.objects.create(
            nombre="Ver Notas",
            codigo="grading.view_grades",
            modulo="grading"
        )

        self.autorizacion = Autorizacion.objects.create(
            perfil=self.perfil_docente,
            permiso=self.permiso_ver_notas
        )

    def test_user_creation_and_custom_fields(self):
        self.assertEqual(self.user.username, "jdoe")
        self.assertEqual(self.user.segundo_nombre, "Alexander")
        self.assertTrue(self.user.requiere_cambio_password)
        self.assertTrue(self.user.habilitado)

    def test_user_history(self):
        self.assertEqual(self.user.history.count(), 1)
        self.user.first_name = "Johnny"
        self.user.save()
        self.assertEqual(self.user.history.count(), 2)

    def test_asigancion_usuario_contextual(self):
        nivel = Nivel.objects.create(nombre="Primaria", codigo="PRIMARIA", orden=1)
        content_type = ContentType.objects.get_for_model(Nivel)

        asignacion = AsignacionUsuario.objects.create(
            usuario=self.user,
            perfil=self.perfil_docente,
            content_type=content_type,
            object_id=nivel.id,
            activo=True
        )

        self.assertEqual(asignacion.usuario, self.user)
        self.assertEqual(asignacion.perfil, self.perfil_docente)
        self.assertEqual(asignacion.ambito_objeto, nivel)
