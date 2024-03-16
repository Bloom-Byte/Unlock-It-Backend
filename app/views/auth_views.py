from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser


from drf_yasg.utils import swagger_auto_schema


from app.util_classes import APIResponses
from app.enum_classes import APIMessages
from app.serializers.auth_serializers import (
    ForgotPasswordThirdSerializer,
    SignUpSerializer,
    LoginSerializer,
    ProfileSerializer,
    ProfileEditSerializer,
    DeleteAccountSerializer,
    PasswordChangeSerializer,
    ForgotPasswordFirstSerializer,
    ForgotPasswordSecondSerializer,
    GoogleOAuthSerializer,
    FaceBookOAuthSerializer,
)


######################################### Login View ################################################


class LoginView(APIView):
    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request, *args, **kwargs):
        form = LoginSerializer(data=request.data)

        if form.is_valid():
            data, error = form.login(request=request)

            if error:
                return APIResponses.error_response(message=error, status_code=HTTP_401_UNAUTHORIZED)

            return APIResponses.success_response(
                status_code=HTTP_200_OK, message=APIMessages.LOGIN_SUCCESS, data=data
            )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST,
            message=APIMessages.FORM_ERROR,
            errors=form.errors,
        )


################################## Signup Views #############################################


class SignUpView(APIView):
    @swagger_auto_schema(request_body=SignUpSerializer)
    def post(self, request, *args, **kwargs):
        form = SignUpSerializer(data=request.data)

        if form.is_valid():
            data = form.create_account()

            return APIResponses.success_response(
                status_code=HTTP_200_OK, message=APIMessages.ACCOUNT_CREATED, data=data
            )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST,
            message=APIMessages.FORM_ERROR,
            errors=form.errors,
        )


class GoogleSignUpView(APIView):
    def get(self, request):
        data = data = {
            "code": request.query_params.get("code"),
        }

        referral_code = request.query_params.get("referral_code", None)

        if referral_code:
            data["referral_code"] = referral_code

        form = GoogleOAuthSerializer(data=data)

        if form.is_valid():
            data, success = form.process_google_oauth()

            if success:
                return APIResponses.success_response(
                    message=APIMessages.ACCOUNT_CREATED, status_code=201, data=data
                )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.GOOGLE_OAUTH_ERROR
        )

    @swagger_auto_schema(request_body=GoogleOAuthSerializer)
    def post(self, request):
        form = GoogleOAuthSerializer(data=request.data)

        if form.is_valid():
            data, success = form.process_google_oauth()

            if success:
                return APIResponses.success_response(
                    message=APIMessages.ACCOUNT_CREATED, status_code=201, data=data
                )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.GOOGLE_OAUTH_ERROR
        )


class FacebookSignUpView(APIView):
    def get(self, request):
        data = data = {
            "code": request.query_params.get("code"),
        }

        referral_code = request.query_params.get("referral_code", None)

        if referral_code:
            data["referral_code"] = referral_code

        form = FaceBookOAuthSerializer(data=data)

        if form.is_valid():
            data, success = form.process_facebook_oauth()

            if success:
                return APIResponses.success_response(
                    message=APIMessages.ACCOUNT_CREATED, status_code=201, data=data
                )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.FACEBOOK_OAUTH_ERROR
        )

    @swagger_auto_schema(request_body=FaceBookOAuthSerializer)
    def post(self, request):
        form = FaceBookOAuthSerializer(data=request.data)

        if form.is_valid():
            data, success = form.process_facebook_oauth()

            if success:
                return APIResponses.success_response(
                    message=APIMessages.ACCOUNT_CREATED, status_code=201, data=data
                )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.FACEBOOK_OAUTH_ERROR
        )


########################################## Profile View ################################################


class ProfileView(APIView):
    permission_classes = [IsAuthenticated, FormParser, MultiPartParser]

    def get(self, request, *args, **kwargs):
        data = ProfileSerializer.get_profile_details(user=request.user)

        return APIResponses.success_response(
            message=APIMessages.SUCCESS, status_code=HTTP_200_OK, data=data
        )

    @swagger_auto_schema(request_body=ProfileEditSerializer)
    def patch(self, request, *args, **kwargs):
        form = ProfileEditSerializer(data=request.data, context={"user": request.user})

        if form.is_valid():
            data = form.edit_profile()

            return APIResponses.success_response(
                message=APIMessages.PROFILE_UPDATED_SUCCESSFULLY, status_code=HTTP_200_OK, data=data
            )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.FORM_ERROR, errors=form.errors
        )


###################################################################### PASSWORD CHANGE ENDPOINTS ##############################################


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=PasswordChangeSerializer)
    def post(self, request, *args, **kwargs):
        form = PasswordChangeSerializer(data=request.data, context={"user": request.user})

        if form.is_valid():
            form.change_password()

            return APIResponses.success_response(
                message=APIMessages.PASSWORD_CHANGED, status_code=HTTP_200_OK
            )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.FORM_ERROR, errors=form.errors
        )


# ########################################################### Delete Account ENDPOINTS ###############################################


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    # @swagger_auto_schema(request_body=DeleteAccountSerializer)
    def delete(self, request, *args, **kwargs):
        # form = DeleteAccountSerializer(data=request.data, context={"user": request.user})

        # if form.is_valid():
        #     form.delete_account()

        DeleteAccountSerializer.delete_account(user=request.user)

        return APIResponses.success_response(
            message=APIMessages.ACCOUNT_DELETED, status_code=HTTP_200_OK
        )

        # return APIResponses.error_response(
        #     status_code=HTTP_400_BAD_REQUEST, message=APIMessages.FORM_ERROR, errors=form.errors
        # )


# ########################################################### RESET PASSWORD ENDPOINTS ###############################################


class ResetPasswordGenerateView(APIView):
    @swagger_auto_schema(request_body=ForgotPasswordFirstSerializer)
    def post(self, request, *args, **kwargs):
        if request.user:
            return APIResponses.error_response(
                status_code=HTTP_403_FORBIDDEN, message=APIMessages.FORBIDDEN
            )

        form = ForgotPasswordFirstSerializer(data=request.data)

        if form.is_valid():
            form.send_reset_otp()

            return APIResponses.success_response(
                message=APIMessages.PASSWORD_RESET_CODE_SENT, status_code=HTTP_200_OK
            )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.FORM_ERROR, errors=form.errors
        )


class ResetPasswordVerifyView(APIView):
    @swagger_auto_schema(request_body=ForgotPasswordSecondSerializer)
    def post(self, request, *args, **kwargs):
        if request.user:
            return APIResponses.error_response(
                status_code=HTTP_403_FORBIDDEN, message=APIMessages.FORBIDDEN
            )

        form = ForgotPasswordSecondSerializer(data=request.data)

        if form.is_valid():
            form.verify_otp()

            return APIResponses.success_response(
                message=APIMessages.OTP_VERIFIED, status_code=HTTP_200_OK
            )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.FORM_ERROR, errors=form.errors
        )


class ResetPasswordCompleteView(APIView):
    @swagger_auto_schema(request_body=ForgotPasswordThirdSerializer)
    def post(self, request, *args, **kwargs):
        if request.user:
            return APIResponses.error_response(
                status_code=HTTP_403_FORBIDDEN, message=APIMessages.FORBIDDEN
            )

        form = ForgotPasswordThirdSerializer(data=request.data)

        if form.is_valid():
            form.verify_otp()

            return APIResponses.success_response(
                message=APIMessages.PASSWORD_RESET, status_code=HTTP_200_OK
            )

        return APIResponses.error_response(
            status_code=HTTP_400_BAD_REQUEST, message=APIMessages.FORM_ERROR, errors=form.errors
        )
