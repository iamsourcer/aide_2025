# Generated by Django 5.1.1 on 2024-10-08 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_remove_company_phone'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='company',
            options={'verbose_name_plural': 'Companies'},
        ),
        migrations.AlterModelOptions(
            name='companycontact',
            options={'verbose_name_plural': 'Company Contacts'},
        ),
        migrations.AlterField(
            model_name='companycontact',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='companycontact',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
