from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LoginTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username='operador',
            password='senha-segura-123',
        )

    def test_home_redireciona_para_login_sem_autenticacao(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{reverse('login')}?next={reverse('home')}")

    def test_login_com_credenciais_validas(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'operador', 'password': 'senha-segura-123'},
        )

        self.assertRedirects(response, reverse('home'))

    def test_usuario_autenticado_acessa_home(self):
        self.client.force_login(self.usuario)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Painel de Controle')

    def test_logout_por_post(self):
        self.client.force_login(self.usuario)

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('login'))
