# Generated by Django 3.2.9 on 2021-12-02 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0020_settings_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='tguser',
            name='rating',
            field=models.BigIntegerField(default=1000, verbose_name='Рейтинг'),
        ),
    ]
