"use client";

/**
 * Forgot Password Page
 *
 * Sends a password reset link to the user's email address.
 * Two states:
 *  1. Form view — user enters their email
 *  2. Success view — confirmation with instructions to check email
 */

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft, Mail, Send } from "lucide-react";
import { toast } from "sonner";
import { apiPost } from "@/lib/api";
import { cn } from "@/lib/utils";

/* ── Schema ──────────────────────────────────────────────────────── */
const forgotPasswordSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address"),
});

type ForgotPasswordValues = z.infer<typeof forgotPasswordSchema>;

/* ── Component ───────────────────────────────────────────────────── */
export default function ForgotPasswordPage() {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordValues>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (values: ForgotPasswordValues) => {
    setIsLoading(true);
    try {
      await apiPost("/auth/password/reset/", { email: values.email });
      setSubmittedEmail(values.email);
      setIsSubmitted(true);
    } catch (err: unknown) {
      // We intentionally show a generic success message even on error
      // to prevent email enumeration attacks
      setSubmittedEmail(values.email);
      setIsSubmitted(true);
    } finally {
      setIsLoading(false);
    }
  };

  /* ── Success state ─────────────────────────────────────────────── */
  if (isSubmitted) {
    return (
      <div className="text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
          <Mail className="h-8 w-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900">Check Your Email</h2>
        <p className="mt-3 text-sm text-gray-500">
          If an account exists for{" "}
          <span className="font-medium text-gray-900">{submittedEmail}</span>,
          we&apos;ve sent a password reset link. The link expires in 30 minutes.
        </p>

        <div className="mt-6 rounded-lg bg-blue-50 border border-blue-100 px-4 py-3 text-sm text-blue-700 text-left">
          <p className="font-medium mb-1">Didn&apos;t receive it?</p>
          <ul className="list-disc list-inside space-y-1 text-blue-600 text-xs">
            <li>Check your spam / junk mail folder</li>
            <li>Make sure you entered the correct email</li>
            <li>Wait up to 2 minutes for delivery</li>
          </ul>
        </div>

        <div className="mt-6 space-y-3">
          <button
            onClick={() => setIsSubmitted(false)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Try a different email
          </button>
          <Link
            href="/login"
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-800 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Sign In
          </Link>
        </div>
      </div>
    );
  }

  /* ── Form state ────────────────────────────────────────────────── */
  return (
    <>
      <div className="mb-8">
        <Link
          href="/login"
          className="mb-6 inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to sign in
        </Link>

        <h2 className="text-2xl font-bold text-gray-900">Reset Your Password</h2>
        <p className="mt-2 text-sm text-gray-500">
          Enter the email address associated with your account and we&apos;ll
          send you a secure reset link.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
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
            placeholder="you@yourschool.edu.gh"
            className={cn(
              "input-field",
              errors.email && "border-red-400 focus:border-red-500 focus:ring-red-500",
            )}
          />
          {errors.email && (
            <p className="mt-1.5 text-xs text-red-600">{errors.email.message}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className={cn(
            "flex w-full items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-semibold text-white transition-colors",
            "bg-primary-700 hover:bg-primary-800",
            isLoading && "cursor-not-allowed opacity-70",
          )}
        >
          {isLoading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Sending…
            </>
          ) : (
            <>
              <Send className="h-4 w-4" />
              Send Reset Link
            </>
          )}
        </button>
      </form>
    </>
  );
}
