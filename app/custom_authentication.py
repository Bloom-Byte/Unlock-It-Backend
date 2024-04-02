from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.conf import settings


from app.enum_classes import AccountStatuses
from app.models import CustomUser


class CustomAuthenticationBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user with the given username and password.

        Args:
            request: The request object.
            username: The username of the user.
            password: The password of the user.
            kwargs: Additional keyword arguments.

        Returns:
            The authenticated user if successful, otherwise None.

        """
        user_model = get_user_model()

        user: CustomUser = user_model.objects.filter(email=username.lower().strip()).first()

        if user:
            # Check if password is correct or user is already deactivated
            if user.check_password(password):  # or user.status == AccountStatuses.INACTIVE:
                if user.login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                    self.deactivate_user(user)
                else:
                    self.reset_login_attempts(user)

                return user

            self.increment_login_attempts(user)
            return None

        return None

    def deactivate_user(self, user: CustomUser):
        """
        Deactivates a user by setting their account status to INACTIVE.

        Args:
            user (CustomUser): The user object to be deactivated.

        Returns:
            None
        """

        user.account_status = AccountStatuses.INACTIVE
        user.save()

    def reset_login_attempts(self, user: CustomUser):
        """
        Reset the login attempts for a given user.

        Parameters:
            user (CustomUser): The user for whom the login attempts will be reset.

        Returns:
            None
        """
        user.login_attempts = 0
        user.save()

    def increment_login_attempts(self, user: CustomUser):
        """
        Increments the login attempts of a user and saves the updated user object.

        Args:
            user (CustomUser): The user object whose login attempts will be incremented.

        Returns:
            None
        """
        user.login_attempts += 1
        user.save()
