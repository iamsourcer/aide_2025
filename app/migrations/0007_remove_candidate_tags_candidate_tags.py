# Generated by Django 5.1.1 on 2024-10-11 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_alter_candidate_location'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='candidate',
            name='tags',
        ),
        migrations.AddField(
            model_name='candidate',
            name='tags',
            field=models.ManyToManyField(blank=True, null=True, related_name='candidates', to='app.tag'),
        ),
    ]
