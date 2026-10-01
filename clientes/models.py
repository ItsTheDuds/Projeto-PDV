from django.core.validators import RegexValidator
from django.db import models


celular_validator = RegexValidator(
    regex=r'^[1-9][0-9]9[0-9]{8}$',
    message='Informe um celular válido com DDD, por exemplo: (61) 99999-9999.',
)


class Cliente(models.Model):
    nome = models.CharField(max_length=120)
    celular = models.CharField(
        max_length=11,
        db_index=True,
        validators=[celular_validator],
    )
    email = models.EmailField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    @property
    def celular_formatado(self):
        if len(self.celular) == 11 and self.celular.isdigit():
            return (
                f'({self.celular[:2]}) '
                f'{self.celular[2:7]}-{self.celular[7:]}'
            )
        return self.celular

    def __str__(self):
        return self.nome
