from drf_yasg import openapi


class AuthResponseExamples:
    """This class holds the example response for the auth endpoints"""

    LOGIN_RESPONSE = {
        "200": openapi.Response(
            description="Login Successful",
            examples={
                "application/json": {
                    "message": "Login successful",
                    "data": {
                        "authToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp",
                        "authTokenExp": "2024-04-17T19:42:11.864809Z",
                        "data": {
                            "id": "ac870942-efc2-42ca-bdc3-",
                            "username": "username",
                            "email": "user@example.com",
                            "profilePicture": "link",
                            "stripeSetupComplete": False,
                        },
                    },
                }
            },
        ),
        "401": openapi.Response(
            description="Login Failed",
            examples={"application/json": {"message": "Invalid login credentials"}},
        ),
    }

    PASSWORD_RESET_FIRST_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={"application/json": {"message": "Password reset code sent successfully."}},
        ),
        "400": openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "message": "One or more validation(s) failed",
                    "errors": [{"fieldName": "email", "error": "Invalid email address"}],
                }
            },
        ),
    }

    PASSWORD_RESET_SECOND_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={"application/json": {"message": "OTP verified successfully"}},
        ),
        "400": openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "message": "One or more validation(s) failed",
                    "errors": [
                        {
                            "fieldName": "code",
                            "error": "Invalid or expired OTP, please check and try again",
                        }
                    ],
                }
            },
        ),
    }

    PASSWORD_RESET_THIRD_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={"application/json": {"message": "Password reset successfully"}},
        ),
        "400": openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "message": "One or more validation(s) failed",
                    "errors": [
                        {"fieldName": "newPassword", "error": "Please enter a stronger password."}
                    ],
                }
            },
        ),
    }

    SIGN_UP_RESPONSE = {
        "201": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Account created successfully",
                    "data": {
                        "authToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.",
                        "authTokenExp": "2024-04-24T10:50:45.391180Z",
                        "data": {
                            "id": "6e0f0ef6-9030-4ef6-bd15-0b75c9d9bff8",
                            "username": "String",
                            "email": "user@example.com",
                            "profilePicture": None,
                        },
                    },
                }
            },
        ),
        "400": openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {
                    "message": "One or more validation(s) failed",
                    "errors": [
                        {"fieldName": "email", "error": "This email already exist."},
                        {"fieldName": "password", "error": "Please enter a stronger password."},
                    ],
                }
            },
        ),
    }

    PROFILE_UPDATE_ERROR_RESPONSE = openapi.Response(
        description="Bad Request",
        examples={
            "application/json": {
                "message": "One or more validation(s) failed",
                "errors": [{"fieldName": "email", "error": "Invalid email address"}],
            }
        },
    )
