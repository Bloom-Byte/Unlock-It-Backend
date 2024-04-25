import requests

from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

import stripe

from app.models import CustomUser, Story, Transaction
from app.response_examples.download_examples import DownloadResponseExamples
from app.util_classes import APIResponses, EncryptionHelper, EmailSender
from app.enum_classes import APIMessages, TransactionStatuses
from app.serializers.download_serializers import GetStoryDetailsSerializer, GetPaymentLinkSerializer


stripe.api_key = settings.STRIPE_SECRET_KEY


class GetStoryDetailsView(APIView):
    story_reference = openapi.Parameter(
        "storyReference", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True
    )

    @swagger_auto_schema(
        manual_parameters=[story_reference],
        responses=DownloadResponseExamples.STORY_DETAILS_RESPONSE,
    )
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
    @swagger_auto_schema(
        request_body=GetPaymentLinkSerializer,
        responses=DownloadResponseExamples.STORY_PAYMENT_LINK_RESPONSE,
    )
    def post(self, request):
        form = GetPaymentLinkSerializer(data=request.data)

        if form.is_valid():
            # get the story
            story: Story = form.get_story()

            if story is None:
                return APIResponses.error_response(
                    status_code=HTTP_400_BAD_REQUEST, message=APIMessages.STORY_NOT_FOUND
                )

            # check if download is still possible before generation of payment link
            if not story.can_still_download:
                return APIResponses.error_response(
                    status_code=HTTP_400_BAD_REQUEST, message=APIMessages.STORY_LINK_USAGE_EXCEEDED
                )

            # generate the actual payment link
            success, data = form.get_payment_link(story=story)

            if success:
                return APIResponses.success_response(
                    message=APIMessages.SUCCESS, status_code=HTTP_200_OK, data=data
                )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.PAYMENT_LINK_ERROR
        )


class StoryDownloadView(APIView):
    swagger_schema = None

    def get(self, request):
        token = request.query_params.get("token", None)

        if token:
            payload = EncryptionHelper.decrypt_download_payload(token=token)

            if payload:
                # replace this with transaction reference later on
                transaction_reference = payload["transaction_reference"]
                story_reference = payload["story_reference"]

                story_reference_split = story_reference.split("-")

                actual_story_reference = "-".join(story_reference_split[1:])

                story = Story.objects.filter(reference_number=actual_story_reference).first()

                # get transaction for the story based on the story, and transaction reference that will replace email later on
                transaction_object = Transaction.objects.get(
                    story=story, reference=transaction_reference
                )

                # check if the file had been downloaded before from the transaction model
                if transaction_object.file_downloaded:
                    return HttpResponseRedirect(settings.FRONTEND_DOWNLOAD_ERROR_URL)

                # Download the file from the URL
                response = requests.get(story.file.url, timeout=None)

                if response.status_code == 200:
                    # mark the file as downloaded in transaction model
                    transaction_object.file_downloaded = True
                    transaction_object.save()

                    # Build the response with the file content
                    file_data = response.content
                    response = HttpResponse(file_data, content_type="application/octet-stream")
                    response["Content-Disposition"] = f'attachment; filename="{story.file.name}"'
                    return response

                else:
                    # redirect to an error page on the frontend
                    return HttpResponseRedirect(settings.FRONTEND_DOWNLOAD_ERROR_URL)

            # redirect to an error page on the frontend
            return HttpResponseRedirect(settings.FRONTEND_DOWNLOAD_ERROR_URL)

        # redirect to an error page on the frontend
        return HttpResponseRedirect(settings.FRONTEND_DOWNLOAD_ERROR_URL)


class StripeWebhookView(APIView):
    swagger_schema = None

    def post(self, request):
        event = request.data

        # print(event)

        # # TODO handle payout webhook
        # if event["data"]["object"]["object"] == "payout":
        #     pass

        # # handle payment intent webhook
        # if event["data"]["object"]["object"] == "payment_intent":
        #     try:
        #         payment_id = event["data"]["object"]["id"]

        #     except Exception as error:
        #         print(f"error: {error}")

        #     response = stripe.PaymentIntent.retrieve(payment_id)

        #     print(response)

        #     client_secret = response["client_secret"]

        #     # get transaction

        #     transaction = Transaction.objects.filter(stripe_client_secret=client_secret).first()

        #     if transaction is None:
        #         # transaction not found
        #         return APIResponses.success_response(
        #             message=APIMessages.TRANSACTION_NOT_FOUND, status_code=HTTP_200_OK
        #         )

        #     # transaction completed already is status is success or failed
        #     if transaction.status == TransactionStatuses.SUCCESS:
        #         return APIResponses.success_response(
        #             message=APIMessages.TRANSACTION_COMPLETED_ALREADY, status_code=HTTP_200_OK
        #         )

        #     amount_received = response["amount_received"] / 100
        #     status = response["status"]

        #     # update the transaction details

        #     if status == "succeeded":
        #         user: CustomUser = transaction.owner

        #         # TODO do the system share calculation here

        #         transaction.withdrawable_amount = amount_received
        #         transaction.status = TransactionStatuses.SUCCESS
        #         transaction.meta_data = response
        #         transaction.save()

        #         user.wallet_balance += amount_received
        #         user.save()

        #         payload = {
        #             "transaction_reference": transaction.reference,
        #             "story_reference": f"xxxxxx-{transaction.story.reference_number}",
        #         }

        #         download_string = EncryptionHelper.encrypt_download_payload(payload=payload)

        #         download_link = settings.BACKEND_DOWNLOAD_URL + f"={download_string}"

        #         EmailSender.send_download_link_email(
        #             receiver=transaction.email, download_link=download_link
        #         )

        #         return APIResponses.success_response(
        #             message=APIMessages.TRANSACTION_SUCCESSFUL, status_code=HTTP_200_OK
        #         )

        #     if status == "processing":
        #         transaction.status = TransactionStatuses.PENDING
        #         transaction.meta_data = response
        #         transaction.save()
        #         return APIResponses.success_response(
        #             message=APIMessages.TRANSACTION_PROCESSING, status_code=HTTP_200_OK
        #         )

        #     if status == "failed":
        #         transaction.status = TransactionStatuses.FAILED
        #         transaction.meta_data = response
        #         transaction.save()
        #         return APIResponses.success_response(
        #             message=APIMessages.TRANSACTION_FAILED, status_code=HTTP_200_OK
        #         )

        #     # return status not found
        #     return APIResponses.success_response(
        #         message=APIMessages.TRANSACTION_NOT_FOUND, status_code=HTTP_200_OK
        #     )

        if event["data"]["object"]["object"] == "checkout.session":
            try:
                checkout_id = event["data"]["object"]["id"]

            except Exception as error:
                print(f"error: {error}")
                return APIResponses.success_response(
                    message="Error when fetching checkout id", status_code=HTTP_200_OK
                )

            # event_type = event["type"]

            response = stripe.checkout.Session.retrieve(checkout_id)

            reference = response["client_reference_id"]

            # get transaction

            transaction = Transaction.objects.filter(reference=reference).first()

            if transaction is None:
                # transaction not found
                return APIResponses.success_response(
                    message=APIMessages.TRANSACTION_NOT_FOUND, status_code=HTTP_200_OK
                )

            # transaction completed already is status is success or failed
            if transaction.status == TransactionStatuses.SUCCESS:
                return APIResponses.success_response(
                    message=APIMessages.TRANSACTION_COMPLETED_ALREADY, status_code=HTTP_200_OK
                )

            amount_received = response["amount_received"] / 100
            status = response["status"]

            # # update the transaction details

            if status == "paid":
                user: CustomUser = transaction.owner

                transaction.withdrawable_amount = amount_received
                transaction.status = TransactionStatuses.SUCCESS
                transaction.meta_data = response
                transaction.save()

                user.wallet_balance += amount_received
                user.save()

                payload = {
                    "transaction_reference": transaction.reference,
                    "story_reference": f"xxxxxx-{transaction.story.reference_number}",
                }

                download_string = EncryptionHelper.encrypt_download_payload(payload=payload)

                download_link = settings.BACKEND_DOWNLOAD_URL + f"={download_string}"

                EmailSender.send_download_link_email(
                    receiver=transaction.email, download_link=download_link
                )

                return APIResponses.success_response(
                    message=APIMessages.TRANSACTION_SUCCESSFUL, status_code=HTTP_200_OK
                )

            if status == "processing":
                transaction.status = TransactionStatuses.PENDING
                transaction.meta_data = response
                transaction.save()
                return APIResponses.success_response(
                    message=APIMessages.TRANSACTION_PROCESSING, status_code=HTTP_200_OK
                )

            if status == "failed":
                transaction.status = TransactionStatuses.FAILED
                transaction.meta_data = response
                transaction.save()
                return APIResponses.success_response(
                    message=APIMessages.TRANSACTION_FAILED, status_code=HTTP_200_OK
                )

            # return status not found
            return APIResponses.success_response(
                message=APIMessages.TRANSACTION_STATUS_NOT_CAPTURED, status_code=HTTP_200_OK
            )
