from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import Perfil, Permiso, Autorizacion
from apps.people.models import Estudiante, FichaMedica

User = get_user_model()


class SecuritySectionDUITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="admin_test_d",
            email="admin_d@test.com",
            password="adminpassword123"
        )
        self.client.force_login(self.user)

        self.perfil = Perfil.objects.create(
            nombre="Coordinador",
            codigo="COORD",
            descripcion="Coordinación docente"
        )
        self.permiso = Permiso.objects.create(
            nombre="Ver Dashboard",
            codigo="accounts.dashboard_ver",
            modulo="accounts"
        )
        Autorizacion.objects.create(perfil=self.perfil, permiso=self.permiso)

        self.estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-2026-MED",
            primer_nombre="Elena",
            primer_apellido="Rivas",
            genero="F",
            activo=True
        )
        self.ficha = FichaMedica.objects.create(
            estudiante=self.estudiante,
            tipo_sangre="O+",
            alergias="Penicilina",
            seguro_medico="Cruz Roja",
            contacto_emergencia_nombre="María Rivas",
            contacto_emergencia_telefono="555-9988"
        )

    def test_usuarios_and_roles_views_render_200(self):
        res_user_list = self.client.get(reverse("usuarios_list"))
        self.assertEqual(res_user_list.status_code, 200)
        self.assertContains(res_user_list, "Cuentas de Usuario")

        res_user_create = self.client.get(reverse("usuario_create"))
        self.assertEqual(res_user_create.status_code, 200)

        res_user_edit = self.client.get(reverse("usuario_edit", args=[self.user.id]))
        self.assertEqual(res_user_edit.status_code, 200)

        res_roles_list = self.client.get(reverse("roles_list"))
        self.assertEqual(res_roles_list.status_code, 200)
        self.assertContains(res_roles_list, "Coordinador")

        res_rol_create = self.client.get(reverse("rol_create"))
        self.assertEqual(res_rol_create.status_code, 200)

        res_rol_edit = self.client.get(reverse("rol_edit", args=[self.perfil.id]))
        self.assertEqual(res_rol_edit.status_code, 200)

    def test_ficha_medica_view_render_200(self):
        res_ficha = self.client.get(reverse("ficha_medica", args=[self.estudiante.id]))
        self.assertEqual(res_ficha.status_code, 200)
        self.assertContains(res_ficha, "Ficha Médica")
        self.assertContains(res_ficha, "Elena Rivas")
        self.assertContains(res_ficha, "Penicilina")

    def test_post_ficha_medica(self):
        post_data = {
            "tipo_sangre": "A+",
            "alergias": "Polvo y Polen",
            "padecimientos_cronicos": "Asma Leve",
            "medicamentos_permanentes": "Salbutamol si lo requiere",
            "seguro_medico": "Seguros Nacionales",
            "numero_poliza": "POL-12345",
            "contacto_emergencia_nombre": "Carlos Rivas",
            "contacto_emergencia_telefono": "555-1122",
            "autoriza_traslado_hospital": True,
            "observaciones": "Evitar esfuerzos extremos al aire libre."
        }
        res = self.client.post(reverse("ficha_medica", args=[self.estudiante.id]), post_data)
        self.assertEqual(res.status_code, 302)
        self.ficha.refresh_from_db()
        self.assertEqual(self.ficha.tipo_sangre, "A+")
        self.assertEqual(self.ficha.alergias, "Polvo y Polen")
