# Generated by Django 5.1 on 2024-11-03 20:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contract', '0005_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='job',
            old_name='Paid',
            new_name='paid',
        ),
        migrations.RenameField(
            model_name='job',
            old_name='Payment_Date',
            new_name='payment_date',
        ),
    ]