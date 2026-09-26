/**
 * Public Homepage — Edubest Marketing Site
 *
 * Sections:
 *  1. Hero — headline, sub-copy, CTA buttons, hero image placeholder
 *  2. Statistics — animated counters (schools, students, teachers)
 *  3. Features — three feature cards with icons
 *  4. How It Works — numbered steps
 *  5. Call-to-Action banner — trial / demo request
 */
import Link from "next/link";
import {
  GraduationCap,
  DollarSign,
  Users,
  BarChart3,
  CheckCircle2,
  ArrowRight,
  BookOpen,
  Bell,
  ShieldCheck,
} from "lucide-react";

/* ── Stat item component ─────────────────────────────────────────── */
function StatItem({
  value,
  label,
  suffix = "",
}: {
  value: string;
  label: string;
  suffix?: string;
}) {
  return (
    <div className="text-center">
      <p className="text-4xl font-extrabold text-primary-700 md:text-5xl">
        {value}
        <span className="text-2xl">{suffix}</span>
      </p>
      <p className="mt-1 text-sm font-medium text-gray-500">{label}</p>
    </div>
  );
}

/* ── Feature card component ──────────────────────────────────────── */
function FeatureCard({
  icon: Icon,
  title,
  description,
  accentColor,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
  accentColor: string;
}) {
  return (
    <div className="group relative rounded-2xl border border-gray-100 bg-white p-8 shadow-card transition-all duration-300 hover:shadow-card-hover hover:-translate-y-1">
      <div
        className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl ${accentColor}`}
      >
        <Icon className="h-6 w-6 text-white" />
      </div>
      <h3 className="mb-3 text-lg font-semibold text-gray-900">{title}</h3>
      <p className="text-sm leading-relaxed text-gray-500">{description}</p>
    </div>
  );
}

/* ── Step component ──────────────────────────────────────────────── */
function Step({
  number,
  title,
  description,
}: {
  number: number;
  title: string;
  description: string;
}) {
  return (
    <div className="flex gap-5">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary-700 text-sm font-bold text-white">
        {number}
      </div>
      <div>
        <h4 className="font-semibold text-gray-900">{title}</h4>
        <p className="mt-1 text-sm text-gray-500">{description}</p>
      </div>
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────────────── */
export default function HomePage() {
  return (
    <>
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          HERO SECTION
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-950 via-primary-800 to-primary-700 py-20 md:py-28">
        {/* Background decoration */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-primary-600 opacity-20 blur-3xl" />
          <div className="absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-accent-500 opacity-10 blur-3xl" />
        </div>

        <div className="page-container relative">
          <div className="mx-auto max-w-3xl text-center">
            {/* Badge */}
            <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-blue-100 backdrop-blur">
              <span className="flex h-2 w-2 rounded-full bg-accent-400" />
              Trusted by 500+ Schools Across Africa
            </div>

            {/* Headline */}
            <h1 className="text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl md:text-6xl">
              The Smarter Way to{" "}
              <span className="text-accent-400">Manage Your School</span>
            </h1>

            {/* Sub-copy */}
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-blue-100">
              Edubest brings academics, finance, attendance, results, and parent
              engagement into a single, beautifully designed platform — tailored
              for every school, from primary to senior high.
            </p>

            {/* CTAs */}
            <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Link
                href="/login"
                className="inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 text-base font-semibold text-primary-700 shadow-lg hover:bg-blue-50 transition-colors"
              >
                Start Free Trial
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="#how-it-works"
                className="inline-flex items-center gap-2 rounded-lg border border-white/30 px-6 py-3 text-base font-semibold text-white hover:bg-white/10 transition-colors"
              >
                See How It Works
              </Link>
            </div>

            {/* Social proof */}
            <p className="mt-6 text-xs text-blue-200">
              No credit card required · 30-day free trial · Setup in minutes
            </p>
          </div>

          {/* Hero visual — dashboard preview placeholder */}
          <div className="mx-auto mt-16 max-w-4xl">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm shadow-2xl">
              <div className="grid grid-cols-4 gap-3 mb-3">
                {[
                  { label: "Students", value: "1,248", color: "bg-blue-500" },
                  { label: "Teachers", value: "86", color: "bg-emerald-500" },
                  { label: "Collected", value: "₵128K", color: "bg-amber-500" },
                  { label: "Attendance", value: "94%", color: "bg-purple-500" },
                ].map((s) => (
                  <div
                    key={s.label}
                    className="rounded-xl bg-white/10 p-4 text-center"
                  >
                    <div
                      className={`mx-auto mb-2 h-2 w-8 rounded-full ${s.color}`}
                    />
                    <p className="text-lg font-bold text-white">{s.value}</p>
                    <p className="text-xs text-blue-200">{s.label}</p>
                  </div>
                ))}
              </div>
              <div className="rounded-xl bg-white/5 p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-blue-200">Fee Collection — This Term</span>
                  <span className="text-xs text-blue-300">Jan–Apr 2026</span>
                </div>
                {/* Mini bar chart visual */}
                <div className="flex items-end gap-2 h-16">
                  {[60, 80, 55, 90, 70, 95, 65, 85, 75, 100, 88, 92].map(
                    (h, i) => (
                      <div
                        key={i}
                        className="flex-1 rounded-sm bg-primary-400 opacity-80"
                        style={{ height: `${h}%` }}
                      />
                    ),
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          STATISTICS
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="border-b border-gray-100 bg-white py-12">
        <div className="page-container">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            <StatItem value="500" suffix="+" label="Schools Onboarded" />
            <StatItem value="120" suffix="K+" label="Active Students" />
            <StatItem value="8" suffix="K+" label="Educators" />
            <StatItem value="99.9" suffix="%" label="Uptime SLA" />
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          FEATURES
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section id="features" className="section bg-gray-50">
        <div className="page-container">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Everything Your School Needs
            </h2>
            <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto">
              From student registration to report card generation, Edubest
              covers every workflow so your staff can focus on education.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            <FeatureCard
              icon={GraduationCap}
              title="Academic Excellence"
              description="Manage classes, subjects, timetables, exams, and results in one place. Auto-generate report cards with your custom grading scale."
              accentColor="bg-primary-700"
            />
            <FeatureCard
              icon={DollarSign}
              title="Smart Finance"
              description="Create fee structures, generate invoices, track payments, and send automated reminders. Full audit trail for every naira/cedi collected."
              accentColor="bg-secondary-600"
            />
            <FeatureCard
              icon={Users}
              title="Parent Engagement"
              description="Give parents real-time access to their child's results, attendance, and fee statements. Direct messaging keeps everyone connected."
              accentColor="bg-accent-500"
            />
            <FeatureCard
              icon={BarChart3}
              title="Powerful Analytics"
              description="Visual dashboards for administrators with attendance trends, fee collection progress, and academic performance heatmaps."
              accentColor="bg-purple-600"
            />
            <FeatureCard
              icon={Bell}
              title="Smart Notifications"
              description="Automated SMS and email alerts for exam schedules, fee due dates, low attendance, and school announcements."
              accentColor="bg-rose-600"
            />
            <FeatureCard
              icon={ShieldCheck}
              title="Enterprise Security"
              description="Role-based access control, complete audit logging, data encryption at rest and in transit, and GDPR-compliant data handling."
              accentColor="bg-teal-600"
            />
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          HOW IT WORKS
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section id="how-it-works" className="section bg-white">
        <div className="page-container">
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 md:text-4xl">
                Up and Running in Minutes
              </h2>
              <p className="mt-4 text-gray-500">
                Our onboarding wizard guides you through setup step by step.
                No technical expertise required.
              </p>

              <div className="mt-10 space-y-6">
                <Step
                  number={1}
                  title="Create Your School Account"
                  description="Register your school and get a unique subdomain (e.g. yourschool.edubest.app) instantly."
                />
                <Step
                  number={2}
                  title="Import Your Data"
                  description="Upload students, teachers, and classes via CSV or our guided registration forms."
                />
                <Step
                  number={3}
                  title="Configure Your Settings"
                  description="Set academic years, terms, grading scales, and fee structures to match your school's system."
                />
                <Step
                  number={4}
                  title="Invite Your Team"
                  description="Add admin staff, teachers, and send parent/student portal invitations in bulk."
                />
              </div>
            </div>

            <div className="rounded-2xl bg-gradient-to-br from-primary-50 to-blue-100 p-8">
              <div className="space-y-4">
                {[
                  { icon: CheckCircle2, text: "Multi-school multi-tenant architecture" },
                  { icon: CheckCircle2, text: "Automatic data isolation per school" },
                  { icon: CheckCircle2, text: "Daily automated database backups" },
                  { icon: CheckCircle2, text: "Custom branding with school logo & colours" },
                  { icon: CheckCircle2, text: "Works on any device — mobile, tablet, PC" },
                  { icon: CheckCircle2, text: "Offline-capable PWA for poor connectivity" },
                  { icon: CheckCircle2, text: "Dedicated customer support & training" },
                  { icon: CheckCircle2, text: "Regular free feature updates" },
                ].map(({ icon: Icon, text }) => (
                  <div key={text} className="flex items-center gap-3">
                    <Icon className="h-5 w-5 shrink-0 text-secondary-600" />
                    <span className="text-sm text-gray-700">{text}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          CALL TO ACTION
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="bg-primary-700 py-16">
        <div className="page-container text-center">
          <h2 className="text-3xl font-bold text-white md:text-4xl">
            Ready to Transform Your School?
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-blue-100">
            Join hundreds of schools already saving hours every week. Start your
            free 30-day trial today — no credit card, no lock-in.
          </p>
          <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-lg bg-white px-8 py-3.5 text-base font-semibold text-primary-700 shadow-lg hover:bg-blue-50 transition-colors"
            >
              Start Free Trial
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="mailto:demo@edubest.app"
              className="inline-flex items-center gap-2 rounded-lg border-2 border-white/50 px-8 py-3.5 text-base font-semibold text-white hover:bg-white/10 transition-colors"
            >
              Request a Demo
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
