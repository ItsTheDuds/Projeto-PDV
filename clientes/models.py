from django.db import models


class Cliente(models.Model):
    nome = models.CharField(max_length=120)
    celular = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome
