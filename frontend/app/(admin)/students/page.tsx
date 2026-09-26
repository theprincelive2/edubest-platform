"use client";

/**
 * Students List Page
 *
 * Features:
 *  - Paginated data table with search, class filter, and status filter
 *  - Add Student button opens an inline drawer / navigates to /admin/students/new
 *  - Row actions: View, Edit, Delete (with confirmation)
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Search,
  Plus,
  Filter,
  Eye,
  Pencil,
  Trash2,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import { toast } from "sonner";
import { useStudents, useDeleteStudent } from "@/hooks/useStudents";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Avatar } from "@/components/ui/Avatar";
import { formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { StudentStatus, StudentFilters } from "@/types";

/* ── Status badge helper ─────────────────────────────────────────── */
const STATUS_VARIANT: Record<StudentStatus, "success" | "error" | "warning" | "neutral" | "info"> = {
  active: "success",
  graduated: "info",
  transferred: "warning",
  suspended: "error",
  withdrawn: "neutral",
};

/* ── Page component ──────────────────────────────────────────────── */
export default function StudentsPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<StudentFilters>({
    page: 1,
    page_size: 20,
    search: "",
    status: undefined,
    class_room: undefined,
  });
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const { data, isLoading, error } = useStudents(filters);
  const deleteMutation = useDeleteStudent();

  const totalPages = data ? Math.ceil(data.count / (filters.page_size ?? 20)) : 0;

  const handleSearch = (value: string) => {
    setFilters((prev) => ({ ...prev, search: value, page: 1 }));
  };

  const handleStatusFilter = (status: StudentStatus | "") => {
    setFilters((prev) => ({
      ...prev,
      status: status || undefined,
      page: 1,
    }));
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMutation.mutateAsync(id);
      toast.success("Student record deleted.");
      setDeleteConfirm(null);
    } catch {
      toast.error("Failed to delete student. Please try again.");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Students"
        subtitle={`${data?.count ?? 0} students enrolled`}
        actions={
          <Link
            href="/admin/students/new"
            className="inline-flex items-center gap-2 rounded-lg bg-primary-700 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-800 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Student
          </Link>
        }
      />

      {/* ── Filters ─────────────────────────────────────────────── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name or admission number…"
            value={filters.search ?? ""}
            onChange={(e) => handleSearch(e.target.value)}
            className="input-field pl-9"
          />
        </div>

        {/* Status filter */}
        <select
          value={filters.status ?? ""}
          onChange={(e) => handleStatusFilter(e.target.value as StudentStatus | "")}
          className="input-field w-auto min-w-[140px]"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="transferred">Transferred</option>
          <option value="graduated">Graduated</option>
          <option value="withdrawn">Withdrawn</option>
        </select>

        {/* Per-page */}
        <select
          value={filters.page_size ?? 20}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, page_size: Number(e.target.value), page: 1 }))
          }
          className="input-field w-auto"
        >
          <option value={10}>10 per page</option>
          <option value={20}>20 per page</option>
          <option value={50}>50 per page</option>
        </select>
      </div>

      {/* ── Table ───────────────────────────────────────────────── */}
      <div className="rounded-xl border border-gray-100 bg-white overflow-hidden">
        {error ? (
          <div className="flex items-center gap-3 p-6 text-red-700">
            <AlertCircle className="h-5 w-5" />
            <p className="text-sm">Failed to load students. Please refresh.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead>
                <tr>
                  <th className="w-12">#</th>
                  <th>Student</th>
                  <th>Admission No.</th>
                  <th>Class</th>
                  <th>Guardian</th>
                  <th>Admission Date</th>
                  <th>Status</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading
                  ? Array.from({ length: 8 }).map((_, i) => (
                      <tr key={i}>
                        {Array.from({ length: 8 }).map((_, j) => (
                          <td key={j}>
                            <div className="skeleton h-4 w-full max-w-[120px]" />
                          </td>
                        ))}
                      </tr>
                    ))
                  : data?.results.map((student, index) => {
                      const primaryGuardian = student.guardians.find((g) => g.is_primary);
                      return (
                        <tr key={student.id}>
                          <td className="text-gray-400 text-xs">
                            {((filters.page ?? 1) - 1) * (filters.page_size ?? 20) + index + 1}
                          </td>
                          <td>
                            <div className="flex items-center gap-3">
                              <Avatar
                                src={student.photo}
                                name={student.full_name}
                                size="sm"
                              />
                              <div>
                                <p className="font-medium text-gray-900">
                                  {student.full_name}
                                </p>
                                <p className="text-xs text-gray-400 capitalize">
                                  {student.gender}
                                </p>
                              </div>
                            </div>
                          </td>
                          <td className="font-mono text-sm text-gray-600">
                            {student.admission_number}
                          </td>
                          <td className="text-gray-700">{student.current_class_name}</td>
                          <td className="text-gray-700">
                            {primaryGuardian
                              ? `${primaryGuardian.full_name} (${primaryGuardian.relationship})`
                              : "—"}
                          </td>
                          <td className="text-gray-500">{formatDate(student.admission_date)}</td>
                          <td>
                            <Badge variant={STATUS_VARIANT[student.status]}>
                              {student.status.charAt(0).toUpperCase() + student.status.slice(1)}
                            </Badge>
                          </td>
                          <td>
                            <div className="flex items-center justify-end gap-1">
                              <Link
                                href={`/admin/students/${student.id}`}
                                className="rounded-lg p-1.5 text-gray-400 hover:bg-blue-50 hover:text-blue-700 transition-colors"
                                title="View"
                              >
                                <Eye className="h-4 w-4" />
                              </Link>
                              <Link
                                href={`/admin/students/${student.id}/edit`}
                                className="rounded-lg p-1.5 text-gray-400 hover:bg-amber-50 hover:text-amber-700 transition-colors"
                                title="Edit"
                              >
                                <Pencil className="h-4 w-4" />
                              </Link>
                              {deleteConfirm === student.id ? (
                                <div className="flex items-center gap-1">
                                  <button
                                    onClick={() => handleDelete(student.id)}
                                    className="rounded px-2 py-1 text-xs font-medium bg-red-600 text-white hover:bg-red-700"
                                  >
                                    Confirm
                                  </button>
                                  <button
                                    onClick={() => setDeleteConfirm(null)}
                                    className="rounded px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 hover:bg-gray-200"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              ) : (
                                <button
                                  onClick={() => setDeleteConfirm(student.id)}
                                  className="rounded-lg p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-700 transition-colors"
                                  title="Delete"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}

                {!isLoading && data?.results.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-gray-400">
                      No students found. Try adjusting your filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* ── Pagination ───────────────────────────────────────── */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-gray-100 px-6 py-3">
            <p className="text-xs text-gray-500">
              Page {filters.page} of {totalPages} · {data?.count} total
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() =>
                  setFilters((p) => ({ ...p, page: Math.max(1, (p.page ?? 1) - 1) }))
                }
                disabled={(filters.page ?? 1) <= 1}
                className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={() =>
                  setFilters((p) => ({ ...p, page: Math.min(totalPages, (p.page ?? 1) + 1) }))
                }
                disabled={(filters.page ?? 1) >= totalPages}
                className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
