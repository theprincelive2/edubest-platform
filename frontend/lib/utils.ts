import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow, isValid, parseISO } from "date-fns";

/**
 * General-purpose utility functions for Edubest frontend.
 *
 * Kept intentionally small — each function does exactly one thing.
 * Import only what you need to keep bundle size down.
 */

/* ── Tailwind / class utilities ──────────────────────────────────── */

/**
 * Merges Tailwind CSS class names, intelligently resolving conflicts.
 * Wraps clsx (conditional classes) + tailwind-merge (dedup/override).
 *
 * @example
 *   cn("px-4 py-2", condition && "bg-blue-500", "px-6") → "py-2 bg-blue-500 px-6"
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/* ── Date formatting ─────────────────────────────────────────────── */

/** Formats an ISO date string or Date object for display.
 *  Falls back gracefully to "—" if the value is null/undefined/invalid. */
export function formatDate(
  value: string | Date | null | undefined,
  fmt: string = "dd MMM yyyy",
): string {
  if (!value) return "—";

  const date = typeof value === "string" ? parseISO(value) : value;
  if (!isValid(date)) return "—";

  return format(date, fmt);
}

/** Formats a date as a relative string e.g. "3 days ago". */
export function formatRelativeDate(
  value: string | Date | null | undefined,
): string {
  if (!value) return "—";
  const date = typeof value === "string" ? parseISO(value) : value;
  if (!isValid(date)) return "—";
  return formatDistanceToNow(date, { addSuffix: true });
}

/** Formats a date-time for display in tables: "25 Sep 2026, 08:30". */
export function formatDateTime(
  value: string | Date | null | undefined,
): string {
  return formatDate(value, "dd MMM yyyy, HH:mm");
}

/* ── Currency formatting ─────────────────────────────────────────── */

/**
 * Formats a number as currency.
 * Uses Intl.NumberFormat so it respects locale settings.
 *
 * @param amount   - numeric value
 * @param currency - ISO 4217 code (default: "GHS" — Ghanaian Cedi)
 * @param locale   - BCP 47 locale string (default: "en-GH")
 */
export function formatCurrency(
  amount: number | null | undefined,
  currency: string = "GHS",
  locale: string = "en-GH",
): string {
  if (amount === null || amount === undefined) return "—";

  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/* ── Grade / score formatting ────────────────────────────────────── */

/**
 * Maps a numeric score to a letter grade using a standard scale.
 * Schools can override this via their settings; this is the default.
 *
 * @param score - value between 0 and 100
 */
export function formatGrade(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";

  if (score >= 90) return "A+";
  if (score >= 80) return "A";
  if (score >= 75) return "B+";
  if (score >= 70) return "B";
  if (score >= 65) return "C+";
  if (score >= 60) return "C";
  if (score >= 55) return "D+";
  if (score >= 50) return "D";
  return "F";
}

/** Returns a Tailwind colour class for a letter grade (for badges). */
export function gradeToColor(grade: string): string {
  const map: Record<string, string> = {
    "A+": "text-green-700 bg-green-50",
    A: "text-green-600 bg-green-50",
    "B+": "text-blue-700 bg-blue-50",
    B: "text-blue-600 bg-blue-50",
    "C+": "text-yellow-700 bg-yellow-50",
    C: "text-yellow-600 bg-yellow-50",
    "D+": "text-orange-700 bg-orange-50",
    D: "text-orange-600 bg-orange-50",
    F: "text-red-700 bg-red-50",
  };
  return map[grade] ?? "text-gray-600 bg-gray-50";
}

/* ── String utilities ────────────────────────────────────────────── */

/**
 * Derives initials from a full name (up to 2 characters).
 *
 * @example
 *   getInitials("Kwame Asante") → "KA"
 *   getInitials("Madonna")     → "M"
 */
export function getInitials(name: string | null | undefined): string {
  if (!name) return "?";

  return name
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

/** Truncates a string to `maxLength` characters, appending "…" if cut. */
export function truncate(text: string, maxLength: number = 80): string {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1)}…`;
}

/** Converts a snake_case or kebab-case string to Title Case. */
export function toTitleCase(value: string): string {
  return value
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/* ── Number utilities ────────────────────────────────────────────── */

/** Formats a number with locale-aware thousands separators. */
export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-GH").format(value);
}

/** Computes a percentage string rounded to 1 decimal place. */
export function formatPercent(
  value: number | null | undefined,
  decimals: number = 1,
): string {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(decimals)}%`;
}

/* ── Attendance helpers ──────────────────────────────────────────── */

/** Maps an attendance status code to a human-readable label. */
export function attendanceLabel(
  status: "present" | "absent" | "late" | "excused",
): string {
  const labels: Record<string, string> = {
    present: "Present",
    absent: "Absent",
    late: "Late",
    excused: "Excused",
  };
  return labels[status] ?? status;
}

/** Returns Tailwind colour classes for an attendance status badge. */
export function attendanceColor(status: string): string {
  const colors: Record<string, string> = {
    present: "text-green-700 bg-green-50 border-green-200",
    absent: "text-red-700 bg-red-50 border-red-200",
    late: "text-yellow-700 bg-yellow-50 border-yellow-200",
    excused: "text-blue-700 bg-blue-50 border-blue-200",
  };
  return colors[status] ?? "text-gray-700 bg-gray-50 border-gray-200";
}

/* ── URL / routing helpers ───────────────────────────────────────── */

/** Builds a query string from a plain object, omitting null/undefined values. */
export function buildQueryString(
  params: Record<string, string | number | boolean | null | undefined>,
): string {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      searchParams.set(key, String(value));
    }
  }
  const qs = searchParams.toString();
  return qs ? `?${qs}` : "";
}

/* ── File helpers ────────────────────────────────────────────────── */

/** Converts a byte count to a human-readable size string. */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}
