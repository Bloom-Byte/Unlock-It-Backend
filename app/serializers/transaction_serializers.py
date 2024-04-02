from typing import Tuple, Dict, List
from rest_framework import serializers


from app.models import CustomUser, Transaction
from app.util_classes import MyPagination


class TransactionDataSerializer(serializers.ModelSerializer):
    """Serializer for transaction data"""

    amount = serializers.DecimalField(source="payable_amount", max_digits=10, decimal_places=2)

    class Meta:
        model = Transaction
        fields = ["id", "amount", "payment_type", "status", "created_at"]


class TransactionSerializer:

    @staticmethod
    def get_user_transactions(request) -> Tuple[bool, List[Dict], Dict]:
        """
        Get the transactions of a user.

        Args:
            request (Request): The request object containing the user information.

        Returns:
            Tuple[bool, List[Dict], Dict]: A tuple containing a boolean indicating if the request was successful,
            a list of dictionaries representing the transaction data, and a dictionary containing pagination data.
        """

        user: CustomUser = request.user

        # TODO add filter later

        transactions = Transaction.objects.filter(owner=user)

        paginate_data, result, page_error = MyPagination.get_paginated_response(
            queryset=transactions, request=request
        )

        if page_error:
            return False, None, None

        data = TransactionDataSerializer(result, many=True).data

        return True, data, paginate_data
