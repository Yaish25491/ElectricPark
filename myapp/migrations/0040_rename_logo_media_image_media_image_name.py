# Generated by Django 4.2.3 on 2023-09-23 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0039_media"),
    ]

    operations = [
        migrations.RenameField(
            model_name="media",
            old_name="logo",
            new_name="image",
        ),
        migrations.AddField(
            model_name="media",
            name="image_name",
            field=models.CharField(default="image", max_length=100),
        ),
    ]
