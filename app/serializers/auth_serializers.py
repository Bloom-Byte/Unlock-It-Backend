from typing import Any, Tuple

from django.contrib.auth import authenticate
from django.conf import settings

from rest_framework import serializers

import requests

from app.validators import password_validator, email_not_exist_checker, email_exist_checker
from app.enum_classes import APIMessages, AccountStatuses, OTPChannels, OTPPurposes
from app.api_authentication import MyAPIAuthentication
from app.models import CustomUser
from app.util_classes import (
    CodeGenerator,
    OTPHelper,
    EmailSender,
    StripeHelper,
    FireBaseHelper,
    EncryptionHelper,
)


######################################## USER SERIALIZERS ############################################


class ProfileDetailsSerializer(serializers.ModelSerializer):
    """Serializer class for returning the data for a particular user object"""

    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "profile_picture", "stripe_setup_complete"]


class ProfileSerializer:
    """Class for fetching the the profile details of a particular user"""

    @staticmethod
    def get_profile_details(user: CustomUser):
        """
        Get the profile details of a user.

        Args:
            user (CustomUser): The user object for which to retrieve the profile details.

        Returns:
            dict: A dictionary containing the serialized profile details of the user.
        """
        return ProfileDetailsSerializer(user).data

    @staticmethod
    def complete_stripe_setup(user: CustomUser):
        data = StripeHelper.create_connected_account_onboarding_link(user_id=str(user.id))
        return data

    @staticmethod
    def get_connected_account_login_link(user: CustomUser):
        data = StripeHelper.get_connected_account_login_link(connected_account_id=user.customer_id)
        return data

    @staticmethod
    def refresh_stripe_onboarding_link(token: str):
        decrypted_data = EncryptionHelper.decrypt_download_payload(token=token)

        _, data = StripeHelper.create_connected_account_onboarding_link(
            user_id=decrypted_data["user_id"]
        )

        return data["account_link"]


################################################ Sign Up / Login Serializer ###########################################


class SignUpSerializer(serializers.Serializer):
    """Serializer class for creating an account"""

    username = serializers.CharField()
    email = serializers.EmailField(validators=[email_not_exist_checker])
    password = serializers.CharField(validators=[password_validator])
    referral_code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs: Any) -> dict:
        """Extending the validate method to validate the data before performing any action"""
        data = super().validate(attrs)

        username = data["username"].title()
        referral_code = data.get("referral_code", None)

        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                {"username": "A user with this username already exist"}
            )

        if referral_code:
            if not CustomUser.objects.filter(referral_code=referral_code).exists():
                raise serializers.ValidationError(
                    {"referral_code": "Invalid Referral Code, please check and try again"}
                )

        return data

    def create_account(self) -> dict:
        """
        Create a new user account with the provided data, including email, password, username, and referral code if provided.
        Save the user to the database, update referral user (if applicable), create a Stripe connected account for payments, and return authentication token and user profile data.

        Returns:
            dict: A dictionary containing the authentication token, token expiration time, and user profile data.

        """
        new_user = CustomUser()
        new_user.email = self.validated_data["email"].lower().strip()
        new_user.set_password(self.validated_data["password"])
        new_user.username = self.validated_data["username"].title()
        new_user.account_status = AccountStatuses.ACTIVE
        new_user.referral_code = CodeGenerator.generate_referral_code()
        new_user.save()

        # get referral user and update
        referral_code = self.validated_data.get("referral_code", None)

        if referral_code:
            referral_user = CustomUser.objects.filter(referral_code=referral_code).first()
            if referral_user:
                referral_user.referred_users += 1
                referral_user.save()

        # create stripe connected account
        StripeHelper.create_connected_account(user_id=new_user.id)

        # login successful
        auth_token, auth_exp = MyAPIAuthentication.get_access_token(
            {
                "user_id": str(new_user.id),
            }
        )

        data = {
            "auth_token": auth_token,
            "auth_token_exp": auth_exp,
            "data": ProfileDetailsSerializer(new_user).data,
        }

        return data


class LoginSerializer(serializers.Serializer):
    """Serializer class for logging in"""

    email = serializers.EmailField(
        required=True, error_messages={"blank": "This field is required"}
    )
    password = serializers.CharField(
        required=True, error_messages={"blank": "This field is required"}
    )

    def login(self, request) -> Tuple[dict | None, str | None]:
        """
        Authenticates a user with the given request, email, and password.

        Args:
            request: The request object.
            email: The email of the user.
            password: The password of the user.

        Returns:
            A tuple containing the authentication data and any error message. The authentication data is a dictionary with the following keys:
                - auth_token: The authentication token.
                - auth_token_exp: The expiration time of the authentication token.
                - data: The serialized profile details of the user.

            The error message is a string indicating the reason for the login failure.

        """

        email = self.validated_data["email"].lower()
        password = self.validated_data["password"]

        user: CustomUser = authenticate(request, username=email, password=password)

        if user:
            if user.account_status == AccountStatuses.DEACTIVATED:
                return None, APIMessages.ACCOUNT_DEACTIVATED

            if user.account_status == AccountStatuses.INACTIVE:
                return None, APIMessages.ACCOUNT_BLOCKED

            if user.account_status == AccountStatuses.PENDING:
                return None, APIMessages.ACCOUNT_PENDING

            # login successful

            # check the account setup on stripe, and update if needed
            StripeHelper.get_connected_account(user_id=user.id)
            user.refresh_from_db()

            auth_token, auth_exp = MyAPIAuthentication.get_access_token(
                {
                    "user_id": str(user.id),
                }
            )

            data = {
                "auth_token": auth_token,
                "auth_token_exp": auth_exp,
                "data": ProfileDetailsSerializer(user).data,
            }

            return data, None

        return None, APIMessages.LOGIN_FAILURE


################################################# Profile Serializer #######################################


class ProfileEditSerializer(serializers.Serializer):
    """Serializer class for editing the profile"""

    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    picture = serializers.ImageField(required=False)

    def validate(self, attrs) -> dict[str, Any]:
        """Extending the validate method to validate the data before performing any action"""
        data = super().validate(attrs)

        user: CustomUser = self.context.get("user")

        if "email" in data:
            if (
                CustomUser.objects.filter(email=data["email"].lower().strip())
                .exclude(id=user.id)
                .exists()
            ):
                raise serializers.ValidationError({"email": "Email already exist"})

        if "username" in data:
            if (
                CustomUser.objects.filter(username=data["username"].title())
                .exclude(id=user.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    {"username": "A user with this username already exist"}
                )

        return data

    def edit_profile(self) -> dict:
        """
        Edit the user profile and return the profile details.

        Parameters:
            self: The instance of the class.

        Returns:
            dict: The profile details data.
        """
        user: CustomUser = self.context.get("user")

        user.username = self.validated_data.get("username", user.username)
        user.email = self.validated_data.get("email", user.email)
        user.save()

        # TODO do the image upload to s3 bucket here

        return ProfileDetailsSerializer(user).data


################################################# Password Change Serializer #######################################


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer class for handling password change"""

    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[password_validator])

    def validate(self, attrs) -> dict:
        """Extending the validate method to validate the data before performing any action"""
        data = super().validate(attrs)

        old_password = data["old_password"]

        user: CustomUser = self.context.get("user")

        if not user.check_password(old_password):
            raise serializers.ValidationError({"old_password": "Current password is incorrect"})

        return data

    def change_password(self) -> None:
        """
        A function to change the user's password. It retrieves the user object from the context, sets a new password provided in the validated data, saves the updated user object.
        """

        user: CustomUser = self.context.get("user")
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()


##################################### Delete Account Serializer ########################################
class DeleteAccountSerializer(serializers.Serializer):
    """Serializer class for initiating the deletion of an account"""

    password = serializers.CharField()

    def validate(self, attrs: Any) -> dict[str, str]:
        """Extending the validate method to validate the data before performing any action"""
        data = super().validate(attrs)

        password = data["password"]

        user: CustomUser = self.context.get("user")

        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Invalid password"})

        return data

    @staticmethod
    def delete_account(user: CustomUser) -> None:
        """
        Deletes a user account.

        Args:
            user (CustomUser): The user object to be deleted.

        Returns:
            None: This function does not return anything.
        """

        # if user.account_type == AccountTypes.AGENT:

        user.account_status = AccountStatuses.DEACTIVATED
        user.save()

        # TODO finish this


############################################# Forgot Password Serializers #############################3


class ForgotPasswordFirstSerializer(serializers.Serializer):
    """Serializer class for initiating the forgot password process"""

    email = serializers.EmailField(validators=[email_exist_checker])

    def send_reset_otp(self):
        """
        Sends a reset OTP to the user's email address.

        This function generates a one-time password (OTP) for resetting the user's password. The OTP is generated using the `OTPHelper.generate_otp` method, with the purpose set to `OTPPurposes.RESET_PASSWORD`, the channel set to `OTPChannels.EMAIL`, and the recipient set to the user's email address.

        The generated OTP is then sent to the user's email address using the `EmailSender.send_password_reset_email` method.

        Parameters:
            self (object): The current instance of the class.

        Returns:
            None
        """

        email = self.validated_data["email"].strip().lower()

        otp = OTPHelper.generate_otp(
            purpose=OTPPurposes.RESET_PASSWORD, channel=OTPChannels.EMAIL, recipient=email
        )

        EmailSender.send_password_reset_email(receiver=email, otp=otp)


class ForgotPasswordSecondSerializer(serializers.Serializer):
    """Serializer class for verifying the OTP for password reset"""

    email = serializers.EmailField(validators=[email_exist_checker])
    code = serializers.CharField()

    def validate(self, attrs) -> dict:
        """Extending the validate method to validate the data before performing any action"""
        data = super().validate(attrs)

        # verify the opt here
        email = data["email"].lower().strip()
        code = data["code"]

        success = OTPHelper.verify_otp(
            otp=code, purpose=OTPPurposes.RESET_PASSWORD, recipient=email, mark_used=False
        )

        if success is False:
            raise serializers.ValidationError(
                {"code": "Invalid or expired OTP, please check and try again"}
            )

        return data

    def verify_otp(self) -> None:
        """
        Verify the OTP (One-Time Password) provided by the user for password reset.

        This function takes no parameters.

        The function first retrieves the email and code from the validated data. It then calls the `verify_otp` function from the `OTPHelper` class, passing in the OTP, purpose, recipient, and mark_used parameters.

        The purpose parameter is set to `OTPPurposes.RESET_PASSWORD` to indicate that the OTP is being used for password reset. The recipient parameter is set to the lowercase and stripped email retrieved from the validated data. The mark_used parameter is set to False, indicating that the OTP should not be marked as used.

        This function does not return any value.
        """

        email = self.validated_data["email"].lower().strip()
        code = self.validated_data["code"]

        OTPHelper.verify_otp(
            otp=code, purpose=OTPPurposes.RESET_PASSWORD, recipient=email, mark_used=False
        )


class ForgotPasswordThirdSerializer(serializers.Serializer):
    """Serializer class for resetting the password"""

    email = serializers.EmailField(validators=[email_exist_checker])
    code = serializers.CharField()
    new_password = serializers.CharField(validators=[password_validator])

    def validate(self, attrs) -> dict:
        """Extending the validate method to validate the data before performing any action"""
        data = super().validate(attrs)

        # verify the opt here
        email = data["email"].lower().strip()
        code = data["code"]

        verified = OTPHelper.check_verified(
            otp=code, purpose=OTPPurposes.RESET_PASSWORD, recipient=email
        )

        if verified is False:
            raise serializers.ValidationError({"code": "Unverified OTP, please verify to continue"})

        return data

    def reset_password(self) -> None:
        """
        Resets the password for a user.

        This function takes no parameters.

        Returns:
            None: This function does not return any value.
        """

        email = self.validated_data["email"].lower().strip()
        code = self.validated_data["code"]
        new_password = self.validated_data["new_password"]

        OTPHelper.verify_otp(
            otp=code, purpose=OTPPurposes.RESET_PASSWORD, recipient=email, mark_used=True
        )

        user = CustomUser.objects.get(email=email)
        user.account_status = AccountStatuses.ACTIVE
        user.set_password(new_password)
        user.save()


######################################## GOOGLE OAuth Serializer ###############################3
class GoogleOAuthSerializer(serializers.Serializer):
    """Serializer class for Google OAuth"""

    code = serializers.CharField()
    referral_code = serializers.CharField(required=False)

    def process_google_oauth(self) -> Tuple[dict | None, bool]:
        """
        Process the Google OAuth flow, including getting the access token,
        retrieving user information, creating a new user if necessary, and
        returning the authentication token with user data.
        """

        code = self.validated_data["code"]
        referral_code = self.validated_data.get("referral_code", None)

        redirect_uri = settings.FRONTEND_GOOGLE_OAUTH_URL

        access_token, success = self.google_get_access_token(code=code, redirect_uri=redirect_uri)

        if success is False:
            return None, False

        user_data, success = self.google_get_user_info(access_token=access_token)

        if success is False:
            return None, False

        try:
            user = CustomUser.objects.get(email=user_data["email"].lower().strip())

            auth_token, auth_exp = MyAPIAuthentication.get_access_token(
                {
                    "user_id": str(user.id),
                }
            )

            data = {
                "auth_token": auth_token,
                "auth_token_exp": auth_exp,
                "data": ProfileDetailsSerializer(user).data,
            }

            return data, True

        except CustomUser.DoesNotExist:
            new_user = CustomUser()
            new_user.username = user_data["name"].title()
            new_user.email = user_data["email"].lower().strip()
            new_user.account_status = AccountStatuses.ACTIVE
            new_user.referral_code = CodeGenerator.generate_referral_code()
            new_user.google_auth_token = access_token
            new_user.profile_picture = user_data["picture"]
            new_user.save()

            # get referral user and update
            if referral_code:
                referral_user = CustomUser.objects.filter(referral_code=referral_code).first()
                if referral_user:
                    referral_user.referred_users += 1
                    referral_user.save()

            # create stripe connected account
            StripeHelper.create_customer_account(user_id=new_user.id)

            auth_token, auth_exp = MyAPIAuthentication.get_access_token(
                {
                    "user_id": str(new_user.id),
                }
            )

            data = {
                "auth_token": auth_token,
                "auth_token_exp": auth_exp,
                "data": ProfileDetailsSerializer(new_user).data,
            }

            return data, True

    @classmethod
    def google_get_access_token(cls, *, code: str, redirect_uri: str) -> Tuple[str | None, bool]:
        """
        Retrieves the access token from Google OAuth2 using the provided authorization code, redirect URI, and client credentials.

        Args:
            code (str): The authorization code obtained from Google OAuth2.
            redirect_uri (str): The redirect URI used in the authorization request.

        Returns:
            Tuple[str | None, bool]: A tuple containing the access token (str) if successful, or None if an error occurred. The second element of the tuple indicates the success status, where True indicates success and False indicates failure.
        """

        data = {
            "code": code,
            "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        response = requests.post(settings.GOOGLE_ACCESS_TOKEN_OBTAIN_URL, data=data, timeout=60)

        if not response.ok:
            return None, False

        access_token = response.json()["access_token"]

        return access_token, True

    @classmethod
    def google_get_user_info(cls, *, access_token: str) -> Tuple[dict | None, bool]:
        """
        Retrieves user information from Google using the provided access token.

        Args:
            access_token (str): The access token used to authenticate the request.

        Returns:
            Tuple[dict | None, bool]: A tuple containing the user information as a dictionary
            if the request is successful, and a boolean indicating the success status.
            If the request is unsuccessful, returns (None, False).

        Raises:
            None
        """

        response = requests.get(
            settings.GOOGLE_USER_INFO_URL, params={"access_token": access_token}, timeout=60
        )

        if not response.ok:
            return None, False

        return response.json(), True


class FaceBookOAuthSerializer(serializers.Serializer):
    """Serializer class for Facebook OAuth"""

    code = serializers.CharField()
    referral_code = serializers.CharField(required=False)

    def process_facebook_oauth(self) -> Tuple[dict | None, bool]:
        """
        Process the Facebook OAuth authentication flow and return the user data and success status.

        Returns:
            - A tuple containing the user data and success status:
                - If the authentication flow is successful, the user data is returned as a dictionary with the following keys:
                    - "auth_token": The authentication token.
                    - "auth_token_exp": The expiration time of the authentication token.
                    - "data": The serialized profile details of the user.
                - If the authentication flow fails, None is returned.
            - The success status, indicating whether the authentication flow was successful or not.

        Raises:
            - None.

        """

        code = self.validated_data["code"]
        referral_code = self.validated_data.get("referral_code", None)

        redirect_uri = settings.FRONTEND_FACEBOOK_OAUTH_URL

        access_token, success = self.facebook_get_access_token(code=code, redirect_uri=redirect_uri)

        if success is False:
            return None, False

        user_data, success = self.facebook_get_user_info(access_token=access_token)

        if success is False:
            return None, False

        try:
            user = CustomUser.objects.get(email=user_data["email"].lower().strip())

            auth_token, auth_exp = MyAPIAuthentication.get_access_token(
                {
                    "user_id": str(user.id),
                }
            )

            data = {
                "auth_token": auth_token,
                "auth_token_exp": auth_exp,
                "data": ProfileDetailsSerializer(user).data,
            }

            return data, True

        except CustomUser.DoesNotExist:
            new_user = CustomUser()
            new_user.username = user_data["name"].title()
            new_user.email = user_data["email"].lower().strip()
            new_user.account_status = AccountStatuses.ACTIVE
            new_user.referral_code = CodeGenerator.generate_referral_code()
            new_user.facebook_auth_token = access_token
            new_user.profile_picture = user_data["picture"]["data"]["url"]
            new_user.save()

            if referral_code:
                referral_user = CustomUser.objects.filter(referral_code=referral_code).first()
                if referral_user:
                    referral_user.referred_users += 1
                    referral_user.save()

            # create stripe connected account
            StripeHelper.create_customer_account(user_id=new_user.id)

            auth_token, auth_exp = MyAPIAuthentication.get_access_token(
                {
                    "user_id": str(new_user.id),
                }
            )

            data = {
                "auth_token": auth_token,
                "auth_token_exp": auth_exp,
                "data": ProfileDetailsSerializer(new_user).data,
            }

            return data, True

    @classmethod
    def facebook_get_access_token(cls, *, code: str, redirect_uri: str) -> Tuple[str | None, bool]:
        """
        Get the access token from Facebook using the provided code and redirect URI.

        Args:
            code (str): The authorization code.
            redirect_uri (str): The URI to redirect to after authorization.

        Returns:
            Tuple[str | None, bool]: A tuple containing the access token and a boolean indicating success.
        """

        query_params = {
            "code": code,
            "client_id": settings.FACEBOOK_OAUTH_CLIENT_ID,
            "client_secret": settings.FACEBOOK_OAUTH_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
        }

        response = requests.get(
            settings.FACEBOOK_ACCESS_TOKEN_OBTAIN_URL, params=query_params, timeout=60
        )

        if not response.ok:
            return None, False

        access_token = response.json()["access_token"]

        return access_token, True

    @classmethod
    def facebook_get_user_info(cls, *, access_token: str) -> Tuple[dict | None, bool]:
        """
        Retrieves user information from Facebook using an access token.

        Args:
            access_token (str): The access token for the user.

        Returns:
            Tuple[dict | None, bool]: A tuple containing the user information as a dictionary if successful, or None if unsuccessful. The second element of the tuple indicates whether the request was successful or not.
        """

        response = requests.get(
            settings.FACEBOOK_PROFILE_ENDPOINT_URL,
            params={"access_token": access_token},
            timeout=60,
        )

        if not response.ok:
            return None, False

        user_id = response.json()["id"]

        details_response = requests.get(
            settings.FACEBOOK_PROFILE_DETAILS_URL.replace("USER-ID", user_id),
            params={"access_token": access_token},
            timeout=60,
        )

        if not details_response.ok:
            return None, False

        return details_response.json(), True


class FireBaseOauthSerializer(serializers.Serializer):
    id_token = serializers.CharField()

    def process_auth(self):
        success, user_data = FireBaseHelper.Firebase_validation(self.validated_data["id_token"])

        if success is False:
            return None, False

        try:
            user = CustomUser.objects.get(email=user_data["email"].lower().strip())

            auth_token, auth_exp = MyAPIAuthentication.get_access_token(
                {
                    "user_id": str(user.id),
                }
            )

            data = {
                "auth_token": auth_token,
                "auth_token_exp": auth_exp,
                "data": ProfileDetailsSerializer(user).data,
            }

            return data, True

        except CustomUser.DoesNotExist:
            new_user = CustomUser()
            new_user.username = user_data["name"].title()
            new_user.email = user_data["email"].lower().strip()
            new_user.account_status = AccountStatuses.ACTIVE
            new_user.referral_code = CodeGenerator.generate_referral_code()
            new_user.firebase_access_token = self.validated_data["id_token"]
            new_user.profile_picture = user_data["picture"]
            new_user.save()

            # create stripe connected account
            StripeHelper.create_connected_account(user_id=new_user.id)

            auth_token, auth_exp = MyAPIAuthentication.get_access_token(
                {
                    "user_id": str(new_user.id),
                }
            )

            data = {
                "auth_token": auth_token,
                "auth_token_exp": auth_exp,
                "data": ProfileDetailsSerializer(new_user).data,
            }

            return data, True
