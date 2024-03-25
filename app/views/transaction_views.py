from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


from app.util_classes import APIResponses
from app.enum_classes import APIMessages
from app.serializers.transaction_serializers import (
    serializers,
    TransactionSerializer,
    TransactionDataSerializer,
)


class TransactionView(APIView):
    permission_classes = [IsAuthenticated]

    page = openapi.Parameter(
        "page",
        openapi.IN_QUERY,
        type=openapi.TYPE_INTEGER,
        required=False,
        default=1,
    )
    page_size = openapi.Parameter(
        "pageSize",
        openapi.IN_QUERY,
        type=openapi.TYPE_INTEGER,
        required=False,
        default=25,
    )

    @swagger_auto_schema(
        responses={200: serializers.ListSerializer(child=TransactionDataSerializer())},
        manual_parameters=[page, page_size],
    )
    def get(self, request):
        success, data, paginate_data = TransactionSerializer.get_user_transactions(request=request)

        if success:
            return APIResponses.success_response(
                message=APIMessages.SUCCESS,
                status_code=HTTP_200_OK,
                data=data,
                paginate_data=paginate_data,
            )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.PAGINATION_PAGE_ERROR
        )
