from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


from drf_yasg.utils import swagger_auto_schema


from app.serializers.referral_serializers import ReferralSerializer
from app.util_classes import APIResponses
from app.enum_classes import APIMessages
from app.response_examples.referral_examples import ReferralResponseExamples


class ReferralView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses=ReferralResponseExamples.GET_REFERRAL_RESPONSE)
    def get(self, request):
        data = ReferralSerializer.get_referral_details(user=request.user)

        return APIResponses.success_response(
            message=APIMessages.SUCCESS, status_code=HTTP_200_OK, data=data
        )
