"""
apps/users/views.py
===================
ViewSets for user management, role management, and profile operations.

Endpoint overview:
  GET/POST     /api/v1/users/          — List and create users (school_admin+)
  GET/PUT/PATCH /api/v1/users/{id}/   — Retrieve/update user (school_admin or self)
  POST          /api/v1/users/{id}/change_password/ — Change own password
  GET           /api/v1/users/me/     — Current user's profile
  GET/POST     /api/v1/roles/          — Manage roles (school_admin+)
  GET/POST     /api/v1/role-assignments/ — Assign roles to users (school_admin+)
"""

from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.users.models import Permission, Role, UserRoleAssignment
from apps.users.permissions import IsSchoolAdmin, IsPlatformAdmin
from apps.users.serializers import (
    PasswordChangeSerializer,
    PermissionSerializer,
    RoleSerializer,
    UserDetailSerializer,
    UserListSerializer,
    UserProfileUpdateSerializer,
    UserRegistrationSerializer,
    UserRoleAssignmentSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for User management.

    - School admins can manage all users in their tenant schema.
    - Regular users can only read their own profile (via /me/).
    - All writes are audit-logged.

    Filtering:
      ?role=teacher         — filter by role
      ?is_active=true       — filter by active status
      ?search=John          — search by name or email
    """

    queryset = User.objects.all().order_by("last_name", "first_name")
    filterset_fields = ["role", "is_active"]
    search_fields = ["email", "first_name", "last_name", "phone"]
    ordering_fields = ["last_name", "first_name", "created_at", "role"]

    def get_permissions(self):
        """
        Granular permission assignment per action.
        - list/retrieve/create/update/destroy: school_admin+
        - me/change_password: authenticated user (self)
        """
        if self.action in ("me", "change_password"):
            return [IsAuthenticated()]
        return [IsSchoolAdmin()]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return UserListSerializer
        if self.action == "create":
            return UserRegistrationSerializer
        if self.action in ("update", "partial_update"):
            # Admins use detail serializer; users use profile serializer
            if self.get_object() == self.request.user:
                return UserProfileUpdateSerializer
            return UserDetailSerializer
        if self.action == "change_password":
            return PasswordChangeSerializer
        return UserDetailSerializer

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request: Request) -> Response:
        """
        GET  /api/v1/users/me/ — Return the authenticated user's profile.
        PATCH /api/v1/users/me/ — Update own profile (name, phone, avatar).
        """
        user = request.user
        if request.method == "GET":
            serializer = UserDetailSerializer(user, context={"request": request})
            return Response(serializer.data)

        # PATCH
        serializer = UserProfileUpdateSerializer(
            user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserDetailSerializer(user, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="change-password")
    def change_password(self, request: Request, pk=None) -> Response:
        """
        POST /api/v1/users/{id}/change-password/
        Allows a user to change their own password by providing the current one.
        """
        # Security: ensure user can only change their own password
        user = self.get_object()
        if user != request.user and not request.user.role in ("platform_admin", "school_admin"):
            return Response(
                {"detail": "You can only change your own password."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Log password change in audit log
        AuditLog.objects.create(
            tenant_schema=request.tenant.schema_name if hasattr(request, "tenant") else "public",
            user=request.user,
            action=AuditLog.Action.PASSWORD_CHANGE,
            resource_type="users.User",
            resource_id=str(user.pk),
            resource_repr=str(user),
            ip_address=getattr(request, "audit_ip", None),
            user_agent=getattr(request, "audit_user_agent", ""),
        )

        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request: Request, pk=None) -> Response:
        """
        POST /api/v1/users/{id}/deactivate/
        Deactivate a user account (soft delete — preserves all data).
        """
        user = self.get_object()
        if user == request.user:
            return Response(
                {"detail": "You cannot deactivate your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return Response({"detail": f"User {user.email} has been deactivated."})


class RoleViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Role management.

    System roles (is_system=True) are read-only via the API.
    School admins can create custom roles with any combination of permissions.

    Filtering:
      ?is_system=true  — show only system roles
      ?search=Teacher  — search by name or description
    """

    queryset = Role.objects.prefetch_related("permissions").all()
    serializer_class = RoleSerializer
    permission_classes = [IsSchoolAdmin]
    filterset_fields = ["is_system", "name"]
    search_fields = ["name", "display_name", "description"]
    ordering_fields = ["name", "created_at"]

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Prevent deletion of system roles."""
        role = self.get_object()
        if role.is_system:
            return Response(
                {"detail": "System roles cannot be deleted."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for listing available permissions.
    Used by the admin UI to build role configuration screens.

    Filtering:
      ?module=exams   — filter permissions by module
      ?search=result  — search by name or codename
    """

    queryset = Permission.objects.all().order_by("module", "codename")
    serializer_class = PermissionSerializer
    permission_classes = [IsSchoolAdmin]
    filterset_fields = ["module"]
    search_fields = ["codename", "name", "description"]


class UserRoleAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for assigning and revoking roles from users.

    School admins can:
    - GET    /api/v1/role-assignments/         — List all assignments in tenant
    - POST   /api/v1/role-assignments/         — Assign a role to a user
    - PATCH  /api/v1/role-assignments/{id}/    — Update assignment (e.g., deactivate)
    - DELETE /api/v1/role-assignments/{id}/    — Remove assignment

    Filtering:
      ?user=123        — filter by user ID
      ?role=1          — filter by role ID
      ?is_active=true  — filter by active status
    """

    queryset = (
        UserRoleAssignment.objects.select_related("user", "role", "assigned_by")
        .all()
        .order_by("-assigned_at")
    )
    serializer_class = UserRoleAssignmentSerializer
    permission_classes = [IsSchoolAdmin]
    filterset_fields = ["user", "role", "is_active"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    ordering_fields = ["assigned_at", "is_active"]
