"""
apps/attendance/models.py
=========================
Attendance tracking models.

Two-model design:
- AttendanceSession: represents a single attendance-taking event
  (e.g., JSS1A morning attendance on 2024-09-15)
- AttendanceRecord: one record per student per session with their status

This separation allows:
- Querying "which sessions have been taken?" without fetching all records
- Detecting missing attendance (sessions with no records)
- Supporting different periods (morning, afternoon, full-day)
"""

from django.conf import settings
from django.db import models

from apps.academics.models import Class, Student, Term
from apps.audit.mixins import AuditableMixin


class AttendanceSession(AuditableMixin, models.Model):
    """
    A single attendance-taking event for a class on a specific date and period.
    Prevents duplicate attendance sessions via the unique_together constraint.
    """

    PERIOD_CHOICES = [
        ("morning", "Morning"),
        ("afternoon", "Afternoon"),
        ("full_day", "Full Day"),
    ]

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
        verbose_name="Class",
    )
    date = models.DateField(help_text="Date the attendance was taken.")
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )
    period = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        default="full_day",
    )
    taken_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="attendance_sessions_taken",
        help_text="Teacher who submitted this attendance record.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes about this session.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "class_obj"]
        verbose_name = "Attendance Session"
        verbose_name_plural = "Attendance Sessions"
        unique_together = [("class_obj", "date", "period", "term")]

    def __str__(self) -> str:
        return f"{self.class_obj} | {self.date} | {self.get_period_display()}"

    @property
    def present_count(self) -> int:
        """Count of students marked as present or late in this session."""
        return self.records.filter(status__in=["present", "late"]).count()

    @property
    def absent_count(self) -> int:
        """Count of students marked as absent in this session."""
        return self.records.filter(status="absent").count()


class AttendanceRecord(AuditableMixin, models.Model):
    """
    Individual student attendance record within a session.
    One record per student per session.
    """

    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("excused", "Excused Absence"),
    ]

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="records",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="present",
    )
    remark = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional remark about this attendance entry.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["session", "student__user__last_name"]
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        unique_together = [("session", "student")]

    def __str__(self) -> str:
        return f"{self.student} — {self.get_status_display()} on {self.session.date}"
