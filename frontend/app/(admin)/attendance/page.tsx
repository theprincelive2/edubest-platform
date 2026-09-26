"use client";

/**
 * Attendance Marking Page
 *
 * Features:
 *  - Class selector dropdown
 *  - Date picker (defaults to today)
 *  - Student list with Present / Late / Absent toggle buttons per row
 *  - Bulk "Mark All Present" button
 *  - Submission with loading state
 */

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { CheckCircle2, Clock, XCircle, Users, AlertCircle, Save } from "lucide-react";
import { apiGet } from "@/lib/api";
import { useMarkAttendance } from "@/hooks/useAttendance";
import { PageHeader } from "@/components/ui/PageHeader";
import { Avatar } from "@/components/ui/Avatar";
import { cn } from "@/lib/utils";
import type { Student, Class, AttendanceStatus } from "@/types";

type AttendanceEntry = {
  student_id: string;
  status: AttendanceStatus;
  remark?: string;
};

const STATUS_BUTTONS: { status: AttendanceStatus; label: string; icon: React.ElementType; activeClass: string }[] = [
  { status: "present", label: "Present", icon: CheckCircle2, activeClass: "bg-green-100 text-green-700 border-green-300" },
  { status: "late", label: "Late", icon: Clock, activeClass: "bg-yellow-100 text-yellow-700 border-yellow-300" },
  { status: "absent", label: "Absent", icon: XCircle, activeClass: "bg-red-100 text-red-700 border-red-300" },
];

export default function AttendancePage() {
  const [selectedClass, setSelectedClass] = useState<string>("");
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0],
  );
  const [attendance, setAttendance] = useState<Record<string, AttendanceStatus>>({});

  const markAttendanceMutation = useMarkAttendance();

  /* Fetch classes */
  const { data: classes } = useQuery<{ results: Class[] }>({
    queryKey: ["classes-simple"],
    queryFn: () => apiGet<{ results: Class[] }>("/classes/?page_size=100"),
  });

  /* Fetch students for selected class */
  const { data: students, isLoading: studentsLoading } = useQuery<{ results: Student[] }>({
    queryKey: ["students-by-class", selectedClass],
    queryFn: () =>
      apiGet<{ results: Student[] }>(
        `/students/?current_class=${selectedClass}&status=active&page_size=100`,
      ),
    enabled: !!selectedClass,
  });

  /* Initialise all students as "present" when the list loads */
  useEffect(() => {
    if (students?.results) {
      const initial: Record<string, AttendanceStatus> = {};
      students.results.forEach((s) => { initial[s.id] = "present"; });
      setAttendance(initial);
    }
  }, [students]);

  const markAll = (status: AttendanceStatus) => {
    const updated: Record<string, AttendanceStatus> = {};
    students?.results.forEach((s) => { updated[s.id] = status; });
    setAttendance(updated);
  };

  const markOne = (studentId: string, status: AttendanceStatus) => {
    setAttendance((prev) => ({ ...prev, [studentId]: status }));
  };

  const handleSubmit = async () => {
    if (!selectedClass || !selectedDate) {
      toast.error("Please select a class and date.");
      return;
    }
    if (!students?.results.length) {
      toast.error("No students to mark.");
      return;
    }

    const entries: AttendanceEntry[] = students.results.map((s) => ({
      student_id: s.id,
      status: attendance[s.id] ?? "absent",
    }));

    try {
      await markAttendanceMutation.mutateAsync({
        class_room: selectedClass,
        date: selectedDate,
        records: entries,
      });
      toast.success(`Attendance saved for ${students.results.length} students.`);
    } catch {
      toast.error("Failed to save attendance. Please try again.");
    }
  };

  /* Stats for the current attendance state */
  const presentCount = Object.values(attendance).filter((s) => s === "present").length;
  const lateCount = Object.values(attendance).filter((s) => s === "late").length;
  const absentCount = Object.values(attendance).filter((s) => s === "absent").length;
  const total = students?.results.length ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance"
        subtitle="Mark daily attendance for a class"
      />

      {/* Selector row */}
      <div className="flex flex-col gap-4 rounded-xl border border-gray-100 bg-white p-4 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label className="block text-xs font-medium text-gray-700 mb-1.5">
            Select Class
          </label>
          <select
            value={selectedClass}
            onChange={(e) => setSelectedClass(e.target.value)}
            className="input-field"
          >
            <option value="">— Choose a class —</option>
            {classes?.results.map((cls) => (
              <option key={cls.id} value={cls.id}>{cls.name}</option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <label className="block text-xs font-medium text-gray-700 mb-1.5">
            Date
          </label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            max={new Date().toISOString().split("T")[0]}
            className="input-field"
          />
        </div>
        {selectedClass && total > 0 && (
          <div className="flex gap-2">
            <button
              onClick={() => markAll("present")}
              className="rounded-lg bg-green-50 px-3 py-2 text-xs font-medium text-green-700 hover:bg-green-100 transition-colors"
            >
              All Present
            </button>
            <button
              onClick={() => markAll("absent")}
              className="rounded-lg bg-red-50 px-3 py-2 text-xs font-medium text-red-700 hover:bg-red-100 transition-colors"
            >
              All Absent
            </button>
          </div>
        )}
      </div>

      {/* Stats summary (shown after class is selected) */}
      {selectedClass && total > 0 && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Present", count: presentCount, color: "text-green-700 bg-green-50" },
            { label: "Late", count: lateCount, color: "text-yellow-700 bg-yellow-50" },
            { label: "Absent", count: absentCount, color: "text-red-700 bg-red-50" },
          ].map((item) => (
            <div key={item.label} className={cn("rounded-xl p-4 text-center", item.color)}>
              <p className="text-2xl font-bold">{item.count}</p>
              <p className="text-xs font-medium mt-0.5">{item.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Student list */}
      {!selectedClass ? (
        <div className="rounded-xl border border-gray-100 bg-white p-12 text-center text-gray-400">
          <Users className="mx-auto mb-3 h-10 w-10 text-gray-300" />
          <p>Select a class above to start marking attendance.</p>
        </div>
      ) : studentsLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between rounded-xl border border-gray-100 bg-white p-4">
              <div className="flex items-center gap-3">
                <div className="skeleton h-10 w-10 rounded-full" />
                <div>
                  <div className="skeleton h-4 w-32 mb-1.5" />
                  <div className="skeleton h-3 w-20" />
                </div>
              </div>
              <div className="skeleton h-8 w-48" />
            </div>
          ))}
        </div>
      ) : students?.results.length === 0 ? (
        <div className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-800">
          <AlertCircle className="h-5 w-5" />
          <p className="text-sm">No active students found in this class.</p>
        </div>
      ) : (
        <>
          <div className="rounded-xl border border-gray-100 bg-white overflow-hidden">
            <div className="border-b border-gray-50 px-6 py-3 flex items-center justify-between">
              <p className="text-sm font-medium text-gray-700">
                {students?.results.length} students · {selectedDate}
              </p>
              <p className="text-xs text-gray-400">
                Attendance rate: {total > 0 ? Math.round(((presentCount + lateCount) / total) * 100) : 0}%
              </p>
            </div>

            <div className="divide-y divide-gray-50">
              {students?.results.map((student, index) => {
                const currentStatus = attendance[student.id] ?? "present";
                return (
                  <div
                    key={student.id}
                    className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
                  >
                    {/* Student info */}
                    <div className="flex items-center gap-3">
                      <span className="w-6 text-xs text-gray-400 text-right">{index + 1}</span>
                      <Avatar src={student.photo} name={student.full_name} size="sm" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{student.full_name}</p>
                        <p className="text-xs text-gray-400">{student.admission_number}</p>
                      </div>
                    </div>

                    {/* Status toggle */}
                    <div className="flex items-center gap-1">
                      {STATUS_BUTTONS.map(({ status, label, icon: Icon, activeClass }) => (
                        <button
                          key={status}
                          onClick={() => markOne(student.id, status)}
                          className={cn(
                            "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
                            currentStatus === status
                              ? activeClass
                              : "border-gray-200 bg-white text-gray-500 hover:bg-gray-50",
                          )}
                        >
                          <Icon className="h-3.5 w-3.5" />
                          <span className="hidden sm:inline">{label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Submit button */}
          <div className="flex justify-end">
            <button
              onClick={handleSubmit}
              disabled={markAttendanceMutation.isPending}
              className={cn(
                "flex items-center gap-2 rounded-lg px-6 py-3 text-sm font-semibold text-white transition-colors",
                "bg-primary-700 hover:bg-primary-800",
                markAttendanceMutation.isPending && "opacity-70 cursor-not-allowed",
              )}
            >
              {markAttendanceMutation.isPending ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Saving…
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Save Attendance
                </>
              )}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
