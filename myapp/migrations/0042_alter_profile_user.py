# Generated by Django 4.2.3 on 2023-10-28 15:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0041_usercars"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="myapp.user"
            ),
        ),
    ]
