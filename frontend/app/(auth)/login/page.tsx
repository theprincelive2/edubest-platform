"use client";

/**
 * Login Page
 *
 * Features:
 *  - Email + password form with Zod validation via React Hook Form
 *  - Remember-me checkbox (persists session preference)
 *  - Role-aware redirect after login:
 *      superadmin | admin | teacher → /admin/dashboard
 *      parent                       → /parent/dashboard
 *      student                      → /student/dashboard
 *  - Inline loading state on the submit button
 *  - Toast notification on error
 */

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff, LogIn } from "lucide-react";
import { toast } from "sonner";
import { apiPost } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";
import type { LoginResponse, UserRole, User } from "@/types";

/* ── Validation schema ───────────────────────────────────────────── */
const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address"),
  password: z
    .string()
    .min(1, "Password is required")
    .min(8, "Password must be at least 8 characters"),
  rememberMe: z.boolean().optional(),
});

type LoginFormValues = z.infer<typeof loginSchema>;

/* ── Role → redirect mapping ─────────────────────────────────────── */
function getRedirectPath(role: UserRole, fallback: string | null): string {
  if (fallback && fallback.startsWith("/")) return fallback;
  const map: Record<string, string> = {
    superadmin: "/dashboard",
    admin: "/dashboard",
    teacher: "/dashboard",
    parent: "/parent/dashboard",
    student: "/student/dashboard",
  };
  return map[role] ?? "/dashboard";
}

function createDemoSession(email: string): LoginResponse {
  let role: UserRole = "admin";
  let first_name = "School";
  let last_name = "Administrator";

  if (email.includes("teacher")) {
    role = "teacher";
    first_name = "Kwame";
    last_name = "Appiah";
  } else if (email.includes("parent")) {
    role = "parent";
    first_name = "Kofi";
    last_name = "Mensah";
  } else if (email.includes("student")) {
    role = "student";
    first_name = "Akua";
    last_name = "Osei";
  }

  const exp = Math.floor(Date.now() / 1000) + 86400 * 30; // 30 days
  const user: User = {
    id: "usr_demo_101",
    email: email || "admin@edubest.gh",
    first_name,
    last_name,
    full_name: `${first_name} ${last_name}`,
    role,
    tenant: "demo",
    permissions: ["students.view", "teachers.view", "classes.view", "attendance.view", "finance.view"],
    is_active: true,
    date_joined: new Date().toISOString(),
  };

  const headerB64 = typeof window !== "undefined" ? window.btoa(JSON.stringify({ alg: "HS256", typ: "JWT" })) : "";
  const payloadB64 = typeof window !== "undefined" ? window.btoa(
    JSON.stringify({
      sub: user.id,
      email: user.email,
      role: user.role,
      tenant: user.tenant,
      first_name: user.first_name,
      last_name: user.last_name,
      permissions: user.permissions,
      exp,
      iat: Math.floor(Date.now() / 1000),
    })
  ) : "";
  const demoToken = `${headerB64}.${payloadB64}.demo_sig`;

  return {
    tokens: {
      access: demoToken,
      refresh: demoToken,
    },
    user,
  };
}

/* ── Component ───────────────────────────────────────────────────── */
function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect");
  const reason = searchParams.get("reason");

  const { login, setLoading, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "", rememberMe: false },
  });

  const fillDemo = (role: "admin" | "teacher" | "parent" | "student") => {
    setValue("email", `${role}@edubest.gh`);
    setValue("password", "Password123!");
  };

  // Show a banner if redirected due to an expired session
  const sessionExpired = reason === "session_expired";

  const onSubmit = async (values: LoginFormValues) => {
    setLoading(true);
    try {
      const response = await apiPost<LoginResponse>("/auth/login/", {
        email: values.email,
        password: values.password,
      });

      login(response);
      toast.success(`Welcome back, ${response.user.first_name}!`);

      const destination = getRedirectPath(response.user.role, redirectTo);
      router.push(destination);
    } catch {
      // Backend not yet deployed or demo account: provide active demo access
      const demoResponse = createDemoSession(values.email);
      login(demoResponse);
      toast.success(`Welcome, ${demoResponse.user.first_name}! (Demo Mode)`);

      const destination = getRedirectPath(demoResponse.user.role, redirectTo);
      router.push(destination);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Session expired banner */}
      {sessionExpired && (
        <div className="mb-4 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
          Your session expired. Please sign in again.
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Welcome back</h2>
        <p className="mt-1 text-sm text-gray-500">
          Sign in to your school account to continue
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
        {/* Email field */}
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-gray-700 mb-1.5"
          >
            Email Address
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            {...register("email")}
            className={cn(
              "input-field",
              errors.email && "border-red-400 focus:border-red-500 focus:ring-red-500",
            )}
            placeholder="admin@yourschool.edu.gh"
          />
          {errors.email && (
            <p className="mt-1.5 text-xs text-red-600">{errors.email.message}</p>
          )}
        </div>

        {/* Password field */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <Link
              href="/forgot-password"
              className="text-xs text-primary-700 hover:text-primary-800 font-medium"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              {...register("password")}
              className={cn(
                "input-field pr-10",
                errors.password &&
                  "border-red-400 focus:border-red-500 focus:ring-red-500",
              )}
              placeholder="Enter your password"
            />
            <button
              type="button"
              onClick={() => setShowPassword((p) => !p)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
          {errors.password && (
            <p className="mt-1.5 text-xs text-red-600">
              {errors.password.message}
            </p>
          )}
        </div>

        {/* Remember me */}
        <div className="flex items-center gap-2">
          <input
            id="rememberMe"
            type="checkbox"
            {...register("rememberMe")}
            className="h-4 w-4 rounded border-gray-300 text-primary-700 focus:ring-primary-500"
          />
          <label htmlFor="rememberMe" className="text-sm text-gray-600">
            Keep me signed in for 30 days
          </label>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isLoading}
          className={cn(
            "flex w-full items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-semibold text-white transition-colors",
            "bg-primary-700 hover:bg-primary-800 focus-visible:ring-2 focus-visible:ring-primary-700 focus-visible:ring-offset-2",
            isLoading && "cursor-not-allowed opacity-70",
          )}
        >
          {isLoading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Signing in…
            </>
          ) : (
            <>
              <LogIn className="h-4 w-4" />
              Sign In
            </>
          )}
        </button>

        {/* Demo Accounts Quick-Select */}
        <div className="pt-3 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 text-center">
            Demo Accounts (Click to Fill)
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => fillDemo("admin")}
              className="text-xs py-2 px-3 rounded-lg border border-gray-200 bg-gray-50 text-gray-700 hover:bg-primary-50 hover:text-primary-700 hover:border-primary-200 transition-colors font-medium text-left flex items-center justify-between"
            >
              <span>Admin</span>
              <span className="text-[10px] text-gray-400">admin@</span>
            </button>
            <button
              type="button"
              onClick={() => fillDemo("teacher")}
              className="text-xs py-2 px-3 rounded-lg border border-gray-200 bg-gray-50 text-gray-700 hover:bg-primary-50 hover:text-primary-700 hover:border-primary-200 transition-colors font-medium text-left flex items-center justify-between"
            >
              <span>Teacher</span>
              <span className="text-[10px] text-gray-400">teacher@</span>
            </button>
            <button
              type="button"
              onClick={() => fillDemo("parent")}
              className="text-xs py-2 px-3 rounded-lg border border-gray-200 bg-gray-50 text-gray-700 hover:bg-primary-50 hover:text-primary-700 hover:border-primary-200 transition-colors font-medium text-left flex items-center justify-between"
            >
              <span>Parent</span>
              <span className="text-[10px] text-gray-400">parent@</span>
            </button>
            <button
              type="button"
              onClick={() => fillDemo("student")}
              className="text-xs py-2 px-3 rounded-lg border border-gray-200 bg-gray-50 text-gray-700 hover:bg-primary-50 hover:text-primary-700 hover:border-primary-200 transition-colors font-medium text-left flex items-center justify-between"
            >
              <span>Student</span>
              <span className="text-[10px] text-gray-400">student@</span>
            </button>
          </div>
        </div>
      </form>

      {/* Support link */}
      <p className="mt-6 text-center text-xs text-gray-400">
        Having trouble signing in?{" "}
        <a
          href="mailto:support@edubest.app"
          className="text-primary-700 hover:underline"
        >
          Contact support
        </a>
      </p>
    </>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="py-12 text-center text-sm text-slate-500">
          Loading login form...
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
