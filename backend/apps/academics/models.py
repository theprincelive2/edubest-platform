"""
apps/academics/models.py
=========================
Core academic models for a school tenant.

These models live in each tenant's private PostgreSQL schema.
All models inherit AuditableMixin for automatic audit trail.

Model hierarchy:
  AcademicYear → Term → Class → Subject
  AcademicYear → Student (via Class)
  User(Teacher) → Teacher profile → Class.class_teacher
  Student ← StudentParentRelationship → User(Parent)
"""

import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.audit.mixins import AuditableMixin


class AcademicYear(AuditableMixin, models.Model):
    """
    Represents a school/academic year (e.g., 2024/2025).
    Only one academic year can be current at a time (enforced in save()).
    """

    name = models.CharField(
        max_length=20,
        help_text="Academic year label, e.g. '2024/2025'.",
    )
    start_date = models.DateField(help_text="First day of the academic year.")
    end_date = models.DateField(help_text="Last day of the academic year.")
    is_current = models.BooleanField(
        default=False,
        help_text="Only one academic year can be active at a time.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "Academic Year"
        verbose_name_plural = "Academic Years"

    def __str__(self) -> str:
        current = " [CURRENT]" if self.is_current else ""
        return f"{self.name}{current}"

    def save(self, *args, **kwargs) -> None:
        """Ensure only one academic year is marked as current."""
        if self.is_current:
            # Unset is_current on all other academic years
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Term(AuditableMixin, models.Model):
    """
    A term within an academic year (e.g., First Term, Second Term, Third Term).
    Nigerian schools typically have 3 terms per year.
    """

    TERM_CHOICES = [
        ("first", "First Term"),
        ("second", "Second Term"),
        ("third", "Third Term"),
    ]

    name = models.CharField(max_length=10, choices=TERM_CHOICES)
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="terms",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["academic_year", "start_date"]
        verbose_name = "Term"
        verbose_name_plural = "Terms"
        unique_together = [("academic_year", "name")]

    def __str__(self) -> str:
        return f"{self.get_name_display()} — {self.academic_year.name}"

    def save(self, *args, **kwargs) -> None:
        """Ensure only one term is current."""
        if self.is_current:
            Term.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Class(AuditableMixin, models.Model):
    """
    A class/form group within the school (e.g., JSS1A, SS2B).
    Combines a level (e.g., JSS1) with a section (A, B, C...) for uniqueness.
    """

    SECTION_CHOICES = [(s, s) for s in "ABCDEFGH"]

    name = models.CharField(
        max_length=20,
        help_text="Class level, e.g. 'JSS1', 'SS2', 'Primary 4'.",
    )
    section = models.CharField(
        max_length=5,
        choices=SECTION_CHOICES,
        default="A",
        help_text="Class section/stream (A, B, C...).",
    )
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="class_teacher_of",
        limit_choices_to={"role": "teacher"},
        help_text="Primary teacher responsible for this class.",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="classes",
    )
    capacity = models.PositiveIntegerField(
        default=40,
        help_text="Maximum number of students allowed in this class.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "section"]
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        unique_together = [("name", "section", "academic_year")]

    def __str__(self) -> str:
        return f"{self.name}{self.section} ({self.academic_year.name})"

    @property
    def full_name(self) -> str:
        """Human-readable class name."""
        return f"{self.name} {self.section}"

    @property
    def current_student_count(self) -> int:
        """Number of active students currently in this class."""
        return self.students.filter(is_active=True).count()


class Subject(AuditableMixin, models.Model):
    """
    A subject taught in a class (e.g., Mathematics, English Language).
    Subjects are scoped to a specific class to allow different curricula
    per level (e.g., JSS1 has Basic Science but SS3 has Biology).
    """

    name = models.CharField(max_length=100, help_text="Subject name (e.g., 'Mathematics').")
    code = models.CharField(
        max_length=20,
        help_text="Short code for the subject (e.g., 'MATH', 'ENG').",
    )
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="subjects",
        verbose_name="Class",
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subjects_taught",
        limit_choices_to={"role": "teacher"},
        help_text="Teacher assigned to teach this subject.",
    )
    is_core = models.BooleanField(
        default=True,
        help_text="Core subjects are compulsory for all students in this class.",
    )
    credit_units = models.PositiveSmallIntegerField(
        default=1,
        help_text="Credit unit weight for GPA calculation.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        unique_together = [("code", "class_obj")]

    def __str__(self) -> str:
        return f"{self.name} ({self.code}) — {self.class_obj}"


class Teacher(AuditableMixin, models.Model):
    """
    Extended profile for users with role='teacher'.
    Linked OneToOne to User; stores professional/employment details.
    """

    QUALIFICATION_CHOICES = [
        ("nce", "NCE"),
        ("bsc", "B.Sc / B.Ed"),
        ("pgde", "PGDE"),
        ("msc", "M.Sc / M.Ed"),
        ("phd", "Ph.D"),
        ("other", "Other"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        limit_choices_to={"role": "teacher"},
    )
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="School-issued employee ID (e.g., 'TCH-0042').",
    )
    qualification = models.CharField(
        max_length=10,
        choices=QUALIFICATION_CHOICES,
        blank=True,
    )
    specialization = models.CharField(
        max_length=100,
        blank=True,
        help_text="Main subject area or field of expertise.",
    )
    date_joined = models.DateField(
        default=timezone.now,
        help_text="Date the teacher joined the school.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"

    def __str__(self) -> str:
        return f"{self.user.get_full_name()} [{self.employee_id}]"


class Student(AuditableMixin, models.Model):
    """
    Extended profile for users with role='student'.
    Contains academic enrollment details, guardian info, and medical notes.
    """

    GENDER_CHOICES = [("M", "Male"), ("F", "Female")]
    BLOOD_GROUP_CHOICES = [
        ("A+", "A+"), ("A-", "A-"), ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"), ("O+", "O+"), ("O-", "O-"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": "student"},
    )
    admission_number = models.CharField(
        max_length=30,
        unique=True,
        help_text="Unique admission/enrollment number (e.g., 'EDU/2024/001').",
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to="student_photos/", null=True, blank=True)

    # Current class enrollment
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name="Class",
    )
    admission_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive students have graduated, transferred, or been withdrawn.",
    )

    # Guardian details — separate from parent_user (which is the portal account)
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    guardian_email = models.EmailField(blank=True)
    guardian_relationship = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self) -> str:
        return f"{self.user.get_full_name()} [{self.admission_number}]"

    @property
    def age(self) -> int | None:
        """Calculate student's current age in years."""
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        delta = today - self.date_of_birth
        return delta.days // 365


class StudentParentRelationship(AuditableMixin, models.Model):
    """
    Links student profiles to parent user accounts.
    A student can have multiple parent portal accounts
    (e.g., father AND mother both have access).
    """

    RELATIONSHIP_CHOICES = [
        ("father", "Father"),
        ("mother", "Mother"),
        ("guardian", "Guardian"),
        ("sibling", "Sibling"),
        ("other", "Other"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="parent_relationships",
    )
    parent_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="children",
        limit_choices_to={"role": "parent"},
    )
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    is_primary_contact = models.BooleanField(
        default=False,
        help_text="Primary contact receives all school notifications.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["student", "relationship"]
        verbose_name = "Student-Parent Relationship"
        verbose_name_plural = "Student-Parent Relationships"
        unique_together = [("student", "parent_user")]

    def __str__(self) -> str:
        return f"{self.parent_user.get_full_name()} is {self.relationship} of {self.student}"
