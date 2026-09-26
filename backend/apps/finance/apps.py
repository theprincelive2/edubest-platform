"""apps/finance/apps.py"""
from django.apps import AppConfig


class FinanceConfig(AppConfig):
    """AppConfig for the finance app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.finance"
    verbose_name = "Finance"
