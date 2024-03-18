from django.conf import settings

from rest_framework import serializers

from app.models import Story
from app.util_classes import EmailSender, EncryptionHelper
from app.serializers.story_serializers import StoryBriefDataSerializer


class GetStoryDetailsSerializer:

    @staticmethod
    def validate_story_reference(story_reference: str):

        story_reference_split = story_reference.split("-")

        if len(story_reference_split) != 3:
            return None

        actual_story_reference = "-".join(story_reference_split[1:])

        story = Story.objects.filter(reference_number=actual_story_reference).first()

        if story is None:
            return None

        return story

    @staticmethod
    def get_story_details(story):

        data = StoryBriefDataSerializer(story).data
        data.pop("shareable_link")

        return data


class GetPaymentLinkSerializer(serializers.Serializer):
    story_id = serializers.UUIDField()
    email = serializers.EmailField()

    def get_story(self):
        story_id = self.validated_data["story_id"]

        story = Story.objects.filter(id=story_id).first()

        if story is None:
            return None

        return story

    def check_payment_generation(self, story: Story):

        return story.can_still_download

    def get_payment_link(self, story: Story):

        # TODO move this to webhook, and set the transaction reference instead of email
        payload = {
            "transaction_reference": "omo",
            "story_reference": f"xxxxxx-{story.reference_number}",
        }

        download_string = EncryptionHelper.encrypt_download_payload(payload=payload)

        download_link = settings.BACKEND_DOWNLOAD_URL + f"={download_string}"

        EmailSender.send_download_link_email(
            receiver=self.validated_data["email"], download_link=download_link
        )

        # payment_data = [
        #     {
        #         "quantity": 1,
        #         "price_data": {
        #             "currency": "BRL",
        #             "unit_amount_decimal": story.price,
        #             "product_data": {
        #                 "description": f"Payment for {story.title}",
        #                 "name": story.title,
        #             },
        #         },
        #     },
        # ]

        # data = {"payment_link": StripPaymentHelper.generate_payment_link(payment_data)}

        return "data"
