from decimal import Decimal

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

from clientes.models import Cliente
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
    valor_pago = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    pago_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['pago', '-venda__criada_em']

    @property
    def saldo_devedor(self):
        saldo = self.venda.total - self.valor_pago
        return max(saldo, Decimal('0.00'))

    def registrar_pagamento(self, valor):
        valor = Decimal(valor).quantize(Decimal('0.01'))

        if valor <= 0:
            raise ValueError('O valor do pagamento deve ser maior que zero.')

        saldo = self.saldo_devedor
        if valor > saldo:
            raise ValueError('O pagamento não pode ser maior que o saldo da compra.')

        self.valor_pago = (self.valor_pago + valor).quantize(Decimal('0.01'))

        if self.valor_pago >= self.venda.total:
            self.valor_pago = self.venda.total
            self.pago = True
            self.pago_em = timezone.now()
            self.save(update_fields=['valor_pago', 'pago', 'pago_em'])
        else:
            self.pago = False
            self.pago_em = None
            self.save(update_fields=['valor_pago', 'pago', 'pago_em'])

    def marcar_como_pago(self):
        if not self.pago:
            self.valor_pago = self.venda.total
            self.pago = True
            self.pago_em = timezone.now()
            self.save(update_fields=['valor_pago', 'pago', 'pago_em'])

    def __str__(self):
        status = 'Pago' if self.pago else 'Em aberto'
        return f'Fiado da venda #{self.venda_id} - {status}'


class RecebimentoFiado(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='recebimentos_fiado',
    )
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recebimentos_fiado',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'Recebimento #{self.pk} - {self.cliente} - R$ {self.valor_total}'


class AplicacaoRecebimento(models.Model):
    recebimento = models.ForeignKey(
        RecebimentoFiado,
        on_delete=models.CASCADE,
        related_name='aplicacoes',
    )
    fiado = models.ForeignKey(
        Fiado,
        on_delete=models.PROTECT,
        related_name='aplicacoes_recebimento',
    )
    valor = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['fiado__venda__criada_em', 'fiado_id']

    def __str__(self):
        return f'R$ {self.valor} na venda #{self.fiado.venda_id}'
