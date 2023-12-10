# Generated by Django 4.2.3 on 2023-08-21 09:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0024_remove_car_plug_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="car",
            name="plug_type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="myapp.charger",
            ),
        ),
    ]
