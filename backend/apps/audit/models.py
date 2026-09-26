"""
apps/audit/models.py
====================
Audit log infrastructure for the Edubest platform.

Every significant action (CRUD, login, logout) is recorded here.
The AuditLog lives in the SHARED schema so platform admins can
query across tenants, and tenant-scoped queries use the tenant FK.

Design decisions:
- `changes` is a JSONField storing {field: [old_value, new_value]} diffs.
  This avoids a separate AuditChange table and is fast to query for simple use cases.
- `is_sensitive` marks entries that contain PII or financial data,
  allowing stricter access controls on those rows.
- `resource_type` uses dot-notation (e.g., "academics.Student") for
  unambiguous model identification across apps.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditLogManager(models.Manager):
    """
    Custom manager for AuditLog with convenience filtering methods.
    These methods support the audit dashboard and compliance exports.
    """

    def for_tenant(self, schema_name: str) -> models.QuerySet:
        """Return all audit logs for a specific tenant schema."""
        return self.filter(tenant_schema=schema_name)

    def for_user(self, user_id: int) -> models.QuerySet:
        """Return all audit logs created by a specific user."""
        return self.filter(user_id=user_id)

    def for_resource(self, resource_type: str, resource_id: str) -> models.QuerySet:
        """Return audit trail for a specific model instance."""
        return self.filter(resource_type=resource_type, resource_id=resource_id)

    def sensitive(self) -> models.QuerySet:
        """Return only sensitive audit entries (PII, financial)."""
        return self.filter(is_sensitive=True)

    def logins(self) -> models.QuerySet:
        """Return login/logout/failed-login events."""
        return self.filter(action__in=[
            AuditLog.Action.LOGIN,
            AuditLog.Action.LOGOUT,
            AuditLog.Action.FAILED_LOGIN,
        ])


class AuditLog(models.Model):
    """
    Immutable audit trail entry for every significant system event.

    This model is stored in the public schema (shared across all tenants)
    so that platform administrators can perform cross-tenant compliance queries.
    The `tenant_schema` field identifies which school the action belongs to.

    Important: AuditLog rows should NEVER be deleted or updated —
    they are append-only. Enforce this with DB-level triggers in production.
    """

    class Action(models.TextChoices):
        """Enumeration of auditable action types."""
        CREATE = "CREATE", _("Create")
        UPDATE = "UPDATE", _("Update")
        DELETE = "DELETE", _("Delete")
        VIEW = "VIEW", _("View")
        LOGIN = "LOGIN", _("Login")
        LOGOUT = "LOGOUT", _("Logout")
        FAILED_LOGIN = "FAILED_LOGIN", _("Failed Login")
        EXPORT = "EXPORT", _("Export")
        IMPORT = "IMPORT", _("Import")
        PASSWORD_CHANGE = "PASSWORD_CHANGE", _("Password Change")
        PERMISSION_CHANGE = "PERMISSION_CHANGE", _("Permission Change")

    # -----------------------------------------------------------------------
    # Tenant context — which school did this happen in?
    # Using schema_name string (not FK) so logs survive tenant deletion.
    # -----------------------------------------------------------------------
    tenant_schema = models.CharField(
        max_length=63,
        db_index=True,
        help_text="PostgreSQL schema name of the tenant where this action occurred.",
    )

    # -----------------------------------------------------------------------
    # Actor — who did this?
    # Null for system/automated actions (Celery tasks, management commands).
    # SET_NULL so logs survive user deletion.
    # -----------------------------------------------------------------------
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        help_text="User who performed the action. Null for system actions.",
    )
    user_email = models.EmailField(
        blank=True,
        help_text="Snapshot of email at time of action (preserved after user deletion).",
    )

    # -----------------------------------------------------------------------
    # Action details
    # -----------------------------------------------------------------------
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        db_index=True,
    )
    resource_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Dot-notation model label, e.g. 'academics.Student'.",
    )
    resource_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Primary key of the affected record as a string.",
    )
    resource_repr = models.CharField(
        max_length=500,
        blank=True,
        help_text="Human-readable representation of the resource at time of action.",
    )
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Field-level diff: {field_name: [old_value, new_value]}. "
            "Empty for DELETE and VIEW actions."
        ),
    )

    # -----------------------------------------------------------------------
    # Request context — for forensic investigation
    # -----------------------------------------------------------------------
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the client that made the request.",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="HTTP User-Agent header from the request.",
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        help_text="Django session key if session auth was used.",
    )

    # -----------------------------------------------------------------------
    # Metadata
    # -----------------------------------------------------------------------
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="UTC timestamp when the action occurred.",
    )
    is_sensitive = models.BooleanField(
        default=False,
        help_text="True for actions involving PII, financial, or medical data.",
    )
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context-specific metadata (e.g., export format, filter params).",
    )

    objects = AuditLogManager()

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=["tenant_schema", "timestamp"]),
            models.Index(fields=["tenant_schema", "action"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["user", "timestamp"]),
        ]

    def __str__(self) -> str:
        actor = self.user_email or "system"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {actor} {self.action} {self.resource_type}:{self.resource_id}"

    def save(self, *args, **kwargs) -> None:
        """
        Snapshot user email on creation so the record remains useful
        even if the user is later deleted or changes their email.
        """
        if not self.pk and self.user:
            self.user_email = self.user.email
        super().save(*args, **kwargs)
