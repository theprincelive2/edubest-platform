"""
Edubest - Master API URL Router (v1)
======================================
All API endpoints are versioned under /api/v1/
Tenant routing is handled by nginx + django-tenants middleware
before requests even reach these URL patterns.

Endpoint organization:
  /api/v1/auth/         - Authentication (login, refresh, logout)
  /api/v1/users/        - User management
  /api/v1/students/     - Student management
  /api/v1/teachers/     - Teacher management
  /api/v1/classes/      - Class management
  /api/v1/subjects/     - Subject management
  /api/v1/timetable/    - Timetable
  /api/v1/attendance/   - Attendance
  /api/v1/exams/        - Exams & Results
  /api/v1/finance/      - Fees, invoices, payments
  /api/v1/messaging/    - Internal messages
  /api/v1/admissions/   - Admission applications
  /api/v1/announcements/- Announcements
  /api/v1/audit/        - Audit logs (admin only)
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.academics.views import (
    AcademicYearViewSet,
    ClassViewSet,
    StudentViewSet,
    SubjectViewSet,
    TeacherViewSet,
    TermViewSet,
)
from apps.admissions.views import AdmissionApplicationViewSet
from apps.announcements.views import AnnouncementViewSet
from apps.attendance.views import AttendanceSessionViewSet, AttendanceRecordViewSet
from apps.audit.views import AuditLogViewSet
from apps.exams.views import ExamViewSet, ResultViewSet, ReportCardViewSet, GradingScaleViewSet
from apps.finance.views import FeeStructureViewSet, InvoiceViewSet, PaymentViewSet
from apps.messaging.views import MessageViewSet, AnnouncementViewSet as MsgAnnouncementViewSet
from apps.timetable.views import TimetableSlotViewSet, PeriodViewSet
from apps.users.views import UserViewSet, RoleViewSet

# Create the DRF router
router = DefaultRouter()

# ---- Users & Auth ----
router.register(r"users", UserViewSet, basename="user")
router.register(r"roles", RoleViewSet, basename="role")

# ---- Academic Management ----
router.register(r"academic-years", AcademicYearViewSet, basename="academic-year")
router.register(r"terms", TermViewSet, basename="term")
router.register(r"classes", ClassViewSet, basename="class")
router.register(r"subjects", SubjectViewSet, basename="subject")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"teachers", TeacherViewSet, basename="teacher")

# ---- Timetable ----
router.register(r"timetable/periods", PeriodViewSet, basename="period")
router.register(r"timetable/slots", TimetableSlotViewSet, basename="timetable-slot")

# ---- Attendance ----
router.register(r"attendance/sessions", AttendanceSessionViewSet, basename="attendance-session")
router.register(r"attendance/records", AttendanceRecordViewSet, basename="attendance-record")

# ---- Exams & Results ----
router.register(r"grading-scales", GradingScaleViewSet, basename="grading-scale")
router.register(r"exams", ExamViewSet, basename="exam")
router.register(r"results", ResultViewSet, basename="result")
router.register(r"report-cards", ReportCardViewSet, basename="report-card")

# ---- Finance ----
router.register(r"finance/fee-structures", FeeStructureViewSet, basename="fee-structure")
router.register(r"finance/invoices", InvoiceViewSet, basename="invoice")
router.register(r"finance/payments", PaymentViewSet, basename="payment")

# ---- Communication ----
router.register(r"messages", MessageViewSet, basename="message")
router.register(r"announcements", AnnouncementViewSet, basename="announcement")

# ---- Admissions ----
router.register(r"admissions", AdmissionApplicationViewSet, basename="admission")

# ---- Audit ----
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    # Auth endpoints (JWT)
    path("auth/", include("apps.authentication.urls")),

    # All resource endpoints via router
    path("", include(router.urls)),
]
