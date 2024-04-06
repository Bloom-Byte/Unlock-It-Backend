from random import choices
from datetime import timedelta
import string
import uuid
import jwt

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

from app.enum_classes import AccountStatuses


USER_MODEL = get_user_model()


class MyAPIAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """
        Authenticate user based on request headers.

        Parameters:
            request (dict): The request object containing headers.

        Returns:
            tuple: A tuple containing user information and an error message.
        """
        data = self.validate_request(request.headers)
        if not data:
            return None, None

        return self.get_user(data["user_id"]), None

    def get_user(self, user_id):
        """
        Retrieves a user from the database based on their user ID.

        Parameters:
            user_id (str): The ID of the user to retrieve.

        Returns:
            UserModel or None: The user object if found, None otherwise.
        """
        try:
            user_id = uuid.UUID(user_id)

            user = (
                USER_MODEL.objects.filter(id=user_id)
                .filter(account_status=AccountStatuses.ACTIVE)
                .first()
            )
            return user
        except Exception:
            return None

    def validate_request(self, headers):
        """
        Validates the request by checking the presence of the 'Authorization' header.
        If the header is present, it verifies the token and returns the decoded data.
        If the token is invalid or expired, it raises an AuthenticationFailed exception.
        If the token header is invalid, it raises an AuthenticationFailed exception.
        If the 'Authorization' header is not provided, it raises an AuthenticationFailed exception.
        """
        authorization = headers.get("Authorization", None)

        if not authorization:
            return None

        token_header = authorization.split(" ")
        if len(token_header) == 2:
            header = token_header[0]
            if header == "Bearer":
                token = token_header[1]

                decoded_data = self.verify_token(token)

                if decoded_data:
                    return decoded_data

                raise exceptions.AuthenticationFailed(_("Invalid or Expired token."))

            raise exceptions.AuthenticationFailed(
                _("Invalid token header. No credentials provided.")
            )

        raise exceptions.AuthenticationFailed(_("Invalid token header. No credentials provided."))

    @staticmethod
    def verify_token(token):
        """
        Verify the given token by decoding it using the provided secret key and algorithm.
        If the token is valid and not expired, return the decoded content.
        If the token is invalid or expired, return None.

        Parameters:
            token (str): The token to be verified.

        Returns:
            dict or None: The decoded content of the token if it's valid and not expired, or None if it's invalid or expired.
        """
        try:
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")

        except Exception:
            return None

        exp = decoded["exp"]

        if timezone.now().timestamp() > exp:
            return None

        return decoded

    @classmethod
    def get_random_token(cls, length):
        """
        Generate a random token of the specified length.

        Parameters:
            length (int): The length of the token to generate.

        Returns:
            str: The randomly generated token.
        """

        return "".join(choices(string.ascii_uppercase + string.digits, k=length))

    @classmethod
    def get_access_token(cls, payload):
        """
        Generates an access token for the given payload.

        Args:
            payload (dict): The payload to be encoded in the access token.

        Returns:
            tuple: A tuple containing the encoded access token and the expiration time of the token.
        """
        return jwt.encode(
            {"exp": timezone.now() + timedelta(days=30), **payload},
            settings.SECRET_KEY,
            algorithm="HS256",
        ), timezone.now() + timedelta(days=30)

    @classmethod
    def get_refresh_token(cls):
        """
        Return a refresh token encoded with the current time and a random token using the given secret key.
        """
        return jwt.encode(
            {
                "exp": timezone.now() + timedelta(days=365),
                "data": cls.get_random_token(15),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )
