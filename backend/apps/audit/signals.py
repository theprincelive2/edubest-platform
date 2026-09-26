"""
apps/audit/signals.py
=====================
Django signals that auto-create AuditLog entries on model save/delete.

These signals complement the AuditableMixin:
- Mixin captures state snapshots in memory
- Signals read those snapshots and write to AuditLog

Why use both signals AND the mixin?
- The mixin ensures state is captured even when signals are not connected.
- Signals keep audit writing logic separate from business logic.
- The combination allows QuerySet.bulk_create/update to be detected
  (though we add explicit audit calls for bulk operations in views).

Signal handlers are connected in apps/audit/apps.py via ready().
"""

import logging
from typing import Any, Type

from django.db.models import Model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.audit.middleware import _thread_local
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)

# Models to EXCLUDE from auto-audit logging (to prevent infinite loops
# and to skip low-value/high-volume models like sessions)
EXCLUDED_MODELS = {
    "AuditLog",           # Don't audit the audit log itself
    "Session",            # Too high volume
    "LogEntry",           # Django admin's own log
    "TokenBlacklist",     # SimpleJWT internals
    "OutstandingToken",   # SimpleJWT internals
}


def _get_tenant_schema() -> str:
    """Get the current tenant schema from thread-local or django-tenants context."""
    try:
        from django_tenants.utils import get_current_schema
        schema = get_current_schema()
        return schema or "public"
    except Exception:
        return "public"


def _get_request_context() -> dict[str, Any]:
    """Extract IP and user agent from the current request context."""
    return {
        "ip_address": getattr(_thread_local, "ip_address", None),
        "user_agent": getattr(_thread_local, "user_agent", ""),
    }


def _get_current_user() -> Any | None:
    """Get the authenticated user from the current request."""
    request = getattr(_thread_local, "request", None)
    if request and hasattr(request, "user") and request.user.is_authenticated:
        return request.user
    return None


def _compute_changes(
    pre_state: dict[str, Any] | None,
    post_state: dict[str, Any] | None,
) -> dict[str, list]:
    """
    Compute field-level diff between pre and post save states.

    Args:
        pre_state: Field values before save (None for new records).
        post_state: Field values after save.

    Returns:
        Dict of {field_name: [old_value, new_value]} for changed fields only.
    """
    if not pre_state or not post_state:
        return {}

    changes: dict[str, list] = {}
    all_fields = set(pre_state.keys()) | set(post_state.keys())

    for field in all_fields:
        old_val = pre_state.get(field)
        new_val = post_state.get(field)
        if str(old_val) != str(new_val):  # Use string comparison for safety
            changes[field] = [str(old_val), str(new_val)]

    return changes


@receiver(post_save)
def audit_post_save(
    sender: Type[Model],
    instance: Model,
    created: bool,
    **kwargs: Any,
) -> None:
    """
    Signal handler: create AuditLog entry after any model save.

    Skips:
    - Excluded model types (AuditLog itself, sessions, etc.)
    - Models that don't have the AuditableMixin state attributes
      (prevents double-logging from non-auditable models)
    """
    # Skip excluded models
    model_name = sender.__name__
    if model_name in EXCLUDED_MODELS:
        return

    # Only auto-log models that use AuditableMixin (they have _pre_save_state)
    if not hasattr(instance, "_post_save_state"):
        return

    try:
        action = AuditLog.Action.CREATE if created else AuditLog.Action.UPDATE
        pre_state = getattr(instance, "_pre_save_state", None)
        post_state = getattr(instance, "_post_save_state", None)
        changes = _compute_changes(pre_state, post_state) if not created else {}

        context = _get_request_context()
        user = _get_current_user()
        schema = _get_tenant_schema()

        AuditLog.objects.create(
            tenant_schema=schema,
            user=user,
            action=action,
            resource_type=f"{sender._meta.app_label}.{model_name}",
            resource_id=str(instance.pk),
            resource_repr=str(instance)[:500],
            changes=changes,
            ip_address=context["ip_address"],
            user_agent=context["user_agent"],
        )
    except Exception as exc:
        # NEVER let audit logging break the main application flow
        logger.error("Failed to write audit log (post_save): %s", exc, exc_info=True)


@receiver(post_delete)
def audit_post_delete(
    sender: Type[Model],
    instance: Model,
    **kwargs: Any,
) -> None:
    """
    Signal handler: create AuditLog entry after any model deletion.
    Records the final state of the object before it was deleted.
    """
    model_name = sender.__name__
    if model_name in EXCLUDED_MODELS:
        return

    if not hasattr(instance, "_pre_delete_state"):
        return

    try:
        pre_state = getattr(instance, "_pre_delete_state", {})
        context = _get_request_context()
        user = _get_current_user()
        schema = _get_tenant_schema()

        AuditLog.objects.create(
            tenant_schema=schema,
            user=user,
            action=AuditLog.Action.DELETE,
            resource_type=f"{sender._meta.app_label}.{model_name}",
            resource_id=str(instance.pk),
            resource_repr=str(instance)[:500],
            changes={"deleted_state": [str(pre_state), ""]},
            ip_address=context["ip_address"],
            user_agent=context["user_agent"],
        )
    except Exception as exc:
        logger.error("Failed to write audit log (post_delete): %s", exc, exc_info=True)
