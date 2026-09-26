"""
Edubest - Authentication Views
================================
Handles login, logout, token refresh, and password reset.

Security features:
  - Login attempts are rate-limited (5/min per IP)
  - Failed logins are logged to audit trail
  - JWT tokens include tenant context in claims
  - Logout blacklists the refresh token
"""

import logging

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.audit.models import AuditAction, AuditLog
from apps.authentication.serializers import (
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)
from utils.helpers import get_client_ip

logger = logging.getLogger(__name__)


class LoginRateThrottle(AnonRateThrottle):
    """Strict rate limit for login endpoint: 5 attempts per minute per IP."""
    rate = "5/min"
    scope = "login"


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/

    Authenticate with email + password. Returns JWT access and refresh tokens.
    The access token contains: user_id, email, role, school_schema (tenant).

    Audit trail: logs LOGIN success or FAILED_LOGIN for every attempt.
    """

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError) as exc:
            # Log failed login attempt
            email = request.data.get("email", "unknown")
            self._log_failed_login(request, email)
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "AUTHENTICATION_FAILED",
                        "message": "Invalid email or password.",
                        "details": {},
                    },
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = serializer.user

        # Update last login IP
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=["last_login_ip"])

        # Log successful login
        AuditLog.log(
            action=AuditAction.LOGIN,
            resource_type="User",
            resource_id=str(user.pk),
            resource_repr=str(user),
            user=user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            is_sensitive=True,
        )

        return Response(
            {
                "success": True,
                "data": {
                    "access": serializer.validated_data["access"],
                    "refresh": serializer.validated_data["refresh"],
                    "user": {
                        "id": user.pk,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                        "avatar": user.avatar.url if user.avatar else None,
                    },
                },
            }
        )

    def _log_failed_login(self, request, email: str) -> None:
        """Log a failed login attempt for security monitoring."""
        AuditLog.log(
            action=AuditAction.FAILED_LOGIN,
            resource_type="User",
            resource_id="",
            resource_repr=f"email: {email}",
            user=None,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            is_sensitive=True,
            extra_data={"attempted_email": email},
        )


class LogoutView(generics.GenericAPIView):
    """
    POST /api/v1/auth/logout/

    Blacklist the provided refresh token, effectively logging the user out.
    Requires a valid access token in Authorization header.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"success": False, "error": {"code": "MISSING_FIELD", "message": "Refresh token is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass  # Token might already be expired/blacklisted

        # Audit log
        AuditLog.log(
            action=AuditAction.LOGOUT,
            resource_type="User",
            resource_id=str(request.user.pk),
            resource_repr=str(request.user),
            user=request.user,
            ip_address=get_client_ip(request),
        )

        return Response({"success": True, "message": "Logged out successfully."})


class TokenVerifyView(generics.GenericAPIView):
    """
    POST /api/v1/auth/verify/

    Verify that an access token is valid and return the decoded user info.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({
            "success": True,
            "data": {
                "valid": True,
                "user": {
                    "id": request.user.pk,
                    "email": request.user.email,
                    "role": request.user.role,
                },
            },
        })


class PasswordResetRequestView(generics.GenericAPIView):
    """
    POST /api/v1/auth/password-reset/

    Send a password reset email to the provided email address.
    Always returns 200 (doesn't reveal if email exists).
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "success": True,
            "message": "If this email is registered, a password reset link has been sent.",
        })


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    POST /api/v1/auth/password-reset/confirm/<uid>/<token>/

    Confirm password reset using uid and token from the email link.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, uid, token):
        serializer = self.get_serializer(
            data=request.data,
            context={"uid": uid, "token": token},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"success": True, "message": "Password has been reset successfully."})


class PasswordChangeView(generics.GenericAPIView):
    """
    POST /api/v1/auth/password-change/

    Change password for the currently authenticated user.
    Requires current password for verification.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Audit log
        AuditLog.log(
            action=AuditAction.PASSWORD_CHANGE,
            resource_type="User",
            resource_id=str(request.user.pk),
            resource_repr=str(request.user),
            user=request.user,
            ip_address=get_client_ip(request),
            is_sensitive=True,
        )

        return Response({"success": True, "message": "Password changed successfully."})
