# Generated by Django 4.1.2 on 2024-04-06 13:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0010_customuser_referred_users"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="firebase_access_token",
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
    ]