from django.urls import path

from app.views.auth_views import (
    LoginView,
    SignUpView,
    ChangePasswordView,
    ProfileView,
    ResetPasswordVerifyView,
    ResetPasswordGenerateView,
    ResetPasswordCompleteView,
    GoogleSignUpView,
    FacebookSignUpView,
    FirebaseOauthView,
    ProfileStripeSetupView,
    ProfileStripeExpressLoginView,
    ProfileStripeSetupRefreshView,
    # TODO add delete account later
    # DeleteAccountView,
)
from app.views.download_views import (
    GetStoryDetailsView,
    GetPaymentLinkView,
    StoryDownloadView,
    StripeWebhookView,
)
from app.views.referral_views import ReferralView
from app.views.story_views import StoryView, SingleStoryView
from app.views.transaction_views import TransactionView
from app.views.wallet_views import WalletView


urlpatterns = [
    ######################################### auth paths #########################################
    path("auth/login/", LoginView.as_view(), name="login-view"),
    path("auth/signup/", SignUpView.as_view(), name="sign-up-view"),
    path("auth/signup/google/", GoogleSignUpView.as_view(), name="google-sign-up-view"),
    path("auth/signup/facebook/", FacebookSignUpView.as_view(), name="facebook-sign-up-view"),
    path("auth/signup/oauth/", FirebaseOauthView.as_view(), name="firebase-sign-up-view"),
    path(
        "auth/reset-password-first/",
        ResetPasswordGenerateView.as_view(),
        name="reset-password-first-view",
    ),
    path(
        "auth/reset-password-second/",
        ResetPasswordVerifyView.as_view(),
        name="reset-password-second-view",
    ),
    path(
        "auth/reset-password-third/",
        ResetPasswordCompleteView.as_view(),
        name="reset-password-third-view",
    ),
    ########################################## settings paths #####################################3
    path("settings/profile/", ProfileView.as_view(), name="profile-view"),
    path(
        "settings/profile/stripe-setup/",
        ProfileStripeSetupView.as_view(),
        name="profile-stripe-setup-view",
    ),
    path(
        "settings/profile/stripe-setup/refresh/",
        ProfileStripeSetupRefreshView.as_view(),
        name="profile-stripe-setup-refresh-view",
    ),
    path(
        "settings/profile/stripe-login/",
        ProfileStripeExpressLoginView.as_view(),
        name="profile-stripe-login-view",
    ),
    path("settings/change-password/", ChangePasswordView.as_view(), name="change-password-view"),
    ########################################### story paths ###################################
    path("stories/", StoryView.as_view(), name="story-views"),
    path("stories/<str:story_id>/", SingleStoryView.as_view(), name="single-story-views"),
    ########################################### download paths ####################################
    path("download/story-details/", GetStoryDetailsView.as_view(), name="get-story-details"),
    path("download/payment-link/", GetPaymentLinkView.as_view(), name="get-payment-link"),
    path("download/", StoryDownloadView.as_view(), name="story-download-view"),
    ############################################ webhook paths ####################################
    path("webhook/stripe/", StripeWebhookView.as_view(), name="stripe-webhook-view"),
    ############################################ transaction and wallet paths #############################
    path("transactions/", TransactionView.as_view(), name="transaction-view"),
    path("wallet/", WalletView.as_view(), name="wallet-view"),
    ############################################ referral paths #############################
    path("referral/", ReferralView.as_view(), name="referral-view"),
]
