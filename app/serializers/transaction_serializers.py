from rest_framework import serializers


from app.models import CustomUser, Transaction
from app.util_classes import MyPagination


class TransactionDataSerializer(serializers.ModelSerializer):

    amount = serializers.DecimalField(source="payable_amount", max_digits=10, decimal_places=2)

    class Meta:
        model = Transaction
        fields = ["id", "amount", "payment_type", "status", "created_at"]


class TransactionSerializer:

    @staticmethod
    def get_user_transactions(request):

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
