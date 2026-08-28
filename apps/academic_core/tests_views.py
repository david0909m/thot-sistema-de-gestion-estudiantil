from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from apps.accounts.models import User
from apps.academic_core.models import PeriodoLectivo


class AcademicCoreViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="acadadmin", password="TestPass123!", is_superuser=True)
        self.periodo = PeriodoLectivo.objects.create(
            nombre="Año Lectivo 2026",
            fecha_inicio=date(2026, 1, 15),
            fecha_fin=date(2026, 11, 30),
            activo=True
        )

    def test_periodos_list_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("periodos_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Año Lectivo 2026")
