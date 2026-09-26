"""
apps/exams/views.py
===================
Exam ViewSets with bulk result entry and PDF report card generation.
"""

import io
import logging
from decimal import Decimal

from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.exams.models import Exam, ExamSubject, GradingScale, ReportCard, Result
from apps.exams.serializers import (
    BulkResultSerializer,
    ExamSerializer,
    ExamSubjectSerializer,
    GradingScaleSerializer,
    ReportCardSerializer,
    ResultSerializer,
)
from apps.users.permissions import IsSchoolAdmin, IsTeacher, IsPrincipal

logger = logging.getLogger(__name__)


class GradingScaleViewSet(viewsets.ModelViewSet):
    """CRUD for the school's grading scale configuration."""
    queryset = GradingScale.objects.all()
    serializer_class = GradingScaleSerializer
    permission_classes = [IsSchoolAdmin]
    ordering_fields = ["min_score"]


class ExamViewSet(viewsets.ModelViewSet):
    """CRUD for exams."""
    queryset = Exam.objects.select_related("term", "class_obj").prefetch_related("exam_subjects__subject").all()
    serializer_class = ExamSerializer
    filterset_fields = ["term", "class_obj", "exam_type", "is_published"]
    search_fields = ["name"]
    ordering_fields = ["start_date", "name"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsTeacher()]
        return [IsSchoolAdmin()]


class ExamSubjectViewSet(viewsets.ModelViewSet):
    """CRUD for exam subjects."""
    queryset = ExamSubject.objects.select_related("exam", "subject").all()
    serializer_class = ExamSubjectSerializer
    filterset_fields = ["exam", "subject"]
    search_fields = ["subject__name"]
    ordering_fields = ["subject__name"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsTeacher()]
        return [IsSchoolAdmin()]


class ResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for result entry, listing, and bulk upload.

    Endpoints:
      GET  /api/v1/results/           — List results (filter by exam, student, class)
      POST /api/v1/results/           — Enter a single result
      POST /api/v1/results/bulk/      — Bulk upload results for an exam subject
    """
    queryset = (
        Result.objects.select_related(
            "student__user", "exam_subject__exam", "exam_subject__subject", "recorded_by"
        ).all()
    )
    serializer_class = ResultSerializer
    filterset_fields = ["student", "exam_subject", "exam_subject__exam"]
    search_fields = [
        "student__user__first_name", "student__user__last_name",
        "student__admission_number",
    ]
    ordering_fields = ["score", "grade", "created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsTeacher()]
        return [IsTeacher()]

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_upload(self, request: Request) -> Response:
        """
        POST /api/v1/results/bulk/
        Bulk enter results for an entire exam subject in one request.
        Uses update_or_create to support re-submission (corrections).
        """
        serializer = BulkResultSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        exam_subject = data["exam_subject"]

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for r in data["results"]:
                obj, created = Result.objects.update_or_create(
                    student=r["student"],
                    exam_subject=exam_subject,
                    defaults={
                        "score": r["score"],
                        "remark": r.get("remark", ""),
                        "recorded_by": request.user,
                    },
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        return Response(
            {
                "detail": "Results saved successfully.",
                "created": created_count,
                "updated": updated_count,
            },
            status=status.HTTP_201_CREATED,
        )


class ReportCardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for report card management and PDF generation.

    Endpoints:
      GET  /api/v1/report-cards/                     — List report cards
      POST /api/v1/report-cards/generate/{exam_id}/  — Generate report cards for all students in exam
      GET  /api/v1/report-cards/{id}/pdf/            — Download PDF
    """
    queryset = ReportCard.objects.select_related("student__user", "exam").all()
    serializer_class = ReportCardSerializer
    filterset_fields = ["student", "exam"]
    search_fields = ["student__user__last_name", "exam__name"]
    ordering_fields = ["position", "average_score", "generated_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsTeacher()]
        return [IsPrincipal()]

    @action(detail=False, methods=["post"], url_path="generate/(?P<exam_id>[^/.]+)")
    def generate_for_exam(self, request: Request, exam_id: int = None) -> Response:
        """
        POST /api/v1/report-cards/generate/{exam_id}/

        Computes and saves ReportCard records for every student in the exam's class.
        Calculates total, average, and assigns class positions.
        """
        try:
            exam = Exam.objects.select_related("class_obj").get(pk=exam_id)
        except Exam.DoesNotExist:
            return Response({"detail": "Exam not found."}, status=status.HTTP_404_NOT_FOUND)

        from apps.academics.models import Student
        students = Student.objects.filter(class_obj=exam.class_obj, is_active=True)

        report_cards_data = []
        with transaction.atomic():
            for student in students:
                results = Result.objects.filter(
                    student=student, exam_subject__exam=exam
                )
                total = sum(r.score for r in results)
                count = results.count()
                average = Decimal(str(total / count)) if count > 0 else Decimal("0.00")

                report_card, _ = ReportCard.objects.update_or_create(
                    student=student,
                    exam=exam,
                    defaults={
                        "total_score": total,
                        "average_score": average,
                    },
                )
                report_cards_data.append((report_card, average))

            # Assign positions based on average score (1 = highest)
            report_cards_data.sort(key=lambda x: x[1], reverse=True)
            for idx, (report_card, _) in enumerate(report_cards_data, start=1):
                report_card.position = idx
                report_card.save(update_fields=["position"])

        return Response(
            {
                "detail": f"Report cards generated for {len(report_cards_data)} students.",
                "exam": exam.name,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="pdf")
    def download_pdf(self, request: Request, pk=None) -> HttpResponse:
        """
        GET /api/v1/report-cards/{id}/pdf/
        Generate and return a PDF report card using ReportLab.
        """
        report_card = self.get_object()
        pdf_content = self._generate_pdf(report_card)

        # Save to model for caching
        filename = f"report_card_{report_card.student.admission_number}_{report_card.exam.pk}.pdf"
        report_card.pdf_file.save(filename, ContentFile(pdf_content), save=True)

        response = HttpResponse(pdf_content, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def _generate_pdf(self, report_card: ReportCard) -> bytes:
        """
        Generate a PDF report card using ReportLab.
        Returns the PDF as bytes.
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        elements = []

        # Header
        student = report_card.student
        exam = report_card.exam
        school_name = "Edubest School"  # TODO: get from tenant

        elements.append(Paragraph(school_name, styles["Title"]))
        elements.append(Paragraph("STUDENT REPORT CARD", styles["Heading2"]))
        elements.append(Spacer(1, 0.5*cm))

        # Student info table
        info_data = [
            ["Student Name:", student.user.get_full_name(), "Admission No:", student.admission_number],
            ["Class:", exam.class_obj.full_name, "Exam:", exam.name],
            ["Term:", str(exam.term), "Position:", str(report_card.position or "—")],
            ["Average:", f"{report_card.average_score:.2f}%", "Total Score:", f"{report_card.total_score:.2f}"],
        ]
        info_table = Table(info_data, colWidths=[4*cm, 6*cm, 4*cm, 3*cm])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("BACKGROUND", (2, 0), (2, -1), colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.5*cm))

        # Results table
        results = Result.objects.filter(
            student=student, exam_subject__exam=exam
        ).select_related("exam_subject__subject")

        result_data = [["Subject", "Score", "Max Score", "Grade", "Remark"]]
        for r in results:
            result_data.append([
                r.exam_subject.subject.name,
                str(r.score),
                str(r.exam_subject.max_score),
                r.grade,
                r.remark or "",
            ])

        results_table = Table(result_data, colWidths=[6*cm, 2.5*cm, 2.5*cm, 2*cm, 4*cm])
        results_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(Paragraph("SUBJECT RESULTS", styles["Heading3"]))
        elements.append(results_table)
        elements.append(Spacer(1, 0.5*cm))

        # Remarks
        if report_card.teacher_remark:
            elements.append(Paragraph(f"<b>Class Teacher's Remark:</b> {report_card.teacher_remark}", styles["Normal"]))
        if report_card.principal_remark:
            elements.append(Paragraph(f"<b>Principal's Remark:</b> {report_card.principal_remark}", styles["Normal"]))

        doc.build(elements)
        return buffer.getvalue()
