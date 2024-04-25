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

from firebase_admin import auth

from rest_framework.response import Response

import stripe


from app.enum_classes import OTPStatuses
from app.models import OTP


USER_MODEL = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY


def snake_case_to_camel_case(value: str):
    """
    Convert a snake_case string to camelCase.

    Args:
        value (str): The snake_case string to be converted.

    Returns:
        str: The camelCase string.
    """
    splitted_string = value.split("_")

    camel_string = splitted_string.pop(0)

    for other_words in splitted_string:
        camel_string += other_words.title()

    return camel_string


class APIResponses:
    @classmethod
    def success_response(cls, message: str, status_code, data=None, paginate_data=None):
        """
        Creates a success response with a message, status code, optional data, and optional paginated data.

        :param message: A string message.
        :param status_code: The HTTP status code.
        :param data: Optional data to include in the response.
        :param paginate_data: Optional paginated data to include in the response.
        :return: A Response object with the context and status code.
        """
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
        """
        Generate an error response with the given status code, message, and optional errors dictionary.

        :param status_code: The HTTP status code to be included in the response
        :param message: The error message to be included in the response
        :param errors: (optional) A dictionary containing error details
        :return: A Response object with the provided context and status code
        """
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
        """
        A class method that handles server errors.
        Takes in a message (str) and a status code, and returns a Response object.
        """
        context = {"message": message}

        return Response(context, status=status_code)


class CodeGenerator:
    @staticmethod
    def generate_code():
        """
        A description of the entire function, its parameters, and its return types.
        """
        if not settings.GENERATE_CODE:
            code = settings.DEFAULT_OTP

        else:
            code = "".join(choices(string.digits, k=6))

        return code

    @staticmethod
    def generate_transaction_reference():
        """
        A static method that generates a transaction reference.
        Returns a string of 14 characters consisting of 7 uppercase letters followed by 7 digits.
        """
        upper = choices(string.ascii_uppercase, k=7)
        digits = choices(string.digits, k=7)
        total = upper + digits

        return "".join(total)

    @staticmethod
    def generate_referral_code():
        """
        Generates a random referral code consisting of 8 characters.

        Returns:
            str: The generated referral code.
        """
        upper = choices(string.ascii_uppercase, k=4)
        digits = choices(string.digits, k=4)
        total = upper + digits

        shuffle(total)

        return "".join(total)

    @staticmethod
    def generate_story_reference():
        """
        Generate a random story reference consisting of 4 uppercase letters followed by 4 digits and return it.
        """
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
        """
        A method to get a paginated response based on the request parameters.

        Parameters:
            cls: The class itself.
            request: The HTTP request object.
            queryset: The queryset to paginate.
            page_size_param: The parameter name for page size (default is "page_size").
            page_number_param: The parameter name for page number (default is "page").

        Returns:
            tuple: A tuple containing total data dictionary, current page object list, and an error message (if any).
        """
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
    """
    This class is a helper class for sending of emails.
    """

    @staticmethod
    def send_password_reset_email(receiver: str, otp: str):
        """
        Sends a password reset email to the specified receiver with the provided OTP (One-Time Password).

        Parameters:
            receiver (str): The email address of the receiver.
            otp (str): The OTP to be included in the email body.

        Returns:
            None

        Raises:
            Exception: If there is an error sending the email.
        """
        try:
            with open("emails/otp_email.html") as f:
                customer_template = f.read()

            customer_template = customer_template.replace("#code", otp)

            # Create a multipart message and set headers
            customer_message = MIMEMultipart()
            customer_message["From"] = settings.EMAIL_HOST_USER
            customer_message["To"] = receiver
            customer_message["Subject"] = "Verification Code"

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

    @staticmethod
    def send_download_link_email(receiver: str, download_link: str):
        """
        Sends a download link email to the specified receiver.

        Args:
            receiver (str): The email address of the recipient.
            download_link (str): The download link to be included in the email.

        Returns:
            None
        """
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
        """
        Generates a one-time password (OTP) for the specified purpose, channel, and recipient.

        Parameters:
            purpose (str): The purpose of the OTP.
            channel (str): The channel through which the OTP will be sent.
            recipient (str): The recipient of the OTP.

        Returns:
            str: The generated OTP code.

        Raises:
            None
        """
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
        """
        Sends an OTP (One-Time Password) to the specified recipient for the given purpose.

        Args:
            purpose (str): The purpose of the OTP.
            recipient (str): The recipient of the OTP.
            email (str, optional): The email address of the recipient. Defaults to None.
            phone_number (str, optional): The phone number of the recipient. Defaults to None.

        Returns:
            str: The generated OTP code.

        Raises:
            None

        Notes:
            - This method checks if there is an existing OTP for the given purpose and recipient.
              If an existing OTP is found, it is marked as inactive.
            - The generated OTP code is saved in the database.
            - If the DEBUG setting is False, the OTP is sent to the recipient's email address using the EmailSender.send_otp_email() method.

        """
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
        """
        Verify the provided OTP (One-Time Password) for a specific purpose and recipient.

        Args:
            otp (str): The OTP to be verified.
            purpose (str): The purpose of the OTP.
            recipient (str): The recipient of the OTP.
            mark_used (bool, optional): Whether to mark the OTP as used if it is valid. Defaults to False.

        Returns:
            bool: True if the OTP is valid and has not expired, False otherwise.
        """
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
        """
        Check if the provided OTP is verified for the given purpose and recipient.

        Parameters:
            otp (str): The one-time password to check.
            purpose (str): The purpose for which the OTP was generated.
            recipient (str): The recipient for whom the OTP was generated.

        Returns:
            bool: True if the provided OTP is verified, False otherwise.
        """
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
        """
        Ensure that the given key is exactly 32 bytes long by hashing it with SHA256 and returning the first 32 bytes.

        Parameters:
            key (bytes): The key to be hashed.

        Returns:
            bytes: The first 32 bytes of the hashed key.
        """
        hashed_key = sha256(key).digest()
        return hashed_key[:32]

    @classmethod
    def encrypt_download_payload(cls, payload: dict):
        """
        Encrypts the given payload dictionary using the Fernet encryption algorithm.

        Parameters:
            payload (dict): The dictionary to be encrypted.

        Returns:
            str: The encrypted payload as a string.

        Raises:
            None

        Algorithm:
            1. Get the secret key from the settings module.
            2. Ensure that the secret key is 32 bytes long.
            3. Generate a Fernet key from the secret key.
            4. Initialize a Fernet cipher instance with the key.
            5. Convert the dictionary to a JSON string.
            6. Encrypt the JSON string using the Fernet cipher.
            7. Return the encrypted payload as a string.

        Note:
            - The secret key is obtained from the settings module.
            - The secret key is converted to a Fernet key using the urlsafe_b64encode function.
            - The Fernet cipher is initialized with the generated key.
            - The dictionary is converted to a JSON string using the json.dumps function.
            - The JSON string is encrypted using the Fernet cipher.
            - The encrypted payload is returned as a string.

        Example:
            payload = {'name': 'John', 'age': 30}
            encrypted_payload = encrypt_download_payload(payload)
            print(encrypted_payload)
            # Output: 'gAAAAABd2Y5cQXc0Fk_x5DQ=='
        """
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
        """
        Decrypts a download payload using a Fernet cipher.

        Args:
            token (str): The encrypted download payload token.

        Returns:
            dict or None: The decrypted JSON dictionary if successful, None otherwise.
        """
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
            print("Error when decrypting download payload: ", error)

            return None


class StripeHelper:
    @staticmethod
    def get_connected_account_login_link(connected_account_id: str):
        try:
            login_link = stripe.Account.create_login_link(connected_account_id)

            print("Done creating login link for the user")

            return True, {"login_link": login_link["url"]}

        except Exception as e:
            print(f"Error when creating login link: {e}")
            return False, None

    @staticmethod
    def get_connected_account_balance(connected_account_id: str):
        try:
            account_balance = stripe.Balance.retrieve(stripe_account=connected_account_id)

            data = {
                "available": account_balance["available"][0]["amount"] / 100,
                "pending": account_balance["pending"][0]["amount"] / 100,
            }

            print("Done fetching account balance for the user")

            return True, data

        except Exception as e:
            print(f"Error when fetching account balance: {e}")
            return False, None

    @staticmethod
    def generate_payment_link(data: dict):
        """
        Generates a payment link using the provided data.

        Args:
            data (dict): The data required to create a payment intent in Stripe.

        Returns:
            tuple: A tuple containing the client secret of the payment intent and a boolean indicating the success of the operation.
                   If the payment intent creation is successful, the tuple will be (data, True), where data is a dictionary with the client secret.
                   If there is an error during the creation of the payment intent, the tuple will be (None, False).

        Raises:
            Exception: If there is an error when creating the payment intent from Stripe.

        """

        try:
            payment_intent = stripe.PaymentIntent.create(**data)

        except Exception as e:
            print(f"Error when creating payment intent from stripe: {e}")
            return None, False

        data = {"client_secret": payment_intent.client_secret}

        return data, True

    @staticmethod
    def generate_checkout_session_link(
        line_items: list, connected_account_id: str, application_fee_amount: int, reference: str
    ):
        try:
            checkout = stripe.checkout.Session.create(
                mode="payment",
                line_items=line_items,
                client_reference_id=reference,
                payment_intent_data={
                    "application_fee_amount": application_fee_amount,
                    "transfer_data": {"destination": connected_account_id},
                },
                success_url=settings.FRONTEND_PAYMENT_SUCCESS_URL,
                cancel_url=settings.FRONTEND_PAYMENT_CANCEL_URL,
            )

            print("Done creating a checkout session")
            return True, {"payment_link": checkout["url"]}

        except Exception as e:
            print(f"Error when creating a checkout session: {e}")
            return False, None

    @classmethod
    def create_connected_account(cls, user_id: str):
        try:
            user_account = USER_MODEL.objects.get(id=user_id)

            customer = stripe.Account.create(
                type="express",
                country="BR",
                email=user_account.email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
            )

            user_account.customer_id = customer["id"]
            user_account.save()

            print("Done creating a connected account for the new user")
            return True

        except Exception as e:
            print(f"Error when creating a new connected account: {e}")
            return False

    @classmethod
    def get_connected_account(cls, user_id: str):
        try:
            user_account = USER_MODEL.objects.get(id=user_id)

            connected_account = stripe.Account.retrieve(user_account.customer_id)

            print(connected_account)

            user_account.stripe_setup_complete = connected_account["charges_enabled"]
            user_account.save()

            print("Done fetching a connected account for the user")

        except Exception as e:
            print(f"Error when fetching a connected account: {e}")

    @classmethod
    def create_connected_account_onboarding_link(cls, user_id: str):
        try:
            user_account = USER_MODEL.objects.get(id=user_id)

            if user_account.customer_id is None:
                account_success = cls.create_connected_account(user_id)

                if not account_success:
                    return False, None

            # encrypt the user id here
            payload = {"user_id": user_id}
            encrypted_auth_token = EncryptionHelper.encrypt_download_payload(payload=payload)

            refresh_url = (
                settings.BACKEND_BASE_URL
                + "api/v1/settings/profile/stripe-setup/refresh/?token="
                + encrypted_auth_token
            )

            print(refresh_url)

            account_link = stripe.AccountLink.create(
                account=user_account.customer_id,
                refresh_url=refresh_url,
                return_url=settings.FRONTEND_STRIPE_ACCOUNT_SETUP_RETURN_URL,
                type="account_onboarding",
            )

            print("Done creating a new account link for the user")
            return True, {"account_link": account_link["url"]}

        except Exception as e:
            print(f"Error when creating a new account link: {e}")
            return False, None

    @staticmethod
    def create_customer_account(user_id: str):
        """
        Create a customer account for a given user ID.

        Args:
            user_id (str): The ID of the user for whom the customer account is to be created.

        Returns:
            None
        """
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
        """
        Create a bank account for a user.

        Args:
            user_id (str): The ID of the user.
            account_id (str): The ID of the account.
            account_number (str): The account number.
            account_name (str): The name of the account holder.

        Returns:
            None

        Raises:
            Exception: If there is an error when creating the bank account.

        Prints:
            - "Bank account created successfully" if the bank account is created successfully.
            - "Error when creating bank account: {error_message}" if there is an error.
        """
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
        """
        Process a payout by creating a Stripe payout object.

        Args:
            amount (float): The amount of the payout in BRL.
            bank_account_id (str): The ID of the bank account to which the payout will be sent.
            transaction_id (str): The ID of the transaction associated with the payout.
            transaction_reference (str): The reference of the transaction associated with the payout.

        Returns:
            None
        """

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


class FireBaseHelper:
    @staticmethod
    def Firebase_validation(id_token: str):
        """
        This function receives id token sent by Firebase and
        validate the id token then check if the user exist on
        Firebase or not if exist it returns True else False
        """
        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token["uid"]
            provider = decoded_token["firebase"]["sign_in_provider"]

            image = None
            name = None

            if "name" in decoded_token:
                name = decoded_token["name"]

            if "picture" in decoded_token:
                image = decoded_token["picture"]

            try:
                user = auth.get_user(uid)
                if user:
                    email = user.email
                    data = {
                        "uid": uid,
                        "email": email,
                        "name": name,
                        "provider": provider,
                        "picture": image,
                    }

                    return True, data

                return False, None

            except Exception as error:
                print(f"Error when fetching user details for firebase oauth: {error}")
                return False, None

        except Exception as error2:
            print(f"Error during the whole firebase oauth process: {error2}")
            return False, None
