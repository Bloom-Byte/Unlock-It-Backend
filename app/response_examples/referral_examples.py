from drf_yasg import openapi


class ReferralResponseExamples:
    """This class holds the example response for the referral endpoints"""

    GET_REFERRAL_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Operation completed successfully",
                    "data": {
                        "referralCode": "XD19B0R8",
                        "referredUsers": 0,
                    },
                }
            },
        )
    }
