from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0003_alter_produtosmodel_quantidade'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='produtosmodel',
            name='quantidade',
        ),
    ]
