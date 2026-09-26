/**
 * Auth Layout
 *
 * Centred card design used by login, forgot-password, and reset-password pages.
 * Displays the Edubest logo + school branding on the left panel (desktop)
 * and the form content on the right.
 *
 * Mobile: single column, centred form only.
 */
import Link from "next/link";
import { GraduationCap } from "lucide-react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      {/* ── Left Branding Panel (hidden on mobile) ────────────── */}
      <div className="hidden lg:flex lg:w-1/2 flex-col items-center justify-center bg-gradient-to-br from-primary-950 via-primary-800 to-primary-700 p-12 relative overflow-hidden">
        {/* Decorative blobs */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-32 -left-32 h-64 w-64 rounded-full bg-primary-600 opacity-30 blur-3xl" />
          <div className="absolute -bottom-32 -right-32 h-64 w-64 rounded-full bg-accent-500 opacity-20 blur-3xl" />
        </div>

        <div className="relative max-w-sm text-center">
          {/* Logo icon */}
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-white/10 backdrop-blur">
            <GraduationCap className="h-10 w-10 text-white" />
          </div>

          <h1 className="text-3xl font-extrabold text-white">
            Edu<span className="text-accent-400">best</span>
          </h1>
          <p className="mt-3 text-blue-200 text-sm leading-relaxed">
            The all-in-one school management platform. Academics, finance,
            attendance, and parent engagement — in one place.
          </p>

          {/* Feature bullets */}
          <div className="mt-8 space-y-3 text-left">
            {[
              "Manage students, classes & timetables",
              "Collect fees & track payments",
              "Generate report cards automatically",
              "Real-time parent & student portals",
            ].map((feature) => (
              <div key={feature} className="flex items-center gap-3">
                <div className="h-5 w-5 shrink-0 rounded-full bg-accent-400 flex items-center justify-center">
                  <svg
                    className="h-3 w-3 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={3}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
                <span className="text-sm text-blue-100">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right Form Panel ────────────────────────────────────── */}
      <div className="flex flex-1 flex-col items-center justify-center px-4 py-12 sm:px-6 lg:px-8 bg-gray-50">
        {/* Mobile-only logo */}
        <div className="mb-8 flex flex-col items-center lg:hidden">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-700 text-white">
            <GraduationCap className="h-6 w-6" />
          </div>
          <span className="mt-2 text-xl font-bold text-gray-900">
            Edu<span className="text-primary-700">best</span>
          </span>
        </div>

        {/* Form card */}
        <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-card">
          {children}
        </div>

        {/* Footer link */}
        <p className="mt-6 text-center text-xs text-gray-400">
          By signing in you agree to our{" "}
          <Link href="/privacy" className="text-primary-700 hover:underline">
            Privacy Policy
          </Link>{" "}
          and{" "}
          <Link href="/terms" className="text-primary-700 hover:underline">
            Terms of Service
          </Link>
          .
        </p>
      </div>
    </div>
  );
}
