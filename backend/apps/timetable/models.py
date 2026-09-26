"""
Edubest - Timetable Models
============================
Manages class timetables (weekly schedule).

Data model:
  - TimetableSlot: One period on one day for one class
  - Links: Class → Subject → Teacher → Room → Day → Time

Validation rules:
  - A teacher cannot be in two places at the same time
  - A class cannot have two subjects at the same time
  - A room cannot be double-booked
"""

from django.conf import settings
from django.db import models

from apps.audit.mixins import AuditableMixin


class Period(models.Model):
    """
    Defines the time slots in a school day.

    Example:
        Period 1: 08:00 - 08:45
        Period 2: 08:45 - 09:30
        Break:    09:30 - 10:00
        Period 3: 10:00 - 10:45
    """

    class PeriodType(models.TextChoices):
        LESSON = "lesson", "Lesson"
        BREAK = "break", "Break"
        LUNCH = "lunch", "Lunch"
        ASSEMBLY = "assembly", "Assembly"

    name = models.CharField(max_length=50, help_text="e.g., 'Period 1', 'Break'")
    period_type = models.CharField(
        max_length=10,
        choices=PeriodType.choices,
        default=PeriodType.LESSON,
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    order = models.PositiveSmallIntegerField(help_text="Sort order for display")

    class Meta:
        ordering = ["order"]
        verbose_name = "Period"
        verbose_name_plural = "Periods"

    def __str__(self) -> str:
        return f"{self.name} ({self.start_time:%H:%M} - {self.end_time:%H:%M})"

    @property
    def duration_minutes(self) -> int:
        """Duration of this period in minutes."""
        from datetime import datetime, date
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        return int((end - start).seconds / 60)


class Room(models.Model):
    """Physical room or venue within the school."""

    name = models.CharField(max_length=100, help_text="e.g., 'Classroom A', 'Science Lab'")
    capacity = models.PositiveSmallIntegerField(null=True, blank=True)
    room_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g., classroom, lab, sports hall",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class TimetableSlot(AuditableMixin, models.Model):
    """
    One entry in the timetable: a class has a subject taught by a teacher
    in a room during a specific period on a specific day.
    """

    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"

    term = models.ForeignKey(
        "academics.Term",
        on_delete=models.PROTECT,
        related_name="timetable_slots",
    )
    class_obj = models.ForeignKey(
        "academics.Class",
        on_delete=models.CASCADE,
        related_name="timetable_slots",
        verbose_name="Class",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.PROTECT,
        related_name="timetable_slots",
    )
    teacher = models.ForeignKey(
        "academics.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timetable_slots",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timetable_slots",
    )
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    period = models.ForeignKey(
        Period,
        on_delete=models.PROTECT,
        related_name="timetable_slots",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["day_of_week", "period__order"]
        verbose_name = "Timetable Slot"
        verbose_name_plural = "Timetable Slots"
        # A class can't have two subjects in the same period on the same day
        unique_together = [["class_obj", "day_of_week", "period", "term"]]

    def __str__(self) -> str:
        day = self.get_day_of_week_display()
        return f"{self.class_obj} | {day} | {self.period} | {self.subject}"

    def clean(self):
        """Validate no scheduling conflicts."""
        from django.core.exceptions import ValidationError

        if self.teacher:
            # Teacher cannot teach two classes at the same time
            conflict = TimetableSlot.objects.filter(
                term=self.term,
                teacher=self.teacher,
                day_of_week=self.day_of_week,
                period=self.period,
                is_active=True,
            ).exclude(pk=self.pk)

            if conflict.exists():
                raise ValidationError(
                    f"Teacher '{self.teacher}' already has a class at this time: "
                    f"{conflict.first()}"
                )

        if self.room:
            # Room cannot be double-booked
            room_conflict = TimetableSlot.objects.filter(
                term=self.term,
                room=self.room,
                day_of_week=self.day_of_week,
                period=self.period,
                is_active=True,
            ).exclude(pk=self.pk)

            if room_conflict.exists():
                raise ValidationError(
                    f"Room '{self.room}' is already booked at this time: "
                    f"{room_conflict.first()}"
                )
