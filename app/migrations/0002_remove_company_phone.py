# Generated by Django 5.1.1 on 2024-10-08 14:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='phone',
        ),
    ]
