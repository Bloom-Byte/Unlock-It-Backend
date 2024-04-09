from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


from drf_yasg.utils import swagger_auto_schema


from app.serializers.wallet_serializers import WalletSerializer
from app.util_classes import APIResponses
from app.enum_classes import APIMessages
from app.response_examples.wallet_examples import WalletResponseExamples


class WalletView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses=WalletResponseExamples.GET_WALLET_RESPONSE)
    def get(self, request):
        data = WalletSerializer.get_wallet_details(user=request.user)

        return APIResponses.success_response(
            message=APIMessages.SUCCESS, status_code=HTTP_200_OK, data=data
        )

    # TODO Add this back later on
    # @swagger_auto_schema(request_body=WalletWithdrawalSerializer)
    # def post(self, request):

    #     form = WalletWithdrawalSerializer(data=request.data, context={"user": request.user})

    #     if form.is_valid():
    #         form.process_withdrawal()

    #         return APIResponses.success_response(
    #             message=APIMessages.PAYOUT_PROCESSING_STARTED, status_code=HTTP_200_OK
    #         )

    #     return APIResponses.error_response(
    #         status_code=HTTP_400_BAD_REQUEST, message=APIMessages.FORM_ERROR, errors=form.errors
    #     )
