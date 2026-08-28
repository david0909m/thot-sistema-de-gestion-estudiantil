from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User
from apps.people.models import Estudiante


class PeopleViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="peopleadmin", password="TestPass123!", is_superuser=True)
        self.estudiante = Estudiante.objects.create(
            codigo_estudiante="EST-TEST-01",
            primer_nombre="Carlos",
            primer_apellido="Mendoza",
            genero="M"
        )

    def test_estudiantes_list_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("estudiantes_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EST-TEST-01")

    def test_estudiante_detail_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("estudiante_detail", kwargs={"estudiante_id": self.estudiante.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Carlos Mendoza")
