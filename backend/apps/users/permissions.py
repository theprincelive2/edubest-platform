"""
apps/users/permissions.py
=========================
Custom DRF permission classes for Edubest RBAC.

Permission design philosophy:
- Broad role checks (IsPrincipal, IsTeacher) are used on ViewSets.
- Fine-grained checks (HasPermission) are used on individual actions.
- IsSameTenant is a safety net ensuring cross-tenant data leakage is impossible.

All permissions inherit from BasePermission and implement has_permission()
and optionally has_object_permission() for object-level security.
"""

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsPlatformAdmin(BasePermission):
    """
    Grants access only to users with the 'platform_admin' role.
    Platform admins manage the entire Edubest SaaS platform:
    creating/suspending tenants, viewing cross-tenant audit logs, etc.
    """

    message = "Access restricted to Edubest platform administrators."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "platform_admin"
        )


class IsSchoolAdmin(BasePermission):
    """
    Grants access to school administrators and above.
    School admins configure school-wide settings, manage users, and view all data.
    Platform admins also pass this check (superusers bypass all checks).
    """

    message = "Access restricted to school administrators."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("platform_admin", "school_admin")
        )


class IsPrincipal(BasePermission):
    """
    Grants access to principals and above.
    Principals have read/write access to academic records and can publish report cards.
    """

    message = "Access restricted to school principals."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("platform_admin", "school_admin", "principal")
        )


class IsTeacher(BasePermission):
    """
    Grants access to teachers and above.
    Teachers can mark attendance, enter results, and view class data.
    """

    message = "Access restricted to teachers."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                "platform_admin", "school_admin", "principal", "teacher"
            )
        )


class IsAccountant(BasePermission):
    """
    Grants access to accountants and above.
    Accountants can create invoices, record payments, and view financial summaries.
    """

    message = "Access restricted to accountants."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                "platform_admin", "school_admin", "principal", "accountant"
            )
        )


class IsReceptionist(BasePermission):
    """
    Grants access to receptionists and above.
    Receptionists handle admissions, visitor logs, and general front-desk operations.
    """

    message = "Access restricted to receptionists."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                "platform_admin", "school_admin", "principal", "receptionist"
            )
        )


class IsParent(BasePermission):
    """
    Grants access to parent portal features.
    Parents can view their children's results, attendance, and invoices.
    """

    message = "Access restricted to parents."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "parent"
        )


class IsStudent(BasePermission):
    """
    Grants access to student portal features.
    Students can view their own results, timetables, and announcements.
    """

    message = "Access restricted to students."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "student"
        )


class IsStaffMember(BasePermission):
    """
    Grants access to any staff member (not parent or student).
    Used as a broad gate for staff-only sections of the portal.
    """

    message = "Access restricted to school staff."

    STAFF_ROLES = (
        "platform_admin", "school_admin", "principal",
        "teacher", "accountant", "receptionist",
    )

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in self.STAFF_ROLES
        )


class HasPermission(BasePermission):
    """
    Fine-grained permission check using the custom permission codename system.

    Usage in ViewSets:
        permission_classes = [HasPermission("can_view_results")]

    The check delegates to User.has_role_permission() which queries
    the UserRoleAssignment → Role → Permission chain.

    Args:
        permission_codename: The codename of the required permission
                             (e.g., 'can_export_pdf', 'can_manage_fees').
    """

    def __init__(self, permission_codename: str) -> None:
        self.permission_codename = permission_codename
        self.message = f"You do not have the '{permission_codename}' permission."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.has_role_permission(self.permission_codename)
        )

    def __call__(self) -> "HasPermission":
        """
        Make HasPermission callable so it can be used in permission_classes list.
        DRF instantiates permission classes from the list, so we return self.
        """
        return self


class IsSameTenant(BasePermission):
    """
    Ensures a user can only access resources within their own tenant schema.

    This is a defence-in-depth check. django-tenants already enforces schema
    isolation at the DB level, but this permission adds an explicit API-level
    check, making intent clear and preventing any accidental cross-schema ops.

    Object-level: compares the object's `tenant_schema` attribute (if present)
    against the current schema set by TenantMainMiddleware.
    """

    message = "You cannot access resources from another school."

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Request-level check: user must be authenticated
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        # Import here to avoid circular imports
        from django_tenants.utils import get_current_schema

        current_schema = get_current_schema()
        obj_schema = getattr(obj, "tenant_schema", None) or getattr(
            getattr(obj, "tenant", None), "schema_name", None
        )

        # If the object doesn't have a tenant attribute, allow access
        # (it might be a shared/public schema object)
        if obj_schema is None:
            return True

        return current_schema == obj_schema


class ReadOnly(BasePermission):
    """
    Allows read-only access (GET, HEAD, OPTIONS) to any authenticated user.
    Useful for endpoints where writes require elevated permissions but reads are open.
    """

    SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.method in self.SAFE_METHODS
        )
