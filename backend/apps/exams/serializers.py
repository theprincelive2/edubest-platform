"""
apps/exams/serializers.py
==========================
Exam, result entry, bulk upload, and report card serializers.
"""

from decimal import Decimal
from rest_framework import serializers

from apps.exams.models import Exam, ExamSubject, GradingScale, ReportCard, Result


class GradingScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingScale
        fields = ["id", "grade_letter", "min_score", "max_score", "gpa_point", "remark"]
        read_only_fields = ["id"]


class ExamSubjectSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)

    class Meta:
        model = ExamSubject
        fields = [
            "id", "exam", "subject", "subject_name", "subject_code",
            "max_score", "pass_score", "exam_date", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ExamSerializer(serializers.ModelSerializer):
    exam_subjects = ExamSubjectSerializer(many=True, read_only=True)
    class_name = serializers.CharField(source="class_obj.full_name", read_only=True)
    exam_type_display = serializers.CharField(source="get_exam_type_display", read_only=True)

    class Meta:
        model = Exam
        fields = [
            "id", "name", "term", "class_obj", "class_name",
            "exam_type", "exam_type_display", "start_date", "end_date",
            "is_published", "exam_subjects", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ResultSerializer(serializers.ModelSerializer):
    """Single result entry serializer."""

    student_name = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source="exam_subject.subject.name", read_only=True)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Result
        fields = [
            "id", "student", "student_name", "exam_subject", "subject_name",
            "score", "grade", "percentage", "remark",
            "recorded_by", "recorded_by_name", "created_at",
        ]
        read_only_fields = ["id", "grade", "percentage", "recorded_by", "created_at"]

    def get_student_name(self, obj: Result) -> str:
        return obj.student.user.get_full_name()

    def get_recorded_by_name(self, obj: Result) -> str | None:
        return obj.recorded_by.get_full_name() if obj.recorded_by else None

    def create(self, validated_data: dict) -> Result:
        """Inject the requesting user as recorded_by."""
        validated_data["recorded_by"] = self.context["request"].user
        return super().create(validated_data)


class BulkResultSerializer(serializers.Serializer):
    """
    Bulk result upload for an entire exam subject.

    Expected payload:
    {
        "exam_subject": 1,
        "results": [
            {"student": 1, "score": 85.0, "remark": "Good effort"},
            {"student": 2, "score": 62.5},
            ...
        ]
    }
    """

    class SingleResultSerializer(serializers.Serializer):
        student = serializers.PrimaryKeyRelatedField(
            queryset=__import__("apps.academics.models", fromlist=["Student"]).Student.objects.all()
        )
        score = serializers.DecimalField(max_digits=6, decimal_places=2)
        remark = serializers.CharField(max_length=200, required=False, allow_blank=True)

    exam_subject = serializers.PrimaryKeyRelatedField(queryset=ExamSubject.objects.all())
    results = SingleResultSerializer(many=True)

    def validate(self, attrs: dict) -> dict:
        """Validate all scores are within the allowed range."""
        exam_subject = attrs["exam_subject"]
        for r in attrs["results"]:
            if r["score"] < 0 or r["score"] > exam_subject.max_score:
                raise serializers.ValidationError(
                    f"Score {r['score']} for student {r['student'].pk} is out of range "
                    f"(0 - {exam_subject.max_score})."
                )
        return attrs


class ReportCardSerializer(serializers.ModelSerializer):
    """Full report card detail with student and exam information."""

    student_name = serializers.SerializerMethodField()
    exam_name = serializers.CharField(source="exam.name", read_only=True)
    class_name = serializers.CharField(source="exam.class_obj.full_name", read_only=True)
    results = serializers.SerializerMethodField()

    class Meta:
        model = ReportCard
        fields = [
            "id", "student", "student_name", "exam", "exam_name",
            "class_name", "total_score", "average_score", "position",
            "teacher_remark", "principal_remark", "pdf_file",
            "generated_at", "results",
        ]
        read_only_fields = [
            "id", "total_score", "average_score", "position",
            "pdf_file", "generated_at",
        ]

    def get_student_name(self, obj: ReportCard) -> str:
        return obj.student.user.get_full_name()

    def get_results(self, obj: ReportCard) -> list[dict]:
        """Return all result entries for this student in this exam."""
        results = Result.objects.filter(
            student=obj.student,
            exam_subject__exam=obj.exam,
        ).select_related("exam_subject__subject")
        return [
            {
                "subject": r.exam_subject.subject.name,
                "score": str(r.score),
                "max_score": str(r.exam_subject.max_score),
                "grade": r.grade,
                "percentage": str(r.percentage),
            }
            for r in results
        ]
