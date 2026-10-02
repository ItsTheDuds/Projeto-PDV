from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0002_alter_produtosmodel_descricao'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produtosmodel',
            name='quantidade',
            field=models.IntegerField(default=999999),
        ),
    ]
