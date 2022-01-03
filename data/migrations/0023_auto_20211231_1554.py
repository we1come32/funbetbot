# Generated by Django 3.2.9 on 2021-12-31 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0022_auto_20211231_1113'),
    ]

    operations = [
        migrations.AddField(
            model_name='express',
            name='canceled',
            field=models.BooleanField(default=False, verbose_name='Отменено'),
        ),
        migrations.AddField(
            model_name='express',
            name='money',
            field=models.IntegerField(default=100, verbose_name='Сумма'),
        ),
        migrations.AddField(
            model_name='express',
            name='winner',
            field=models.BooleanField(default=False, verbose_name='Выиграно'),
        ),
        migrations.AlterField(
            model_name='express',
            name='payed',
            field=models.BooleanField(default=False, verbose_name='Оплачено'),
        ),
    ]