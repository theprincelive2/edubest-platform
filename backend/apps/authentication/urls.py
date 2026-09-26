"""
Edubest - Authentication URLs
================================
JWT authentication endpoints.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.authentication.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    TokenVerifyView,
)

urlpatterns = [
    # Login: returns access + refresh tokens
    path("login/", LoginView.as_view(), name="auth-login"),

    # Refresh: exchange refresh token for new access token
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),

    # Verify: check if a token is valid
    path("verify/", TokenVerifyView.as_view(), name="auth-verify"),

    # Logout: blacklist the refresh token
    path("logout/", LogoutView.as_view(), name="auth-logout"),

    # Password reset flow
    path("password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path(
        "password-reset/confirm/<str:uid>/<str:token>/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),

    # Password change (authenticated users)
    path("password-change/", PasswordChangeView.as_view(), name="auth-password-change"),
]
