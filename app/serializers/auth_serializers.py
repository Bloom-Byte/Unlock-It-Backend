from django.contrib.auth import authenticate
from django.conf import settings

from rest_framework import serializers

import requests

from app.validators import password_validator, email_not_exist_checker, email_exist_checker
from app.enum_classes import APIMessages, AccountStatuses, OTPChannels, OTPPurposes
from app.api_authentication import MyAPIAuthentication
from app.models import CustomUser
from app.util_classes import CodeGenerator, OTPHelper, EmailSender


######################################## USER SERIALIZERS ############################################


class ProfileDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "profile_picture"]


class ProfileSerializer:
    @staticmethod
    def get_profile_details(user: CustomUser):
        return ProfileDetailsSerializer(user).data


################################################ Sign Up / Login Serializer ###########################################


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField(validators=[email_not_exist_checker])
    password = serializers.CharField(validators=[password_validator])
    referral_code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
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

    def create_account(self):
        new_user = CustomUser()
        new_user.email = self.validated_data["email"].lower().strip()
        new_user.set_password(self.validated_data["password"])
        new_user.username = self.validated_data["username"].title()
        new_user.account_status = AccountStatuses.ACTIVE
        new_user.referral_code = CodeGenerator.generate_referral_code()
        new_user.save()

        # TODO process the referral stuff here

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
    email = serializers.EmailField(
        required=True, error_messages={"blank": "This field is required"}
    )
    password = serializers.CharField(
        required=True, error_messages={"blank": "This field is required"}
    )

    def login(self, request):
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
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    picture = serializers.ImageField(required=False)

    def validate(self, attrs):
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

    def edit_profile(self):
        user: CustomUser = self.context.get("user")

        user.username = self.validated_data.get("username", user.username)
        user.email = self.validated_data.get("email", user.email)
        user.save()

        # TODO do the image upload to s3 bucket here

        return ProfileDetailsSerializer(user).data


################################################# Password Change Serializer #######################################


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[password_validator])

    def validate(self, attrs):
        data = super().validate(attrs)

        old_password = data["old_password"]

        user: CustomUser = self.context.get("user")

        if not user.check_password(old_password):
            raise serializers.ValidationError({"old_password": "Current password is incorrect"})

        return data

    def change_password(self):
        user: CustomUser = self.context.get("user")
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()


##################################### Delete Account Serializer ########################################
class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField()

    def validate(self, attrs):
        data = super().validate(attrs)

        password = data["password"]

        user: CustomUser = self.context.get("user")

        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Invalid password"})

        return data

    @staticmethod
    def delete_account(user: CustomUser):
        # if user.account_type == AccountTypes.AGENT:

        user.account_status = AccountStatuses.DEACTIVATED
        user.save()

        # TODO finish this


############################################# Forgot Password Serializers #############################3


class ForgotPasswordFirstSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[email_exist_checker])

    def send_reset_otp(self):
        email = self.validated_data["email"].strip().lower()

        otp = OTPHelper.generate_otp(
            purpose=OTPPurposes.RESET_PASSWORD, channel=OTPChannels.EMAIL, recipient=email
        )

        EmailSender.send_password_reset_email(receiver=email, otp=otp)


class ForgotPasswordSecondSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[email_exist_checker])
    code = serializers.CharField()

    def validate(self, attrs):
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

    def verify_otp(self):
        email = self.validated_data["email"].lower().strip()
        code = self.validated_data["code"]

        OTPHelper.verify_otp(
            otp=code, purpose=OTPPurposes.RESET_PASSWORD, recipient=email, mark_used=False
        )


class ForgotPasswordThirdSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[email_exist_checker])
    code = serializers.CharField()
    new_password = serializers.CharField(validators=[password_validator])

    def validate(self, attrs):
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

    def reset_password(self):
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
    code = serializers.CharField()
    referral_code = serializers.CharField(required=False)

    def process_google_oauth(self):
        code = self.validated_data["code"]
        _ = self.validated_data.get("referral_code", None)

        redirect_uri = settings.FRONTEND_GOOGLE_OAUTH_URL

        access_token, success = self.google_get_access_token(code=code, redirect_uri=redirect_uri)

        if success is False:
            return None, False

        user_data, success = self.google_get_user_info(access_token=access_token)

        if success is False:
            return None, False

        # TODO add the referral stuff

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
            user = CustomUser()
            user.username = user_data["name"].title()
            user.email = user_data["email"].lower().strip()
            user.account_status = AccountStatuses.ACTIVE
            user.referral_code = CodeGenerator.generate_referral_code()
            user.google_auth_token = access_token
            user.profile_picture = user_data["picture"]
            user.save()

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

    @classmethod
    def google_get_access_token(cls, *, code: str, redirect_uri: str):
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
    def google_get_user_info(cls, *, access_token: str):
        response = requests.get(
            settings.GOOGLE_USER_INFO_URL, params={"access_token": access_token}, timeout=60
        )

        if not response.ok:
            return None, False

        return response.json(), True


class FaceBookOAuthSerializer(serializers.Serializer):
    code = serializers.CharField()
    referral_code = serializers.CharField(required=False)

    def process_facebook_oauth(self):
        code = self.validated_data["code"]
        _ = self.validated_data.get("referral_code", None)

        redirect_uri = settings.FRONTEND_FACEBOOK_OAUTH_URL

        access_token, success = self.facebook_get_access_token(code=code, redirect_uri=redirect_uri)

        if success is False:
            return None, False

        user_data, success = self.facebook_get_user_info(access_token=access_token)

        if success is False:
            return None, False

        # TODO add the referral stuff

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
            user = CustomUser()
            user.username = user_data["name"].title()
            user.email = user_data["email"].lower().strip()
            user.account_status = AccountStatuses.ACTIVE
            user.referral_code = CodeGenerator.generate_referral_code()
            user.facebook_auth_token = access_token
            user.profile_picture = user_data["picture"]["data"]["url"]
            user.save()

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

    @classmethod
    def facebook_get_access_token(cls, *, code: str, redirect_uri: str):
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
    def facebook_get_user_info(cls, *, access_token: str):
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
