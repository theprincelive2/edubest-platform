"""apps/admissions/apps.py"""
from django.apps import AppConfig


class AdmissionsConfig(AppConfig):
    """AppConfig for the admissions app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admissions"
    verbose_name = "Admissions"
