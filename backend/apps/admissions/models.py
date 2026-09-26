"""
Edubest - Admissions Models
=============================
Manages the student application and enrollment process.

Flow:
  1. Applicant submits online form (no authentication required)
  2. Admin reviews application
  3. Admin sets status to "admitted" or "rejected"
  4. On admission: system auto-creates Student + User accounts
  5. Login credentials emailed to parent/guardian
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.audit.mixins import AuditableMixin


class AdmissionApplication(AuditableMixin, models.Model):
    """
    Online admission application submitted by a parent/guardian.

    The application is PUBLICLY accessible — no login required to submit.
    After review, admins can:
      - Admit: creates Student + User accounts automatically
      - Reject: sends rejection email
      - Request more info: sends follow-up email
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        REVIEWING = "reviewing", "Under Review"
        INTERVIEW_SCHEDULED = "interview", "Interview Scheduled"
        ADMITTED = "admitted", "Admitted"
        REJECTED = "rejected", "Rejected"
        WAITLISTED = "waitlisted", "Waitlisted"
        WITHDRAWN = "withdrawn", "Withdrawn"

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    # Auto-generated application reference number
    application_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Unique reference number shared with applicant.",
    )

    # Student information
    applicant_first_name = models.CharField(max_length=100)
    applicant_last_name = models.CharField(max_length=100)
    applicant_other_names = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    nationality = models.CharField(max_length=100, default="Nigerian")
    state_of_origin = models.CharField(max_length=100, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    address = models.TextField()

    # Class applying for
    class_applied = models.ForeignKey(
        "academics.Class",
        on_delete=models.SET_NULL,
        null=True,
        related_name="applications",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.SET_NULL,
        null=True,
        related_name="applications",
    )

    # Previous school
    previous_school_name = models.CharField(max_length=200, blank=True)
    previous_school_address = models.CharField(max_length=500, blank=True)
    last_class_attended = models.CharField(max_length=100, blank=True)

    # Parent/Guardian information
    guardian_name = models.CharField(max_length=200)
    guardian_relationship = models.CharField(
        max_length=50,
        help_text="e.g., Father, Mother, Guardian",
    )
    guardian_phone = models.CharField(max_length=20)
    guardian_email = models.EmailField()
    guardian_address = models.TextField(blank=True)
    guardian_occupation = models.CharField(max_length=200, blank=True)

    # Documents
    birth_certificate = models.FileField(
        upload_to="admissions/documents/%Y/%m/",
        null=True,
        blank=True,
    )
    passport_photo = models.ImageField(
        upload_to="admissions/photos/%Y/%m/",
        null=True,
        blank=True,
    )
    report_card = models.FileField(
        upload_to="admissions/documents/%Y/%m/",
        null=True,
        blank=True,
        help_text="Last school report card.",
    )

    # Application status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_applications",
    )
    review_notes = models.TextField(
        blank=True,
        help_text="Internal notes from the reviewing admin.",
    )
    admission_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date the applicant was officially admitted.",
    )

    # After admission: link to created student
    admitted_student = models.OneToOneField(
        "academics.Student",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admission_application",
    )

    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Admission Application"
        verbose_name_plural = "Admission Applications"

    def __str__(self) -> str:
        return (
            f"APP-{self.application_number} | "
            f"{self.applicant_first_name} {self.applicant_last_name} | "
            f"{self.get_status_display()}"
        )

    def save(self, *args, **kwargs):
        """Auto-generate application number on first save."""
        if not self.application_number:
            year = timezone.now().year
            unique = uuid.uuid4().hex[:6].upper()
            self.application_number = f"{year}-{unique}"
        super().save(*args, **kwargs)

    @property
    def applicant_full_name(self) -> str:
        parts = [self.applicant_first_name]
        if self.applicant_other_names:
            parts.append(self.applicant_other_names)
        parts.append(self.applicant_last_name)
        return " ".join(parts)

    def admit(self, admitted_by, admission_date=None) -> "AdmissionApplication":
        """
        Admit this applicant: set status to admitted and trigger
        student + user account creation via Celery task.
        """
        from apps.admissions.tasks import create_student_from_application

        self.status = self.Status.ADMITTED
        self.reviewed_by = admitted_by
        self.admission_date = admission_date or timezone.now().date()
        self.save(update_fields=["status", "reviewed_by", "admission_date", "updated_at"])

        # Async: create student account and send welcome email
        create_student_from_application.delay(self.pk)

        return self
