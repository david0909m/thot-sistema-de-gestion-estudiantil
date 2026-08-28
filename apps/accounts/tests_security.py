from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User


class SecurityMiddlewareTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="user_expirado",
            password="OldPassword123!",
            requiere_cambio_password=True,
            is_superuser=True
        )

    def test_middleware_redirects_user_requiring_password_change(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("cambiar_password"))

    def test_user_can_change_password_and_clears_flag(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("cambiar_password"),
            {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!",
                "confirm_password": "NewPassword456!",
            }
        )
        self.assertRedirects(response, reverse("dashboard"))
        
        self.user.refresh_from_db()
        self.assertFalse(self.user.requiere_cambio_password)
        self.assertTrue(self.user.check_password("NewPassword456!"))
