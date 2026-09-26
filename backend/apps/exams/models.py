"""
apps/exams/models.py
====================
Exam, result, grading, and report card models.

Model hierarchy:
  Exam → ExamSubject → Result
  GradingScale: maps score ranges to letter grades
  ReportCard: aggregated result for a student per exam
"""

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.academics.models import Class, Student, Subject, Term
from apps.audit.mixins import AuditableMixin


class GradingScale(AuditableMixin, models.Model):
    """
    Defines grade letters and their score ranges for the school.
    Each school configures its own grading scale (Nigerian schools vary).
    """

    grade_letter = models.CharField(max_length=3)
    min_score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2)
    gpa_point = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("0.00"))
    remark = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-min_score"]
        verbose_name = "Grading Scale"
        verbose_name_plural = "Grading Scales"

    def __str__(self) -> str:
        return f"{self.grade_letter} ({self.min_score}-{self.max_score}) — {self.remark}"


class Exam(AuditableMixin, models.Model):
    """An examination event within a term."""

    EXAM_TYPE_CHOICES = [
        ("ca", "Continuous Assessment (CA)"),
        ("midterm", "Mid-Term Exam"),
        ("final", "Final / End of Term Exam"),
        ("mock", "Mock Exam"),
        ("entrance", "Entrance Exam"),
    ]

    name = models.CharField(max_length=200)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="exams")
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="exams", verbose_name="Class")
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "Exam"
        verbose_name_plural = "Exams"

    def __str__(self) -> str:
        return f"{self.name} — {self.class_obj} ({self.term})"


class ExamSubject(AuditableMixin, models.Model):
    """A subject within an exam, with its score configuration."""

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="exam_subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="exam_subjects")
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("100.00"))
    pass_score = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("40.00"))
    exam_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["subject__name"]
        verbose_name = "Exam Subject"
        verbose_name_plural = "Exam Subjects"
        unique_together = [("exam", "subject")]

    def __str__(self) -> str:
        return f"{self.subject.name} — {self.exam.name}"


class Result(AuditableMixin, models.Model):
    """A student's score for a specific exam subject. Grade auto-calculated on save."""

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="results")
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name="results")
    score = models.DecimalField(max_digits=6, decimal_places=2)
    grade = models.CharField(max_length=3, blank=True)
    remark = models.CharField(max_length=200, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="recorded_results",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["exam_subject__subject__name", "student__user__last_name"]
        verbose_name = "Result"
        verbose_name_plural = "Results"
        unique_together = [("student", "exam_subject")]

    def __str__(self) -> str:
        return f"{self.student} — {self.exam_subject.subject.name}: {self.score} ({self.grade})"

    def save(self, *args, **kwargs) -> None:
        """Auto-calculate grade from GradingScale before saving."""
        self.grade = self._calculate_grade()
        super().save(*args, **kwargs)

    def _calculate_grade(self) -> str:
        """Look up the appropriate grade letter for the current score."""
        if self.exam_subject.max_score == 0:
            return "N/A"
        percentage = (self.score / self.exam_subject.max_score) * 100
        scale = GradingScale.objects.filter(
            min_score__lte=percentage, max_score__gte=percentage
        ).first()
        return scale.grade_letter if scale else "N/A"

    @property
    def percentage(self) -> Decimal:
        """Score as a percentage of max_score."""
        if self.exam_subject.max_score == 0:
            return Decimal("0.00")
        return (self.score / self.exam_subject.max_score) * 100


class ReportCard(AuditableMixin, models.Model):
    """Aggregated academic report for a student per exam."""

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="report_cards")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="report_cards")
    total_score = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    position = models.PositiveIntegerField(null=True, blank=True)
    teacher_remark = models.TextField(blank=True)
    principal_remark = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to="report_cards/", null=True, blank=True)

    class Meta:
        ordering = ["-generated_at"]
        verbose_name = "Report Card"
        verbose_name_plural = "Report Cards"
        unique_together = [("student", "exam")]

    def __str__(self) -> str:
        return f"Report Card — {self.student} | {self.exam.name}"
