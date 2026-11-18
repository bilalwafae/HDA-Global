from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model


class CoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.staff_user = User.objects.create_user(
            username="directeur",
            password="secretpassword",
            is_staff=True,
        )

    def test_home_page(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "H.D.A GLOBAL")

    def test_about_page(self):
        response = self.client.get(reverse("core:about"))
        self.assertEqual(response.status_code, 200)

    def test_contact_page(self):
        response = self.client.get(reverse("core:contact"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_login_required(self):
        response = self.client.get(reverse("core:dashboard"))
        # Redirection vers le login admin
        self.assertEqual(response.status_code, 302)

    def test_dashboard_staff_access(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tableau de Bord Exécutif")
        self.assertContains(response, "donut-metiers")
        self.assertContains(response, "donut-pipeline")

