# Generated by Django 3.2.9 on 2021-12-02 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0018_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='news',
            field=models.BooleanField(default=True, verbose_name='Новости'),
        ),
    ]
