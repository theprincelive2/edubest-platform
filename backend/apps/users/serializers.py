"""
apps/users/serializers.py
=========================
DRF serializers for user registration, profile, roles, and authentication.

Key decisions:
- `CustomTokenObtainPairSerializer` adds `role` and `full_name` to the JWT
  payload so the frontend can gate UI elements without an extra API call.
- `UserRegistrationSerializer` validates password complexity and uniqueness.
- `RoleAssignmentSerializer` records `assigned_by` from `request.user`.
- `PasswordChangeSerializer` requires both old and new passwords for security.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import Permission, Role, UserRoleAssignment

User = get_user_model()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends SimpleJWT's default serializer to include user context
    in the token payload and the response body.

    The extra payload claims allow the frontend to:
    - Display the user's name without an extra /me API call
    - Gate menu items based on role
    - Identify the current tenant (school)
    """

    @classmethod
    def get_token(cls, user: User) -> RefreshToken:  # type: ignore[override]
        """Add custom claims to the JWT payload."""
        token = super().get_token(user)
        # Claims embedded in the token — readable by the frontend
        token["email"] = user.email
        token["full_name"] = user.get_full_name()
        token["role"] = user.role
        token["is_staff"] = user.is_staff
        return token

    def validate(self, attrs: dict) -> dict:
        """Add additional fields to the response body (not the token)."""
        data = super().validate(attrs)
        user = self.user
        data["user"] = {
            "id": user.pk,
            "email": user.email,
            "full_name": user.get_full_name(),
            "role": user.role,
            "avatar": user.avatar.url if user.avatar else None,
        }
        return data


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new user account.
    Validates password complexity and ensures email uniqueness.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="Must be at least 8 characters and not a common password.",
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="Must match the password field.",
    )

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "phone", "role", "password", "password_confirm",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "role": {"required": False},
        }

    def validate_email(self, value: str) -> str:
        """Normalize and check email uniqueness."""
        normalized = value.lower().strip()
        if User.objects.filter(email=normalized).exists():
            raise serializers.ValidationError(
                "A user with this email address already exists."
            )
        return normalized

    def validate(self, attrs: dict) -> dict:
        """Cross-field validation: passwords must match and pass Django validators."""
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        # Run Django's built-in password validators
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data: dict) -> User:
        """Create the user using the custom manager (handles password hashing)."""
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing users (no sensitive data)."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "first_name", "last_name",
            "phone", "role", "is_active", "created_at",
        ]
        read_only_fields = fields

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name()


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Full user detail serializer including avatar and last login IP.
    Used for GET /users/{id}/ by admins.
    """

    full_name = serializers.SerializerMethodField()
    active_roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "first_name", "last_name",
            "phone", "role", "avatar", "is_active", "is_staff",
            "last_login_ip", "created_at", "updated_at", "active_roles",
        ]
        read_only_fields = ["id", "email", "last_login_ip", "created_at", "updated_at"]

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name()

    def get_active_roles(self, obj: User) -> list[dict]:
        """Return the user's currently active role assignments."""
        assignments = obj.role_assignments.filter(is_active=True).select_related("role")
        return [
            {
                "role_name": a.role.name,
                "display_name": a.role.display_name,
                "assigned_at": a.assigned_at,
            }
            for a in assignments
        ]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Allows users to update their own profile.
    Email and role changes are NOT allowed via this serializer —
    those require admin action via UserDetailSerializer.
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "avatar"]


class PasswordChangeSerializer(serializers.Serializer):
    """
    Validates old password and sets a new one.
    Requires the user to know their current password — prevents
    account takeover if a session is hijacked.
    """

    old_password = serializers.CharField(
        required=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        required=True,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={"input_type": "password"},
    )

    def validate_old_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        validate_password(attrs["new_password"], user=self.context["request"].user)
        return attrs

    def save(self, **kwargs) -> None:
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])


# ---------------------------------------------------------------------------
# Roles & Permissions
# ---------------------------------------------------------------------------

class PermissionSerializer(serializers.ModelSerializer):
    """Read-only serializer for Permission model."""

    class Meta:
        model = Permission
        fields = ["id", "codename", "name", "description", "module"]
        read_only_fields = fields


class RoleSerializer(serializers.ModelSerializer):
    """Full role detail with embedded permissions list."""

    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        source="permissions",
        required=False,
    )

    class Meta:
        model = Role
        fields = [
            "id", "name", "display_name", "description",
            "permissions", "permission_ids", "is_system",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        """Prevent modification of system roles."""
        if self.instance and self.instance.is_system:
            raise serializers.ValidationError(
                "System roles cannot be modified. Create a custom role instead."
            )
        return attrs


class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for assigning/revoking roles.
    `assigned_by` is automatically set to the requesting user.
    """

    role_name = serializers.CharField(source="role.display_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    assigned_by_email = serializers.EmailField(source="assigned_by.email", read_only=True)

    class Meta:
        model = UserRoleAssignment
        fields = [
            "id", "user", "user_email", "role", "role_name",
            "assigned_by", "assigned_by_email", "assigned_at",
            "is_active", "notes",
        ]
        read_only_fields = ["id", "assigned_by", "assigned_at", "role_name", "user_email", "assigned_by_email"]

    def create(self, validated_data: dict) -> UserRoleAssignment:
        """Inject the requesting user as assigned_by."""
        validated_data["assigned_by"] = self.context["request"].user
        return super().create(validated_data)
