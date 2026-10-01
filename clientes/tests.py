from django.test import TestCase

from .forms import ClienteForm


class ClienteFormTests(TestCase):
    def test_celular_e_obrigatorio(self):
        form = ClienteForm(data={'nome': 'Maria', 'celular': '', 'email': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('celular', form.errors)

    def test_email_e_opcional(self):
        form = ClienteForm(
            data={'nome': 'Maria', 'celular': '61999999999', 'email': ''}
        )
        self.assertTrue(form.is_valid())

    def test_celular_formatado_e_normalizado(self):
        form = ClienteForm(
            data={'nome': 'Maria', 'celular': '(61) 99999-9999', 'email': ''}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['celular'], '61999999999')

    def test_celular_sem_ddd_e_invalido(self):
        form = ClienteForm(
            data={'nome': 'Maria', 'celular': '99999-9999', 'email': ''}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('celular', form.errors)

    def test_telefone_fixo_e_invalido_como_celular(self):
        form = ClienteForm(
            data={'nome': 'Maria', 'celular': '(61) 3333-4444', 'email': ''}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('celular', form.errors)

    def test_celular_com_letras_e_invalido(self):
        form = ClienteForm(
            data={'nome': 'Maria', 'celular': '(61) 9999A-9999', 'email': ''}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('celular', form.errors)
