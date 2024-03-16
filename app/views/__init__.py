from django.http import JsonResponse

from rest_framework.status import HTTP_404_NOT_FOUND

from app.enum_classes import APIMessages


def handler404(request, exception):
    return JsonResponse(
        {
            "message": APIMessages.NOT_FOUND,
        },
        status=HTTP_404_NOT_FOUND,
    )
