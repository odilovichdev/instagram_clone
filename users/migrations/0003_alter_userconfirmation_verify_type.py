# Generated by Django 5.1.1 on 2024-10-06 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userconfirmation',
            name='verify_type',
            field=models.CharField(choices=[('VIA_EMAIL', 'Via email'), ('VIA_PHONE', 'Via phone')], max_length=9),
        ),
    ]
