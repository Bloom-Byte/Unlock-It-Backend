# Generated by Django 4.1.2 on 2024-03-24 17:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0007_transaction_meta_data_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="account_number",
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
        migrations.AddField(
            model_name="customuser",
            name="acount_name",
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
        migrations.AddField(
            model_name="customuser",
            name="connected_account_id",
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
        migrations.AddField(
            model_name="customuser",
            name="wallet_balance",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
