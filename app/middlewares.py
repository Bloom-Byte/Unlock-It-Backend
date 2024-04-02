import logging

import traceback

from django.http import JsonResponse


from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR


logger = logging.getLogger("server_error")


class Log500ErrorsMiddleware:
    def __init__(self, get_response):
        """
        Initialize the class with the given get_response function.

        Parameters:
            get_response (function): The function to be used for getting the response.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Call the function with the given request and return the response.

        Parameters:
            request: the request to be processed

        Returns:
            the response generated from processing the request
        """
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        A method to process exceptions that occur during request handling.

        Parameters:
            self: the instance of the class
            request: the request object that triggered the exception
            exception: the exception that was raised

        Returns:
            JsonResponse: a JSON response indicating the occurrence of an error with a specific message and status code
        """
        logger.error(
            "\n".join(
                traceback.format_exception(type(exception), exception, exception.__traceback__)
            )
        )

        return JsonResponse(
            {
                "success": False,
                "message": "An error has occurred but don't worry. We will worry about it",
            },
            status=HTTP_500_INTERNAL_SERVER_ERROR,
        )
