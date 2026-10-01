from decimal import Decimal

from django.db import models

from clientes.models import Cliente
from produtos.models import produtosModel


class Venda(models.Model):
    DINHEIRO = 'DINHEIRO'
    PIX = 'PIX'
    CARTAO = 'CARTAO'
    FIADO = 'FIADO'

    FORMAS_PAGAMENTO = [
        (FIADO, 'Fiado'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='vendas',
        null=True,
        blank=True,
    )
    forma_pagamento = models.CharField(max_length=20, choices=FORMAS_PAGAMENTO)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criada_em']

    def __str__(self):
        return f'Venda #{self.pk} - R$ {self.total}'


class ItemVenda(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(produtosModel, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f'{self.quantidade}x {self.produto.nome}'
