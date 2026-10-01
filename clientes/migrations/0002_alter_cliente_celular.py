# Generated manually for celular normalization and validation.

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='celular',
            field=models.CharField(
                db_index=True,
                max_length=11,
                validators=[
                    django.core.validators.RegexValidator(
                        message='Informe um celular válido com DDD, por exemplo: (61) 99999-9999.',
                        regex='^[1-9][0-9]9[0-9]{8}$',
                    )
                ],
            ),
        ),
    ]
