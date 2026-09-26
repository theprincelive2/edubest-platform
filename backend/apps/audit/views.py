"""
apps/audit/views.py
===================
Read-only ViewSet for audit log access.
Only school admins and principals can view audit logs for their tenant.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.users.permissions import IsSchoolAdmin, IsPrincipal


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for browsing audit logs.

    Filtering:
      ?action=LOGIN               — filter by action type
      ?resource_type=users.User   — filter by resource model
      ?user=123                   — filter by user ID
      ?is_sensitive=true          — show only sensitive entries
      ?search=<query>             — search in resource_repr, user_email

    Ordering:
      ?ordering=-timestamp        — newest first (default)
      ?ordering=action            — alphabetical by action
    """

    serializer_class = AuditLogSerializer
    filterset_fields = ["action", "resource_type", "user", "is_sensitive", "tenant_schema"]
    search_fields = ["resource_repr", "user_email", "resource_id", "ip_address"]
    ordering_fields = ["timestamp", "action", "resource_type"]
    ordering = ["-timestamp"]

    def get_permissions(self):
        """School admins and principals can view audit logs."""
        return [IsSchoolAdmin() or IsPrincipal()]

    def get_queryset(self):
        """
        Filter audit logs to the current tenant schema.
        Platform admins can see all schemas by passing ?tenant_schema=<name>.
        """
        from django_tenants.utils import get_current_schema
        user = self.request.user

        # Platform admins can query across tenants
        if user.role == "platform_admin":
            return AuditLog.objects.all()

        # Other admins only see their own tenant's logs
        current_schema = get_current_schema()
        return AuditLog.objects.filter(tenant_schema=current_schema)
