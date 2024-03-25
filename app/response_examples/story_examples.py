from drf_yasg import openapi


class StoryResponseExamples:

    GET_ALL_STORIES = {
        "200": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Operation completed successfully",
                    "data": [
                        {
                            "id": "3851e277-6b0f-41b0-b39a-b143b36d7105",
                            "title": "A cartoon picture",
                            "price": "400.00",
                            "author": "String",
                            "fileType": "JPG",
                            "referenceNumber": "RN-10y26OHO",
                            "createdAt": "2024-03-24T20:52:30.877917Z",
                            "shareableLink": "http://localhost:8000/xxxxxx-RN-10y26OHO",
                        }
                    ],
                    "pagination": {
                        "itemsCount": 1,
                        "currentPage": 1,
                        "numberOfPages": 1,
                        "nextPage": None,
                        "previousPage": None,
                    },
                }
            },
        )
    }

    GET_SINGLE_STORY = {
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
                        "shareableLink": "http://localhost:8000/xxxxxx-RN-10y26OHO",
                    },
                }
            },
        ),
        "404": openapi.Response(
            description="Failure", examples={"application/json": {"message": "Story not found"}}
        ),
    }

    DELETE_STORY = {
        "200": openapi.Response(
            description="Success",
            examples={"application/json": {"message": "Story deleted successfully"}},
        ),
        "404": openapi.Response(
            description="Failure",
            examples={"application/json": {"message": "Story not found"}},
        ),
    }

    CREATE_STORY = {
        "200": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Story created successfully",
                    "data": {
                        "id": "0f3c0229-565f-4bcc-a3f1-4f4665f27df8",
                        "title": "Another story to test response",
                        "price": "300.00",
                        "author": "String",
                        "fileType": "JPEG",
                        "referenceNumber": "RN-l6733Vai",
                        "createdAt": "2024-03-25T11:33:55.422336Z",
                        "shareableLink": "http://localhost:8000/xxxxxx-RN-l6733Vai",
                    },
                }
            },
        ),
    }
