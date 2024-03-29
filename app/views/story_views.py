from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


from app.util_classes import APIResponses
from app.enum_classes import APIMessages
from app.serializers.story_serializers import StorySerializer, CreateStorySerializer
from app.response_examples.story_examples import StoryResponseExamples


class StoryView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    search = openapi.Parameter(
        "search",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        required=False,
    )
    page = openapi.Parameter(
        "page", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False, default=1
    )
    page_size = openapi.Parameter(
        "pageSize", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=False, default=25
    )

    @swagger_auto_schema(
        responses=StoryResponseExamples.GET_ALL_STORIES,
        manual_parameters=[search, page, page_size],
    )
    def get(self, request):
        success, data, paginate_data = StorySerializer.get_all_stories(
            user=request.user, request=request
        )

        if success:
            return APIResponses.success_response(
                message=APIMessages.SUCCESS,
                status_code=HTTP_200_OK,
                data=data,
                paginate_data=paginate_data,
            )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.PAGINATION_PAGE_ERROR
        )

    @swagger_auto_schema(
        request_body=CreateStorySerializer,
        responses=StoryResponseExamples.CREATE_STORY,
    )
    def post(self, request):
        form = CreateStorySerializer(data=request.data)

        if form.is_valid():
            data = form.create_story(user=request.user)

            return APIResponses.success_response(
                message=APIMessages.STORY_CREATED, status_code=HTTP_201_CREATED, data=data
            )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.FORM_ERROR, errors=form.errors
        )


class SingleStoryView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses=StoryResponseExamples.GET_SINGLE_STORY,
    )
    def get(self, request, story_id):
        story_data = StorySerializer.get_single_story(
            user=request.user, story_id=story_id, return_data=True
        )

        if story_data:
            return APIResponses.success_response(
                message=APIMessages.SUCCESS, status_code=HTTP_200_OK, data=story_data
            )

        return APIResponses.error_response(
            status_code=HTTP_404_NOT_FOUND, message=APIMessages.STORY_NOT_FOUND
        )

    @swagger_auto_schema(
        responses=StoryResponseExamples.DELETE_STORY,
    )
    def delete(self, request, story_id):
        story_object = StorySerializer.get_single_story(
            user=request.user, story_id=story_id, return_data=False
        )

        if story_object:
            success = StorySerializer.delete_story(story=story_object)

            if success:
                return APIResponses.success_response(
                    message=APIMessages.STORY_DELETED, status_code=HTTP_200_OK
                )

            return APIResponses.error_response(
                status_code=HTTP_400_BAD_REQUEST, message=APIMessages.STORY_DELETION_ERROR
            )

        return APIResponses.error_response(
            status_code=HTTP_404_NOT_FOUND, message=APIMessages.STORY_NOT_FOUND
        )
