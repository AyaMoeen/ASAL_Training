# Generated by Django 5.1 on 2024-11-04 08:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contract', '0006_rename_paid_job_paid_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contract',
            options={'permissions': [('can_view_contract', 'Can view the contract')]},
        ),
    ]
