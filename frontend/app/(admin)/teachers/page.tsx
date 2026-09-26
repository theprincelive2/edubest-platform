"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, Plus, Eye, Pencil, Mail, Phone, AlertCircle } from "lucide-react";
import { useTeachers } from "@/hooks/useTeachers";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Avatar } from "@/components/ui/Avatar";
import { formatDate } from "@/lib/utils";
import type { TeacherFilters, TeacherStatus } from "@/types";

const STATUS_VARIANT: Record<TeacherStatus, "success" | "warning" | "error" | "neutral"> = {
  active: "success",
  on_leave: "warning",
  resigned: "error",
  retired: "neutral",
};

export default function TeachersPage() {
  const [filters, setFilters] = useState<TeacherFilters>({ page: 1, page_size: 20 });

  const { data, isLoading, error } = useTeachers(filters);
  const totalPages = data ? Math.ceil(data.count / (filters.page_size ?? 20)) : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Teachers"
        subtitle={`${data?.count ?? 0} staff members`}
        actions={
          <Link
            href="/admin/teachers/new"
            className="inline-flex items-center gap-2 rounded-lg bg-primary-700 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-800 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Teacher
          </Link>
        }
      />

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name or staff ID…"
            onChange={(e) => setFilters((p) => ({ ...p, search: e.target.value, page: 1 }))}
            className="input-field pl-9"
          />
        </div>
        <select
          onChange={(e) => setFilters((p) => ({ ...p, status: (e.target.value as TeacherStatus) || undefined, page: 1 }))}
          className="input-field w-auto"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="on_leave">On Leave</option>
          <option value="resigned">Resigned</option>
          <option value="retired">Retired</option>
        </select>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-gray-100 bg-white overflow-hidden">
        {error ? (
          <div className="flex items-center gap-3 p-6 text-red-700">
            <AlertCircle className="h-5 w-5" />
            <p className="text-sm">Failed to load teachers.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table w-full">
              <thead>
                <tr>
                  <th>Teacher</th>
                  <th>Staff ID</th>
                  <th>Subjects</th>
                  <th>Qualification</th>
                  <th>Phone</th>
                  <th>Joined</th>
                  <th>Status</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading
                  ? Array.from({ length: 8 }).map((_, i) => (
                      <tr key={i}>
                        {Array.from({ length: 8 }).map((_, j) => (
                          <td key={j}><div className="skeleton h-4 w-24" /></td>
                        ))}
                      </tr>
                    ))
                  : data?.results.map((teacher) => (
                      <tr key={teacher.id}>
                        <td>
                          <div className="flex items-center gap-3">
                            <Avatar src={teacher.photo} name={teacher.full_name} size="sm" />
                            <div>
                              <p className="font-medium text-gray-900">{teacher.full_name}</p>
                              <p className="text-xs text-gray-400">{teacher.user.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="font-mono text-sm text-gray-600">{teacher.staff_id}</td>
                        <td>
                          <div className="flex flex-wrap gap-1">
                            {teacher.subjects_names.slice(0, 2).map((s) => (
                              <span key={s} className="status-pill bg-blue-50 text-blue-700 text-xs">{s}</span>
                            ))}
                            {teacher.subjects_names.length > 2 && (
                              <span className="text-xs text-gray-400">+{teacher.subjects_names.length - 2}</span>
                            )}
                          </div>
                        </td>
                        <td className="capitalize text-gray-700">{teacher.qualification.replace("_", " ")}</td>
                        <td>
                          <a href={`tel:${teacher.phone}`} className="flex items-center gap-1.5 text-sm text-gray-700 hover:text-primary-700">
                            <Phone className="h-3.5 w-3.5" />
                            {teacher.phone}
                          </a>
                        </td>
                        <td className="text-gray-500">{formatDate(teacher.employment_date)}</td>
                        <td>
                          <Badge variant={STATUS_VARIANT[teacher.status]}>
                            {teacher.status.replace("_", " ")}
                          </Badge>
                        </td>
                        <td>
                          <div className="flex items-center justify-end gap-1">
                            <Link href={`/admin/teachers/${teacher.id}`} className="rounded-lg p-1.5 text-gray-400 hover:bg-blue-50 hover:text-blue-700 transition-colors" title="View">
                              <Eye className="h-4 w-4" />
                            </Link>
                            <Link href={`/admin/teachers/${teacher.id}/edit`} className="rounded-lg p-1.5 text-gray-400 hover:bg-amber-50 hover:text-amber-700 transition-colors" title="Edit">
                              <Pencil className="h-4 w-4" />
                            </Link>
                          </div>
                        </td>
                      </tr>
                    ))}

                {!isLoading && data?.results.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-gray-400">No teachers found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
