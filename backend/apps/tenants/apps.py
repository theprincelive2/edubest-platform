"""apps/tenants/apps.py"""
from django.apps import AppConfig


class TenantsConfig(AppConfig):
    """AppConfig for the tenants app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tenants"
    verbose_name = "Tenants"
