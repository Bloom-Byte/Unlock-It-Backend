from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class OTPPurposes(TextChoices):
    EMAIL_VERIFICATION = "Email Verification", _("Email Verification")
    PHONE_NUMBER_VERIFICATION = "Phone number Verification", _("Phone number Verification")
    RESET_PASSWORD = "Reset Password", _("Reset Password")
    LOGIN = "Login", _("Login")
    SINGLE_SIGN_IN = "Single Sign In", _("Single Sign In")


class OTPStatuses(TextChoices):
    USED = "Used", _("Used")
    ACTIVE = "Active", _("Active")
    EXPIRED = "Expired", _("Expired")
    INACTIVE = "Inactive", _("Inactive")


class OTPChannels(TextChoices):
    EMAIL = "Email", _("Email")
    SMS = "Sms", _("Sms")


class AccountStatuses(TextChoices):
    ACTIVE = "Active", _("Active")
    INACTIVE = "Inactive", _("Inactive")
    PENDING = "Pending", _("Pending")
    DEACTIVATED = "Deactivated", _("Deactivated")


class TransactionStatuses(TextChoices):
    PENDING = "Pending", _("Pending")
    SUCCESS = "Success", _("Success")
    FAILED = "Failed", _("Failed")
    IN_PROGRESS = "In Progress", _("In Progress")


class TransactionTypes(TextChoices):
    PAYMENT = "Payment", _("Payment")
    WITHDRAWAL = "Withdrawal", _("Withdrawal")


class LinkUsageTypes(TextChoices):
    ONCE = "Once", _("Once")
    MULTIPLE = "Multiple", _("Multiple")
    UNLIMITED = "Unlimited", _("Unlimited")


class APIMessages:
    SUCCESS = "Operation completed successfully"
    FORM_ERROR = "One or more validation(s) failed"
    ACCOUNT_CREATED = "Account created successfully"
    ACCOUNT_SETUP_NOT_COMPLETED = "Account setup not completed"
    ACCOUNT_SETUP_COMPLETED = "Account setup completed"
    ACCOUNT_SETUP_COMPLETED_ALREADY = "Account setup completed already"
    ACCOUNT_DEACTIVATED = (
        "Your account has been deactivated, please reach out to your organization admin"
    )
    ACCOUNT_DELETED = "Your account has been deleted successfully"
    ACCOUNT_BLOCKED = "Your account has been blocked, please see your admin"
    ACCOUNT_PENDING = "Your account has not been activated, please see your admin"
    GOOGLE_OAUTH_ERROR = "Error when signing in with Google"
    FACEBOOK_OAUTH_ERROR = "Error when signing in with Facebook"

    FEEDBACK_MESSAGE = "Your message has been received"

    OTP_SENT = "OTP sent successfully"
    OTP_VERIFIED = "OTP verified successfully"

    PASSWORD_CHANGED = "Password changed successfully"
    PASSWORD_RESET = "Password reset successfully"
    PASSWORD_RESET_LOGGED_IN_ERROR = "You cannot reset password while logged in."
    PASSWORD_RESET_CODE_SENT = "Password reset code sent successfully."
    PASSWORD_RESET_CODE_VERIFIED = "Code verified successfully."
    PASSWORD_CREATE_SUCCESS = "Password created successfully."

    LOGIN_SUCCESS = "Login successful"
    LOGIN_FAILURE = "Invalid login credentials"
    ACCOUNT_LOCKED = (
        "Your account has been locked, please reset your password to unlock your account."
    )

    INVITE_SUCCESS = "User invited successfully"

    TOKEN_REFRESH_FAILURE = "Invalid or expired token"

    PROFILE_UPDATED_SUCCESSFULLY = "Profile Updated"

    FORBIDDEN = "Access denied"
    NOT_FOUND = "Page not found."
    INVALID_QUERY = "Invalid query"

    PAGINATION_PAGE_ERROR = "Page not found"

    # transaction messages
    TRANSACTION_COMPLETED_ALREADY = "Transaction completed already"
    TRANSACTION_NOT_FOUND = "Transaction not found"
    TRANSACTION_SUCCESSFUL = "Transaction Successful"
    TRANSACTION_FAILED = "Transaction Failed"
    TRANSACTION_INITIALIZED = "Transaction initiated successfully"

    STORY_CREATED = "Story created successfully"
    STORY_UPDATED = "Story updated successfully"
    STORY_DELETED = "Story deleted successfully"
    STORY_NOT_FOUND = "Story not found"
    STORY_DELETION_ERROR = "Error when deleting story, please try again"
