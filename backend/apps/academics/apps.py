"""apps/academics/apps.py"""
from django.apps import AppConfig


class AcademicsConfig(AppConfig):
    """AppConfig for the academics app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.academics"
    verbose_name = "Academics"
