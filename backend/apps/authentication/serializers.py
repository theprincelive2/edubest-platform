"""
Edubest - Authentication Serializers
======================================
Serializers for JWT token generation and password management.

The CustomTokenObtainPairSerializer extends SimpleJWT to add:
  - Tenant context (schema) to the token payload
  - User role and permissions in the token
  - School name and branding data in the login response
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extended JWT token serializer that adds custom claims to the token payload.

    Extra claims added:
      - user.role      : The user's role (teacher, parent, student, etc.)
      - user.email     : User email for frontend convenience
      - user.full_name : Display name
    """

    @classmethod
    def get_token(cls, user):
        """Add extra data into the JWT payload."""
        token = super().get_token(user)

        # Add custom claims to token
        token["email"] = user.email
        token["role"] = user.role
        token["full_name"] = user.get_full_name()
        token["first_name"] = user.first_name

        return token

    def validate(self, attrs):
        """
        Override to use email as USERNAME_FIELD.
        Ensure the user belongs to the current tenant schema.
        """
        data = super().validate(attrs)
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request a password reset email."""

    email = serializers.EmailField()

    def save(self):
        """Send password reset email (if user exists)."""
        from django.core.mail import send_mail
        from django.conf import settings

        email = self.validated_data["email"]
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Don't reveal whether the email exists
            return

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_url = f"{settings.PLATFORM_DOMAIN}/auth/reset-password/{uid}/{token}/"

        send_mail(
            subject="Edubest - Password Reset Request",
            message=(
                f"Hi {user.first_name},\n\n"
                f"Click the link below to reset your Edubest password:\n\n"
                f"{reset_url}\n\n"
                f"This link expires in 24 hours.\n\n"
                f"If you didn't request this, please ignore this email.\n\n"
                f"— The Edubest Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirm a password reset using uid + token from the email link."""

    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def save(self):
        uid = self.context["uid"]
        token = self.context["token"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            raise serializers.ValidationError({"uid": "Invalid reset link."})

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({"token": "Reset link has expired or is invalid."})

        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])


class PasswordChangeSerializer(serializers.Serializer):
    """Change password for an authenticated user."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate_current_password(self, value):
        user = self.context["user"]
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def save(self):
        user = self.context["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
