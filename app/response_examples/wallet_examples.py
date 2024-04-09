from drf_yasg import openapi


class WalletResponseExamples:
    """This class holds the response examples for the wallet endpoints"""

    GET_WALLET_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Operation completed successfully",
                    "data": {
                        "available": 0,
                        "pending": 800,
                    },
                }
            },
        )
    }
