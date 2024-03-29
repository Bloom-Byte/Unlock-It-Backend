from rest_framework import serializers

from app.models import Story, Transaction, TransactionStatuses, TransactionTypes
from app.util_classes import CodeGenerator, StripePaymentHelper
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

    def get_payment_link(self, story: Story):

        new_transaction = Transaction()
        new_transaction.story = story
        new_transaction.owner = story.owner
        new_transaction.email = self.validated_data["email"]
        new_transaction.payable_amount = story.price
        new_transaction.payment_type = TransactionTypes.PAYMENT
        new_transaction.status = TransactionStatuses.PENDING
        new_transaction.reference = CodeGenerator.generate_transaction_reference()
        new_transaction.save()

        data = {
            "amount": int(story.price) * 100,
            "currency": "brl",
            "automatic_payment_methods": {"enabled": True},
            # "confirm": True,
            "description": f"Payment for {story.title}",
            "receipt_email": self.validated_data["email"],
            # "return_url": settings.FRONTEND_STRIPE_RETURN_URL,
            "metadata": {"transaction_reference": new_transaction.reference},
            # "payment_method_types": ["pix"],
        }

        client_secret = StripePaymentHelper.generate_payment_link(data=data)

        if client_secret[0]:
            new_transaction.stripe_client_secret = client_secret[0]["client_secret"]
            new_transaction.save()

        return client_secret
