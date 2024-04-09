from drf_yasg import openapi


class SettingsResponseExamples:
    """This class holds the response examples for the settings endpoints"""

    CHANGE_PASSWORD_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={"application/json": {"message": "Password changed successfully"}},
        ),
        "400": openapi.Response(
            description="Failure",
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

    PROFILE_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Operation completed successfully",
                    "data": {
                        "id": "a879c358-a915-4ebc-9fbe-5634a1d0e812",
                        "username": "String",
                        "email": "user@example.com",
                        "profilePicture": None,
                        "stripeSetupComplete": False,
                    },
                }
            },
        )
    }

    PROFILE_EDIT_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Profile Updated",
                    "data": {
                        "id": "a879c358-a915-4ebc-9fbe-5634a1d0e812",
                        "username": "String",
                        "email": "user@example.com",
                        "profilePicture": None,
                        "stripeSetupComplete": False,
                    },
                }
            },
        ),
        "400": openapi.Response(
            description="Failure",
            examples={
                "application/json": {
                    "message": "One or more validation(s) failed",
                    "errors": [{"fieldName": "email", "error": "Enter a valid email address."}],
                }
            },
        ),
    }

    STRIPE_SETUP_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Operation completed successfully",
                    "data": {
                        "accountLink": "https://connect.stripe.com/setup/e/acct_1P2pnO07FMBQsnSl/pv5JZpy6ANR8"
                    },
                }
            },
        ),
        "400": openapi.Response(
            description="Setup Completed Already",
            examples={
                "application/json": {
                    "message": "Stripe Account Setup Completed Already.",
                }
            },
        ),
    }

    STRIPE_EXPRESS_ACCOUNT_LOGIN_RESPONSE = {
        "200": openapi.Response(
            description="Success",
            examples={
                "application/json": {
                    "message": "Operation completed successfully",
                    "data": {
                        "loginLink": "https://connect.stripe.com/express/acct_1P2ZhTP83XYAyrzG/HzsUHK0ANABY"
                    },
                }
            },
        ),
    }
