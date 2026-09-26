"""
apps/attendance/serializers.py
===============================
Attendance serializers with bulk marking support.
"""

from rest_framework import serializers

from apps.attendance.models import AttendanceRecord, AttendanceSession


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Single student attendance record."""

    student_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            "id", "session", "student", "student_name",
            "status", "status_display", "remark", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_student_name(self, obj: AttendanceRecord) -> str:
        return obj.student.user.get_full_name()


class BulkAttendanceRecordSerializer(serializers.Serializer):
    """
    Nested serializer for a single student's attendance in bulk marking.
    Used within BulkAttendanceSerializer.
    """
    student = serializers.PrimaryKeyRelatedField(
        queryset=__import__("apps.academics.models", fromlist=["Student"]).Student.objects.all()
    )
    status = serializers.ChoiceField(choices=AttendanceRecord.STATUS_CHOICES)
    remark = serializers.CharField(max_length=200, required=False, allow_blank=True)


class BulkAttendanceSerializer(serializers.Serializer):
    """
    Serializer for marking attendance for an entire class in one API call.

    Expected payload:
    {
        "class_obj": 1,
        "date": "2024-09-15",
        "term": 1,
        "period": "full_day",
        "records": [
            {"student": 1, "status": "present"},
            {"student": 2, "status": "absent", "remark": "Sick"},
            ...
        ]
    }
    """
    class_obj = serializers.PrimaryKeyRelatedField(
        queryset=__import__("apps.academics.models", fromlist=["Class"]).Class.objects.all()
    )
    date = serializers.DateField()
    term = serializers.PrimaryKeyRelatedField(
        queryset=__import__("apps.academics.models", fromlist=["Term"]).Term.objects.all()
    )
    period = serializers.ChoiceField(choices=AttendanceSession.PERIOD_CHOICES, default="full_day")
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    records = BulkAttendanceRecordSerializer(many=True)

    def validate_records(self, records: list) -> list:
        if not records:
            raise serializers.ValidationError("At least one attendance record is required.")
        return records


class AttendanceSessionSerializer(serializers.ModelSerializer):
    """Full attendance session with summary stats."""

    records = AttendanceRecordSerializer(many=True, read_only=True)
    present_count = serializers.IntegerField(read_only=True)
    absent_count = serializers.IntegerField(read_only=True)
    class_name = serializers.CharField(source="class_obj.full_name", read_only=True)
    taken_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSession
        fields = [
            "id", "class_obj", "class_name", "date", "term", "period",
            "taken_by", "taken_by_name", "notes", "present_count",
            "absent_count", "records", "created_at",
        ]
        read_only_fields = ["id", "created_at", "present_count", "absent_count"]

    def get_taken_by_name(self, obj: AttendanceSession) -> str | None:
        return obj.taken_by.get_full_name() if obj.taken_by else None


class AttendanceSummarySerializer(serializers.Serializer):
    """
    Read-only serializer for attendance summary statistics.
    Used in the summary dashboard endpoint.
    """
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    admission_number = serializers.CharField()
    total_sessions = serializers.IntegerField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    late = serializers.IntegerField()
    excused = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()
