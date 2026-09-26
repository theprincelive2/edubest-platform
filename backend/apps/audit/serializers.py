"""
apps/audit/serializers.py
==========================
Serializers for the AuditLog model.
"""

from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for AuditLog entries.
    Includes computed display fields for better frontend consumption.
    """

    action_display = serializers.CharField(source="get_action_display", read_only=True)
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id", "tenant_schema", "user", "user_email", "user_display",
            "action", "action_display", "resource_type", "resource_id",
            "resource_repr", "changes", "ip_address", "user_agent",
            "session_key", "timestamp", "is_sensitive", "extra_data",
        ]
        read_only_fields = fields

    def get_user_display(self, obj: AuditLog) -> str:
        """Return user's full name + email, or just the email snapshot."""
        if obj.user:
            return f"{obj.user.get_full_name()} <{obj.user_email}>"
        return obj.user_email or "System"
