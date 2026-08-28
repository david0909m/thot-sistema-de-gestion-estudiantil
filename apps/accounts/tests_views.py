from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.accounts.forms import LoginForm


class AccountViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = "testwebadmin"
        self.password = "TestWebPass123!"
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            is_staff=True,
            is_superuser=True
        )

    def test_login_form_validation(self):
        form = LoginForm(data={"username": self.username, "password": self.password})
        self.assertTrue(form.is_valid())

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_login_successful_authenticates_and_redirects(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.username, "password": self.password}
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(AuditEvent.objects.filter(accion="LOGIN_EXITOSO").exists())

    def test_login_failed_shows_error(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.username, "password": "WrongPassword"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Usuario o contraseña incorrectos.")
        self.assertTrue(AuditEvent.objects.filter(accion="LOGIN_FALLIDO").exists())

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_dashboard_access_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/index.html")
