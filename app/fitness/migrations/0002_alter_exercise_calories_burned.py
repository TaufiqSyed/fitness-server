# Generated by Django 4.2.3 on 2024-12-03 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fitness', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercise',
            name='calories_burned',
            field=models.FloatField(default=200),
        ),
    ]