"""
apps/academics/serializers.py
==============================
Serializers for all academic models with nested representations.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.academics.models import (
    AcademicYear,
    Class,
    Student,
    StudentParentRelationship,
    Subject,
    Teacher,
    Term,
)

User = get_user_model()


class AcademicYearSerializer(serializers.ModelSerializer):
    """Serializer for academic year CRUD."""

    class Meta:
        model = AcademicYear
        fields = ["id", "name", "start_date", "end_date", "is_current", "created_at"]
        read_only_fields = ["id", "created_at"]


class TermSerializer(serializers.ModelSerializer):
    """Serializer for term management within an academic year."""

    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True)

    class Meta:
        model = Term
        fields = [
            "id", "name", "academic_year", "academic_year_name",
            "start_date", "end_date", "is_current", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for subject listing within a class."""

    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            "id", "name", "code", "class_obj", "teacher",
            "teacher_name", "is_core", "credit_units", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_teacher_name(self, obj: Subject) -> str | None:
        return obj.teacher.get_full_name() if obj.teacher else None


class ClassSerializer(serializers.ModelSerializer):
    """Serializer for class listing with student count."""

    class_teacher_name = serializers.SerializerMethodField()
    student_count = serializers.IntegerField(source="current_student_count", read_only=True)
    subjects = SubjectSerializer(many=True, read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Class
        fields = [
            "id", "name", "section", "full_name", "class_teacher",
            "class_teacher_name", "academic_year", "capacity",
            "student_count", "subjects", "created_at",
        ]
        read_only_fields = ["id", "created_at", "full_name", "student_count"]

    def get_class_teacher_name(self, obj: Class) -> str | None:
        return obj.class_teacher.get_full_name() if obj.class_teacher else None


class TeacherListSerializer(serializers.ModelSerializer):
    """Lightweight teacher serializer for dropdowns."""

    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id", "user", "full_name", "email", "employee_id",
            "qualification", "specialization", "is_active",
        ]
        read_only_fields = fields

    def get_full_name(self, obj: Teacher) -> str:
        return obj.user.get_full_name()


class TeacherDetailSerializer(serializers.ModelSerializer):
    """Full teacher detail serializer."""

    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    avatar = serializers.ImageField(source="user.avatar", read_only=True)

    class Meta:
        model = Teacher
        fields = [
            "id", "user", "full_name", "email", "phone", "avatar",
            "employee_id", "qualification", "specialization",
            "date_joined", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_full_name(self, obj: Teacher) -> str:
        return obj.user.get_full_name()


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight student list serializer."""

    full_name = serializers.SerializerMethodField()
    class_name = serializers.CharField(source="class_obj.full_name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id", "user", "full_name", "admission_number",
            "class_name", "gender", "is_active",
        ]
        read_only_fields = fields

    def get_full_name(self, obj: Student) -> str:
        return obj.user.get_full_name()


class StudentDetailSerializer(serializers.ModelSerializer):
    """Full student detail with guardian info and age."""

    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)
    age = serializers.IntegerField(read_only=True)
    class_name = serializers.CharField(source="class_obj.full_name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id", "user", "full_name", "email", "admission_number",
            "date_of_birth", "age", "gender", "blood_group",
            "address", "photo", "class_obj", "class_name",
            "admission_date", "is_active",
            "guardian_name", "guardian_phone", "guardian_email",
            "guardian_relationship", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "age", "created_at", "updated_at"]

    def get_full_name(self, obj: Student) -> str:
        return obj.user.get_full_name()


class StudentParentRelationshipSerializer(serializers.ModelSerializer):
    """Serializer for student-parent relationships."""

    parent_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentParentRelationship
        fields = [
            "id", "student", "student_name", "parent_user",
            "parent_name", "relationship", "is_primary_contact", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_parent_name(self, obj: StudentParentRelationship) -> str:
        return obj.parent_user.get_full_name()

    def get_student_name(self, obj: StudentParentRelationship) -> str:
        return obj.student.user.get_full_name()
