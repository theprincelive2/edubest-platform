"""
apps/academics/views.py
========================
ViewSets for all academic models with role-based access control.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.academics.models import (
    AcademicYear, Class, Student, StudentParentRelationship, Subject, Teacher, Term,
)
from apps.academics.serializers import (
    AcademicYearSerializer, ClassSerializer, StudentDetailSerializer,
    StudentListSerializer, StudentParentRelationshipSerializer,
    SubjectSerializer, TeacherDetailSerializer, TeacherListSerializer, TermSerializer,
)
from apps.users.permissions import IsSchoolAdmin, IsTeacher, IsPrincipal


class AcademicYearViewSet(viewsets.ModelViewSet):
    """CRUD for academic years. School admins and principals manage; others read-only."""
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    filterset_fields = ["is_current"]
    search_fields = ["name"]
    ordering_fields = ["start_date", "name"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsSchoolAdmin()]


class TermViewSet(viewsets.ModelViewSet):
    """CRUD for terms within academic years."""
    queryset = Term.objects.select_related("academic_year").all()
    serializer_class = TermSerializer
    filterset_fields = ["academic_year", "name", "is_current"]
    search_fields = ["name"]
    ordering_fields = ["start_date"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsSchoolAdmin()]


class ClassViewSet(viewsets.ModelViewSet):
    """CRUD for classes. Teachers see their own class; admins see all."""
    queryset = (
        Class.objects.select_related("class_teacher", "academic_year")
        .prefetch_related("subjects", "students")
        .all()
    )
    serializer_class = ClassSerializer
    filterset_fields = ["academic_year", "name", "section"]
    search_fields = ["name", "section"]
    ordering_fields = ["name", "section"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsSchoolAdmin()]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        # Teachers only see classes they are assigned to
        if user.role == "teacher":
            return qs.filter(class_teacher=user)
        return qs


class SubjectViewSet(viewsets.ModelViewSet):
    """CRUD for subjects scoped to a class."""
    queryset = Subject.objects.select_related("class_obj", "teacher").all()
    serializer_class = SubjectSerializer
    filterset_fields = ["class_obj", "is_core", "teacher"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsSchoolAdmin()]


class TeacherViewSet(viewsets.ModelViewSet):
    """CRUD for teacher profiles."""
    queryset = Teacher.objects.select_related("user").all()
    filterset_fields = ["is_active", "qualification"]
    search_fields = ["user__first_name", "user__last_name", "employee_id", "specialization"]
    ordering_fields = ["user__last_name", "date_joined"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsTeacher()]
        return [IsSchoolAdmin()]

    def get_serializer_class(self):
        if self.action == "list":
            return TeacherListSerializer
        return TeacherDetailSerializer


class StudentViewSet(viewsets.ModelViewSet):
    """CRUD for student profiles."""
    queryset = (
        Student.objects.select_related("user", "class_obj")
        .prefetch_related("parent_relationships")
        .all()
    )
    filterset_fields = ["class_obj", "gender", "is_active"]
    search_fields = [
        "user__first_name", "user__last_name", "admission_number",
        "guardian_name", "guardian_phone",
    ]
    ordering_fields = ["user__last_name", "admission_number", "admission_date"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsTeacher()]
        return [IsSchoolAdmin()]

    def get_serializer_class(self):
        if self.action == "list":
            return StudentListSerializer
        return StudentDetailSerializer

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        # Parents only see their own children
        if user.role == "parent":
            return qs.filter(parent_relationships__parent_user=user)
        # Students see only their own profile
        if user.role == "student":
            return qs.filter(user=user)
        # Teachers see students in their classes
        if user.role == "teacher":
            return qs.filter(class_obj__class_teacher=user)
        return qs


class StudentParentRelationshipViewSet(viewsets.ModelViewSet):
    """CRUD for student-parent relationships."""
    queryset = StudentParentRelationship.objects.select_related(
        "student__user", "parent_user"
    ).all()
    serializer_class = StudentParentRelationshipSerializer
    permission_classes = [IsSchoolAdmin]
    filterset_fields = ["student", "parent_user", "relationship"]
    search_fields = ["student__user__last_name", "parent_user__email"]
    ordering_fields = ["created_at"]
