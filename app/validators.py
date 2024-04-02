import re

from rest_framework import serializers

from django.contrib.auth import get_user_model

USER_MODEL = get_user_model()


def phone_number_serializer_validator(value: str):
    """
    Validate the given phone number value.

    Args:
        value (str): The phone number to be validated.

    Raises:
        serializers.ValidationError: If the phone number is not 11 digits, does not start with '0', or contains non-numeric characters.
    """
    if len(value) != 11:
        raise serializers.ValidationError("Please enter a valid phone number.")

    if not value.startswith("0"):
        raise serializers.ValidationError("Please enter a valid phone number.")

    if not value.isnumeric():
        raise serializers.ValidationError("Please enter a valid phone number.")


# def phone_number_bool_validator(value: str):
#     if len(value) != 14:
#         return False

#     if not value.replace("+", "").isnumeric():
#         return False

#     return True


# def phone_number_exist_checker(value: str):
#     if not USER_MODEL.objects.filter(phone_number=value).exists():
#         raise serializers.ValidationError("Phone number does not exist.")


def email_exist_checker(value):
    """
    Check if the given email exists in the user model.

    Args:
        value (str): The email address to be checked.

    Raises:
        serializers.ValidationError: If the email address is invalid.
    """
    if not USER_MODEL.objects.filter(email=value.lower()).exists():
        raise serializers.ValidationError("Invalid email address")


def phone_number_not_exist_checker(value: str):
    """
    A function that checks if a phone number already exists in the user model.

    Parameters:
        value (str): The phone number to check.

    Raises:
        serializers.ValidationError: If the phone number already exists.

    """
    if USER_MODEL.objects.filter(phone_number=value).exists():
        raise serializers.ValidationError("Phone number already exist.")


def email_not_exist_checker(value):
    """
    A function that checks if the email does not already exist in the USER_MODEL database.

    Parameter:
        value: str - the email address to check.

    """
    if USER_MODEL.objects.filter(email=value.lower()).exists():
        raise serializers.ValidationError("This email already exist.")


# def organization_industry_checker(value):
#     if not OrganizationIndustry.objects.filter(id=value).exists():
#         raise serializers.ValidationError("Invalid industry")


# def email_serializer_verification(email):
#     regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

#     if not bool(re.fullmatch(regex, email)):
#         raise serializers.ValidationError("Invalid email address.")


# def email_bool_verification(email):
#     regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

#     if not bool(re.fullmatch(regex, email)):
#         return False

#     return True


def password_validator(value: str):
    """
    Validate the given password value.

    Args:
        value (str): The password to be validated.

    Raises:
        serializers.ValidationError: If the password is not strong enough.

    Returns:
        None
    """
    reg = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d!@#$%^&*()\-_=+{};:,<.>?]{8,20}$"

    # compiling regex
    pat = re.compile(reg)

    # searching regex
    mat = re.search(pat, value)
    if not mat:
        raise serializers.ValidationError("Please enter a stronger password.")


def base64_file_validator(value: str):
    """
    A function that validates a base64 file value.

    Parameters:
    value (str): The base64 file value to be validated.

    Raises:
    serializers.ValidationError: If the file is not valid.
    """
    try:
        _ = value.split("base64")[0]
        _ = value.split("base64")[1][1:]
    except Exception:
        raise serializers.ValidationError("Please upload a valid file.")
