from django.conf import settings

from rest_framework import serializers

from app.models import Story, Transaction, TransactionStatuses, TransactionTypes
from app.util_classes import CodeGenerator, StripeHelper
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
        Generate a payment link for a given story.

        Parameters:
        - story: Story object

        Returns:
        - data: dict containing the generated checkout session link
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

        # construct the line items data
        line_items = [
            {
                "price_data": {
                    "currency": "brl",
                    "product_data": {
                        "name": story.title,
                        "description": f"Payment for {story.title}",
                    },
                    "unit_amount": int(story.price) * 100,
                },
                "quantity": 1,
            }
        ]

        # calculate the application fee
        application_fee_amount = (
            int(int(story.price) * settings.STRIPE_APPLICATION_FEE_PERCENTAGE) * 100
        )

        # get connected account id
        connect_account_id = story.owner.customer_id

        data = StripeHelper.generate_checkout_session_link(
            line_items=line_items,
            connected_account_id=connect_account_id,
            application_fee_amount=application_fee_amount,
        )

        # data = {
        #     "amount": int(story.price) * 100,
        #     "currency": "brl",
        #     "automatic_payment_methods": {"enabled": True},
        #     # "confirm": True,
        #     "description": f"Payment for {story.title}",
        #     "receipt_email": self.validated_data["email"],
        #     # "return_url": settings.FRONTEND_STRIPE_RETURN_URL,
        #     "metadata": {"transaction_reference": new_transaction.reference},
        #     # "payment_method_types": ["pix"],
        # }

        # client_secret = StripeHelper.generate_payment_link(data=data)

        return data
