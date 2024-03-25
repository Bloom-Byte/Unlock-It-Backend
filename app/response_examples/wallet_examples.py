from drf_yasg import openapi


class WalletResponseExamples:

    GET_WALLET_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Operation completed successfully",
                    "data": {"walletBalance": "400.00"},
                }
            },
        )
    }
