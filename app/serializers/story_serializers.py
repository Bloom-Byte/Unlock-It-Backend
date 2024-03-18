from django.conf import settings

from rest_framework import serializers


from app.models import CustomUser, Story, models
from app.util_classes import MyPagination, CodeGenerator


########################################### Output serializers ###################################


class StoryBriefDataSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="owner.username")

    class Meta:
        model = Story
        fields = ["id", "title", "price", "author", "file_type", "reference_number", "created_at"]

    def to_representation(self, instance: Story):
        data = super().to_representation(instance)

        data["shareable_link"] = (
            settings.FRONT_END_SHARE_STORY_URL + f"xxxxxx-{instance.reference_number}"
        )

        return data


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
            story.file.delete()
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

        file = data["file"]

        file_size_bytes = file.size
        file_size_mb = (file_size_bytes / 1024) / 1024

        if file_size_mb > settings.FILE_UPLOAD_MAX_SIZE_MB:
            raise serializers.ValidationError(
                {"file": f"Maximum file size of {settings.FILE_UPLOAD_MAX_SIZE_MB} MB exceeded"}
            )

        return data

    def create_story(self, user: CustomUser):
        new_story = Story()
        new_story.owner = user
        new_story.title = self.validated_data["title"]
        new_story.price = self.validated_data["price"]
        new_story.usage_number = self.validated_data["usage_number"]
        new_story.reference_number = CodeGenerator.generate_story_reference()

        new_story.file = self.validated_data["file"]
        new_story.file_type = self.validated_data["file"].name.split(".")[-1].upper()

        new_story.save()

        data = StoryBriefDataSerializer(new_story).data

        return data
