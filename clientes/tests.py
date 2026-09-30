from django.test import TestCase

from .forms import ClienteForm


class ClienteFormTests(TestCase):
    def test_celular_e_obrigatorio(self):
        form = ClienteForm(data={'nome': 'Maria', 'celular': '', 'email': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('celular', form.errors)

    def test_email_e_opcional(self):
        form = ClienteForm(data={'nome': 'Maria', 'celular': '61999999999', 'email': ''})
        self.assertTrue(form.is_valid())
