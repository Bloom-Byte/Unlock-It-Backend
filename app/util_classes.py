from random import choices, shuffle
import string
import json

from datetime import timedelta

import smtplib
import ssl

from hashlib import sha256

from base64 import urlsafe_b64encode


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


from cryptography.fernet import Fernet

from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model


from rest_framework.response import Response

import stripe


from app.enum_classes import OTPStatuses
from app.models import OTP

USER_MODEL = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY


def snake_case_to_camel_case(value: str):
    splitted_string = value.split("_")

    camel_string = splitted_string.pop(0)

    for other_words in splitted_string:
        camel_string += other_words.title()

    return camel_string


class APIResponses:
    @classmethod
    def success_response(cls, message: str, status_code, data=None, paginate_data=None):
        context = {
            "message": message,
        }

        if data is not None:
            context["data"] = data

            if paginate_data:
                context["pagination"] = paginate_data

        return Response(context, status=status_code)

    @classmethod
    def error_response(cls, status_code, message, errors: dict = None):
        context = {
            "message": message,
        }

        if errors is not None:
            errors_list = []
            for key, value in errors.items():
                if isinstance(value, list):
                    value = value[0]

                key = snake_case_to_camel_case(key)

                errors_list.append({"fieldName": key, "error": value})

            context["errors"] = errors_list

        return Response(context, status=status_code)

    @classmethod
    def server_error(cls, message: str, status_code):
        context = {"message": message}

        return Response(context, status=status_code)


class CodeGenerator:
    @staticmethod
    def generate_code():
        if not settings.GENERATE_CODE:
            code = settings.DEFAULT_OTP

        else:
            code = "".join(choices(string.digits, k=6))

        return code

    @staticmethod
    def generate_transaction_reference():
        upper = choices(string.ascii_uppercase, k=7)
        digits = choices(string.digits, k=7)
        total = upper + digits

        return "".join(total)

    @staticmethod
    def generate_referral_code():
        upper = choices(string.ascii_uppercase, k=4)
        digits = choices(string.digits, k=4)
        total = upper + digits

        shuffle(total)

        return "".join(total)

    @staticmethod
    def generate_story_reference():
        upper = choices(string.ascii_letters, k=4)
        digits = choices(string.digits, k=4)
        total = upper + digits

        shuffle(total)

        return "RN-" + "".join(total)


class MyPagination:
    @classmethod
    def get_paginated_response(
        cls, request, queryset, page_size_param="page_size", page_number_param="page"
    ):
        page_number = request.query_params.get(page_number_param, 1)
        page_size = request.query_params.get(page_size_param, 25)

        paginator = Paginator(queryset, page_size)
        try:
            current_page = paginator.page(page_number)
        except Exception:
            return None, None, "Invalid page number"

        total_data = {
            "itemsCount": queryset.count(),
            "currentPage": current_page.number,
            "numberOfPages": paginator.num_pages,
            "nextPage": current_page.next_page_number() if current_page.has_next() else None,
            "previousPage": (
                current_page.previous_page_number() if current_page.has_previous() else None
            ),
        }

        return total_data, current_page.object_list, None


class EmailSender:
    @staticmethod
    def send_password_reset_email(receiver, otp):
        pass

    @staticmethod
    def send_download_link_email(receiver, download_link):
        try:
            with open("emails/payment_completed.html") as f:
                customer_template = f.read()

            customer_template = customer_template.replace("#download_link", download_link)

            # Create a multipart message and set headers
            customer_message = MIMEMultipart()
            customer_message["From"] = settings.EMAIL_HOST_USER
            customer_message["To"] = receiver
            customer_message["Subject"] = "Payment Completed!"

            # Add body to email
            customer_message.attach(MIMEText(customer_template, "html"))

            # convert to string
            customer_text = customer_message.as_string()

            # Log in to server using secure context and send email
            context = ssl.create_default_context()

            with smtplib.SMTP_SSL(
                settings.EMAIL_HOST, settings.EMAIL_PORT, context=context
            ) as server:
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.sendmail(settings.EMAIL_HOST_USER, receiver, customer_text)

        except Exception as error:
            print(f"Error sending download email: {error}")


class OTPHelper:
    @classmethod
    def throttle_otp(cls, recipient, purpose):
        """
        Method for determining wether to allow creation of another otp based on the recipient and the purpose

        Params:
            recipient: an object of the user model
            purpose: the purpose of the otp

        Returns:
            True -> if creation of another otp should be allowed
            False -> if creation of another otp should be denied
        """

        otp_object = OTP.objects.filter(purpose=purpose).filter(recipient=recipient).first()

        if otp_object is None:
            # there is no previous otp, so creation is allowed
            return True

        # there is an otp, compare the time it was created with the current time, to make sure it has passed the period

        if otp_object.created_at < timezone.now().now() + timedelta(
            minutes=settings.OTP_GENERATE_TIME_LAPSE_MINUTES
        ):
            # created_at is lower then the current time, so don't create new otp
            return False

        return True

    @classmethod
    def generate_otp(cls, purpose, channel, recipient):
        code = CodeGenerator.generate_code()

        new_otp = OTP()
        new_otp.otp = code
        new_otp.purpose = purpose
        new_otp.status = OTPStatuses.ACTIVE
        new_otp.channel = channel
        new_otp.recipient = recipient
        new_otp.expire_at = timezone.now().now() + timedelta(
            minutes=settings.OTP_EXPIRATION_MINUTES
        )

        new_otp.save()

        return code

    @classmethod
    def send_otp(cls, purpose, recipient, email=None, phone_number=None):
        # try to see if an otp for this purpose exists already
        previous_otps = (
            OTP.objects.filter(recipient=recipient)
            .filter(purpose=purpose)
            .filter(status=OTPStatuses.ACTIVE)
            # .filter(expire_at__lte=timezone.now().now())  # add this
        )

        previous_otps.update(status=OTPStatuses.INACTIVE)

        code = CodeGenerator.generate_code()

        new_otp = OTP()
        new_otp.otp = code
        new_otp.purpose = purpose
        new_otp.status = OTPStatuses.ACTIVE
        new_otp.recipient = recipient
        new_otp.expire_at = timezone.now().now() + timedelta(
            minutes=settings.OTP_EXPIRATION_MINUTES
        )

        new_otp.save()

        if not settings.DEBUG:
            # DEBUG is false

            if email:
                # send to email address
                EmailSender.send_otp_email(receiver=recipient, otp_code=code)

        return code

    @classmethod
    def verify_otp(cls, otp, purpose, recipient, mark_used=False):
        # update the otp model
        otp_object = (
            OTP.objects.filter(status=OTPStatuses.ACTIVE)
            .filter(recipient=recipient)
            .filter(purpose=purpose)
            .first()
        )

        if otp_object:
            if otp == otp_object.otp:
                if otp_object.expire_at <= timezone.now():
                    otp_object.status = OTPStatuses.EXPIRED
                    otp_object.save()
                    return False

                if mark_used:
                    otp_object.status = OTPStatuses.USED

                otp_object.verified = True
                otp_object.save()

                return True

            return False

        return False

    @classmethod
    def check_verified(cls, otp, purpose, recipient):
        # update the otp model
        otp_object = (
            OTP.objects.filter(status=OTPStatuses.ACTIVE)
            .filter(recipient=recipient)
            .filter(purpose=purpose)
            .first()
        )

        if otp_object:
            if otp == otp_object.otp:
                return otp_object.verified

            return False

        return False


class EncryptionHelper:
    @classmethod
    def ensure_32_bytes(cls, key):
        hashed_key = sha256(key).digest()
        return hashed_key[:32]

    @classmethod
    def encrypt_download_payload(cls, payload: dict):
        secret_key = settings.SECRET_KEY.encode()

        if len(secret_key) != 32:
            secret_key = cls.ensure_32_bytes(secret_key)

        fernet_key = urlsafe_b64encode(secret_key)

        # Initialize a Fernet cipher instance with the key
        cipher_suite = Fernet(fernet_key)

        # Convert the dictionary to a JSON string
        json_str = json.dumps(payload)

        # Encrypt the JSON string
        encrypted_str = cipher_suite.encrypt(json_str.encode()).decode()

        return encrypted_str

    @classmethod
    def decrypt_download_payload(cls, token: str):
        try:
            secret_key = settings.SECRET_KEY.encode()

            if len(secret_key) != 32:
                secret_key = cls.ensure_32_bytes(secret_key)

            fernet_key = urlsafe_b64encode(secret_key)

            # Initialize a Fernet cipher instance with the key
            cipher_suite = Fernet(fernet_key)

            decrypted_data = cipher_suite.decrypt(token).decode()

            # Convert the dictionary to a JSON string
            json_dict = json.loads(decrypted_data)

            return json_dict

        except Exception as error:

            return None


class StripePaymentHelper:
    @staticmethod
    def generate_payment_link(data: dict):

        try:
            payment_intent = stripe.PaymentIntent.create(**data)

        except Exception as e:
            print(f"Error when creating payment intent from stripe: {e}")
            return None, False

        data = {"client_secret": payment_intent.client_secret}

        return data, True

    @staticmethod
    def create_customer_account(user_id: str):
        try:

            user_account = USER_MODEL.objects.get(id=user_id)

            customer = stripe.Customer.create(
                name=user_account.username,
                email=user_account.email,
                description=f"Custom Account for user {str(user_id)}",
            )

            user_account.customer_id = customer["id"]
            user_account.save()

        except Exception as e:
            print(f"Error when creating a new connected account: {e}")

    @staticmethod
    def create_bank_account(user_id: str, account_id: str, account_number: str, account_name: str):
        try:
            bank_account = stripe.Customer.create_source(
                account_id,
                source={
                    "account_number": account_number,
                    "country": "BR",
                    "currency": "BRL",
                    "object": "bank_account",
                    "account_holder_name": account_name,
                    "account_holder_type": "individual",
                },
            )

            user_account = USER_MODEL.objects.get(id=user_id)

            user_account.bank_account_id = bank_account["id"]
            user_account.save()

            print("Bank account created successfully successfully")

        except Exception as e:
            print(f"Error when creating bank account: {e}")

    @staticmethod
    def process_payout(amount, bank_account_id, transaction_id, transaction_reference):

        print(bank_account_id)

        try:

            stripe.Payout.create(
                amount=int(amount * 100),
                currency="BRL",
                description="Payout from UnlockIt",
                destination=bank_account_id,
                method="standard",
                metadata={
                    "transaction_id": transaction_id,
                    "transaction_reference": transaction_reference,
                },
            )

        except Exception as e:
            print(f"Error when processing payout: {e}")
