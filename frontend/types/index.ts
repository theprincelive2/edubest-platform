/**
 * Edubest TypeScript Type Definitions
 *
 * Central type registry for the entire frontend.
 * All interfaces mirror the Django REST Framework serializer output,
 * ensuring consistent naming between backend and frontend layers.
 */

/* ══════════════════════════════════════════════════════════════════
   GENERIC API SHAPES
   ══════════════════════════════════════════════════════════════════ */

/** Standard success/error wrapper returned by every DRF endpoint */
export interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
}

/** Paginated list response from DRF's PageNumberPagination */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
  /** Total number of pages (computed client-side) */
  total_pages?: number;
}

/* ══════════════════════════════════════════════════════════════════
   AUTHENTICATION & RBAC
   ══════════════════════════════════════════════════════════════════ */

export type UserRole =
  | "superadmin"
  | "admin"
  | "teacher"
  | "parent"
  | "student";

/** Fine-grained permission string — e.g. "students.create" */
export type Permission =
  | "students.view"
  | "students.create"
  | "students.edit"
  | "students.delete"
  | "teachers.view"
  | "teachers.create"
  | "teachers.edit"
  | "teachers.delete"
  | "classes.view"
  | "classes.create"
  | "classes.edit"
  | "attendance.view"
  | "attendance.mark"
  | "exams.view"
  | "exams.create"
  | "results.view"
  | "results.enter"
  | "results.publish"
  | "finance.view"
  | "finance.manage"
  | "users.view"
  | "users.create"
  | "users.edit"
  | "settings.manage"
  | "audit_logs.view"
  | string; // allow custom permissions from the backend

/** Core user record returned after login and from /users/me/ */
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  permissions: Permission[];
  avatar?: string | null;
  phone?: string | null;
  is_active: boolean;
  last_login?: string | null;
  date_joined: string;
  tenant: string; // tenant slug
}

/** Tokens returned by /auth/token/ */
export interface TokenPair {
  access: string;
  refresh: string;
}

/** Payload from /auth/login/ endpoint */
export interface LoginResponse {
  tokens: TokenPair;
  user: User;
}

/* ══════════════════════════════════════════════════════════════════
   TENANT / SCHOOL
   ══════════════════════════════════════════════════════════════════ */

export interface TenantConfig {
  id: string;
  name: string;             // e.g. "Sunshine Academy"
  slug: string;             // e.g. "sunshine" (subdomain)
  logo?: string | null;
  address: string;
  city: string;
  country: string;
  phone: string;
  email: string;
  website?: string | null;
  motto?: string | null;
  // Grading configuration
  grading_scale: GradingScale[];
  // Feature flags that can be toggled per school
  features: {
    finance: boolean;
    sms_notifications: boolean;
    parent_portal: boolean;
    student_portal: boolean;
    online_payments: boolean;
  };
  created_at: string;
  is_active: boolean;
}

export interface GradingScale {
  grade: string;    // e.g. "A+"
  min_score: number;
  max_score: number;
  remark: string;   // e.g. "Excellent"
}

/* ══════════════════════════════════════════════════════════════════
   ACADEMIC STRUCTURE
   ══════════════════════════════════════════════════════════════════ */

export interface AcademicYear {
  id: string;
  name: string;       // e.g. "2025/2026"
  start_date: string;
  end_date: string;
  is_current: boolean;
  terms: Term[];
}

export type TermType = "first" | "second" | "third";

export interface Term {
  id: string;
  academic_year: string;    // AcademicYear ID
  academic_year_name: string;
  term_type: TermType;
  name: string;             // e.g. "First Term"
  start_date: string;
  end_date: string;
  is_current: boolean;
}

export interface Subject {
  id: string;
  name: string;             // e.g. "Mathematics"
  code: string;             // e.g. "MATH101"
  description?: string;
  is_compulsory: boolean;
  teachers: string[];       // Teacher IDs
}

export interface Class {
  id: string;
  name: string;             // e.g. "Grade 6B"
  short_name: string;       // e.g. "6B"
  level: number;            // numeric grade level
  section?: string;         // A, B, C …
  class_teacher?: string;   // Teacher ID
  class_teacher_name?: string;
  subjects: string[];       // Subject IDs
  student_count: number;
  capacity: number;
  academic_year: string;
}

/* ══════════════════════════════════════════════════════════════════
   PEOPLE
   ══════════════════════════════════════════════════════════════════ */

export type StudentStatus = "active" | "graduated" | "transferred" | "suspended" | "withdrawn";
export type GenderType = "male" | "female" | "other";

export interface Student {
  id: string;
  user?: User;
  admission_number: string;
  first_name: string;
  last_name: string;
  full_name: string;
  date_of_birth: string;
  gender: GenderType;
  photo?: string | null;
  current_class: string;        // Class ID
  current_class_name: string;
  admission_date: string;
  status: StudentStatus;
  blood_group?: string;
  address?: string;
  guardians: Guardian[];
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  medical_conditions?: string;
  created_at: string;
  updated_at: string;
}

export interface Guardian {
  id: string;
  user?: User;
  first_name: string;
  last_name: string;
  full_name: string;
  relationship: string;   // "Father" | "Mother" | "Guardian" etc.
  phone: string;
  email?: string;
  address?: string;
  occupation?: string;
  is_primary: boolean;
  students: string[];     // Student IDs
}

export type TeacherStatus = "active" | "on_leave" | "resigned" | "retired";
export type QualificationType = "diploma" | "bachelors" | "masters" | "phd" | "other";

export interface Teacher {
  id: string;
  user: User;
  staff_id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  date_of_birth: string;
  gender: GenderType;
  photo?: string | null;
  phone: string;
  address?: string;
  qualification: QualificationType;
  specialisation?: string;
  subjects: string[];       // Subject IDs
  subjects_names: string[];
  classes: string[];        // Class IDs
  status: TeacherStatus;
  employment_date: string;
  created_at: string;
}

/* ══════════════════════════════════════════════════════════════════
   TIMETABLE
   ══════════════════════════════════════════════════════════════════ */

export type DayOfWeek = "monday" | "tuesday" | "wednesday" | "thursday" | "friday";

export interface TimetableSlot {
  id: string;
  class_room: string;       // Class ID
  subject: string;          // Subject ID
  subject_name: string;
  teacher: string;          // Teacher ID
  teacher_name: string;
  day_of_week: DayOfWeek;
  start_time: string;       // "HH:MM"
  end_time: string;
  academic_year: string;
  term: string;
}

/* ══════════════════════════════════════════════════════════════════
   ATTENDANCE
   ══════════════════════════════════════════════════════════════════ */

export type AttendanceStatus = "present" | "absent" | "late" | "excused";

export interface AttendanceRecord {
  id: string;
  student: string;            // Student ID
  student_name: string;
  class_room: string;
  date: string;               // ISO date "YYYY-MM-DD"
  status: AttendanceStatus;
  remark?: string;
  marked_by: string;          // Teacher/Admin ID
  marked_by_name: string;
  created_at: string;
}

export interface AttendanceSession {
  id: string;
  class_obj: string;
  class_name?: string;
  date: string;
  period: "morning" | "afternoon" | "full_day";
  term: string;
  taken_by?: string;
  taken_by_name?: string;
  records_count?: number;
  present_count?: number;
  absent_count?: number;
  created_at: string;
}

export interface AttendanceSummary {
  student_id: string;
  student_name: string;
  total_days: number;
  present_days: number;
  absent_days: number;
  late_days: number;
  excused_days: number;
  attendance_rate: number;    // percentage 0-100
}

/* ══════════════════════════════════════════════════════════════════
   EXAMS & RESULTS
   ══════════════════════════════════════════════════════════════════ */

export type ExamType = "midterm" | "end_of_term" | "mock" | "continuous_assessment" | "other";
export type ExamStatus = "scheduled" | "ongoing" | "completed" | "cancelled";

export interface Exam {
  id: string;
  name: string;
  exam_type: ExamType;
  academic_year: string;
  term: string;
  term_name: string;
  start_date: string;
  end_date: string;
  total_marks: number;
  passing_marks: number;
  status: ExamStatus;
  classes: string[];          // applicable Class IDs
  subjects: string[];         // applicable Subject IDs
  created_at: string;
}

export interface Result {
  id: string;
  student: string;
  student_name: string;
  exam: string;
  exam_name: string;
  subject: string;
  subject_name: string;
  class_room: string;
  marks_obtained: number;
  total_marks: number;
  percentage: number;
  grade: string;
  remark?: string;
  is_published: boolean;
  entered_by: string;
  created_at: string;
}

export interface ReportCard {
  student: Student;
  term: Term;
  academic_year: AcademicYear;
  results: Result[];
  total_marks: number;
  obtained_marks: number;
  percentage: number;
  overall_grade: string;
  class_position: number;
  attendance_summary: AttendanceSummary;
  class_teacher_remark?: string;
  principal_remark?: string;
}

/* ══════════════════════════════════════════════════════════════════
   FINANCE
   ══════════════════════════════════════════════════════════════════ */

export type FeeCategory = "tuition" | "uniform" | "transport" | "meals" | "activity" | "exam" | "other";

export interface FeeStructure {
  id: string;
  name: string;
  category: FeeCategory;
  amount: number;
  academic_year: string;
  term?: string;              // null = applies to all terms
  applicable_classes: string[];
  due_date?: string;
  description?: string;
  is_compulsory: boolean;
  created_at: string;
}

export type InvoiceStatus = "draft" | "sent" | "partially_paid" | "paid" | "overdue" | "cancelled" | "void";

export interface Invoice {
  id: string;
  invoice_number: string;
  student: string;
  student_name: string;
  guardian: string;
  guardian_name: string;
  academic_year: string;
  term?: string;
  items: InvoiceItem[];
  subtotal: number;
  discount: number;
  total_amount: number;
  amount_paid: number;
  balance: number;
  status: InvoiceStatus;
  due_date: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface InvoiceItem {
  id: string;
  fee_structure: string;
  description: string;
  amount: number;
  quantity: number;
  total: number;
}

export type PaymentMethod = "cash" | "bank_transfer" | "mobile_money" | "cheque" | "online";
export type PaymentStatus = "pending" | "completed" | "failed" | "refunded";

export interface Payment {
  id: string;
  invoice: string;
  invoice_number: string;
  student_name: string;
  amount: number;
  payment_method: PaymentMethod;
  reference_number?: string;
  transaction_id?: string;
  status: PaymentStatus;
  payment_date: string;
  received_by: string;
  received_by_name: string;
  notes?: string;
  created_at: string;
}

export interface FinanceSummary {
  total_invoiced: number;
  total_collected: number;
  total_outstanding: number;
  total_overdue: number;
  collection_rate: number;    // percentage
  payment_count: number;
  recent_payments: Payment[];
}

/* ══════════════════════════════════════════════════════════════════
   COMMUNICATION
   ══════════════════════════════════════════════════════════════════ */

export type MessageStatus = "sent" | "delivered" | "read";

export interface Message {
  id: string;
  sender: string;
  sender_name: string;
  recipient: string;
  recipient_name: string;
  subject: string;
  body: string;
  status: MessageStatus;
  is_read: boolean;
  parent_message?: string;    // for threading
  created_at: string;
}

export type AnnouncementAudience = "all" | "students" | "parents" | "teachers" | "staff";

export interface Announcement {
  id: string;
  title: string;
  content: string;
  audience: AnnouncementAudience;
  author: string;
  author_name: string;
  is_pinned: boolean;
  publish_at?: string;
  expires_at?: string;
  created_at: string;
}

/* ══════════════════════════════════════════════════════════════════
   AUDIT LOGS
   ══════════════════════════════════════════════════════════════════ */

export type AuditAction =
  | "create"
  | "update"
  | "delete"
  | "login"
  | "logout"
  | "export"
  | "publish"
  | "payment"
  | string;

export interface AuditLog {
  id: string;
  user: string;
  user_name: string;
  user_email: string;
  action: AuditAction;
  resource: string;           // model name e.g. "Student"
  resource_id?: string;
  resource_display?: string;  // human-readable e.g. "Kwame Asante (STU-001)"
  changes?: Record<string, { before: unknown; after: unknown }>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

/* ══════════════════════════════════════════════════════════════════
   DASHBOARD STATS
   ══════════════════════════════════════════════════════════════════ */

export interface DashboardStats {
  total_students: number;
  total_teachers: number;
  total_classes: number;
  total_subjects: number;
  attendance_rate_today: number;
  fees_collected_this_term: number;
  outstanding_fees: number;
  upcoming_exams_count: number;
}

/* ══════════════════════════════════════════════════════════════════
   FORM / FILTER TYPES
   ══════════════════════════════════════════════════════════════════ */

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface StudentFilters extends PaginationParams {
  search?: string;
  class_room?: string;
  status?: StudentStatus;
  gender?: GenderType;
  academic_year?: string;
}

export interface TeacherFilters extends PaginationParams {
  search?: string;
  subject?: string;
  status?: TeacherStatus;
}

export interface InvoiceFilters extends PaginationParams {
  search?: string;
  status?: InvoiceStatus;
  student?: string;
  term?: string;
  academic_year?: string;
  from_date?: string;
  to_date?: string;
}

export interface AttendanceFilters extends PaginationParams {
  class_room?: string;
  date?: string;
  status?: AttendanceStatus;
  student?: string;
}

export interface AuditLogFilters extends PaginationParams {
  user?: string;
  action?: AuditAction;
  resource?: string;
  from_date?: string;
  to_date?: string;
}
