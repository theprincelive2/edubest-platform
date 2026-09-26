"""apps/attendance/apps.py"""
from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    """AppConfig for the attendance app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.attendance"
    verbose_name = "Attendance"
