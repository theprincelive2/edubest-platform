/**
 * Root Application Layout
 *
 * Wraps every page in:
 *  1. QueryClientProvider  — TanStack Query v5 for all server state
 *  2. ThemeProvider (next-themes) — light/dark toggle
 *  3. Toaster (Sonner) — global toast notifications
 *
 * The <html> lang attribute is set here; the actual <body> font stack
 * comes from Tailwind's fontFamily.sans configuration.
 */

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Edubest — School Management Platform",
    template: "%s | Edubest",
  },
  description:
    "Multi-tenant school management system covering academics, finance, attendance, and parent engagement.",
  keywords: ["school management", "SaaS", "edtech", "student portal", "parent portal"],
  authors: [{ name: "Edubest Technologies" }],
  creator: "Edubest Technologies",
  // Open Graph for link previews
  openGraph: {
    type: "website",
    locale: "en_GH",
    siteName: "Edubest",
    title: "Edubest — Smart School Management",
    description:
      "The all-in-one platform that connects schools, teachers, parents, and students.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
