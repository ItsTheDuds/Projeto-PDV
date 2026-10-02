from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produtosmodel',
            name='descricao',
            field=models.TextField(blank=True),
        ),
    ]
