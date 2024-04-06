import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser


from app.enum_classes import (
    AccountStatuses,
    OTPChannels,
    OTPPurposes,
    OTPStatuses,
    TransactionStatuses,
    TransactionTypes,
)


class BaseModelClass(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, default=uuid.uuid4, editable=False, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_edited_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class CustomUser(AbstractUser, BaseModelClass):
    USERNAME_FIELD: str = "email"
    REQUIRED_FIELDS = ["username"]

    # overriding first_name and last_name field so as to make it optional
    first_name = models.CharField(max_length=1024, null=True, blank=True)
    last_name = models.CharField(max_length=1024, null=True, blank=True)

    # login details
    username = models.CharField(max_length=64, null=False, blank=False, unique=True)
    email = models.EmailField(max_length=1024, null=True, blank=True, unique=True, db_index=True)
    password = models.CharField(max_length=2048, null=False, blank=False, editable=False)
    name = models.CharField(max_length=2048, null=True, blank=True)
    account_status = models.CharField(
        max_length=1024, blank=True, null=True, choices=AccountStatuses.choices
    )

    login_attempts = models.PositiveIntegerField(default=0)

    profile_picture = models.TextField(null=True, blank=True)

    referral_code = models.CharField(max_length=1024, null=True, blank=True)
    referred_users = models.IntegerField(default=0)

    google_auth_token = models.TextField(null=True, blank=True)
    facebook_auth_token = models.TextField(null=True, blank=True)
    facebook_user_id = models.CharField(max_length=1024, null=True, blank=True)
    firebase_access_token = models.CharField(max_length=2048, null=True, blank=True)

    # stripe details
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    customer_id = models.CharField(max_length=2048, null=True, blank=True)
    account_number = models.CharField(max_length=2048, null=True, blank=True)
    account_name = models.CharField(max_length=2048, null=True, blank=True)
    bank_name = models.CharField(max_length=2048, null=True, blank=True)
    bank_account_id = models.CharField(max_length=2048, null=True, blank=True)

    def __str__(self):
        return str(self.username)

    def get_available_balance(self):
        """
        Retrieve the available balance by calculating the total amount of successful payment transactions
        and deducting the total amount of successful withdrawal transactions.
        """
        debit_transactions = (
            self.transactions.filter(payment_type=TransactionTypes.WITHDRAWAL)
            .exclude(status=TransactionStatuses.FAILED)
            .aggregate(total_amount=models.Sum("amount"))
        )

        print(debit_transactions)

        credit_transactions = (
            self.transactions.filter(payment_type=TransactionTypes.PAYMENT)
            .filter(status=TransactionStatuses.SUCCESS)
            .aggregate(total_amount=models.Sum("amount"))
        )

        print(credit_transactions)


class OTP(BaseModelClass):
    otp = models.CharField(max_length=20, null=False, blank=False)
    purpose = models.CharField(max_length=100, null=False, blank=False, choices=OTPPurposes.choices)
    status = models.CharField(max_length=20, null=False, blank=False, choices=OTPStatuses.choices)
    channel = models.CharField(max_length=20, null=False, blank=False, choices=OTPChannels.choices)
    recipient = models.CharField(max_length=1024, null=False, blank=False)
    expire_at = models.DateTimeField(null=True, blank=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return str(self.purpose)


class Story(BaseModelClass):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="my_stories")

    file = models.FileField(upload_to="story_uploads/", null=True, blank=True)

    title = models.CharField(max_length=1024, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    usage_number = models.PositiveIntegerField(default=0)
    used_number = models.PositiveIntegerField(default=0)
    file_type = models.CharField(max_length=20, null=True, blank=True)
    reference_number = models.CharField(max_length=1024, null=True, blank=True)

    @property
    def can_still_download(self):
        """
        A property that checks if the user can still download based on their story transactions and usage number.
        """
        story_transactions: int = self.story_transactions.filter(
            status=TransactionStatuses.SUCCESS
        ).count()

        if story_transactions >= self.usage_number:
            return False

        return True


class Transaction(BaseModelClass):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="transactions")
    story = models.ForeignKey(
        Story, on_delete=models.SET_NULL, null=True, blank=True, related_name="story_transactions"
    )

    email = models.CharField(max_length=1024)

    # this field will hold the amount that a customer will pay into the system
    payable_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # this field will hold the amount the the user can take out from each transaction
    withdrawable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    payment_type = models.CharField(max_length=50, choices=TransactionTypes.choices)
    status = models.CharField(max_length=50, choices=TransactionStatuses.choices)

    stripe_client_secret = models.CharField(max_length=2048, null=True, blank=True)

    meta_data = models.JSONField(default=dict)

    reference = models.CharField(max_length=1024)

    provider_reference = models.CharField(max_length=1024, null=True, blank=True)

    file_downloaded = models.BooleanField(default=False)

    # withdrawal details
    withdraw_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    withdraw_account_number = models.CharField(max_length=1024, null=True, blank=True)
    withdraw_account_name = models.CharField(max_length=1024, null=True, blank=True)
    withdraw_bank_name = models.CharField(max_length=1024, null=True, blank=True)


class Referral(BaseModelClass):
    referred_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="referred_by_me"
    )
    referred_user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="referred_me"
    )
