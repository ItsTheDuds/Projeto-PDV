from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

from vendas.models import Venda


class ConfiguracaoFiado(models.Model):
    senha_hash = models.CharField(max_length=128, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração do fiado'
        verbose_name_plural = 'Configuração do fiado'

    @classmethod
    def carregar(cls):
        configuracao, _ = cls.objects.get_or_create(pk=1)
        return configuracao

    @property
    def senha_configurada(self):
        return bool(self.senha_hash)

    def definir_senha(self, senha):
        self.senha_hash = make_password(senha)
        self.save(update_fields=['senha_hash', 'atualizado_em'])

    def conferir_senha(self, senha):
        return bool(self.senha_hash) and check_password(senha, self.senha_hash)


class Fiado(models.Model):
    venda = models.OneToOneField(Venda, on_delete=models.CASCADE, related_name='fiado')
    pago = models.BooleanField(default=False, db_index=True)
    pago_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['pago', '-venda__criada_em']

    def marcar_como_pago(self):
        if not self.pago:
            self.pago = True
            self.pago_em = timezone.now()
            self.save(update_fields=['pago', 'pago_em'])

    def __str__(self):
        status = 'Pago' if self.pago else 'Em aberto'
        return f'Fiado da venda #{self.venda_id} - {status}'
