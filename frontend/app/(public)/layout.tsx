/**
 * Public Route Layout
 *
 * Wraps the public-facing marketing / information pages:
 *  - / (homepage)
 *  - /about, /contact, /admissions (if added later)
 *
 * Provides a shared header with school branding and a footer.
 * Does NOT require authentication.
 */
import Link from "next/link";
import Image from "next/image";

export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      {/* ── Site Header ───────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="page-container flex h-16 items-center justify-between">
          {/* Brand */}
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-700 text-white font-bold text-lg">
              E
            </div>
            <span className="text-xl font-bold text-gray-900">
              Edu<span className="text-primary-700">best</span>
            </span>
          </Link>

          {/* Navigation links */}
          <nav className="hidden items-center gap-6 md:flex">
            <Link
              href="/#features"
              className="text-sm font-medium text-gray-600 hover:text-primary-700 transition-colors"
            >
              Features
            </Link>
            <Link
              href="/#how-it-works"
              className="text-sm font-medium text-gray-600 hover:text-primary-700 transition-colors"
            >
              How It Works
            </Link>
            <Link
              href="/#pricing"
              className="text-sm font-medium text-gray-600 hover:text-primary-700 transition-colors"
            >
              Pricing
            </Link>
            <Link
              href="/contact"
              className="text-sm font-medium text-gray-600 hover:text-primary-700 transition-colors"
            >
              Contact
            </Link>
          </nav>

          {/* Auth CTA */}
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden rounded-md px-4 py-2 text-sm font-medium text-gray-700 hover:text-primary-700 transition-colors md:block"
            >
              Sign In
            </Link>
            <Link
              href="/login"
              className="rounded-md bg-primary-700 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-800 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* ── Page Content ───────────────────────────────────────── */}
      <main className="flex-1">{children}</main>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className="border-t border-gray-100 bg-gray-50">
        <div className="page-container py-12">
          <div className="grid gap-8 md:grid-cols-4">
            {/* Brand column */}
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-700 text-white font-bold">
                  E
                </div>
                <span className="text-lg font-bold text-gray-900">
                  Edu<span className="text-primary-700">best</span>
                </span>
              </div>
              <p className="max-w-sm text-sm text-gray-500 leading-relaxed">
                The all-in-one school management platform trusted by schools
                across Africa. Streamline academics, finance, and communication.
              </p>
            </div>

            {/* Platform links */}
            <div>
              <h3 className="mb-3 text-sm font-semibold text-gray-900">Platform</h3>
              <ul className="space-y-2">
                {["Admin Portal", "Teacher Dashboard", "Parent Portal", "Student Portal"].map((item) => (
                  <li key={item}>
                    <Link href="/login" className="text-sm text-gray-500 hover:text-primary-700 transition-colors">
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Legal links */}
            <div>
              <h3 className="mb-3 text-sm font-semibold text-gray-900">Company</h3>
              <ul className="space-y-2">
                {["About Us", "Privacy Policy", "Terms of Service", "Support"].map((item) => (
                  <li key={item}>
                    <Link href="#" className="text-sm text-gray-500 hover:text-primary-700 transition-colors">
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-8 border-t border-gray-200 pt-8 text-center">
            <p className="text-xs text-gray-400">
              © {new Date().getFullYear()} Edubest Technologies. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
