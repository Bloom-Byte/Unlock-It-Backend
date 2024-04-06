from app.models import CustomUser


class ReferralSerializer:

    @staticmethod
    def get_referral_details(user: CustomUser):
        """
        Get the referral details for a given user.

        Parameters:
            user (CustomUser): The user for whom to retrieve the referral details.

        Returns:
            dict: A dictionary containing the referral code and the list of referred users.
        """

        data = {"referral_code": user.referral_code, "referred_users": user.referred_users}

        return data
