"""
apps/users/models.py
====================
Custom User model and role/permission system for Edubest.

Architecture:
- `User` uses email as the login identifier (no username).
- `Role` defines a named set of permissions (e.g., "Teacher", "Principal").
- `Permission` is a fine-grained capability (e.g., "can_mark_attendance").
- `UserRoleAssignment` links users to roles with audit fields (who assigned, when).

Role hierarchy (loosely enforced by permission classes, not by DB constraints):
  platform_admin > school_admin > principal > teacher/accountant/receptionist > parent > student

Why not use Django's built-in Group/Permission?
- Django's system uses content types (model-level), not business-capability permissions.
- We need human-readable permission names per module (e.g., "View Results" in "Exams").
- We want role assignment to be auditable (who assigned this role, when?).
- We want `is_system=True` on built-in roles to prevent accidental deletion.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.audit.mixins import AuditableMixin
from apps.users.managers import UserManager


class Permission(AuditableMixin, models.Model):
    """
    Fine-grained capability permission within a specific module.

    Example:
        codename = "can_view_results"
        name = "Can View Exam Results"
        module = "exams"

    These are created programmatically (via data migrations or a management
    command) — not by end users.
    """

    codename = models.CharField(
        max_length=100,
        unique=True,
        help_text="Machine-readable identifier (e.g., 'can_mark_attendance').",
    )
    name = models.CharField(
        max_length=255,
        help_text="Human-readable name shown in the admin UI.",
    )
    description = models.TextField(
        blank=True,
        help_text="Explanation of what this permission grants.",
    )
    module = models.CharField(
        max_length=50,
        db_index=True,
        help_text="App/module this permission belongs to (e.g., 'exams', 'finance').",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["module", "codename"]
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self) -> str:
        return f"{self.module}.{self.codename}"


class Role(AuditableMixin, models.Model):
    """
    A named role that bundles a set of permissions.

    System roles (is_system=True) are created by data migrations and
    cannot be deleted through the admin or API — they represent the
    built-in role definitions for the platform.
    """

    ROLE_CHOICES = [
        ("platform_admin", "Platform Admin"),
        ("school_admin", "School Admin"),
        ("principal", "Principal"),
        ("teacher", "Teacher"),
        ("accountant", "Accountant"),
        ("receptionist", "Receptionist"),
        ("parent", "Parent"),
        ("student", "Student"),
    ]

    name = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        unique=True,
        help_text="Role identifier matching the User.role field.",
    )
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="roles",
        help_text="Set of fine-grained permissions granted to this role.",
    )
    is_system = models.BooleanField(
        default=False,
        help_text="System roles cannot be modified or deleted via the API.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self) -> str:
        system_marker = " [system]" if self.is_system else ""
        return f"{self.display_name}{system_marker}"

    def has_permission(self, codename: str) -> bool:
        """Check if this role grants the given permission codename."""
        return self.permissions.filter(codename=codename).exists()


class User(AuditableMixin, AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for the Edubest platform.

    Uses email as the unique login identifier. The `role` field stores
    the user's primary system role (used for broad permission checks).
    Fine-grained permissions are handled via `UserRoleAssignment`.

    All users (platform admins, school admins, teachers, students, parents)
    share this single model. Tenant isolation is enforced by django-tenants
    at the database schema level, not by filtering in Python.
    """

    ROLE_CHOICES = [
        ("platform_admin", "Platform Admin"),
        ("school_admin", "School Admin"),
        ("principal", "Principal"),
        ("teacher", "Teacher"),
        ("accountant", "Accountant"),
        ("receptionist", "Receptionist"),
        ("parent", "Parent"),
        ("student", "Student"),
    ]

    # -----------------------------------------------------------------------
    # Identity
    # -----------------------------------------------------------------------
    email = models.EmailField(
        _("email address"),
        unique=True,
        help_text="Primary login identifier. Must be unique across the entire system.",
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact phone number (WhatsApp preferred for notifications).",
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        help_text="Profile photo. Stored in S3 in production.",
    )

    # -----------------------------------------------------------------------
    # Role — used for broad RBAC checks
    # -----------------------------------------------------------------------
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="student",
        db_index=True,
        help_text="Primary role determines the user's capabilities in the system.",
    )

    # -----------------------------------------------------------------------
    # Status
    # -----------------------------------------------------------------------
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text="Inactive users cannot log in. Use instead of deleting accounts.",
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text="Designates whether the user can log into the Django admin site.",
    )

    # -----------------------------------------------------------------------
    # Audit fields
    # -----------------------------------------------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address from the user's most recent successful login.",
    )

    # -----------------------------------------------------------------------
    # Manager & auth config
    # -----------------------------------------------------------------------
    objects = UserManager()

    # Use email as the login identifier
    USERNAME_FIELD = "email"
    # Fields prompted by createsuperuser (besides email + password)
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self) -> str:
        full_name = self.get_full_name()
        return f"{full_name} <{self.email}>" if full_name else self.email

    def get_full_name(self) -> str:
        """Return the first_name plus last_name, with a space in between."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        """Return the short name for the user."""
        return self.first_name

    def has_role_permission(self, codename: str) -> bool:
        """
        Check whether this user has a specific fine-grained permission
        via any of their active role assignments.

        Args:
            codename: The permission codename to check (e.g., 'can_view_results').

        Returns:
            True if any active role assignment grants this permission.
        """
        if self.is_superuser:
            return True
        return self.role_assignments.filter(
            is_active=True,
            role__permissions__codename=codename,
        ).exists()


class UserRoleAssignment(AuditableMixin, models.Model):
    """
    Tracks which roles are assigned to which users.

    Separating role assignment from the User model allows:
    - Full audit trail (who assigned this role and when?)
    - Time-bounded assignments (is_active can be set to False without deleting)
    - Multiple active roles per user if needed in future
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="role_assignments",
        help_text="The user receiving the role.",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,  # Don't cascade-delete roles with assignments
        related_name="user_assignments",
        help_text="The role being assigned.",
    )
    assigned_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="role_assignments_made",
        help_text="User who made this assignment. Null for system-created assignments.",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Set to False to revoke role without deleting the assignment record.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional reason or context for this role assignment.",
    )

    class Meta:
        ordering = ["-assigned_at"]
        verbose_name = "User Role Assignment"
        verbose_name_plural = "User Role Assignments"
        unique_together = [("user", "role")]

    def __str__(self) -> str:
        status = "active" if self.is_active else "revoked"
        return f"{self.user.email} → {self.role.display_name} [{status}]"
