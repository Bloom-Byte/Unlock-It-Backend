from rest_framework import serializers


from app.enum_classes import TransactionStatuses, TransactionTypes
from app.models import CustomUser, Transaction
from app.util_classes import CodeGenerator, StripePaymentHelper


class WalletDataSerializer(serializers.Serializer):
    wallet_balance = serializers.DecimalField(max_digits=10, decimal_places=2)


class WalletSerializer:

    @staticmethod
    def get_wallet_details(user: CustomUser):
        """
        Get the wallet details for the specified user.

        Args:
            user (CustomUser): The user for whom the wallet details are to be retrieved.

        Returns:
            dict: A dictionary containing the wallet balance of the specified user.
        """
        return WalletDataSerializer({"wallet_balance": user.wallet_balance}).data


class WalletWithdrawalSerializer(serializers.Serializer):
    # amount = serializers.FloatField(required=False, default=0)
    account_name = serializers.CharField()
    account_number = serializers.CharField()
    bank_name = serializers.CharField()

    def process_withdrawal(self):
        """
        Process a withdrawal for the user, creating a withdrawal transaction and updating user account details if necessary.
        """

        user: CustomUser = self.context.get("user")

        account_number = self.validated_data.get("account_number", None)
        bank_name = self.validated_data.get("bank_name", None)
        account_name = self.validated_data.get("account_name", None)

        withdrawal_transaction = Transaction()
        withdrawal_transaction.owner = user
        withdrawal_transaction.email = user.email
        withdrawal_transaction.withdraw_amount = user.wallet_balance
        withdrawal_transaction.payable_amount = user.wallet_balance

        withdrawal_transaction.payment_type = TransactionTypes.WITHDRAWAL
        withdrawal_transaction.status = TransactionStatuses.PENDING
        withdrawal_transaction.reference = CodeGenerator.generate_transaction_reference()
        withdrawal_transaction.withdraw_account_number = account_number
        withdrawal_transaction.withdraw_account_name = account_name
        withdrawal_transaction.withdraw_bank_name = bank_name
        withdrawal_transaction.save()

        # create a bank account for the customer if possible
        if (
            user.account_number != account_number
            and user.bank_name != bank_name
            and user.account_name != account_name
        ):
            # new account details, create a new one

            user.account_name = account_name
            user.account_number = account_number
            user.bank_name = bank_name
            user.save()

            StripePaymentHelper.create_bank_account(
                user_id=user.id,
                account_id=user.customer_id,
                account_number=account_number,
                account_name=account_name,
            )

        # start the payout processing
        StripePaymentHelper.process_payout(
            amount=withdrawal_transaction.withdraw_amount,
            bank_account_id=user.bank_account_id,
            transaction_id=withdrawal_transaction.id,
            transaction_reference=withdrawal_transaction.reference,
        )
