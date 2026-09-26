"""
apps/attendance/views.py
=========================
Attendance ViewSet with bulk mark_attendance action and summary endpoint.
"""

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.attendance.models import AttendanceRecord, AttendanceSession
from apps.attendance.serializers import (
    AttendanceSessionSerializer,
    AttendanceSummarySerializer,
    BulkAttendanceSerializer,
)
from apps.users.permissions import IsTeacher, IsSchoolAdmin


class AttendanceSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attendance sessions and bulk marking.

    Endpoints:
      GET    /api/v1/attendance/                    — List sessions
      POST   /api/v1/attendance/mark/               — Bulk mark attendance
      GET    /api/v1/attendance/{id}/               — Session detail with records
      GET    /api/v1/attendance/summary/            — Attendance summary stats

    Filtering:
      ?class_obj=1    — filter by class
      ?date=2024-09-15 — filter by date
      ?term=1         — filter by term
    """

    queryset = (
        AttendanceSession.objects.select_related("class_obj", "term", "taken_by")
        .prefetch_related("records__student__user")
        .all()
    )
    serializer_class = AttendanceSessionSerializer
    filterset_fields = ["class_obj", "date", "term", "period"]
    search_fields = ["class_obj__name", "taken_by__first_name", "taken_by__last_name"]
    ordering_fields = ["date", "class_obj"]
    ordering = ["-date"]

    def get_permissions(self):
        if self.action in ("mark_attendance",):
            return [IsTeacher()]
        if self.action in ("list", "retrieve", "summary"):
            return [IsTeacher()]
        return [IsSchoolAdmin()]

    @action(detail=False, methods=["post"], url_path="mark")
    def mark_attendance(self, request: Request) -> Response:
        """
        POST /api/v1/attendance/mark/

        Bulk attendance marking for an entire class.
        Creates or updates an AttendanceSession and all AttendanceRecord entries atomically.

        If a session already exists for the class/date/period, it updates existing records.
        """
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            # Get or create the session
            session, created = AttendanceSession.objects.update_or_create(
                class_obj=data["class_obj"],
                date=data["date"],
                term=data["term"],
                period=data.get("period", "full_day"),
                defaults={
                    "taken_by": request.user,
                    "notes": data.get("notes", ""),
                },
            )

            # Bulk upsert attendance records
            for record_data in data["records"]:
                AttendanceRecord.objects.update_or_create(
                    session=session,
                    student=record_data["student"],
                    defaults={
                        "status": record_data["status"],
                        "remark": record_data.get("remark", ""),
                    },
                )

        action_word = "created" if created else "updated"
        return Response(
            {
                "detail": f"Attendance {action_word} successfully.",
                "session_id": session.pk,
                "records_count": len(data["records"]),
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request: Request) -> Response:
        """
        GET /api/v1/attendance/summary/?class_obj=1&term=1

        Returns per-student attendance summary for a class and term.
        """
        class_id = request.query_params.get("class_obj")
        term_id = request.query_params.get("term")

        if not class_id or not term_id:
            return Response(
                {"detail": "class_obj and term query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.academics.models import Student
        from django.db.models import Count, Q

        students = Student.objects.filter(
            class_obj_id=class_id, is_active=True
        ).select_related("user")

        # Get all sessions for this class and term
        sessions = AttendanceSession.objects.filter(
            class_obj_id=class_id, term_id=term_id
        )
        total_sessions = sessions.count()

        summary_data = []
        for student in students:
            records = AttendanceRecord.objects.filter(
                session__in=sessions,
                student=student,
            )
            counts = records.aggregate(
                present=Count("pk", filter=Q(status="present")),
                absent=Count("pk", filter=Q(status="absent")),
                late=Count("pk", filter=Q(status="late")),
                excused=Count("pk", filter=Q(status="excused")),
            )
            present_total = counts["present"] + counts["late"]
            pct = (present_total / total_sessions * 100) if total_sessions > 0 else 0.0

            summary_data.append({
                "student_id": student.pk,
                "student_name": student.user.get_full_name(),
                "admission_number": student.admission_number,
                "total_sessions": total_sessions,
                "present": counts["present"],
                "absent": counts["absent"],
                "late": counts["late"],
                "excused": counts["excused"],
                "attendance_percentage": round(pct, 2),
            })

        serializer = AttendanceSummarySerializer(summary_data, many=True)
        return Response(serializer.data)
