import React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?:
    | "default"
    | "success"
    | "warning"
    | "destructive"
    | "error"
    | "info"
    | "neutral"
    | "outline"
    | "secondary"
    | string;
  children: React.ReactNode;
}

export function Badge({ variant = "default", className, children, ...props }: BadgeProps) {
  const variantStyles: Record<string, string> = {
    default: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
    success: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300",
    warning: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
    destructive: "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-300",
    error: "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-300",
    info: "bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-300",
    neutral: "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300",
    secondary: "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300",
    outline: "border border-slate-300 text-slate-700 dark:border-slate-700 dark:text-slate-300",
  };

  const selectedStyle = variantStyles[variant] || variantStyles.default;

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
        selectedStyle,
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
