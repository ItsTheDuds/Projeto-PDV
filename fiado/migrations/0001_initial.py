from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('vendas', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracaoFiado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('senha_hash', models.CharField(blank=True, max_length=128)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuração do fiado',
                'verbose_name_plural': 'Configuração do fiado',
            },
        ),
        migrations.CreateModel(
            name='Fiado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pago', models.BooleanField(db_index=True, default=False)),
                ('pago_em', models.DateTimeField(blank=True, null=True)),
                ('venda', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='fiado', to='vendas.venda')),
            ],
            options={'ordering': ['pago', '-venda__criada_em']},
        ),
    ]
