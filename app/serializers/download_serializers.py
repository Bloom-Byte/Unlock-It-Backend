from rest_framework import serializers

from app.models import Story, Transaction, TransactionStatuses, TransactionTypes
from app.util_classes import CodeGenerator, StripePaymentHelper
from app.serializers.story_serializers import StoryBriefDataSerializer


class GetStoryDetailsSerializer:

    @staticmethod
    def validate_story_reference(story_reference: str) -> Story | None:
        """
        A function to validate the story reference provided as input.

        Parameters:
            story_reference (str): The story reference to be validated.

        Returns:
            Story | None: The validated story if found, else None.
        """

        story_reference_split = story_reference.split("-")

        if len(story_reference_split) != 3:
            return None

        actual_story_reference = "-".join(story_reference_split[1:])

        story = Story.objects.filter(reference_number=actual_story_reference).first()

        if story is None:
            return None

        return story

    @staticmethod
    def get_story_details(story) -> dict:
        """
        Returns a dictionary containing the story details after removing the "shareable_link" field.

        Parameters:
            story (Story): The story object from which to extract the details.

        Returns:
            dict: A dictionary containing the story details.
        """

        data = StoryBriefDataSerializer(story).data
        data.pop("shareable_link")

        return data


class GetPaymentLinkSerializer(serializers.Serializer):
    """Serializer class for getting the payment link"""

    story_id = serializers.UUIDField()
    email = serializers.EmailField()

    def get_story(self) -> Story | None:
        """
        Retrieves the story object based on the provided story ID.

        Returns:
            Story: The story object if found, or None if not found.
        """

        story_id = self.validated_data["story_id"]

        story = Story.objects.filter(id=story_id).first()

        if story is None:
            return None

        return story

    def get_payment_link(self, story: Story):
        """
        Generates a payment link for a given story and saves a new transaction.

        Args:
            story (Story): The story for which the payment link is generated.

        Returns:
            tuple: A tuple containing the client secret of the generated payment link.
                   The first element of the tuple is a dictionary with the following keys:
                       - client_secret (str): The client secret of the payment link.

                   If an error occurs during the generation of the payment link, an empty tuple is returned.
        """

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
