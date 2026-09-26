"use client";

import React from "react";
import { useFormContext } from "react-hook-form";
import { cn } from "@/lib/utils";

interface Option {
  value: string;
  label: string;
}

export interface FormFieldProps {
  name?: string;
  label?: string;
  type?: string;
  placeholder?: string;
  options?: Option[];
  error?: string;
  helperText?: string;
  required?: boolean;
  children?: React.ReactNode;
  className?: string;
}

export function FormField({
  name,
  label,
  type = "text",
  placeholder,
  options,
  error: manualError,
  helperText,
  required,
  children,
  className,
}: FormFieldProps) {
  // Gracefully use react-hook-form if rendered within FormProvider
  let formContext: ReturnType<typeof useFormContext> | null = null;
  try {
    formContext = useFormContext();
  } catch {
    formContext = null;
  }

  const registered = formContext && name ? formContext.register(name) : {};
  const fieldError =
    manualError ||
    (formContext && name
      ? (formContext.formState.errors[name]?.message as string | undefined)
      : undefined);

  return (
    <div className={cn("space-y-1.5", className)}>
      {label && (
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          {label}
          {required && <span className="text-rose-500 ml-1">*</span>}
        </label>
      )}

      {children ? (
        children
      ) : type === "select" && options ? (
        <select
          {...registered}
          className={cn(
            "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition-colors focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white",
            fieldError && "border-rose-500 focus:border-rose-500 focus:ring-rose-500"
          )}
        >
          {placeholder && <option value="">{placeholder}</option>}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          type={type}
          placeholder={placeholder}
          {...registered}
          className={cn(
            "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition-colors focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white",
            fieldError && "border-rose-500 focus:border-rose-500 focus:ring-rose-500"
          )}
        />
      )}

      {fieldError ? (
        <p className="text-xs text-rose-500 font-medium">{fieldError}</p>
      ) : helperText ? (
        <p className="text-xs text-slate-500 dark:text-slate-400">{helperText}</p>
      ) : null}
    </div>
  );
}
