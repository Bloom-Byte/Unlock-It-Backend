from app.models import CustomUser


class ReferralSerializer:

    @staticmethod
    def get_referral_details(user: CustomUser):

        data = {"referral_code": user.referral_code, "referred_users": user.referred_users}

        return data
