from rest_framework import serializers


from app.models import CustomUser, Story, models
from app.util_classes import MyPagination, CodeGenerator


########################################### Output serializers ###################################


class StoryBriefDataSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="owner.username")

    class Meta:
        model = Story
        fields = ["id", "title", "price", "author", "file_type", "reference_number", "created_at"]


class StoryFullDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = []


class StorySerializer:
    @staticmethod
    def get_all_stories(user: CustomUser, request):
        search = request.query_params.get("search", None)

        stories = Story.objects.filter(owner=user)

        if search:
            stories = stories.filter(
                models.Q(title__icontains=search) | models.Q(reference_number__icontains=search)
            )

        paginate_data, result, page_error = MyPagination.get_paginated_response(
            queryset=stories, request=request
        )

        if page_error:
            return False, None, None

        data = StoryBriefDataSerializer(result, many=True).data

        return True, data, paginate_data

    @staticmethod
    def get_single_story(user: CustomUser, story_id: str, return_data: bool = True):
        story = Story.objects.filter(id=story_id, owner=user).first()

        if story:
            if return_data:
                data = StoryBriefDataSerializer(story).data
                return data

            return story

        return None

    @staticmethod
    def delete_story(story: Story):
        try:
            # TODO delete the file from s3 here
            story.delete()
            return True

        except Exception as error:
            print(f"Error when deleting story: {error}")
            return False


################################# Input Serializers ###################33


class CreateStorySerializer(serializers.Serializer):
    title = serializers.CharField()
    file = serializers.FileField()
    price = serializers.FloatField()
    usage_number = serializers.IntegerField(min_value=1, max_value=100)

    def validate(self, attrs):
        data = super().validate(attrs)

        _ = data["file"]

        # TODO validate the file size

        return data

    def create_story(self, user: CustomUser):
        new_story = Story()
        new_story.owner = user
        new_story.title = self.validated_data["title"]
        new_story.price = self.validated_data["price"]
        new_story.usage_number = self.validated_data["usage_number"]
        new_story.reference_number = CodeGenerator.generate_story_reference()

        # TODO add link, file type

        new_story.save()

        data = StoryBriefDataSerializer(new_story).data

        return data
