import re
from datetime import timedelta

from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.forms import CambiarPasswordForm
from config import settings as project_settings

User = get_user_model()


class LoginPorCorreoTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="correo_user",
            email="usuario@colegio.edu",
            password="ClaveSegura2026!",
        )

    def test_login_con_email_valido(self):
        response = self.client.post(
            reverse("login"),
            {"username": "usuario@colegio.edu", "password": "ClaveSegura2026!"},
        )
        self.assertRedirects(response, reverse("dashboard"))

    def test_login_con_email_en_diferente_caso(self):
        response = self.client.post(
            reverse("login"),
            {"username": "USUARIO@COLEGIO.EDU", "password": "ClaveSegura2026!"},
        )
        self.assertRedirects(response, reverse("dashboard"))

    def test_login_con_email_desconocido_falla(self):
        response = self.client.post(
            reverse("login"),
            {"username": "desconocido@colegio.edu", "password": "ClaveSegura2026!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="desconocido@colegio.edu").exists())


class ValidacionPasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="validador",
            password="ClaveSegura2026!",
        )

    def test_form_rechaza_password_debil(self):
        form = CambiarPasswordForm(
            data={
                "current_password": "ClaveSegura2026!",
                "new_password": "12345678",
                "confirm_password": "12345678",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors.get("new_password"))

    def test_vista_rechaza_password_debil_y_no_cambia(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("cambiar_password"),
            {
                "current_password": "ClaveSegura2026!",
                "new_password": "12345678",
                "confirm_password": "12345678",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("ClaveSegura2026!"))

    def test_cambio_valido_renueva_fecha_vencimiento(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("cambiar_password"),
            {
                "current_password": "ClaveSegura2026!",
                "new_password": "NuevaClaveFuerte456!",
                "confirm_password": "NuevaClaveFuerte456!",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.user.refresh_from_db()
        esperado_min = timezone.now() + timedelta(days=179)
        esperado_max = timezone.now() + timedelta(days=181)
        self.assertIsNotNone(self.user.fecha_vencimiento_password)
        self.assertLessEqual(self.user.fecha_vencimiento_password, esperado_max)
        self.assertGreaterEqual(self.user.fecha_vencimiento_password, esperado_min)
        self.assertFalse(self.user.requiere_cambio_password)


class RecuperacionPasswordFlujoTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="recuperable",
            email="recuperable@colegio.edu",
            password="ClaveSegura2026!",
        )

    def test_settings_de_operacion_segura(self):
        self.assertEqual(project_settings.SESSION_COOKIE_AGE, 3600)
        self.assertTrue(project_settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)

    def test_flujo_completo_de_recuperacion(self):
        response = self.client.post(
            reverse("password_reset"), {"email": "recuperable@colegio.edu"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)

        cuerpo = mail.outbox[0].body
        coincidencia = re.search(r"/password-reset/([A-Za-z0-9_\-]+)/(\w+-\w+)/", cuerpo)
        self.assertIsNotNone(coincidencia, "El correo no contiene el enlace de restablecimiento")
        uidb64, token = coincidencia.group(1), coincidencia.group(2)

        confirm_url = reverse(
            "password_reset_confirm", kwargs={"uidb64": uidb64, "token": token}
        )
        response_get = self.client.get(confirm_url)
        # Django redirige a la variante con token en sesión antes de mostrar el form
        final_url = response_get.url if response_get.status_code == 302 else confirm_url
        response_form = self.client.get(final_url)
        self.assertEqual(response_form.status_code, 200)

        response_post = self.client.post(
            final_url,
            {"new_password1": "Recuperada2026!", "new_password2": "Recuperada2026!"},
        )
        self.assertRedirects(response_post, reverse("password_reset_complete"))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Recuperada2026!"))

    def test_correo_desconocido_no_rompe_el_flujo(self):
        response = self.client.post(
            reverse("password_reset"), {"email": "nadie@colegio.edu"}
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)
