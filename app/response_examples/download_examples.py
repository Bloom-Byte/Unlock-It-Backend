from drf_yasg import openapi


class DownloadResponseExamples:
    """This class holds the example response for the download endpoints"""

    STORY_DETAILS_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Operation completed successfully",
                    "data": {
                        "id": "3851e277-6b0f-41b0-b39a-b143b36d7105",
                        "title": "A cartoon picture",
                        "price": "400.00",
                        "author": "String",
                        "fileType": "JPG",
                        "referenceNumber": "RN-10y26OHO",
                        "createdAt": "2024-03-24T20:52:30.877917Z",
                    },
                }
            },
        ),
        "404": openapi.Response(
            description="Failure",
            examples={
                "application/json": {
                    "message": "Error while fetching details for the file, please check the link and try again"
                }
            },
        ),
    }

    STORY_PAYMENT_LINK_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Operation completed successfully",
                    "data": {"paymentLink": "https://checkout.stripe.com/c/pay/cs_testl"},
                }
            },
        ),
        "400": openapi.Response(
            description="Failure",
            examples={
                "application/json": {
                    "message": "Story not found",
                }
            },
        ),
    }
