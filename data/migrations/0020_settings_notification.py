# Generated by Django 3.2.9 on 2021-12-02 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0019_settings_news'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='notification',
            field=models.BooleanField(default=True, verbose_name='Оповещения'),
        ),
    ]
