from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clientes', '0001_initial'),
        ('produtos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Venda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forma_pagamento', models.CharField(choices=[('DINHEIRO', 'Dinheiro'), ('PIX', 'Pix'), ('CARTAO', 'Cartão'), ('FIADO', 'Fiado')], max_length=20)),
                ('total', models.DecimalField(decimal_places=2, default='0.00', max_digits=12)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='vendas', to='clientes.cliente')),
            ],
            options={'ordering': ['-criada_em']},
        ),
        migrations.CreateModel(
            name='ItemVenda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.PositiveIntegerField()),
                ('preco_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=12)),
                ('produto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='produtos.produtosmodel')),
                ('venda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='vendas.venda')),
            ],
        ),
    ]
