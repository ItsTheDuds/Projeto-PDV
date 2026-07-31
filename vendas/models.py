from django.db import models
from produtos.models import produtosModel

class Venda(models.Model):
    produto = models.ForeignKey(produtosModel, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    data_venda = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Venda de {self.quantidade}x {self.produto.nome} em {self.data_venda}"

