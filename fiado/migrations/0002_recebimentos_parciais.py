from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def preencher_valor_pago(apps, schema_editor):
    Fiado = apps.get_model('fiado', 'Fiado')
    for fiado in Fiado.objects.select_related('venda').all():
        if fiado.pago:
            fiado.valor_pago = fiado.venda.total
            fiado.save(update_fields=['valor_pago'])


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0002_alter_cliente_celular'),
        ('fiado', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='fiado',
            name='valor_pago',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
        migrations.CreateModel(
            name='RecebimentoFiado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recebimentos_fiado', to='clientes.cliente')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recebimentos_fiado', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-criado_em'],
            },
        ),
        migrations.CreateModel(
            name='AplicacaoRecebimento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor', models.DecimalField(decimal_places=2, max_digits=12)),
                ('fiado', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='aplicacoes_recebimento', to='fiado.fiado')),
                ('recebimento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aplicacoes', to='fiado.recebimentofiado')),
            ],
            options={
                'ordering': ['fiado__venda__criada_em', 'fiado_id'],
            },
        ),
        migrations.RunPython(preencher_valor_pago, migrations.RunPython.noop),
    ]
