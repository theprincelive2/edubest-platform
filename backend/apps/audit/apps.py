"""apps/audit/apps.py"""
from django.apps import AppConfig


class AuditConfig(AppConfig):
    """AppConfig for the audit app. Connects signals on ready()."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit"
    verbose_name = "Audit"

    def ready(self) -> None:
        """Connect audit signals when the app is ready."""
        import apps.audit.signals  # noqa: F401
