# Generated by Django 4.1.2 on 2024-03-19 18:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0006_rename_amount_transaction_payable_amount_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="meta_data",
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name="transaction",
            name="stripe_client_secret",
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
    ]