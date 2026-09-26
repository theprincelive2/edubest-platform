"""apps/exams/apps.py"""
from django.apps import AppConfig


class ExamsConfig(AppConfig):
    """AppConfig for the exams app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.exams"
    verbose_name = "Exams"
