"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus, Eye, Users, AlertCircle } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import type { Class } from "@/types";

export default function ClassesPage() {
  const { data, isLoading, error } = useQuery<{ results: Class[]; count: number }>({
    queryKey: ["classes"],
    queryFn: () => apiGet<{ results: Class[]; count: number }>("/classes/"),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Classes"
        subtitle={`${data?.count ?? 0} classes`}
        actions={
          <Link
            href="/admin/classes/new"
            className="inline-flex items-center gap-2 rounded-lg bg-primary-700 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-800 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Class
          </Link>
        }
      />

      {error ? (
        <div className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          <AlertCircle className="h-5 w-5" />
          <p className="text-sm">Failed to load classes.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {isLoading
            ? Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="rounded-xl border border-gray-100 bg-white p-5">
                  <div className="skeleton h-5 w-24 mb-2" />
                  <div className="skeleton h-4 w-32 mb-4" />
                  <div className="skeleton h-10 w-full" />
                </div>
              ))
            : data?.results.map((cls) => (
                <div
                  key={cls.id}
                  className="rounded-xl border border-gray-100 bg-white p-5 hover:shadow-card-hover transition-shadow"
                >
                  {/* Class name and section */}
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900 text-lg">{cls.name}</h3>
                      {cls.class_teacher_name && (
                        <p className="text-xs text-gray-500 mt-0.5">
                          Teacher: {cls.class_teacher_name}
                        </p>
                      )}
                    </div>
                    <div
                      className="flex h-10 w-10 items-center justify-center rounded-lg text-sm font-bold"
                      style={{ backgroundColor: `hsl(${cls.level * 25}, 70%, 90%)`, color: `hsl(${cls.level * 25}, 60%, 35%)` }}
                    >
                      {cls.short_name}
                    </div>
                  </div>

                  {/* Stats row */}
                  <div className="flex items-center gap-4 text-sm mb-4">
                    <div className="flex items-center gap-1.5 text-gray-600">
                      <Users className="h-4 w-4 text-gray-400" />
                      <span className="font-medium">{cls.student_count}</span>
                      <span className="text-gray-400">/ {cls.capacity}</span>
                    </div>
                    <div className="text-gray-400 text-xs">students enrolled</div>
                  </div>

                  {/* Capacity bar */}
                  <div className="mb-4">
                    <div className="h-1.5 w-full rounded-full bg-gray-100">
                      <div
                        className="h-1.5 rounded-full bg-primary-500 transition-all"
                        style={{ width: `${Math.min((cls.student_count / cls.capacity) * 100, 100)}%` }}
                      />
                    </div>
                    <p className="mt-1 text-xs text-gray-400 text-right">
                      {Math.round((cls.student_count / cls.capacity) * 100)}% capacity
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Link
                      href={`/admin/classes/${cls.id}`}
                      className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-gray-200 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      View Students
                    </Link>
                    <Link
                      href={`/admin/attendance?class=${cls.id}`}
                      className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-primary-50 py-1.5 text-xs font-medium text-primary-700 hover:bg-primary-100 transition-colors"
                    >
                      Mark Attendance
                    </Link>
                  </div>
                </div>
              ))}
        </div>
      )}
    </div>
  );
}
