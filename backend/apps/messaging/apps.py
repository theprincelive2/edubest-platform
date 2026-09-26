"""apps/messaging/apps.py"""
from django.apps import AppConfig


class MessagingConfig(AppConfig):
    """AppConfig for the messaging app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.messaging"
    verbose_name = "Messaging"
