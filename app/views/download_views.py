import requests

from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.views import APIView


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from app.models import Story
from app.util_classes import APIResponses, EncryptionHelper
from app.enum_classes import APIMessages
from app.serializers.download_serializers import GetStoryDetailsSerializer, GetPaymentLinkSerializer


class GetStoryDetailsView(APIView):

    story_reference = openapi.Parameter(
        "storyReference", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True
    )

    @swagger_auto_schema(manual_parameters=[story_reference])
    def get(self, request):

        story_reference = request.query_params.get("story_reference", None)

        story = GetStoryDetailsSerializer.validate_story_reference(story_reference=story_reference)

        if story is None:

            return APIResponses.error_response(
                status_code=HTTP_404_NOT_FOUND,
                message=APIMessages.STORY_DETAILS_ERROR,
            )

        data = GetStoryDetailsSerializer.get_story_details(story=story)

        return APIResponses.success_response(
            message=APIMessages.SUCCESS, status_code=HTTP_200_OK, data=data
        )


class GetPaymentLinkView(APIView):

    @swagger_auto_schema(request_body=GetPaymentLinkSerializer)
    def post(self, request):

        form = GetPaymentLinkSerializer(data=request.data)

        if form.is_valid():

            # get the story
            story = form.get_story()

            if story is None:
                return APIResponses.error_response(
                    status_code=HTTP_400_BAD_REQUEST, message=APIMessages.STORY_NOT_FOUND
                )

            # check if download is still possible before generation of payment link
            can_download = form.check_payment_generation(story=story)

            if can_download is False:
                return APIResponses.error_response(
                    status_code=HTTP_400_BAD_REQUEST, message=APIMessages.STORY_LINK_USAGE_EXCEEDED
                )

            # generate the actual payment link
            data = form.get_payment_link(story=story)

            return APIResponses.success_response(
                message=APIMessages.SUCCESS, status_code=HTTP_200_OK, data=data
            )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.PAYMENT_LINK_ERROR
        )


class StoryDownloadView(APIView):

    def get(self, request):

        token = request.query_params.get("token", None)

        if token:

            payload = EncryptionHelper.decrypt_download_payload(token=token)

            if payload:

                # TODO replace this with transaction reference later on
                _ = payload["transaction_reference"]
                story_reference = payload["story_reference"]

                story_reference_split = story_reference.split("-")

                actual_story_reference = "-".join(story_reference_split[1:])

                story = Story.objects.filter(reference_number=actual_story_reference).first()

                # TODO get transaction for the story based on the story, and transaction reference that will replace email later on

                # TODO check if the file had been downloaded before from the transaction model

                # Download the file from the URL
                response = requests.get(story.file.url, timeout=None)

                if response.status_code == 200:
                    # Build the response with the file content
                    file_data = response.content
                    response = HttpResponse(file_data, content_type="application/octet-stream")
                    response["Content-Disposition"] = f'attachment; filename="{story.file.name}"'
                    return response

                else:
                    # TODO redirect to an error page on the frontend
                    return HttpResponseRedirect(settings.FRONTEND_DOWNLOAD_ERROR_URL)

            # TODO redirect to an error page on the frontend
            return HttpResponseRedirect(settings.FRONTEND_DOWNLOAD_ERROR_URL)

        # TODO redirect to an error page on the frontend
        return HttpResponseRedirect(settings.FRONTEND_DOWNLOAD_ERROR_URL)
