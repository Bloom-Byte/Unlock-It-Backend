from drf_yasg import openapi


class TransactionResponseExamples:

    GET_ALL_TRANSACTIONS = {
        "200": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Operation completed successfully",
                    "data": [
                        {
                            "id": "1ef8dd36-bae4-4296-b650-b6a60ab54019",
                            "amount": "400.00",
                            "paymentType": "Payment",
                            "status": "Success",
                            "createdAt": "2024-03-25T11:19:50.426316Z",
                        },
                        {
                            "id": "1f9f8ca6-4b13-45a4-ae23-5fccec344353",
                            "amount": "400.00",
                            "paymentType": "Withdrawal",
                            "status": "Failed",
                            "createdAt": "2024-03-25T07:08:09.317638Z",
                        },
                        {
                            "id": "8712e8a3-03d0-4c2a-a200-735add9f23b9",
                            "amount": "400.00",
                            "paymentType": "Payment",
                            "status": "Success",
                            "createdAt": "2024-03-24T20:54:38.825740Z",
                        },
                    ],
                    "pagination": {
                        "itemsCount": 6,
                        "currentPage": 1,
                        "numberOfPages": 1,
                        "nextPage": None,
                        "previousPage": None,
                    },
                }
            },
        )
    }
