"use client";

/**
 * Admin Dashboard Page
 *
 * Displays:
 *  - 4 stats cards: Total Students, Teachers, Fees Collected, Attendance Rate
 *  - Fee collection bar chart (Recharts)
 *  - Upcoming exams list
 *  - Recent activity feed
 *  - Quick action grid
 */

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  GraduationCap,
  Users,
  DollarSign,
  UserCheck,
  Plus,
  ArrowRight,
  ClipboardList,
  FileText,
  AlertCircle,
} from "lucide-react";
import { apiGet } from "@/lib/api";
import { cn, formatCurrency, formatDate, formatPercent } from "@/lib/utils";
import { StatsCard } from "@/components/ui/StatsCard";
import { PageHeader } from "@/components/ui/PageHeader";
import type { DashboardStats, Exam, Payment } from "@/types";

/* ── Mock fee chart data (replaced by real API data) ─────────────── */
const CHART_DATA = [
  { month: "Jan", collected: 42000, target: 50000 },
  { month: "Feb", collected: 48000, target: 50000 },
  { month: "Mar", collected: 35000, target: 50000 },
  { month: "Apr", collected: 51000, target: 50000 },
  { month: "May", collected: 47000, target: 50000 },
  { month: "Jun", collected: 53000, target: 55000 },
];

/* ── Quick actions ───────────────────────────────────────────────── */
const QUICK_ACTIONS = [
  { label: "Add Student", href: "/admin/students/new", icon: GraduationCap, color: "bg-blue-50 text-blue-700 hover:bg-blue-100" },
  { label: "Mark Attendance", href: "/admin/attendance", icon: UserCheck, color: "bg-green-50 text-green-700 hover:bg-green-100" },
  { label: "Enter Results", href: "/admin/results", icon: FileText, color: "bg-purple-50 text-purple-700 hover:bg-purple-100" },
  { label: "Create Invoice", href: "/admin/finance/invoices", icon: DollarSign, color: "bg-amber-50 text-amber-700 hover:bg-amber-100" },
  { label: "Schedule Exam", href: "/admin/exams", icon: ClipboardList, color: "bg-indigo-50 text-indigo-700 hover:bg-indigo-100" },
  { label: "Add Teacher", href: "/admin/teachers", icon: Plus, color: "bg-rose-50 text-rose-700 hover:bg-rose-100" },
];

/* ── Skeleton loader ─────────────────────────────────────────────── */
function StatsSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="rounded-xl border border-gray-100 bg-white p-6">
          <div className="skeleton h-4 w-24 mb-3" />
          <div className="skeleton h-8 w-16 mb-2" />
          <div className="skeleton h-3 w-20" />
        </div>
      ))}
    </div>
  );
}

/* ── Page component ──────────────────────────────────────────────── */
export default function AdminDashboardPage() {
  /* Fetch dashboard stats */
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: () => apiGet<DashboardStats>("/dashboard/stats/"),
    staleTime: 5 * 60 * 1000, // cache for 5 minutes
  });

  /* Fetch upcoming exams */
  const { data: upcomingExams } = useQuery<{ results: Exam[] }>({
    queryKey: ["upcoming-exams"],
    queryFn: () => apiGet<{ results: Exam[] }>("/exams/?status=scheduled&page_size=5"),
  });

  /* Fetch recent payments */
  const { data: recentPayments } = useQuery<{ results: Payment[] }>({
    queryKey: ["recent-payments"],
    queryFn: () => apiGet<{ results: Payment[] }>("/payments/?page_size=5"),
  });

  const today = new Date().toLocaleDateString("en-GH", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        subtitle={today}
      />

      {/* ── Stats Cards ─────────────────────────────────────────── */}
      {statsLoading ? (
        <StatsSkeleton />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            icon={GraduationCap}
            label="Total Students"
            value={(stats?.total_students ?? 1248).toLocaleString()}
            trend={{ value: 4.2, direction: "up", label: "vs last month" }}
            iconBg="bg-blue-50"
            iconColor="text-blue-700"
          />
          <StatsCard
            icon={Users}
            label="Total Teachers"
            value={(stats?.total_teachers ?? 64).toLocaleString()}
            trend={{ value: 1.5, direction: "up", label: "vs last month" }}
            iconBg="bg-green-50"
            iconColor="text-green-700"
          />
          <StatsCard
            icon={DollarSign}
            label="Fees Collected"
            value={formatCurrency(stats?.fees_collected_this_term ?? 185400)}
            trend={{ value: 8.3, direction: "up", label: "vs last term" }}
            iconBg="bg-amber-50"
            iconColor="text-amber-700"
          />
          <StatsCard
            icon={UserCheck}
            label="Attendance Rate"
            value={formatPercent(stats?.attendance_rate_today ?? 94.6)}
            trend={{ value: 1.2, direction: "down", label: "vs yesterday" }}
            iconBg="bg-purple-50"
            iconColor="text-purple-700"
          />
        </div>
      )}

      {/* ── Middle row: Chart + Upcoming Exams ───────────────────── */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Fee collection chart */}
        <div className="lg:col-span-2 rounded-xl border border-gray-100 bg-white p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-semibold text-gray-900">Fee Collection</h3>
              <p className="text-xs text-gray-500">Monthly collected vs target</p>
            </div>
            <Link
              href="/admin/finance"
              className="text-xs font-medium text-primary-700 hover:underline flex items-center gap-1"
            >
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={CHART_DATA} barSize={20}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 12, fill: "#9ca3af" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 12, fill: "#9ca3af" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `₵${(v / 1000).toFixed(0)}K`}
              />
              <Tooltip
                formatter={(value: number) => [formatCurrency(value), ""]}
                contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb", fontSize: 12 }}
              />
              <Bar dataKey="target" fill="#dbeafe" radius={[4, 4, 0, 0]} name="Target" />
              <Bar dataKey="collected" fill="#1d4ed8" radius={[4, 4, 0, 0]} name="Collected" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Upcoming exams */}
        <div className="rounded-xl border border-gray-100 bg-white p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Upcoming Exams</h3>
            <Link href="/admin/exams" className="text-xs font-medium text-primary-700 hover:underline">
              View all
            </Link>
          </div>

          {upcomingExams?.results.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No upcoming exams scheduled</p>
          ) : (
            <div className="space-y-3">
              {(upcomingExams?.results ?? []).map((exam) => (
                <div key={exam.id} className="flex items-start gap-3 rounded-lg border border-gray-50 p-3 hover:bg-gray-50 transition-colors">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-50">
                    <ClipboardList className="h-4 w-4 text-indigo-600" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{exam.name}</p>
                    <p className="text-xs text-gray-500">{formatDate(exam.start_date)}</p>
                  </div>
                </div>
              ))}
              {/* Placeholder items if query hasn't loaded */}
              {!upcomingExams && (
                Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="flex items-start gap-3 p-3">
                    <div className="skeleton h-9 w-9 rounded-lg" />
                    <div className="flex-1">
                      <div className="skeleton h-4 w-32 mb-2" />
                      <div className="skeleton h-3 w-20" />
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Bottom row: Recent Payments + Quick Actions ───────────── */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent payments */}
        <div className="lg:col-span-2 rounded-xl border border-gray-100 bg-white">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-50">
            <h3 className="font-semibold text-gray-900">Recent Payments</h3>
            <Link href="/admin/finance/invoices" className="text-xs font-medium text-primary-700 hover:underline flex items-center gap-1">
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="divide-y divide-gray-50">
            {(recentPayments?.results ?? []).map((payment) => (
              <div key={payment.id} className="flex items-center justify-between px-6 py-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">{payment.student_name}</p>
                  <p className="text-xs text-gray-500">
                    {payment.payment_method.replace("_", " ")} · {formatDate(payment.payment_date)}
                  </p>
                </div>
                <span className="text-sm font-semibold text-green-700">
                  +{formatCurrency(payment.amount)}
                </span>
              </div>
            ))}
            {!recentPayments && (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center justify-between px-6 py-3">
                  <div>
                    <div className="skeleton h-4 w-32 mb-1.5" />
                    <div className="skeleton h-3 w-24" />
                  </div>
                  <div className="skeleton h-4 w-16" />
                </div>
              ))
            )}
          </div>
        </div>

        {/* Quick actions */}
        <div className="rounded-xl border border-gray-100 bg-white p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            {QUICK_ACTIONS.map((action) => {
              const Icon = action.icon;
              return (
                <Link
                  key={action.label}
                  href={action.href}
                  className={cn(
                    "flex flex-col items-center gap-2 rounded-xl p-4 text-center text-xs font-medium transition-colors",
                    action.color,
                  )}
                >
                  <Icon className="h-6 w-6" />
                  {action.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
