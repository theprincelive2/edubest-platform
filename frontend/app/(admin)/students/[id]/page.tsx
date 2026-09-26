"use client";

/**
 * Student Detail Page
 *
 * Tabbed view of a single student's data:
 *  - Profile tab: personal info, guardian contacts
 *  - Results tab: exam results per term
 *  - Attendance tab: attendance summary + record list
 *  - Fees tab: invoices and payment history
 *  - Documents tab: uploaded files
 */

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Pencil,
  Mail,
  Phone,
  MapPin,
  Calendar,
  GraduationCap,
  FileText,
  UserCheck,
  DollarSign,
  FolderOpen,
  AlertCircle,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Avatar } from "@/components/ui/Avatar";
import { formatDate, formatCurrency, formatPercent, formatGrade } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Student, Result, AttendanceSummary, Invoice } from "@/types";

type TabId = "profile" | "results" | "attendance" | "fees" | "documents";

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: "profile", label: "Profile", icon: GraduationCap },
  { id: "results", label: "Results", icon: FileText },
  { id: "attendance", label: "Attendance", icon: UserCheck },
  { id: "fees", label: "Fees", icon: DollarSign },
  { id: "documents", label: "Documents", icon: FolderOpen },
];

/* ── Info row ────────────────────────────────────────────────────── */
function InfoRow({ label, value, icon: Icon }: { label: string; value?: string | null; icon?: React.ElementType }) {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-gray-50 last:border-0">
      {Icon && <Icon className="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />}
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium uppercase tracking-wide text-gray-400">{label}</p>
        <p className="mt-0.5 text-sm text-gray-900">{value || "—"}</p>
      </div>
    </div>
  );
}

export default function StudentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const studentId = params.id as string;
  const [activeTab, setActiveTab] = useState<TabId>("profile");

  /* Fetch student */
  const { data: student, isLoading, error } = useQuery<Student>({
    queryKey: ["student", studentId],
    queryFn: () => apiGet<Student>(`/students/${studentId}/`),
    enabled: !!studentId,
  });

  /* Fetch results for this student */
  const { data: results } = useQuery<{ results: Result[] }>({
    queryKey: ["student-results", studentId],
    queryFn: () => apiGet<{ results: Result[] }>(`/results/?student=${studentId}`),
    enabled: activeTab === "results" && !!studentId,
  });

  /* Fetch attendance summary */
  const { data: attendanceSummary } = useQuery<AttendanceSummary>({
    queryKey: ["student-attendance-summary", studentId],
    queryFn: () => apiGet<AttendanceSummary>(`/attendance/summary/${studentId}/`),
    enabled: activeTab === "attendance" && !!studentId,
  });

  /* Fetch invoices for this student */
  const { data: invoices } = useQuery<{ results: Invoice[] }>({
    queryKey: ["student-invoices", studentId],
    queryFn: () => apiGet<{ results: Invoice[] }>(`/invoices/?student=${studentId}`),
    enabled: activeTab === "fees" && !!studentId,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-8 w-48" />
        <div className="skeleton h-32 w-full rounded-xl" />
        <div className="skeleton h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (error || !student) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
        <AlertCircle className="h-5 w-5 shrink-0" />
        <div>
          <p className="font-medium">Student not found</p>
          <p className="text-sm">The student record could not be loaded.</p>
        </div>
      </div>
    );
  }

  const primaryGuardian = student.guardians.find((g) => g.is_primary) ?? student.guardians[0];

  return (
    <div className="space-y-6">
      {/* Back + Page header */}
      <div>
        <button
          onClick={() => router.back()}
          className="mb-4 flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Students
        </button>

        <PageHeader
          title={student.full_name}
          subtitle={`Admission: ${student.admission_number}`}
          actions={
            <Link
              href={`/admin/students/${studentId}/edit`}
              className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <Pencil className="h-4 w-4" />
              Edit Profile
            </Link>
          }
        />
      </div>

      {/* Student profile header card */}
      <div className="rounded-xl border border-gray-100 bg-white p-6">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
          <Avatar
            src={student.photo}
            name={student.full_name}
            size="xl"
          />
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-3 mb-3">
              <h2 className="text-xl font-bold text-gray-900">{student.full_name}</h2>
              <Badge variant={student.status === "active" ? "success" : "error"}>
                {student.status.charAt(0).toUpperCase() + student.status.slice(1)}
              </Badge>
            </div>
            <div className="grid gap-x-8 gap-y-2 sm:grid-cols-3 text-sm">
              <div>
                <span className="text-gray-400">Class:</span>{" "}
                <span className="font-medium text-gray-900">{student.current_class_name}</span>
              </div>
              <div>
                <span className="text-gray-400">Gender:</span>{" "}
                <span className="font-medium text-gray-900 capitalize">{student.gender}</span>
              </div>
              <div>
                <span className="text-gray-400">DOB:</span>{" "}
                <span className="font-medium text-gray-900">{formatDate(student.date_of_birth)}</span>
              </div>
              <div>
                <span className="text-gray-400">Admitted:</span>{" "}
                <span className="font-medium text-gray-900">{formatDate(student.admission_date)}</span>
              </div>
              {student.blood_group && (
                <div>
                  <span className="text-gray-400">Blood Group:</span>{" "}
                  <span className="font-medium text-gray-900">{student.blood_group}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="rounded-xl border border-gray-100 bg-white overflow-hidden">
        {/* Tab bar */}
        <div className="border-b border-gray-100 overflow-x-auto">
          <nav className="flex">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center gap-2 whitespace-nowrap border-b-2 px-5 py-3.5 text-sm font-medium transition-colors",
                    activeTab === tab.id
                      ? "border-primary-700 text-primary-700"
                      : "border-transparent text-gray-500 hover:text-gray-700",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab content */}
        <div className="p-6">
          {/* PROFILE TAB */}
          {activeTab === "profile" && (
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Personal information */}
              <div>
                <h4 className="mb-3 font-semibold text-gray-900">Personal Information</h4>
                <div className="rounded-lg border border-gray-100 p-4">
                  <InfoRow label="Full Name" value={student.full_name} icon={GraduationCap} />
                  <InfoRow label="Date of Birth" value={formatDate(student.date_of_birth)} icon={Calendar} />
                  <InfoRow label="Blood Group" value={student.blood_group} />
                  <InfoRow label="Address" value={student.address} icon={MapPin} />
                  <InfoRow label="Medical Conditions" value={student.medical_conditions} />
                  <InfoRow label="Emergency Contact" value={student.emergency_contact_name} />
                  <InfoRow label="Emergency Phone" value={student.emergency_contact_phone} icon={Phone} />
                </div>
              </div>

              {/* Guardian information */}
              <div>
                <h4 className="mb-3 font-semibold text-gray-900">Guardian Information</h4>
                {student.guardians.map((guardian) => (
                  <div key={guardian.id} className="mb-3 rounded-lg border border-gray-100 p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Avatar name={guardian.full_name} size="sm" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{guardian.full_name}</p>
                        <p className="text-xs text-gray-400">{guardian.relationship}</p>
                      </div>
                      {guardian.is_primary && (
                        <Badge variant="info" className="ml-auto">Primary</Badge>
                      )}
                    </div>
                    <InfoRow label="Phone" value={guardian.phone} icon={Phone} />
                    <InfoRow label="Email" value={guardian.email} icon={Mail} />
                    <InfoRow label="Occupation" value={guardian.occupation} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* RESULTS TAB */}
          {activeTab === "results" && (
            <div>
              <h4 className="mb-4 font-semibold text-gray-900">Academic Results</h4>
              {results?.results.length === 0 ? (
                <p className="py-8 text-center text-gray-400">No results recorded yet.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="data-table w-full">
                    <thead>
                      <tr>
                        <th>Subject</th>
                        <th>Exam</th>
                        <th>Score</th>
                        <th>Percentage</th>
                        <th>Grade</th>
                        <th>Remark</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(results?.results ?? []).map((result) => (
                        <tr key={result.id}>
                          <td className="font-medium">{result.subject_name}</td>
                          <td className="text-gray-500">{result.exam_name}</td>
                          <td>{result.marks_obtained}/{result.total_marks}</td>
                          <td>{formatPercent(result.percentage)}</td>
                          <td>
                            <span className={cn("status-pill", result.percentage >= 50 ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700")}>
                              {result.grade}
                            </span>
                          </td>
                          <td className="text-gray-500">{result.remark || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ATTENDANCE TAB */}
          {activeTab === "attendance" && (
            <div>
              {attendanceSummary && (
                <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-5">
                  {[
                    { label: "Total Days", value: attendanceSummary.total_days },
                    { label: "Present", value: attendanceSummary.present_days, color: "text-green-700" },
                    { label: "Absent", value: attendanceSummary.absent_days, color: "text-red-700" },
                    { label: "Late", value: attendanceSummary.late_days, color: "text-yellow-700" },
                    { label: "Rate", value: `${attendanceSummary.attendance_rate.toFixed(1)}%`, color: "text-blue-700" },
                  ].map((item) => (
                    <div key={item.label} className="rounded-lg bg-gray-50 p-4 text-center">
                      <p className={cn("text-2xl font-bold", item.color ?? "text-gray-900")}>{item.value}</p>
                      <p className="text-xs text-gray-500 mt-1">{item.label}</p>
                    </div>
                  ))}
                </div>
              )}
              <p className="text-sm text-gray-400 text-center py-4">
                Detailed attendance records shown in the attendance module.
              </p>
            </div>
          )}

          {/* FEES TAB */}
          {activeTab === "fees" && (
            <div>
              <h4 className="mb-4 font-semibold text-gray-900">Fee Invoices</h4>
              {invoices?.results.length === 0 ? (
                <p className="py-8 text-center text-gray-400">No invoices found for this student.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="data-table w-full">
                    <thead>
                      <tr>
                        <th>Invoice #</th>
                        <th>Total</th>
                        <th>Paid</th>
                        <th>Balance</th>
                        <th>Due Date</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(invoices?.results ?? []).map((invoice) => (
                        <tr key={invoice.id}>
                          <td className="font-mono text-sm">{invoice.invoice_number}</td>
                          <td>{formatCurrency(invoice.total_amount)}</td>
                          <td className="text-green-700">{formatCurrency(invoice.amount_paid)}</td>
                          <td className={invoice.balance > 0 ? "text-red-600 font-medium" : "text-gray-500"}>
                            {formatCurrency(invoice.balance)}
                          </td>
                          <td>{formatDate(invoice.due_date)}</td>
                          <td>
                            <Badge
                              variant={
                                invoice.status === "paid" ? "success" :
                                invoice.status === "overdue" ? "error" :
                                invoice.status === "partially_paid" ? "warning" : "neutral"
                              }
                            >
                              {invoice.status.replace("_", " ")}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* DOCUMENTS TAB */}
          {activeTab === "documents" && (
            <div className="py-12 text-center text-gray-400">
              <FolderOpen className="mx-auto mb-3 h-10 w-10 text-gray-300" />
              <p>Document management coming soon.</p>
              <p className="text-xs mt-1">Upload birth certificates, transcripts, and other files.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
