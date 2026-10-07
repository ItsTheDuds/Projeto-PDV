from django.db import migrations


class Migration(migrations.Migration):
    """Concilia os dois históricos equivalentes sem alterar dados."""

    dependencies = [
        ('vendas', '0002_alter_venda_forma_pagamento_alter_venda_total'),
        ('vendas', '0003_alter_venda_forma_pagamento'),
    ]

    operations = []
